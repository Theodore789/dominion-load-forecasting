from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.base import clone
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer


def score(pred, y):
    err = y - pred
    
    mae = err.abs().mean()
    rmse = (err ** 2).mean() ** 0.5
    mape = (err / y).abs().mean() * 100 
    me = (err).mean()

    top = y >= y.quantile(0.95)
    mae_top5 = (err[top]).abs().mean()
    
    return {"MAE": mae, 
            "RMSE": rmse, 
            "MAPE": mape, 
            "ME": me, 
            "MAE_top5": mae_top5
            }


def verdict(ci, red):
    if ci[0] > 0 and red >= 0.5:
        return "supported"
    elif ci[0] > 0:
        return "partly supported"
    else:
        return "not supported"


HERE = Path(__file__).parent
df = pd.read_csv(HERE / "data" / "features.csv", index_col=0, parse_dates=True)

print(df.index.tz) # UTC

local = df.index.tz_convert("America/New_York")  # day D = Virginia local day

# splits for the models
train = local.year <= 2022
val = local.year == 2023
test = local.year >= 2024

print(train.sum(), val.sum(), test.sum())

has_y = df["Demand (MW)"].notna()

print((train & ~has_y).sum(),  # 6 of the local days missing
      (val & ~has_y).sum(),  # 2 of the local days missing 
      (test & ~has_y).sum()  # 4 of the local days missing, 2 Nov days and 2 March days
      )

# every model has to beat the baseline: lag_168 
naive_pred = df["lag_168"]
y = df["Demand (MW)"]
m = val & has_y & naive_pred.notna()

# professor Tao Hong's vanilla linear benchmark
df["trend"] = np.arange(len(df))

formula  = ('Q("Demand (MW)") ~ trend + C(month)' 
            '+ C(day_of_week):C(hour)' 
            '+ (temp_mean + temp_sq + temp_cube)' 
            '* (C(month) + C(hour))'
            ) 

model = smf.ols(formula, data=df[train & has_y])
results = model.fit() 
lin_pred = results.predict(df)


# Gradient-boosted trees models: Arms A, B and C

# Arm A (raw model)
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

# Arm B (difference model)
d = y - df["level_7d"]

hgb_diff_model = clone(hgb_model)

hgb_diff_model.fit(df.loc[fit_rows, X_cols], d[fit_rows])
hgb_diff_pred = hgb_diff_model.predict(df[X_cols])
hgb_diff_series = pd.Series(data=hgb_diff_pred, index=df.index)

diff_forecast = df["level_7d"] + hgb_diff_series

print(hgb_diff_series[m].mean())  # mean predicted difference target
print(d[m].mean())  # mean actual difference target

# Arm C (difference + relative features model)
X_rel = ["rel_24", "rel_48", "rel_168", "hour", 
         "day_of_week", "month", "is_holiday", 
         "temp_mean"
        ]

hgb_rel_model = clone(hgb_model)

hgb_rel_model.fit(df.loc[fit_rows, X_rel], d[fit_rows])
hgb_rel_pred = hgb_rel_model.predict(df[X_rel])
hgb_rel_series = pd.Series(data=hgb_rel_pred, index=df.index)

rel_forecast = df["level_7d"] + hgb_rel_series

# organized score table
rows = {}
rows["naive"] = score(naive_pred[m], y[m])
rows["linear"] = score(lin_pred[m], y[m])
rows["A_raw"] = score(hgb_series[m], y[m])
rows["B_diff_target"] = score(diff_forecast[m], y[m])
rows["C_relative"] = score(rel_forecast[m], y[m])

print(f"VALIDATION (2023, frozen)")
print(pd.DataFrame(rows).T.round(2))

# monthly ME table
errs = pd.DataFrame(index=y[m].index)
errs["linear"] = y[m] - lin_pred[m]
errs["A_raw"] = y[m] - hgb_series[m]
errs["B_diff_target"] = y[m] - diff_forecast[m]
errs["C_relative"] = y[m] - rel_forecast[m]

