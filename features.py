import pandas as pd
from pathlib import Path
HERE = Path(__file__).parent

df = pd.read_csv(HERE/"data"/"dom_merged.csv", index_col=0, parse_dates=True)
print(type(df.index)) # DatetimeIndex

# together the asserts guarantee exactly one row per hour
assert not df.index.duplicated().any(), "duplicate timestamps" # forbids duplicate timestamps, not duplicate values; two hours can have the same demand
full_range = pd.date_range(df.index.min(), df.index.max(), freq="h")
assert df.index.equals(full_range) # checks that no rows (timestamps) are missing

df["lag_24"] = df["Demand (MW)"].shift(24) # demand of the previous day
df["lag_48"] = df["Demand (MW)"].shift(48) # demand of two days prior
df["lag_168"] = df["Demand (MW)"].shift(168) # demand of one week prior

print(df.loc["2024-07-15 12:00"]) # sanity check
print(df.loc["2024-07-14 12:00"])

df["level_7d"] = df["Demand (MW)"].shift(24).rolling(168, min_periods=143).mean() # 143 hours --> about 6 days; still a fair mean
print(df["level_7d"].isna().sum()) # missing hours (NaNs) with 143 minimum periods

# calendar features
df.index = df.index.tz_localize("UTC")
local = df.index.tz_convert("America/New_York")

df["hour"] = local.hour
df["day_of_week"] = local.day_of_week
df["month"] = local.month

print(df.loc["2024-07-15 12:00", ["hour", "day_of_week", "month"]])
print(df.loc["2024-01-15 12:00", ["hour", "day_of_week", "month"]])