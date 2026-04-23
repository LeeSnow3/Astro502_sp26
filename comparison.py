import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#My results
results = pd.read_csv("results/age_fit_results_scipy_20000run.csv")
results = results.drop_duplicates(subset=["starname"], keep="first")
""" #Taylor's results
taylor_results = pd.read_csv("k2_star_ages.csv")
#convert age_myr to age_gyr
taylor_results["age_gyr"] = taylor_results["age_myr"] / 1e3
#filter for those that are in both, my under starname and Taylor under starname
merged_results = pd.merge(results, taylor_results, on="starname", suffixes=('_mine', '_taylor'))
#print header of merged results
print(len(merged_results))
#plot my age vs. Taylor's age
plt.figure(figsize=(8, 8))
plt.scatter(merged_results["age_gyr_mine"], merged_results["age_gyr_taylor"], alpha=0.7)
plt.plot([0, 14], [0, 14], 'r--')  # 1:1 line
plt.xlabel("Lee's Age (Gyr)")
plt.ylabel("Taylor's Age (Gyr)")
plt.title("Comparison of Age Estimates")
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.grid()
plt.show()
plt.close() """
#James' results
james_results = pd.read_csv("results/interpolate_20260409_125607_candidate_fits.csv")
james_results = james_results.drop_duplicates(subset=["hostname"], keep="first")
#convert age_yr to age_gyr
james_results["age_gyr"] = james_results["age_yr"] / 1e9
#filter for those that are in both, my under starname and James under hostname
merged_results = pd.merge(results, james_results, left_on="starname", right_on="hostname", suffixes=('_mine', '_james'))
#print column names of merged results
print(merged_results.columns)
print(len(merged_results))
#plot my age vs. James' age
plt.figure(figsize=(8, 8))
plt.errorbar(merged_results["age_gyr_mine"], merged_results["age_gyr_james"], xerr = merged_results["age_gyr_mc_err"], fmt = "o", alpha=0.7, capsize=5)
plt.plot([0, 14], [0, 14], 'r--')  # 1:1 line
plt.xlabel("Lee's Age (Gyr)")
plt.ylabel("James' Age (Gyr)")
plt.title("Comparison of Age Estimates")
plt.xscale("log")
plt.yscale("log")
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.grid()
plt.savefig("plots/lee_vs_james_age_comparison_log.png")
plt.close()

#print stars where lee's age is less than 0.2 Gyr but James' age is greater than 0.2 Gyr
young_lee_old_james = merged_results[(merged_results["age_gyr_mine"] < 0.2) & (merged_results["age_gyr_james"] > 0.2)]
# Stars of interest
stars = young_lee_old_james["starname"].tolist()

# Keep only those rows
subset = merged_results[merged_results["starname"].isin(stars)].copy()

# Bands to include
bands = ["BP", "G", "RP", "J", "H", "K"]

rows = []

for _, row in subset.iterrows():
    star = row["starname"]
    
    for band in bands:
        table_mag = row[f"{band}_mag_obs"]
        lee_val = row[f"{band}_mag_model"]
        james_val = row[f"model_{band}"]
        resid = lee_val - james_val
        
        rows.append({
            "starname": star,
            "band": band,
            "Table_mag": table_mag,
            "Lee_mag": lee_val,
            "James_mag": james_val,
            "Residual": resid
        })

long_table = pd.DataFrame(rows)

# Optional: round for readability
long_table = long_table.round(4)

print(long_table.to_string(index=False))