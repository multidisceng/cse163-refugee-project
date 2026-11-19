"""
Folium map: WA counties colored by number of newly arrived refugee/humanitarian
applicants (DSHS, Oct 2023 - Sep 2024), shown in bins.
Input (same folder): MERGED_applicants_worksource.csv (County, Bin, Strain_Bin)
Output: wa_applicants_map.html
"""
import json
import urllib.request

import folium
import pandas as pd

INPUT_FILE = "MERGED_applicants_worksource.csv"
OUTPUT_FILE = "wa_applicants_map.html"
GEOJSON_URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

# Applicant bins, lightest to darkest green (No applicants is grey)
BIN_COLORS = {
    "No applicants": "#DADADA",
    "1 - 9":         "#EDF8E9",
    "10 - 50":       "#C7E9C0",
    "51 - 100":      "#A1D99B",
    "101 - 200":     "#74C476",
    "201 - 500":     "#41AB5D",
    "501 - 2,000":   "#238B45",
    "Over 2,000":    "#00441B",
}


def load_counties():
    df = pd.read_csv(INPUT_FILE)
    return df.set_index("County")["Bin"].to_dict()


def load_boundaries(bins):
    """Washington counties as GeoJSON, with each county's bin attached."""
    with urllib.request.urlopen(GEOJSON_URL) as r:
        us = json.load(r)
    wa = {"type": "FeatureCollection",
          "features": [f for f in us["features"] if str(f["id"]).startswith("53")]}
    for f in wa["features"]:
        f["properties"]["Applicants"] = bins[f["properties"]["NAME"]]
    return wa


def style(feature):
    return {"fillColor": BIN_COLORS[feature["properties"]["Applicants"]],
            "fillOpacity": 0.85, "color": "#555555", "weight": 0.8}


def build_map(wa):
    m = folium.Map(location=[47.4, -120.7], zoom_start=7, tiles="OpenStreetMap")
    folium.GeoJson(
        wa, name="Applicants by county", style_function=style,
        highlight_function=lambda f: {"weight": 3, "color": "#000000"},
        tooltip=folium.GeoJsonTooltip(fields=["NAME", "Applicants"],
                                      aliases=["County:", "Applicants:"]),
    ).add_to(m)
    return m


def add_legend(m):
    rows = ""
    for label, color in reversed(list(BIN_COLORS.items())):
        rows += (f'<div style="display:flex;gap:8px;align-items:center;margin:3px 0;">'
                 f'<span style="flex:none;width:16px;height:16px;background:{color};border:1px solid #777;"></span>'
                 f'<span>{label}</span></div>')
    legend = f"""
    <div style="position:fixed;bottom:25px;left:25px;z-index:9999;background:white;max-width:270px;
                padding:10px 12px;border:1px solid #999;border-radius:4px;font:12px sans-serif;">
      <b style="font-size:13px;">Newly arrived applicants</b><br>
      <span style="color:#444;">Refugee/humanitarian applicants for DSHS services
      by county of residence, Oct 2023 - Sep 2024.</span>
      <div style="margin-top:6px;">{rows}</div>
      <div style="color:#444;margin-top:6px;">Counties with 1 - 9 applicants are hidden by DSHS
      to protect privacy, so they are shown as a range.</div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))


def main():
    bins = load_counties()
    wa = load_boundaries(bins)
    m = build_map(wa)
    add_legend(m)
    folium.LayerControl(collapsed=True).add_to(m)
    m.save(OUTPUT_FILE)
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
