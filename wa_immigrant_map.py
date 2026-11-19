import json
import urllib.request
from pathlib import Path

import branca.colormap as cm
import folium
import pandas as pd

MERGED_FILE = "worksource_immigrant_merged.csv"
GEOJSON_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/"
    "geojson-counties-fips.json"
)
GEOJSON_CACHE = "wa_counties.geojson"
OUTPUT_MAP = "wa_immigrants_per_center_map.html"

WA_STATE_FIPS = "53"
NO_CENTER_COLOR = "#bdbdbd"


def load_merged_data(path: str) -> pd.DataFrame:
    """
    Load the merged WorkSource / immigrant population CSV.
    """
    return pd.read_csv(path)


def load_wa_geojson(url: str, cache_path: str) -> dict:
    """
    Download US county boundaries (cached locally) and keep only Washington.
    """
    cache = Path(cache_path)
    if cache.exists():
        return json.loads(cache.read_text())

    with urllib.request.urlopen(url) as response:
        us_counties = json.load(response)

    wa_features = [
        f for f in us_counties["features"]
        if f["properties"]["STATE"] == WA_STATE_FIPS
    ]
    wa_geojson = {"type": "FeatureCollection", "features": wa_features}
    cache.write_text(json.dumps(wa_geojson))
    return wa_geojson


def attach_data(geojson: dict, data: pd.DataFrame) -> dict:
    """
    Copy each county's data into its GeoJSON feature so it can drive color
    and tooltips.
    """
    lookup = data.set_index("County").to_dict(orient="index")

    missing = [f["properties"]["NAME"] for f in geojson["features"]
               if f["properties"]["NAME"] not in lookup]
    assert not missing, f"Counties in GeoJSON with no matching data: {missing}"

    for feature in geojson["features"]:
        name = feature["properties"]["NAME"]
        row = lookup[name]
        per_center = row["Immigrants per Location"]
        has_center = row["WorkSource Locations"] > 0

        feature["properties"].update({
            "county": f"{name} County",
            "population": f"{row['Total Population']:,}",
            "immigrants": f"{row['Immigrant (Foreign-Born) Population']:,}",
            "immigrant_pct": row["Immigrant Percentage"],
            "centers": int(row["WorkSource Locations"]),
            "per_center_value": float(per_center) if has_center else None,
            "per_center_text": (
                f"{per_center:,.0f}" if has_center else "No centers"
            ),
        })
    return geojson


def build_colormap(data: pd.DataFrame) -> cm.StepColormap:
    """
    Quantile-based color scale (the data is heavily skewed by a few large
    counties).
    """
    values = data["Immigrants per Location"].dropna()
    colormap = cm.linear.YlOrRd_09.to_step(
        n=6, data=values, method="quantiles")
    colormap.caption = "Immigrants per WorkSource location"
    return colormap


def create_map(geojson: dict, colormap: cm.StepColormap) -> folium.Map:
    """
    Build the choropleth map with tooltips and a legend.
    """
    wa_map = folium.Map(location=[47.4, -120.5],
                        zoom_start=7, tiles="OpenStreetMap")

    def style_function(feature):
        value = feature["properties"]["per_center_value"]
        return {
            "fillColor": (
                colormap(value) if value is not None else NO_CENTER_COLOR
            ),
            "color": "#555555",
            "weight": 1,
            "fillOpacity": 0.8,
        }

    tooltip = folium.GeoJsonTooltip(
        fields=["county", "population", "immigrants",
                "immigrant_pct", "centers", "per_center_text"],
        aliases=["County", "Total population", "Immigrants", "Immigrant %",
                 "WorkSource locations", "Immigrants per location"],
        sticky=True,
    )

    folium.GeoJson(
        geojson,
        name="Washington counties",
        style_function=style_function,
        highlight_function=lambda _: {"weight": 3, "color": "#000000"},
        tooltip=tooltip,
    ).add_to(wa_map)

    colormap.add_to(wa_map)
    wa_map.get_root().html.add_child(folium.Element(_no_center_legend()))
    return wa_map


def _no_center_legend() -> str:
    """
    Small legend entry explaining the gray counties.
    """
    return (
        (
            '<div style="position: fixed; bottom: 50px; left: 20px; '
            'z-index: 9999; background: white; padding: 6px 10px; border: '
            '1px solid #999; font-size: 13px;"><span style="background:'
            f'{NO_CENTER_COLOR}'
            '; display:inline-block; width:14px; height:14px; '
            'margin-right:6px; vertical-align:middle;"></span>No '
            'WorkSource location</div>'
        )
    )


def main() -> None:
    data = load_merged_data(MERGED_FILE)
    geojson = load_wa_geojson(GEOJSON_URL, GEOJSON_CACHE)
    geojson = attach_data(geojson, data)
    colormap = build_colormap(data)
    wa_map = create_map(geojson, colormap)
    wa_map.save(OUTPUT_MAP)
    print(f"Map saved to {OUTPUT_MAP}")


if __name__ == "__main__":
    main()