monthly = errs.groupby(local[m].month).mean()
monthly.index.name = "local month"
print(monthly.round(2).to_markdown())

# monthly MAE table
monthly_mae = errs.abs().groupby(local[m].month).mean()
monthly_mae.index.name = "local month"
print(monthly_mae.round(2).to_markdown())


# MLP model
num_cols = ["rel_24", 
            "rel_48", 
            "rel_168", 
            "temp_mean", 
            "is_holiday"
            ]

cat_cols = ["hour", 
            "day_of_week", 
            "month"
            ]

mlp_cols = num_cols + cat_cols

mlp_forecasts = {}

for seed in range(5):
    num_path = make_pipeline(SimpleImputer(strategy="median"), 
                             StandardScaler(),
                             )

    prep = make_column_transformer((num_path, num_cols), 
                                   (OneHotEncoder(handle_unknown="ignore"), cat_cols),
                                   )

    mlp = make_pipeline(prep, MLPRegressor(hidden_layer_sizes=(64, 32),
                                           alpha=1e-3, max_iter=200, early_stopping=False,
                                           random_state=seed
                                           ))

    mlp.fit(df.loc[fit_rows, mlp_cols], d[fit_rows] / 1000)

    d_gw = pd.Series(mlp.predict(df[mlp_cols]), index=df.index)

    mlp_forecast = df["level_7d"] + 1000 * d_gw  # back to MW
    
    mlp_forecasts[seed] = mlp_forecast
    
    rows[f"MLP_C_s{seed}"] = score(mlp_forecast[m], y[m])


mlp_mae = pd.Series({k: v["MAE"] for k, v in rows.items() if k.startswith("MLP")})

print(mlp_mae.mean(), mlp_mae.std())


table = pd.DataFrame(rows).T
mlp_rows = table[table.index.str.startswith("MLP")]

print(mlp_rows.mean().round(2))
print(mlp_rows.std().round(2))

# final model table
print(f"VALIDATION (2023, frozen)")
print(table.round(2).to_markdown())

# test hours check
print((test & has_y & df["lag_168"].isna()).sum())
print((test & has_y & df["lag_168"].notna()).sum())


# measures taken to actually validate on "val" and test on "test"
SPLIT = "test"

eval_split = val if SPLIT == "val" else test
m_eval = eval_split & has_y & df["lag_168"].notna()

expected = {"val": 8664, "test": 23899}
assert m_eval.sum() == expected[SPLIT]

rows_eval = {}
rows_eval["naive"] = score(naive_pred[m_eval], y[m_eval])
rows_eval["linear"] = score(lin_pred[m_eval], y[m_eval])
rows_eval["A_raw"] = score(hgb_series[m_eval], y[m_eval])
rows_eval["B_diff_target"] = score(diff_forecast[m_eval], y[m_eval])
rows_eval["C_relative"] = score(rel_forecast[m_eval], y[m_eval])

for seed in range(5):
    rows_eval[f"MLP_C_s{seed}"] = score(mlp_forecasts[seed][m_eval], y[m_eval])

print(f"EVALUATION ON {SPLIT}")
print(pd.DataFrame(rows_eval).T.round(2))

eval_table = pd.DataFrame(rows_eval).T
mlp_eval = eval_table[eval_table.index.str.startswith("MLP")]

mlp_summary = pd.DataFrame({"mean" :mlp_eval.mean(),
                            "sd": mlp_eval.std()})
print("MLP, 5 seeds (mean and sd):")
print(mlp_summary.T.round(2))

# every model has a forecast for every one of the 23,899 test hours
test_m = test & has_y & df["lag_168"].notna()


missing_counts = [naive_pred.reindex(df.index)[test_m].isna().sum(), 
               lin_pred.reindex(df.index)[test_m].isna().sum(), 
               hgb_series.reindex(df.index)[test_m].isna().sum(), 
               diff_forecast.reindex(df.index)[test_m].isna().sum(), 
               rel_forecast.reindex(df.index)[test_m].isna().sum()
               ]

