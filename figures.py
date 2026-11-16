from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import StrMethodFormatter, MaxNLocator

plt.rcParams["font.size"] = 8
plt.rcParams.update({"font.family": "serif", 
                     "font.serif": "cmr10", 
                     "mathtext.fontset": "cm", 
                     "axes.unicode_minus": False, 
                     "axes.formatter.use_mathtext": True})

MODEL_COLOURS = {"linear": "#e76f51", "A": "grey", "B": "#7b5ea7", "C": "#1f3b5c", "MLP": "#2a9d8f"}

HERE = Path(__file__).parent
df = pd.read_csv(HERE / "data" / "features.csv", index_col=0, parse_dates=True)

local = df.index.tz_convert("America/New_York")  # day D = Virginia local day
y = df["Demand (MW)"]


# Figure 1: the maximum hourly demand of each day of each year (2018-2026)

daily_max = y.groupby(local.date).max()
daily_max.index = pd.to_datetime(daily_max.index)
train_max = y[local.year <= 2022].max()

floor = daily_max.rolling(365, center=True, min_periods=330).quantile(0.05)

fig, ax = plt.subplots(figsize=(3.2, 2.4))
ax.plot(daily_max.index, daily_max.values, linewidth=0.6, label="daily peak", color="#1f3b5c")  # daily peak demand plot

ax.plot(floor, linestyle="-", color="red", linewidth=1,  # floor line plot
           label=f"floor (rolling 1-year 5th percentile)")

fl = floor.dropna()
ax.text(daily_max.index.max() + pd.Timedelta(days=20), fl.iloc[-1], 
        "floor", color="red", ha="left", va="center", fontsize=8)

ax.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2024-01-01"), alpha=0.15, color="grey", label="validation (2023)")
ax.axvspan(pd.Timestamp("2024-01-01"), pd.Timestamp("2026-10-01"), alpha=0.15, color="#f4a261", label="test (2024-2026)")

ax.axhline(train_max, linestyle="--", color="black", linewidth=1,  # training-max line
           label=f"training max ({train_max:,.0f} MW)")

ax.set_ylabel("Daily peak demand (MW)")
ax.set_xlim(daily_max.index.min(), pd.Timestamp("2026-12-31"))
ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
ax.spines[["top", "right"]].set_visible(False)

ax.text(pd.Timestamp("2023-07-01"), 25500, "validation", ha="center", fontsize=8)
ax.text(pd.Timestamp("2025-05-01"), 25500, "test", ha="center", fontsize=8)
ax.text(daily_max.index.min(), train_max + 100, "training max", va="bottom", fontsize=8)


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

years = [2019, 2025]
fig2, ax2 = plt.subplots(figsize=(3.2, 2.4))

keep = (local.year >= 2019) & (local.year <= 2025)
sc = plt.scatter(df["temp_mean"][keep], y[keep], c=local.year[keep], 
                 cmap="viridis", s=0.3, alpha=0.4, rasterized=True)

for year in years:
      ls = "--" if year == 2019 else "-"
      ax2.plot(curve.index, curve[year], linestyle=ls, linewidth=3)
      last = curve[year].last_valid_index()
      ax2.text(last + 0.5, curve[year][last], str(year),
               fontsize=8, va="center")
      
      ax2.plot(curve.index, curve[year], linestyle=ls, color="black", linewidth=1.2)
      ax2.text(last + 0.5, curve[year][last], str(year), 
               color="black", fontsize=8, va="center")


ax2.set_xlabel(r"Temperature ($^\circ$C)")
ax2.set_ylabel("Hourly demand (MW)", labelpad=8)
ax2.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
ax2.spines[["top", "right"]].set_visible(False)
ax2.set_xlim(curve.index.min() - 1, curve.index.max() + 4)

gap = curve[2025] - curve[2019]
print(gap.loc[[0, 15, 30]].round(0))

fig2.colorbar(sc, ax=ax2, fraction=0.05, pad=0.02, label="Year", ticks=[2019, 2021, 2023, 2025])

fig2.savefig(HERE / "figures" / "fig2_temperature.pdf", bbox_inches="tight")
fig2.savefig(HERE / "figures" / "fig2_temperature.png", dpi=300, bbox_inches="tight")


# Figure 3: model forecasts on test vs true demand diagonal line

f = pd.read_csv(HERE / "data" / "test_forecasts.csv", index_col=0, parse_dates=True)
rec_f = f[f["record"]]
lo, hi = rec_f["y"].min(), rec_f["y"].max()
rec_gw = rec_f[["y", "A", "B", "C"]] / 1000
lo_gw, hi_gw = lo / 1000, hi / 1000
max_gw = train_max / 1000 

fig3, ax3 = plt.subplots(1, 3, figsize=(3.2, 2.4), sharex=True, sharey=True, layout="constrained")

for ax, arm in zip(ax3, ["A", "B", "C"]):
      ax.scatter(rec_gw["y"], rec_gw[arm], s=5, alpha=0.4, color=MODEL_COLOURS[arm])
      ax.plot([lo_gw, hi_gw], [lo_gw, hi_gw], "k--", linewidth=1)
      ax.axhline(max_gw, linestyle=":", color="grey", linewidth=1)
      me = (rec_f["y"] - rec_f[arm]).mean() 
      ax.set_title(f"{arm}: ME = {me:,.0f}", fontsize=9)
      
      ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
      ax.yaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
      ax.yaxis.set_major_locator(MaxNLocator(3))
      ax.xaxis.set_major_locator(MaxNLocator(3))
      ax.spines[["top", "right"]].set_visible(False)

ax3[0].set_ylabel("Forecast (GW)")
fig3.supxlabel("Actual (GW)")
ax3[0].text(hi_gw, max_gw + 0.15, "training max", ha="right", fontsize=7, color="grey")

assert len(rec_f) == 389

fig3.savefig(HERE / "figures" / "fig3_rec_hours.pdf", bbox_inches="tight")
fig3.savefig(HERE / "figures" / "fig3_rec_hours.png", dpi=300, bbox_inches="tight")


# Figure 4: monthly test bias by model

fig4, ax4 = plt.subplots(figsize=(3.2, 2.4), layout="constrained")

models = ["linear", "A", "C", "MLP"]
errs = pd.DataFrame({m: f["y"] - f[m] for m in models})

month = f.index.tz_convert("America/New_York").to_period("M")
monthly = errs.groupby(month).mean()
monthly.index = monthly.index.to_timestamp()


offsets = {"linear": 0, "A": 0, "C": 150, "MLP": -150}

for m in models:
      a = 0.5 if m == "A" else 1.0
      ax4.plot(monthly.index, monthly[m], color=MODEL_COLOURS[m], linewidth=1.5, alpha=a)
      ax4.text(monthly.index[-1], monthly[m].iloc[-1] + offsets[m], 
               f" {m}",color=MODEL_COLOURS[m], alpha=a, fontsize=8, va="center")

ax4.axhline(0, color="black", linewidth=0.8)
ax4.set_ylabel("Monthly ME (MW)")
ax4.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
ax4.xaxis.set_major_locator(mdates.YearLocator())
ax4.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax4.spines[["top", "right"]].set_visible(False)
ax4.set_xlim(right=monthly.index[-1] + pd.Timedelta(days=60))

print(errs.mean().round(2))  # sanity check

fig4.savefig(HERE / "figures" / "fig4_ME.pdf", bbox_inches="tight")
fig4.savefig(HERE / "figures" / "fig4_ME.png", dpi=300, bbox_inches="tight")