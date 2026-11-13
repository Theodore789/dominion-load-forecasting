from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

plt.rcParams["font.size"] = 9

HERE = Path(__file__).parent
df = pd.read_csv(HERE / "data" / "features.csv", index_col=0, parse_dates=True)

local = df.index.tz_convert("America/New_York")  # day D = Virginia local day
y = df["Demand (MW)"]

# Figure 1: the maximum hourly demand of each day of each year (2018-2026)

daily_max = y.groupby(local.date).max()
daily_max.index = pd.to_datetime(daily_max.index)
train_max = y[local.year <= 2022].max()

floor = daily_max.rolling(365, center=True, min_periods=330).quantile(0.05)

fig, ax = plt.subplots(figsize=(6.5, 2.6))
ax.plot(daily_max.index, daily_max.values, linewidth=0.6, label="daily peak", color="#f4a261")  # daily peak demand plot

ax.plot(floor, linestyle="-", color="red", linewidth=1,  # floor line plot
           label=f"floor (rolling 1-year 5th percentile)")

ax.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2024-01-01"), alpha=0.15, color="grey", label="validation (2023)")
ax.axvspan(pd.Timestamp("2024-01-01"), pd.Timestamp("2026-10-01"), alpha=0.15, color="#f4a261", label="test (2024-2026)")

ax.axhline(train_max, linestyle="--", color="black", linewidth=1,  # training-max line
           label=f"training max ({train_max:,.0f} MW)")

ax.set_ylabel("Daily peak demand (MW)")
ax.set_title("Demand keeps setting new records after the training period")
ax.set_xlim(daily_max.index.min(), daily_max.index.max())
ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
ax.spines[["top", "right"]].set_visible(False)

ax.text(pd.Timestamp("2023-07-01"), 25500, "validation", ha="center", fontsize=8)
ax.text(pd.Timestamp("2025-05-01"), 25500, "test", ha="center", fontsize=8)
ax.text(daily_max.index.min(), train_max + 300, "training max", fontsize=8)
ax.text(pd.Timestamp("2019-03-01"), 9000, "floor (1-yr 5th pct.)", color="red", fontsize=8)


print(f"floor 2019: {floor["2019-07-01"]} MW, floor 2022: {floor["2022-07-01"]} MW, floor 2025: {floor["2025-07-01"]} MW")

rise_2019_2022 = (floor["2022-07-01"] - floor["2019-07-01"]) / floor["2019-07-01"] * 100
rise_2022_2025 = (floor["2025-07-01"] - floor["2022-07-01"]) / floor["2022-07-01"] * 100
rise_2019_2025 = (floor["2025-07-01"] - floor["2019-07-01"]) / floor["2019-07-01"] * 100

print(f"The rise in MW from 2019 to 2022: {round(rise_2019_2022, 2)}%, "
      f"from 2022 to 2025: {round(rise_2022_2025, 2)}%, "
      f"and from 2019 to 2025: {round(rise_2019_2025, 2)}%")

(HERE / "figures").mkdir(exist_ok=True)
fig.savefig(HERE / "figures" / "fig1_demand.pdf", bbox_inches="tight")
print("saved fig1")


# Figure 2: demand vs temperature, by year

