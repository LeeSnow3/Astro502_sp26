from __future__ import annotations
from isochrones import get_ichrone, SingleStarModel
from csv_get_mags import read_star_row_from_csv
import pandas as pd
import numpy as np
import pprint
import matplotlib.pyplot as plt
from isochrones.priors import FlatLogPrior, LogNormalPrior
from scipy.stats import gaussian_kde

def kde_peak(samples: np.ndarray, n_grid: int = 2000) -> float:
    """Return the mode of samples via Gaussian KDE in native units."""
    kde  = gaussian_kde(samples, bw_method="scott")
    grid = np.linspace(samples.min(), samples.max(), n_grid)
    return float(grid[np.argmax(kde(grid))])

def percentile_summary(samples: np.ndarray) -> tuple[float, float, float]:
    """Return (16th, 50th, 84th) percentiles."""
    return tuple(np.percentile(samples, [16, 50, 84]))

def props_to_singlestarmodel_kwargs(props: dict) -> dict:
    """
    Convert:
      G_mag=<float>, G_mag_err=<float>
    into:
      G_mag=(value, err)
    Also preserves parallax=(value, err).
    """
    out: dict = {}

    # parallax is already (val, err) in your reader
    if "parallax" in props:
        out["parallax"] = props["parallax"]

    # convert *_mag + *_mag_err pairs into tuples
    for k, v in props.items():
        if not k.endswith("_mag"):
            continue
        err_key = f"{k}_err"
        if err_key not in props:
            continue
        out[k] = (float(v), float(props[err_key]))

    # Optional spectroscopic constraints if you add them later in your reader:
    for k in ("Teff", "logg", "feh"):
        if k in props and f"{k}_err" in props:
            out[k] = (float(props[k]), float(props[f"{k}_err"]))

    return out
from scipy.optimize import curve_fit

mist = get_ichrone("mist")
stars = ["TOI-6016", "WASP-96"]
for host_name in stars:
    props = read_star_row_from_csv(
        host_name=host_name,
        sigma_mag=True,
        sigma_parallax=0.2, #not included in csv
    )
    

    print(f"got props for {host_name}:")

    props = props_to_singlestarmodel_kwargs(props)
    pprint.pprint(props)
    mod = SingleStarModel(mist, name="csv_star", **props)
    
    
    # Run posterior sampling (nested sampling)
    mod.fit(verbose=False)
    samples = mod.samples
    samples["age_gyr"] = 10**samples["age"] / 1e9
    samples["Star"] = host_name
    
    log_age = samples["age"].values            # native: log10(yr)
    age_gyr = samples["age_gyr"].values
    log_peak          = kde_peak(log_age)
    age_peak_gyr      = 10**log_peak / 1e9    # convert peak only
    
    log_lo, log_med, log_hi = percentile_summary(log_age)
    age_lo_gyr     = 10**log_lo  / 1e9
    age_median_gyr = 10**log_med / 1e9
    age_hi_gyr     = 10**log_hi  / 1e9
    
    #plot histogram w/ peak marked
    plt.figure(figsize=(8, 5))
    plt.hist(age_gyr, bins=30, density=True, alpha=0.6, color='g')
    plt.axvline(age_peak_gyr, color='r', linestyle='--', label=f'KDE Peak: {age_peak_gyr:.2f} Gyr')
    plt.xlabel('Age (Gyr)') 
    plt.ylabel('Density')
    plt.title(f'Age Distribution for {host_name}')
    plt.legend()
    plt.savefig(f"age_dist_{host_name}.png")
    
    print(f"Samples for {host_name}:")
    print(samples.describe())
    #write mode results to csv
    mode_samples = samples.groupby("Star").agg(lambda x: x.mode().iloc[0])
    mode_samples.to_csv("age_fit_results_singlestarmodel.csv", mode='a', header=not pd.io.common.file_exists("age_fit_results_singlestarmodel.csv"))
    