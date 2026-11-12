from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

HERE = Path(__file__).parent
df = pd.read_csv(HERE / "data" / "features.csv", index_col=0, parse_dates=True)

local = df.index.tz_convert("America/New_York")  # day D = Virginia local day
y = df["Demand (MW)"]

# Figure 1: the maximum hourly demand of each day of each year (2018-2026)

daily_max = y.groupby(local.date).max()
daily_max.index = pd.to_datetime(daily_max.index)
train_max = y[local.year <= 2022].max()

floor = daily_max.rolling(365, center=True, min_periods=330).quantile(0.05)

fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(daily_max.index, daily_max.values, linewidth=0.6, label="daily peak")

ax.plot(floor, linestyle="--", color="red", linewidth=2,
           label=f"floor (rolling 1-year 5th percentile)")

ax.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2024-01-01"), alpha=0.15, color="grey", label="validation (2023)")
ax.axvspan(pd.Timestamp("2024-01-01"), pd.Timestamp("2026-10-01"), alpha=0.15, color="blue", label="test (2024-2026)")

ax.axhline(train_max, linestyle="--", color="black", linewidth=1,
           label=f"training max ({train_max:,.0f} MW)")

ax.plot(floor, linestyle="--", color="red", linewidth=1,
           label=f"floor (rolling 1-year 5th percentile)")

ax.set_ylabel("Daily peak demand (MW)")
ax.set_title("Demand keeps setting new records after the training period")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=4, frameon=False)
ax.set_xlim(daily_max.index.min(), daily_max.index.max())
ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))

(HERE / "figures").mkdir(exist_ok=True)
fig.savefig(HERE / "figures" / "fig1_demand.png", dpi=300, bbox_inches="tight")
print("saved fig1")