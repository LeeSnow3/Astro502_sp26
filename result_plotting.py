import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

results = pd.read_csv("results/age_fit_results_scipy_20000run.csv")
results = results.drop_duplicates(subset=["starname"], keep="first")
results = results[results["age_observed"] > 0]

print(results[results["age_gyr"] > 10][["starname", "age_gyr", "age_observed"]])
print(results[results["age_gyr"] > 6][["starname", "age_gyr", "age_observed"]])
# --- Load and merge observed age errors ---
targets = pd.read_csv("mega_target_list.csv")
age_errors = (targets[["hostname", "st_ageerr1", "st_ageerr2"]]
              .drop_duplicates(subset=["hostname"], keep="first"))

results = results.merge(age_errors, left_on="starname", right_on="hostname", how="left")

# Calculate average table age uncertainty
avg_table_uncertainty = ((results["st_ageerr1"] + results["st_ageerr2"].abs()) / 2).median()
print(f"Average table age uncertainty: {avg_table_uncertainty:.4f} Gyr")

# --- Error propagation ---
a = results["age_gyr"]
b = results["age_observed"]
sigma_a       = results["age_gyr_mc_err"]
sigma_b_upper = results["st_ageerr1"]
sigma_b_lower = results["st_ageerr2"].abs()

err_upper = np.sqrt((sigma_a / b)**2 + (a / b**2 * sigma_b_lower)**2)
err_lower = np.sqrt((sigma_a / b)**2 + (a / b**2 * sigma_b_upper)**2)

results["rel_err_upper"] = err_upper.fillna(0)
results["rel_err_lower"] = err_lower.fillna(0)

#split on catalog type
results["catalog"] = results["starname"].str.split("-").str[0]
print(np.unique(results["catalog"]))
#print count of each catalog type
print(results["catalog"].value_counts())

kepler_results = results[results["catalog"] == "Kepler"]
k2_results = results[results["catalog"] == "K2"]
toi_results = results[results["catalog"] == "TOI"]
wasp_results = results[results["catalog"] == "WASP"]
other_results = results[~results["catalog"].isin(["Kepler", "K2", "TOI", "WASP"])]

# --- Split on [Fe/H] ---
with_feh    = results[pd.notna(results["feh_observed"])]
without_feh = results[pd.isna(results["feh_observed"])]

x           = (with_feh["age_gyr"]    - with_feh["age_observed"])    / with_feh["age_observed"]
x_noinitfeh = (without_feh["age_gyr"] - without_feh["age_observed"]) / without_feh["age_observed"]

# Count points where error bars cross zero
count_with = ((x - with_feh["rel_err_lower"] <= 0) & (x + with_feh["rel_err_upper"] >= 0)).sum()
count_without = ((x_noinitfeh - without_feh["rel_err_lower"] <= 0) & (x_noinitfeh + without_feh["rel_err_upper"] >= 0)).sum()
print(f"Total points with [Fe/H]: {len(with_feh)}")
print(f"Total points without [Fe/H]: {len(without_feh)}")
print(f"Number of points with [Fe/H] where error bars cross zero: {count_with}")
print(f"Number of points without [Fe/H] where error bars cross zero: {count_without}")
print(f"Percentage with agreement: {(count_with + count_without) / len(results) * 100:.2f}%")

