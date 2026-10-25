import pandas as pd 
import matplotlib.pyplot as plt 
from pathlib import Path

# working on the folder containing the raw files
folder = Path.home() / "Desktop" / "EIA_hourly_demand" # 17 files / tables
files = sorted(folder.glob("*.csv"))

parts = [] # process of combining the 17 tables into 1
for f in files:
    df = pd.read_csv(f, thousands=",")
    dom = df[(df["Balancing Authority"] == "PJM") & (df["Sub-Region"] == "DOM")] # interested only in JPM as the authority and DOM as the sub-region
    parts.append(dom)

load = pd.concat(parts, ignore_index=True) # combination succesful
print(load.shape) # dimensions of our DataFrame

load["UTC Time at End of Hour"] = pd.to_datetime( 
    load["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p")
load = load.set_index("UTC Time at End of Hour")
load = load.sort_index()

print(load.index.min(), load.index.max()) # first and last hour
print(load.index.duplicated().sum())      # hours that appear twice
full = pd.date_range(load.index.min(), load.index.max(), freq="h")
print(len(full.difference(load.index)))   # missing hours
print(load["Demand (MW)"].describe())     # 0s, negatives or absurd values

d = load["Demand (MW)"] 
print(load.shape)
print(d.isna().sum()) # empty values
print(d[d > 30000]) # every posssible value

d[d > 30000] = None
load["Demand (MW)"] = d
gaps = d.isna().groupby(d.notna().cumsum()).sum()
print(gaps[gaps > 0].value_counts().sort_index()) # gap lengths of 1-hour, 2-hours, ...

gap_id = d.notna().cumsum()[d.isna()]
summary = d[d.isna()].index.to_series().groupby(gap_id).agg(["min", "max", "count"])
print(summary[summary["count"] > 23]) # the first and last hour and lenght of every gap of a day or longer

load = load.loc["2018-10-01":"2026-09-30"] # skipping the long gap (July 2018 - September 2018) and stopping at the last full month (September 2026)
d = load["Demand (MW)"]

gap_len = d.isna().groupby(d.notna().cumsum()).transform("sum")
load["Demand (MW)"] = d.interpolate(method="time").where(d.notna() | (gap_len <= 2))
print(load["Demand (MW)"].isna().sum())

out = Path(__file__).parent / "data"
out.mkdir(exist_ok=True)
load[["Demand (MW)"]].to_csv(out / "dom_load_clean.csv") # created from the raw 17 files

# working on the file "weather.csv"
w = pd.read_csv(out / "weather.csv", skiprows=5) # relevant data starts at row 6
w["time"] = pd.to_datetime(w["time"])
w = w.pivot(index="time", columns="location_id", values="temperature_2m (°C)") # long to wide table with pivot()
w.columns = ["ashburn", "richmond", "norfolk"] # the 3 locations
w["temp_mean"] = w.mean(axis=1) # average across each row, one temp for the entire DOM zone

load = pd.read_csv(out / "dom_load_clean.csv", index_col=0, parse_dates=True)
df = load.join(w, how="left") # the joined DataFrame

print(df.shape)
print(df.isna().sum())
df.to_csv(out / "dom_merged.csv") # combined "dom_load_clean.csv" and "weather.csv"

# temperature-demand scatter plot: Demand rises when its either very hot or cold; around 15°C demand is weather dependent-load
plt.scatter(df["temp_mean"], df["Demand (MW)"], c=df.index.year, s=1)
plt.colorbar(label="Year")
plt.xlabel("Temperature (°C)")
plt.ylabel("Demand (MW)")
plt.show()

# line plot: Whether night hours are rising faster than the peak
local = df.index.tz_localize("UTC").tz_convert("America/New_York")
prof = df["Demand (MW)"].groupby([local.year, local.hour]).mean().unstack(0)
prof = prof[list(range(2019, 2026))] # full years only (2019 - 2025)
(prof / prof.mean()).plot(colormap="viridis") # deviding by each year's mean removes the growth so we can compare only the shape of each year
plt.legend(title="Year")
plt.xlabel("Hour ending (Virginia local time)")
plt.ylabel("Demand ÷ that year's mean")
plt.show()

# organising the numbers needed to feed the tree ensembles for my hypothesis
d = df["Demand (MW)"]
train_max = d[:"2022"].max()
test = d["2024":]
print(train_max, (test > train_max).sum(), (test > train_max).mean())
print((test[test > train_max] - train_max).mean()) # 863.3804627249357 MW