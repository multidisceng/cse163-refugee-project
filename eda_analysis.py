import pandas as pd
import seaborn as sns

data = pd.read_csv("refugees_wa_vs_us_long.csv")
print(data.head())

# Filter for Nationality
filtered = data.loc[data["category"] == "Nationality"]
print(filtered.head())

# Plot Nationality
chart = sns.catplot(
    data=filtered,
    x="share_pct",
    y="group",
    hue="geography",
    hue_order=["Washington", "United States"],
    palette=["#0072B2", "#D55E00"],
    kind="bar",
    errorbar=None,
    height=5,
    aspect=1.55,
    legend_out=False,
)
chart.set_axis_labels("Share of refugee arrivals (%)", "Nationality")
chart.figure.suptitle(
    "Refugee arrivals by reported nationality, FY2018–FY2024"
)
sns.move_legend(
    chart, "upper center", bbox_to_anchor=(0.5, 0.92),
    ncol=2, title=None, frameon=False,
)
chart.figure.subplots_adjust(top=0.80)
chart.ax.set_xlim(0, 40)
chart.savefig("nationality.png", dpi=200)
chart.savefig("nationality.png")


# Filter for Primary Language
filtered2 = data.loc[data["category"] == "Primary language"]
print(filtered2.head())

# Plot Primary Language
chart = sns.catplot(
    data=filtered2,
    x="share_pct",
    y="group",
    hue="geography",
    hue_order=["Washington", "United States"],
    palette=["#0072B2", "#D55E00"],
    kind="bar",
    errorbar=None,
    height=5,
    aspect=1.55,
    legend_out=False,
)
chart.set_axis_labels("Share of refugee arrivals (%)", "Primary language")
chart.figure.suptitle(
    "Refugee arrivals by reported primary language, FY2018–FY2024"
)
sns.move_legend(
    chart, "upper center", bbox_to_anchor=(0.5, 0.92),
    ncol=2, title=None, frameon=False,
)
chart.figure.subplots_adjust(top=0.80)
chart.ax.set_xlim(0, 40)
chart.savefig("primary_language.png", dpi=200)
chart.savefig("primary_language.png")