#Plot Table Age vs. Model Age
plt.figure(figsize=(12, 6))
plt.errorbar(
    with_feh["age_observed"], with_feh["age_gyr"],
    yerr=with_feh["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=with_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label="With [Fe/H]"
)   
plt.errorbar(
    without_feh["age_observed"], without_feh["age_gyr"],     
    yerr=without_feh["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=without_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label="Without [Fe/H]"
)   
plt.plot([0, 1], [0, 1], linestyle="--", color="black", label="Perfect Fit", linewidth=1)
# Add shaded region for average table age uncertainty
x_vals = np.linspace(0, 1, 100)
plt.fill_between(x_vals, x_vals - avg_table_uncertainty, x_vals + avg_table_uncertainty, alpha=0.2, color='gray', label=f'Median Table Age Uncertainty (±{avg_table_uncertainty:.3f} Gyr)')
plt.title("Model Age vs. Table Age")
plt.xlabel("Table Age (Gyr)")
plt.ylabel("Modeled Age (Gyr)")
plt.xlim(0., 1)
plt.legend()
plt.grid(which="both", alpha=0.3)
plt.tight_layout()
plt.savefig("plots/modelvstableageshaded.png", dpi=150)
plt.close()

#plot same as above but split on catalog type
#Plot Table Age vs. Model Age
plt.figure(figsize=(12, 6))
plt.errorbar(
    kepler_results["age_observed"], kepler_results["age_gyr"],
    yerr=kepler_results["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=with_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label=f"Kepler n={len(kepler_results)}"
)   
plt.errorbar(
    toi_results["age_observed"], toi_results["age_gyr"],     
    yerr=toi_results["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=without_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label=f"TOI n={len(toi_results)}"
)   
plt.errorbar(
    k2_results["age_observed"], k2_results["age_gyr"],     
    yerr=k2_results["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=without_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label=f"K2 n={len(k2_results)}"
)   
plt.errorbar(
    wasp_results["age_observed"], wasp_results["age_gyr"],     
    yerr=wasp_results["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=without_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label=f"WASP n={len(wasp_results)}"
)   
plt.errorbar(
    other_results["age_observed"], other_results["age_gyr"],     
    yerr=other_results["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=without_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label=f"Other n={len(other_results)}"
)   
plt.plot([0, 1], [0, 1], linestyle="--", color="black", label="Perfect Fit", linewidth=1)
# Add shaded region for average table age uncertainty
x_vals = np.linspace(0, 1, 100)
plt.fill_between(x_vals, x_vals - avg_table_uncertainty, x_vals + avg_table_uncertainty, alpha=0.2, color='gray', label=f'Median Table Age Uncertainty (±{avg_table_uncertainty:.3f} Gyr)')
plt.title("Model Age vs. Table Age")
plt.xlabel("Table Age (Gyr)")
plt.ylabel("Modeled Age (Gyr)")
plt.xlim(0., 1)
plt.legend()
plt.grid(which="both", alpha=0.3)
plt.tight_layout()
plt.savefig("plots/modelvstableageshadedcatalog.png", dpi=150)
plt.close()

plt.figure(figsize=(12, 6))
plt.errorbar(
    kepler_results["age_observed"], kepler_results["age_gyr"],
    yerr=kepler_results["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=with_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label=f"Kepler n={len(kepler_results)}"
)   
plt.errorbar(
    toi_results["age_observed"], toi_results["age_gyr"],     
    yerr=toi_results["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=without_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label=f"TOI n={len(toi_results)}"
)   
plt.errorbar(
    k2_results["age_observed"], k2_results["age_gyr"],     
    yerr=k2_results["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=without_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label=f"K2 n={len(k2_results)}"
)   
plt.errorbar(
    wasp_results["age_observed"], wasp_results["age_gyr"],     
    yerr=wasp_results["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=without_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label=f"WASP n={len(wasp_results)}"
)   
plt.errorbar(
    other_results["age_observed"], other_results["age_gyr"],     
    yerr=other_results["age_gyr_mc_err"], fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    #xerr=without_feh[["st_ageerr2", "st_ageerr1"]].abs().values.T,
    capthick=0.8, markersize=5, label=f"Other n={len(other_results)}"
)   
plt.plot([0, 1], [0, 1], linestyle="--", color="black", label="Perfect Fit", linewidth=1)
# Add shaded region for average table age uncertainty
x_vals = np.linspace(0, 1, 100)
plt.fill_between(x_vals, x_vals - avg_table_uncertainty, x_vals + avg_table_uncertainty, alpha=0.2, color='gray', label=f'Median Table Age Uncertainty (±{avg_table_uncertainty:.3f} Gyr)')
plt.title("Model Age vs. Table Age")
plt.xlabel("Table Age (Gyr)")
plt.ylabel("Modeled Age (Gyr)")
plt.xlim(0., 1)
plt.ylim(-0.1, 1.5)
plt.grid(which="both", alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("plots/modelvstableageshadedzoomed.png", dpi=150)
plt.close()


# --- Plot Relative Age Errors---
plt.figure(figsize=(12, 6))

eb_kwargs = dict(fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
                 capthick=0.8, markersize=5)

plt.errorbar(
    with_feh["age_observed"], x,
    yerr=[with_feh["rel_err_lower"], with_feh["rel_err_upper"]],
    label="With [Fe/H]", **eb_kwargs
)
plt.errorbar(
    without_feh["age_observed"], x_noinitfeh,
    yerr=[without_feh["rel_err_lower"], without_feh["rel_err_upper"]],
    label="Without [Fe/H]", **eb_kwargs
)

#plt.xscale("log")
plt.xlim(0.01, 1)
plt.ylim(-1, 1)
plt.axhline(0, linestyle="--", color="black", label="Perfect Fit", linewidth=1)
plt.xlabel("Table Age (Gyr)")
plt.ylabel("(Model Age - Table Age) / Table Age")
plt.title("Relative Age Error vs. Table Age")
plt.legend()
plt.grid(which="both", alpha=0.3)
plt.tight_layout()
plt.savefig("plots/relativeageerror.png", dpi=150)
plt.close()

# --- Plot Relative Age Errors for points with table uncertainty <= 20% ---
# Calculate relative table age uncertainty
results["rel_table_uncertainty"] = ((results["st_ageerr1"] + results["st_ageerr2"].abs()) / 2) / results["age_observed"]

# Filter for points where relative uncertainty <= 20%
filtered_results = results[results["rel_table_uncertainty"] <= 0.2]
print(f"Number of points with relative table age uncertainty ≤ 20%: {len(filtered_results)}")

# Split filtered data
filtered_with_feh = filtered_results[pd.notna(filtered_results["feh_observed"])]
filtered_without_feh = filtered_results[pd.isna(filtered_results["feh_observed"])]

# Calculate relative errors for filtered data
x_filtered = (filtered_with_feh["age_gyr"] - filtered_with_feh["age_observed"]) / filtered_with_feh["age_observed"]
x_noinitfeh_filtered = (filtered_without_feh["age_gyr"] - filtered_without_feh["age_observed"]) / filtered_without_feh["age_observed"]

plt.figure(figsize=(12, 6))

eb_kwargs = dict(fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
                 capthick=0.8, markersize=5)

plt.errorbar(
    filtered_with_feh["age_observed"], x_filtered,
    yerr=[filtered_with_feh["rel_err_lower"], filtered_with_feh["rel_err_upper"]],
    label="With [Fe/H]", **eb_kwargs
)
plt.errorbar(
    filtered_without_feh["age_observed"], x_noinitfeh_filtered,
    yerr=[filtered_without_feh["rel_err_lower"], filtered_without_feh["rel_err_upper"]],
    label="Without [Fe/H]", **eb_kwargs
)

plt.xlim(0.01, 1)
plt.ylim(-1, 1)
plt.axhline(0, linestyle="--", color="black", label="Perfect Fit", linewidth=1)
plt.xlabel("Table Age (Gyr)")
plt.ylabel("(Model Age - Table Age) / Table Age")
plt.title("Relative Age Error vs. Table Age (Table Uncertainty ≤ 20%)")
plt.legend()
plt.grid(which="both", alpha=0.3)
plt.tight_layout()
plt.savefig("plots/relativeageerror_filtered.png", dpi=150)
plt.close()

# --- Plot Model Age vs. Table Age (filtered for table uncertainty <= 20%) ---
plt.figure(figsize=(12, 6))
plt.errorbar(
    filtered_with_feh["age_observed"], filtered_with_feh["age_gyr"],
    yerr=filtered_with_feh["age_gyr_mc_err"],  xerr = (filtered_with_feh["st_ageerr1"] + filtered_with_feh["st_ageerr2"].abs())/2,fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    capthick=0.8, markersize=5, label="With [Fe/H]"
)   
plt.errorbar(
    filtered_without_feh["age_observed"], filtered_without_feh["age_gyr"],     
    yerr=filtered_without_feh["age_gyr_mc_err"], xerr = (filtered_without_feh["st_ageerr1"] + filtered_without_feh["st_ageerr2"].abs())/2, fmt='o', alpha=0.7, capsize=2, elinewidth=0.8,
    capthick=0.8, markersize=5, label="Without [Fe/H]"
) 
filtered_table_uncertainty = ((filtered_results["st_ageerr1"] + filtered_results["st_ageerr2"].abs()) / 2).median()  
plt.plot([0, 1], [0, 1], linestyle="--", color="black", label="Perfect Fit", linewidth=1)
# Add shaded region for average table age uncertainty
x_vals = np.linspace(0.01, 1, 100)
plt.fill_between(x_vals, x_vals - filtered_table_uncertainty, x_vals + filtered_table_uncertainty, alpha=0.2, color='gray', label=f'Median Table Age Uncertainty (±{filtered_table_uncertainty:.3f} Gyr)')
plt.xlim(0.01, 1)
plt.ylim(0.01, 1)
#plt.xscale("log")
#plt.yscale("log")
plt.title("Model Age vs. Table Age (Table Uncertainty ≤ 20%)")
plt.xlabel("Table Age (Gyr)")
plt.ylabel("Modeled Age (Gyr)")
plt.legend()
plt.grid(which="both", alpha=0.3)
plt.tight_layout()
plt.savefig("plots/modelvstableageshadedzoomed_filtered.png", dpi=150)
plt.close()