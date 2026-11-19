"""
Folium map: WA counties colored by strain (applicants per WorkSource office).
Inputs (same folder): county_bins_strain.csv (County, Bin, Strain_Bin), worksource_locs.csv
Optional cache: worksource_geocoded.csv (created on first run by geocoding addresses)
Output: wa_strain_map.html
"""
import json, os, re, urllib.request
import folium
import pandas as pd

GEOJSON_URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
GEOCODE_CACHE = "worksource_geocoded.csv"

# Strain levels: label -> (fill color, plain-language meaning)
LEVELS = {
    "Very high (over 300)":      ("#4A1486", "Over 300 new applicants for each WorkSource office"),
    "High (101 - 300)":          ("#807DBA", "101 to 300 applicants per office"),
    "Moderate (25 - 100)":       ("#BCBDDC", "25 to 100 applicants per office"),
    "Low (under 25 per office)": ("#EFEDF5", "Under 25 applicants per office, including counties with fewer than 10 applicants"),
    "Applicants, no office":     ("#FFFFFF", "Has applicants but no WorkSource office in the county"),
    "No applicants":             ("#DADADA", "No newly arrived applicants recorded"),
}
GAP = "Applicants, no office"
GAP_OUTLINE = "#D95F02"

counties = pd.read_csv("county_bins_strain.csv").rename(columns={"Bin": "Applicants_Bin"})
worksource = pd.read_csv("worksource_locs.csv")
counties["Offices"] = counties["County"].map(worksource.groupby("County").size()).fillna(0).astype(int)
info = counties.set_index("County").to_dict("index")

# ---------- boundaries ----------
with urllib.request.urlopen(GEOJSON_URL) as r:
    us = json.load(r)
wa = {"type": "FeatureCollection",
      "features": [f for f in us["features"] if str(f["id"]).startswith("53")]}
for f in wa["features"]:
    i = info[f["properties"]["NAME"]]
    f["properties"].update(Strain=i["Strain_Bin"], Applicants=i["Applicants_Bin"], Offices=int(i["Offices"]))

def style(f):
    s = f["properties"]["Strain"]; gap = s == GAP
    return {"fillColor": LEVELS[s][0], "fillOpacity": 0.85,
            "color": GAP_OUTLINE if gap else "#555555", "weight": 3 if gap else 0.8,
            "dashArray": "6 4" if gap else None}

m = folium.Map(location=[47.4, -120.7], zoom_start=7, tiles="OpenStreetMap")
folium.GeoJson(
    wa, name="Strain level", style_function=style,
    highlight_function=lambda f: {"weight": 3, "color": "#000000"},
    tooltip=folium.GeoJsonTooltip(
        fields=["NAME", "Strain", "Applicants", "Offices"],
        aliases=["County:", "Strain level:", "Applicants (bin):", "WorkSource offices:"]),
).add_to(m)

# ---------- office points ----------
def clean(a):
    a = re.sub(r"^\d+\.\s*", "", a)
    return re.sub(r",\s*(Suite|Ste\.?|Unit|Room|Rm\.?|Floor|Fl\.?|#)[^,]*", "", a, flags=re.I).strip()

def offices():
    if os.path.exists(GEOCODE_CACHE):
        return pd.read_csv(GEOCODE_CACHE)
    from geopy.extra.rate_limiter import RateLimiter
    from geopy.geocoders import Nominatim
    df = worksource.copy()
    df["Address"] = df["Location"].map(clean)
    g = RateLimiter(Nominatim(user_agent="wa-worksource-strain-map").geocode, min_delay_seconds=1.1)
    loc = df["Address"].map(g)
    df["lat"] = loc.map(lambda l: l.latitude if l else None)
    df["lon"] = loc.map(lambda l: l.longitude if l else None)
    bad = df[df["lat"].isna()]
    if len(bad): print(f"{len(bad)} addresses failed to geocode:\n", bad[["Address", "County"]])
    df.to_csv(GEOCODE_CACHE, index=False)
    return df

layer = folium.FeatureGroup(name="WorkSource offices")
for _, r in offices().dropna(subset=["lat", "lon"]).iterrows():
    folium.CircleMarker([r["lat"], r["lon"]], radius=4, color="#222", weight=1, fill=True,
                        fill_color="#FFB000", fill_opacity=0.75,
                        popup=folium.Popup(f"{r['Address']}<br><i>{r['County']} County</i>", max_width=250)).add_to(layer)
layer.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

# ---------- legend with meanings ----------
rows = ""
for label, (color, meaning) in LEVELS.items():
    gap = label == GAP
    border = f"2px dashed {GAP_OUTLINE}" if gap else "1px solid #777"
    name = label.split(" (")[0] if "(" in label else label
    rows += (f'<div style="display:flex;gap:8px;margin:5px 0;">'
             f'<span style="flex:none;width:16px;height:16px;background:{color};border:{border};margin-top:2px;"></span>'
             f'<span><b>{name}</b><br><span style="color:#444;">{meaning}</span></span></div>')
legend = f"""
<div style="position:fixed;bottom:25px;left:25px;z-index:9999;background:white;max-width:290px;
            padding:10px 12px;border:1px solid #999;border-radius:4px;font:12px sans-serif;">
  <b style="font-size:13px;">Strain on WorkSource offices</b><br>
  <span style="color:#444;">Newly arrived refugee/humanitarian applicants for DSHS services
  (Oct 2023 - Sep 2024) per WorkSource office in the county.</span>
  <div style="margin-top:6px;">{rows}</div>
  <div style="display:flex;gap:8px;align-items:center;margin-top:4px;">
    <span style="flex:none;width:10px;height:10px;border-radius:50%;background:#FFB000;border:1px solid #222;margin:0 3px;"></span>
    <span>WorkSource office</span></div>
</div>"""
m.get_root().html.add_child(folium.Element(legend))
m.save("wa_strain_map.html")
print("Saved wa_strain_map.html")
