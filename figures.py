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
ax.plot(daily_max.index, daily_max.values, linewidth=0.6, label="daily peak", color="#1f3b5c")  # daily peak demand plot

ax.plot(floor, linestyle="-", color="red", linewidth=1,  # floor line plot
           label=f"floor (rolling 1-year 5th percentile)")

ax.text(pd.Timestamp("2019-03-01"), 11000, "floor (1-yr 5th pct.)", color="red", fontsize=8, 
        bbox=dict(facecolor="white", edgecolor="none", pad=1))


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
ax.text(pd.Timestamp("2019-03-01"), 11000, "floor (1-yr 5th pct.)", color="red", fontsize=8)

f19, f22, f25 = floor["2019-07-01"], floor["2022-07-01"], floor["2025-07-01"]
rate_early = (f22 - f19) / 3  # MW per year, Jul 2019 -> Jul 2022
rate_late = (f25 - f22) / 3  # # MW per year, Jul 2022 -> Jul 2025

print(f"floor: {f19:,.0f} MW (2019), {f22:,.0f} MW (2022), {f25:,.0f} (2025) MW")
print(f"rise: {rate_early:,.0f} MW/yr (2019-22) vs {rate_late:,.0f} MW/yr (2022-25), "
      f"{rate_late / rate_early:.2f} x faster")

(HERE / "figures").mkdir(exist_ok=True)
fig.savefig(HERE / "figures" / "fig1_demand.pdf", bbox_inches="tight")
fig.savefig(HERE / "figures" / "fig1_demand.png", dpi=300, bbox_inches="tight")
print("saved fig1")


# Figure 2: demand vs temperature, by year (2019-2025, full years)

temp_bin = df["temp_mean"].round()
curve = y.groupby([local.year, temp_bin]).mean().unstack(0)
counts = y.groupby([local.year, temp_bin]).count().unstack(0)
curve = curve[counts >= 30]

years = [2019, 2021, 2023, 2025]
colors = plt.cm.Blues([0.4, 0.6, 0.7, 1.0])

fig2, ax2 = plt.subplots(figsize=(6.5, 2.6))
for year, c in zip(years, colors):
      ax2.plot(curve.index, curve[year], color=c, linewidth=1.5)
      last = curve[year].last_valid_index()
      ax2.text(last + 0.5, curve[year][last], str(year),
               color=c, fontsize=8, va="center")

ax2.set_xlabel("Temperature (°C)")
ax2.set_ylabel("Mean hourly demand (MW)")
ax2.set_title("The whole temperature-demand curve shifts upward each year")
ax2.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
ax2.spines[["top", "right"]].set_visible(False)














fig2.savefig(HERE / "figures" / "fig2_temperature.pdf", bbox_inches="tight")
fig2.savefig(HERE / "figures" / "fig2_temperature.png", dpi=300, bbox_inches="tight") 