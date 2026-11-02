import pandas as pd
from pathlib import Path
from pandas.tseries.holiday import USFederalHolidayCalendar

HERE = Path(__file__).parent
df = pd.read_csv(HERE / "data" / "dom_merged.csv", index_col=0, parse_dates=True)

# together the asserts guarantee exactly one row per hour
assert not df.index.duplicated().any(), "duplicate timestamps" # no duplicate timestamps
full_range = pd.date_range(df.index.min(), df.index.max(), freq="h")
assert df.index.equals(full_range) # missing hourly rows

df["lag_24"] = df["Demand (MW)"].shift(24) # same hour yesterday
df["lag_48"] = df["Demand (MW)"].shift(48) # same hour 2 days ago
df["lag_168"] = df["Demand (MW)"].shift(168) # same hour last week

# mean of the 168 h ending 24 h before; 143 so a 25 h clock-change gap doesn't give NaN
df["level_7d"] = df["Demand (MW)"].shift(24).rolling(168, min_periods=143).mean() 

# calendar features (EIA index is UTC, hour-ending -> Virginia local time)
df.index = df.index.tz_localize("UTC")
local = df.index.tz_convert("America/New_York")

df["hour"] = local.hour # hour-ending: 8 = 07:00-08:00
df["day_of_week"] = local.day_of_week # 0 = Monday
df["month"] = local.month

# holidays
hols = USFederalHolidayCalendar().holidays(start="2018-01-01", end="2026-12-31")
df["is_holiday"] = local.tz_localize(None).normalize().isin(hols).astype(int) # 1 the local date is a federal holiday

# temperature features (for the linear benchmark)
df["temp_sq"] = df["temp_mean"] ** 2
df["temp_cube"] = df["temp_mean"] ** 3

df.to_csv(HERE / "data" / "features.csv")

print(df.shape, df.columns.tolist())