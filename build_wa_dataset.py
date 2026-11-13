"""
Builds a tidy dataset on immigrant demographics in Washington State from
the ACS 2024 1-year DP02 export.

Outputs (long format, one row per topic x place x group):
  wa_immigrant_long.csv     all topics in one table
  wa_region_of_birth.csv    foreign-born population by world region of birth
  wa_ancestry.csv           ancestry groups (with an assigned world region)
  wa_language.csv           language spoken at home
  wa_context.csv            population, foreign-born, and citizenship totals
"""
import pandas as pd

SRC = "ACSDP1Y2024_DP02-2026-11-12T224500.csv"

# Approximate map locations (for folium markers), NOT boundaries.
GEO = {
    "Washington":  ("state",  47.50, -120.50),
    "King County": ("county", 47.49, -121.80),
    "Seattle city": ("city",  47.6062, -122.3321),
}

# Ancestry groups -> world region. These assignments are mine, not the
# Census Bureau's. "American" and "Arab" do not fit one region.
ANCESTRY_REGION = {
    "Czech": "Europe", "Danish": "Europe", "Dutch": "Europe",
    "English": "Europe", "French (except Basque)": "Europe",
    "German": "Europe", "Greek": "Europe", "Hungarian": "Europe",
    "Irish": "Europe", "Italian": "Europe", "Lithuanian": "Europe",
    "Norwegian": "Europe", "Polish": "Europe", "Portuguese": "Europe",
    "Russian": "Europe", "Scotch-Irish": "Europe", "Scottish": "Europe",
    "Slovak": "Europe", "Swedish": "Europe", "Swiss": "Europe",
    "Ukrainian": "Europe", "Welsh": "Europe",
    "French Canadian": "Northern America",
    "Subsaharan African": "Africa",
    "West Indian (excluding Hispanic origin groups)": "Latin America",
}


def load_long(path):
    """Raw file -> one row per label x place x measure, numeric values."""
    raw = pd.read_csv(path, encoding="utf-8-sig")
    clean = raw["Label (Grouping)"].str.replace("\xa0", " ")
    raw["label"] = clean.str.strip()
    raw["section"] = raw["label"].where(
        raw["Washington!!Estimate"].isna()).ffill()
    # Order of the row inside its section, used to match child rows
    raw["order"] = raw.groupby("section").cumcount()

    value_cols = [c for c in raw.columns if "!!" in c]
    long = raw.melt(id_vars=["section", "order", "label"],
                    value_vars=value_cols, var_name="col",
                    value_name="value")
    long[["geography", "measure"]] = long["col"].str.split("!!", expand=True)
    long["value"] = pd.to_numeric(
        long["value"].str.replace(",", "").str.replace("%", ""),
        errors="coerce")
    return long.drop(columns="col").dropna(subset=["value"])


def section_table(long, section):
    """One row per label x place with estimate and percent columns."""
    rows = long[long["section"] == section]
    wide = rows.pivot_table(index=["geography", "order", "label"],
                            columns="measure", values="value").reset_index()
    wide = wide.rename(columns={"Estimate": "estimate", "Percent": "percent"})
    return wide.sort_values(["geography", "order"])


def with_geo(df):
    """Adds geo_type, lat, and lon columns."""
    df["geography"] = df["geography"].str.replace(", Washington", "")
    df["geo_type"] = df["geography"].map(lambda g: GEO[g][0])
    df["lat"] = df["geography"].map(lambda g: GEO[g][1])
    df["lon"] = df["geography"].map(lambda g: GEO[g][2])
    return df


def region_of_birth(long):
    t = section_table(long, "WORLD REGION OF BIRTH OF FOREIGN-BORN")
    base = (t[t["label"].str.startswith("Foreign-born population")]
            .set_index("geography")["estimate"])
    t = t[~t["label"].str.startswith("Foreign-born population")].copy()
    t["topic"] = "region_of_birth"
    t["group"] = t["label"]
    t["region"] = t["group"]
    t["base_population"] = t["geography"].map(base)
    t["percent_of"] = "foreign-born population"
    return t


