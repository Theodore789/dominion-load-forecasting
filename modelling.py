import pandas as pd
from pathlib import Path


def score(pred, y):

    err = pred - y
    
    mae = (err).abs().mean()
    rmse = ((err).mean()) ** 0.5
    mape = ((((err) / y).abs().mean())) * 100
    me = (err).mean()

    top = y >= y.quantile(0.95)
    mae_top5 = (err[top]).abs().mean()
    
    return {"MAE": mae, 
            "RMSE": rmse, 
            "MAP": mape, 
            "ME": me, 
            "MAE_TOP5":mae_top5
            }


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

print(score(pred[m], y[m]))

print(y["2022-12-31"].mean(), y["2023-12-31"].mean()) # sanity check