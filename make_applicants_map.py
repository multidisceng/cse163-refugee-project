"""
Folium map: WA counties colored by number of newly arrived refugee/humanitarian
applicants (DSHS, Oct 2023 - Sep 2024), shown in bins.
Input (same folder): MERGED_worksource_applicants.csv (County, Bin, Strain_Bin)
Output: wa_applicants_map.html
"""
import json

import folium
import pandas as pd

INPUT_FILE = "MERGED_worksource_applicants.csv"
OUTPUT_FILE = "wa_applicants_map.html"
BOUNDARIES_FILE = "wa_counties.geojson"

# Applicant bins, lightest to darkest green (No applicants is grey)
BIN_COLORS = {
    "No applicants": "#DADADA",
    "1 - 50 (count unreported)": "#FFF0C2",
    "1 - 9": "#EDF8E9",
    "10 - 50": "#C7E9C0",
    "51 - 100": "#A1D99B",
    "101 - 200": "#74C476",
    "201 - 500": "#41AB5D",
    "501 - 2,000": "#238B45",
    "Over 2,000": "#00441B",
}


def load_counties():
    df = pd.read_csv(INPUT_FILE)
    return df.set_index("County")["Bin"].to_dict()


def load_boundaries(bins):
    """Washington counties as GeoJSON, with each county's bin attached."""
    with open(BOUNDARIES_FILE, encoding="utf-8") as boundaries:
        wa = json.load(boundaries)
    for f in wa["features"]:
        f["properties"]["Applicants"] = bins[f["properties"]["NAME"]]
    return wa


def style(feature):
    return {"fillColor": BIN_COLORS[feature["properties"]["Applicants"]],
            "fillOpacity": 0.85, "color": "#555555", "weight": 0.8}


def build_map(wa):
    m = folium.Map(location=[47.4, -120.7],
                   zoom_start=7, tiles="OpenStreetMap")
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
        rows += ((
            '<div style="display:flex;gap:8px;align-items:center;'
            'margin:3px 0;"><span style="flex:none;width:16px;height:16px;'
            'background:'
            f'{color}'
            ';border:1px solid #777;"></span><span>'
            f'{label}'
            '</span></div>'
        ))
    legend = (
        '\n    <div style="position:fixed;bottom:25px;left:25px;'
        'z-index:9999;background:white;max-width:270px;\n                '
        'padding:10px 12px;border:1px solid #999;border-radius:4px;'
        'font:12px sans-serif;">\n      <b style="font-size:13px;">Newly '
        'arrived applicants</b><br>\n      <span style="color:#444;'
        '">Refugee/humanitarian applicants for DSHS services\n      by '
        'county of residence, Oct 2023 - Sep 2024.</span>\n      <div '
        'style="margin-top:6px;">'
        f'{rows}'
        '</div>\n      <div style="color:#444;margin-top:6px;">Counties '
        'with an asterisk on the DSHS map keep its published 1 - 50 range.'
        '</div>\n    </div>'
    )
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
