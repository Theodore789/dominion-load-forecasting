import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from sklearn.ensemble import HistGradientBoostingRegressor
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

print(score(pred[m], y[m])) # naive baseline results

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

print(score(lin_pred[m], y[m])) # linear model results

# Gradient-boosted trees model
X_cols = ["lag_24", "lag_48", "lag_168", "level_7d", 
          "hour", "day_of_week", "month", "is_holiday",
          "temp_mean"
          ]

hgb_model = HistGradientBoostingRegressor(max_iter=400, 
                                     learning_rate=0.06, 
                                     early_stopping=False, 
                                     random_state=0
                                     )

hgb_results = hgb_model.fit(df.loc[train & has_y, X_cols], y[train & has_y])
hgb_pred = hgb_results.predict(df[X_cols])
hgb_series = pd.Series(data=hgb_pred, index=df.index)

print(score(hgb_pred[m], y[m])) # gradient-boosted trees model results