for check in missing_counts:
    assert check == 0  # error if any forecast is missing 


for seed in range(5):
    assert mlp_forecasts[seed].reindex(df.index)[test_m].isna().sum() == 0 


train_max = y[train].max()

if SPLIT == "val":
    rec_threshold = y[m_eval].quantile(0.99)  # stand-in, dry run only
else:
    rec_threshold = train_max

rec = m_eval & (y > rec_threshold)

rows_rec = {}
rows_rec["A_raw"] = score(hgb_series[rec], y[rec])
rows_rec["B_diff_target"] = score(diff_forecast[rec], y[rec])
rows_rec["C_relative"] = score(rel_forecast[rec], y[rec])

# dry-run numbers on a stand-in threshold --> the code works
print(pd.DataFrame(rows_rec).T.round(2))

print(train_max, round(rec_threshold, 1), rec.sum()) 

print((test_m & (y > train_max)).sum())  # pred --> 389 (from hypothesis.md)


# getting ready for bootstrap sampling

day = pd.Series(local.date, index=df.index)
all_days = day[m_eval].unique()

columns_boot = {}
columns_boot["abs_A"] = (y[rec] - hgb_series[rec]).abs()
columns_boot["abs_B"] = (y[rec] - diff_forecast[rec]).abs()
columns_boot["abs_C"] = (y[rec] - rel_forecast[rec]).abs()
columns_boot["n"] = rec[rec].astype(int)

per_day = pd.DataFrame(columns_boot).groupby(day[rec]).sum()
per_day = per_day.reindex(all_days, fill_value=0)

assert per_day["n"].sum() == rec.sum()

assert np.isclose(per_day["abs_A"].sum() / per_day["n"].sum(), rows_rec["A_raw"]["MAE"])
assert np.isclose(per_day["abs_B"].sum() / per_day["n"].sum(), rows_rec["B_diff_target"]["MAE"])
assert np.isclose(per_day["abs_C"].sum() / per_day["n"].sum(), rows_rec["C_relative"]["MAE"])                  


# bootstrap loop

rng = np.random.default_rng(0)
n_boot = 2000
n_days = len(per_day)

diffs_B = []
diffs_C  = []

for b in range(n_boot):
    idx = rng.integers(0, n_days, size=n_days)
    sample = per_day.iloc[idx]
    n_tot = sample["n"].sum()

    mae_A = sample["abs_A"].sum() / n_tot
    mae_B = sample["abs_B"].sum() / n_tot
    mae_C = sample["abs_C"].sum() / n_tot

    diffs_B.append(mae_A - mae_B)
    diffs_C.append(mae_A - mae_C)


ci_B = np.percentile(diffs_B, [2.5, 97.5])
ci_C = np.percentile(diffs_C, [2.5, 97.5])


# verdict numbers

# A - arm (B or C); positive --> arm is better
point_diff_A_to_B = rows_rec["A_raw"]["MAE"] - rows_rec["B_diff_target"]["MAE"]
point_diff_A_to_C = rows_rec["A_raw"]["MAE"] - rows_rec["C_relative"]["MAE"]


# bias reduction

# pred -> 1 - 1.086 = -0.086 (bias went up 8.6%)
red_B = 1 - abs(rows_rec["B_diff_target"]["ME"]) / abs(rows_rec["A_raw"]["ME"])

# pred -> 1 - 0.431 = 0.569 (bias went down 57%)
red_C = 1 - abs(rows_rec["C_relative"]["ME"]) / abs(rows_rec["A_raw"]["ME"])  


print(f"Pre-registered experiment on {SPLIT}")

for arm, diff, ci, red in [("B", point_diff_A_to_B, ci_B, red_B),
                           ("C", point_diff_A_to_C, ci_C, red_C)]:
    
    print(f"Arm {arm}: MEA_A - MAE_{arm} = {diff:.1f} MW | "
          f"95% CI [{ci[0]:.1f}, {ci[1]:.1f}] | "
          f"bias reduction = {red:.1%} | "
          f"verdict = {verdict(ci, red)}")