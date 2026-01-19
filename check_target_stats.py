import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1. Load the Data
filename = "ASTR502_Mega_Target_List.csv"
print(f"Reading {filename}...")
try:
    df = pd.read_csv(filename)
except FileNotFoundError:
    print("Error: File not found. Make sure you ran the generator script first!")
    exit()

# 2. Clean/Prep Data for Statistics
# Filter for stars that actually have an age in the literature
df_ages = df.dropna(subset=['st_age'])

# Calculate average uncertainty: (upper_err + abs(lower_err)) / 2
# Note: NASA archive errors are often NaN if the parameter is a limit, so we fill with 0 for basic stats
age_err1 = df_ages['st_ageerr1'].fillna(0)
age_err2 = df_ages['st_ageerr2'].fillna(0).abs()
df_ages['mean_age_err'] = (age_err1 + age_err2) / 2.0

# 3. Print Text Statistics
total_stars = len(df)
stars_with_ages = len(df_ages)
stars_young = len(df_ages[df_ages['st_age'] < 1.0]) # Less than 1 Gyr
stars_very_young = len(df_ages[df_ages['st_age'] < 0.1]) # Less than 100 Myr

print("-" * 40)
print(f"Total Targets in List:      {total_stars}")
print("-" * 40)
print(f"Stars with Literature Ages: {stars_with_ages} ({stars_with_ages/total_stars:.1%})")
print(f"Stars < 1 Gyr:              {stars_young} ({stars_young/stars_with_ages:.1%} of aged stars)")
print(f"Stars < 100 Myr:            {stars_very_young}")
print("-" * 40)

# 4. Generate Plots
# We'll make a 2x2 grid
sns.set_style("whitegrid") # Make it look nice
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
plt.subplots_adjust(hspace=0.3, wspace=0.3)

# Plot A: Distribution of Ages
ax1 = axes[0, 0]
sns.histplot(data=df_ages, x='st_age', bins=30, kde=False, color='skyblue', ax=ax1)
ax1.set_xlabel("Literature Age [Gyr]")
ax1.set_ylabel("Number of Stars")
ax1.set_title("Distribution of Literature Ages")
ax1.axvline(1.0, color='red', linestyle='--', label='1 Gyr')
ax1.legend()

# Plot B: Age Uncertainties
ax2 = axes[0, 1]
# Filter out crazy outliers for the plot (errors > 5 Gyr are usually bad fits)
valid_errors = df_ages[df_ages['mean_age_err'] < 5.0]
sns.histplot(data=valid_errors, x='mean_age_err', bins=30, color='salmon', ax=ax2)
ax2.set_xlabel("Age Uncertainty [Gyr]")
ax2.set_ylabel("Number of Stars")
ax2.set_title("How precise are current ages?")

# Plot C: Temperature vs Age (The "Evolution" Check)
# Hot stars die young, so the top right of this plot should be empty.
ax3 = axes[1, 0]
sc = ax3.scatter(df_ages['st_age'], df_ages['st_teff'], 
                 c=df_ages['st_met'], cmap='viridis', 
                 alpha=0.6, s=15, vmin=-0.5, vmax=0.5)
ax3.set_xlabel("Age [Gyr]")
ax3.set_ylabel("Effective Temperature [K]")
ax3.set_title("Teff vs. Age (Color = Metallicity)")
ax3.set_xlim(0, 14)
ax3.set_ylim(3000, 7500) # Focus on FGKM stars
# Add colorbar
cbar = plt.colorbar(sc, ax=ax3)
cbar.set_label('[Fe/H]')

# Plot D: Magnitude Distribution
ax4 = axes[1, 1]
# We check V mag first, fill with Gaia mag if missing for the plot
mags = df['sy_vmag'].fillna(df['sy_gaiamag'])
sns.histplot(mags, bins=30, color='purple', kde=True, ax=ax4)
ax4.set_xlabel("Brightness (V mag)")
ax4.set_title("Target Brightness Distribution")
ax4.axvline(12.5, color='k', linestyle=':', label='Spec Limit (~12.5)')
ax4.legend()

# Save and Show
output_file = "target_statistics_plot.png"
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"Plots saved to {output_file}")
plt.show()