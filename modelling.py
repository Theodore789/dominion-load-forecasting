import pandas as pd
import numpy as np
import tabulate
import statsmodels.formula.api as smf
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.base import clone
from pathlib import Path


def score(pred, y):

    err = y - pred
    
    mae = (err).abs().mean()
    rmse = (err ** 2).mean() ** 0.5
    mape = (((err / y).abs().mean())) * 100 
    me = (err).mean()

    top = y >= y.quantile(0.95)
    mae_top5 = (err[top]).abs().mean()
    
    return {"MAE": mae, 
            "RMSE": rmse, 
            "MAPE": mape, 
            "ME": me, 
            "MAE_top5": mae_top5
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

print((train & ~has_y).sum(), 
      (val & ~has_y).sum(), 
      (test & ~has_y).sum()
      )

# every model has to beat the baseline: lag_168 
pred = df["lag_168"]
y = df["Demand (MW)"]
m = val & has_y & pred.notna()

# Professor Tao Hong's vanilla linear benchmark
df["trend"] = np.arange(len(df))

formula  = ('Q("Demand (MW)") ~ trend + C(month)' 
            '+ C(day_of_week):C(hour)' 
            '+ (temp_mean + temp_sq + temp_cube)' 
            '* (C(month) + C(hour))'
            ) 

model = smf.ols(formula, data=df[train & has_y])
results = model.fit() 
lin_pred = results.predict(df)

# The 3 models: raw, difference and real

# Gradient-boosted trees model (raw model)
fit_rows = train & has_y & df["level_7d"].notna()

X_cols = ["lag_24", "lag_48", "lag_168", "level_7d", 
          "hour", "day_of_week", "month", "is_holiday",
          "temp_mean"
          ]

hgb_model = HistGradientBoostingRegressor(max_iter=400, 
                                     learning_rate=0.06, 
                                     early_stopping=False, 
                                     random_state=0
                                     )

hgb_model.fit(df.loc[fit_rows, X_cols], y[fit_rows])
hgb_pred = hgb_model.predict(df[X_cols])
hgb_series = pd.Series(data=hgb_pred, index=df.index)

# the difference target (difference model)
d = y - df["level_7d"]

hgb_diff_model = clone(hgb_model)

hgb_diff_model.fit(df.loc[fit_rows, X_cols], d[fit_rows])
hgb_diff_pred = hgb_diff_model.predict(df[X_cols])
hgb_diff_series = pd.Series(data=hgb_diff_pred, index=df.index)

diff_forecast = df["level_7d"] + hgb_diff_series

print(hgb_diff_series[m].mean()) # mean predicted difference target
print(d[m].mean()) # mean actual difference target

# the corrected trees model (difference + relative features model)
X_rel = ["rel_24", "rel_48", "rel_168", "hour", 
         "day_of_week", "month", "is_holiday", 
         "temp_mean"
        ]

hgb_rel_model = clone(hgb_model)

hgb_rel_model.fit(df.loc[fit_rows, X_rel], d[fit_rows])
hgb_rel_pred = hgb_rel_model.predict(df[X_rel])
hgb_rel_series = pd.Series(data=hgb_rel_pred, index=df.index)

rel_forecast = df["level_7d"] + hgb_rel_series

# organized table
rows = {}
rows["naive"] = score(pred[m], y[m])
rows["linear"] = score(lin_pred[m], y[m])
rows["A_raw"] = score(hgb_series[m], y[m])
rows["B_diff_target"] = score(diff_forecast[m], y[m])
rows["C_relative"] = score(rel_forecast[m], y[m])

print(pd.DataFrame(rows).T.round(2))

# monthly ME
errs = pd.DataFrame(index=y[m].index)
errs["linear"] = y[m] - lin_pred[m]
errs["A_raw"] = y[m] - hgb_series[m]
errs["B_diff_target"] = y[m] - diff_forecast[m]
errs["C_relative"] = y[m] - rel_forecast[m]

monthly = errs.groupby(local[m].month).mean()
monthly.index.name = "local month"
print(monthly.round(2).to_markdown())

# monthly MAE
monthly_mae = errs.abs().groupby(local[m].month).mean()
monthly_mae.index.name = "local month"
print(monthly_mae.round(2).to_markdown())

