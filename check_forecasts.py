import pandas as pd

old = pd.read_csv("old_forecasts.csv")
new = pd.read_csv("data/test_forecasts.csv")

print(old.shape, new.shape)

cols = ["naive", "linear", "A", "B", "C", "MLP"]

print((new[cols] - old[cols]).abs().max())
print(old.columns.equals(new.columns))
print(old["record"].equals(new["record"]))