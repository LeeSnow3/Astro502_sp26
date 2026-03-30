import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

results = pd.read_csv("age_fit_results_scipy.csv")
#remove duplicate rows
results = results.drop_duplicates(subset=["starname"], keep="first")
print(len(results))
with_feh = results[pd.notna(results["feh_observed"])]
without_feh = results[pd.isna(results["feh_observed"])]

x = (with_feh["age_gyr"] - with_feh["age_observed"]) / with_feh["age_observed"]
x_noinitfeh = (without_feh["age_gyr"] - without_feh["age_observed"]) / without_feh["age_observed"]

plt.figure(figsize=(10, 6))
plt.scatter(with_feh["age_observed"], x, label="With [Fe/H]", alpha=0.7)
plt.scatter(without_feh["age_observed"], x_noinitfeh, label="Without [Fe/H]", alpha=0.7)

plt.axhline(0, linestyle="--", label="Perfect Fit")

plt.xlabel("Table Age (Gyr)")
plt.ylabel("(Model Age - Table Age)/ Table Age")
plt.title("Relative Age Error vs. Table Age")
plt.legend()
plt.grid()
plt.savefig("relativeageerror.png")
