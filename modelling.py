import pandas as pd
from pathlib import Path

HERE = Path(__file__).parent
df = pd.read_csv(HERE / "data" / "features.csv", index_col=0, parse_dates=True)

print(df.index.tz) # UTC

local = df.index.tz_convert("America/New_York") # day D = Virginia local day

# splits for the model
train = local.year <= 2022
val = local.year == 2023
test = local.year >= 2024

print(train.sum(), val.sum(), test.sum())

# 288 hours have no demand value
has_y = df["Demand (MW)"].notna()
print((train & ~has_y).sum(), (val & ~has_y).sum(), (test & ~has_y).sum())

# every model has to beat the baseline: lag_168 
pred = df["lag_168"]
y = df["Demand (MW)"]
m = val & has_y & pred.notna()

err = pred[m] - y[m]
mae = err.abs().mean()
me = err.mean()

print(m.sum(), mae, me) 