def ancestry(long):
    t = section_table(long, "ANCESTRY")
    base = (t[t["label"] == "Total population"]
            .set_index("geography")["estimate"])
    t = t[t["label"] != "Total population"].copy()
    t["topic"] = "ancestry"
    t["group"] = t["label"]
    t["region"] = t["group"].map(ANCESTRY_REGION)
    t["base_population"] = t["geography"].map(base)
    t["percent_of"] = "total population"
    return t


def language(long):
    t = section_table(long, "LANGUAGE SPOKEN AT HOME")
    base = (t[t["label"] == "Population 5 years and over"]
            .set_index("geography")["estimate"])
    t = t[t["label"] != "Population 5 years and over"].copy()
    # "Speak English less than very well" rows belong to the row above
    is_lep = t["label"].str.startswith("Speak English less than")
    t["parent"] = t["label"].where(~is_lep)
    t["parent"] = t.groupby("geography")["parent"].ffill()
    lep = (t[is_lep].set_index(["geography", "parent"])["estimate"]
           .rename("limited_english_estimate"))
    t = t[~is_lep].join(lep, on=["geography", "parent"])
    t["topic"] = "language"
    t["group"] = t["label"]
    t["is_subtotal"] = t["group"] == "Language other than English"
    t["region"] = None
    t["base_population"] = t["geography"].map(base)
    t["percent_of"] = "population 5 and over"
    return t


def context(long):
    """Total population, foreign-born, and citizenship totals."""
    pob = section_table(long, "PLACE OF BIRTH")
    cit = section_table(long, "U.S. CITIZENSHIP STATUS")
    total = (pob[pob["label"] == "Total population"]
             .set_index("geography")["estimate"])
    keep = pob[pob["label"].isin(["Total population", "Foreign-born"])]
    keep = keep.assign(topic="context")
    cit = cit[cit["label"] != "Foreign-born population"].copy()
    cit["topic"] = "citizenship"
    out = pd.concat([keep, cit])
    out["group"] = out["label"]
    out["region"] = None
    out["base_population"] = out["geography"].map(total)
    out["percent_of"] = "total population"
    # Citizenship percents are shares of the foreign-born population
    fb = (pob[pob["label"] == "Foreign-born"]
          .set_index("geography")["estimate"])
    is_cit = out["topic"] == "citizenship"
    out.loc[is_cit, "base_population"] = out.loc[is_cit, "geography"].map(fb)
    out.loc[is_cit, "percent_of"] = "foreign-born population"
    # The total row's percent repeats its count; make it 100
    out.loc[out["label"] == "Total population", "percent"] = 100.0
    return out


COLS = ["topic", "geography", "geo_type", "lat", "lon", "group", "region",
        "estimate", "percent", "percent_of", "base_population",
        "is_subtotal", "limited_english_estimate"]


def main():
    long = load_long(SRC)
    tables = {
        "wa_region_of_birth": region_of_birth(long),
        "wa_ancestry": ancestry(long),
        "wa_language": language(long),
        "wa_context": context(long),
    }
    parts = []
    for name, t in tables.items():
        t = with_geo(t)
        if "is_subtotal" not in t:
            t["is_subtotal"] = False
        t["is_subtotal"] = t["is_subtotal"].fillna(False).astype(bool)
        if "limited_english_estimate" not in t:
            t["limited_english_estimate"] = pd.NA
        t = t[COLS].reset_index(drop=True)
        t["percent"] = t["percent"].round(1)
        t.to_csv(f"{name}.csv", index=False)
        parts.append(t)
    pd.concat(parts, ignore_index=True).to_csv(
        "wa_immigrant_long.csv", index=False)


if __name__ == "__main__":
    main()
