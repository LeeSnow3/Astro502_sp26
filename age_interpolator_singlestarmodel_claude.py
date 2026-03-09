from __future__ import annotations
from isochrones import get_ichrone, SingleStarModel
from csv_get_mags import read_star_row_from_csv
import pandas as pd
import numpy as np
import pprint
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde


# ── Helpers ───────────────────────────────────────────────────────────────────

def props_to_singlestarmodel_kwargs(props: dict) -> dict:
    """
    Convert flat dict of:
      G_mag, G_mag_err  ->  G_mag=(value, err)
      Teff, Teff_err    ->  Teff=(value, err)
      parallax          ->  already (value, err)
    """
    out: dict = {}

    if "parallax" in props:
        out["parallax"] = props["parallax"]

    # Photometric bands
    for k, v in props.items():
        if not k.endswith("_mag"):
            continue
        err_key = f"{k}_err"
        if err_key not in props:
            continue
        out[k] = (float(v), float(props[err_key]))

    # Spectroscopic constraints
    for k in ("Teff", "logg", "feh"):
        if k in props and f"{k}_err" in props:
            out[k] = (float(props[k]), float(props[f"{k}_err"]))

    return out


def kde_peak(samples: np.ndarray, n_grid: int = 2000) -> float:
    """Return the mode of samples via Gaussian KDE in native units."""
    kde  = gaussian_kde(samples, bw_method="scott")
    grid = np.linspace(samples.min(), samples.max(), n_grid)
    return float(grid[np.argmax(kde(grid))])


def percentile_summary(samples: np.ndarray) -> tuple[float, float, float]:
    """Return (16th, 50th, 84th) percentiles."""
    return tuple(np.percentile(samples, [16, 50, 84]))

def find_col(df: pd.DataFrame, keyword: str) -> str:
    """
    Return the first column name whose lowercase form contains `keyword`.
    Raises a clear error listing all available columns if nothing matches.
    """
    matches = [c for c in df.columns if keyword.lower() in c.lower()]
    if not matches:
        raise KeyError(
            f"No column containing '{keyword}' found.\n"
            f"Available columns: {df.columns.tolist()}"
        )
    if len(matches) > 1:
        print(f"  [Warning] Multiple matches for '{keyword}': {matches} — using '{matches[0]}'")
    return matches[0]

# ── Core fitter ───────────────────────────────────────────────────────────────

def fit_star(
    host_name: str,
    mist,
    sigma_parallax: float = 0.2,
    verbose: bool = False,
) -> tuple[dict, pd.DataFrame]:

    # --- Load & build model --------------------------------------------------
    props  = read_star_row_from_csv(
        host_name=host_name,
        sigma_mag=True,
        sigma_parallax=sigma_parallax,
    )
    print(f"\n{'='*55}\nProps for {host_name}:")
    pprint.pprint(props)

    kwargs = props_to_singlestarmodel_kwargs(props)
    mod    = SingleStarModel(mist, name=host_name, **kwargs)
    mod.fit(verbose=verbose)

    samples = mod.samples
    print(f"\nSample columns for {host_name}: {samples.columns.tolist()}")

    # --- Age (log10 yr -> Gyr) ------------------------------------------------
    log_age = samples["age"].values            # native: log10(yr)

    log_peak          = kde_peak(log_age)
    age_peak_gyr      = 10**log_peak / 1e9    # convert peak only

    log_lo, log_med, log_hi = percentile_summary(log_age)
    age_lo_gyr     = 10**log_lo  / 1e9
    age_median_gyr = 10**log_med / 1e9
    age_hi_gyr     = 10**log_hi  / 1e9

    # --- [Fe/H] (dex, linear) ------------------------------------------------
    feh = samples["feh"].values

    feh_peak                = kde_peak(feh)
    feh_lo, feh_med, feh_hi = percentile_summary(feh)

    # --- AV (mag, linear) ----------------------------------------------------
    AV = samples["AV"].values

    AV_peak               = kde_peak(AV)
    AV_lo, AV_med, AV_hi  = percentile_summary(AV)

    # --- Pack results --------------------------------------------------------
    results = {
        "Star": host_name,
        # Age
        "age_peak_gyr":   age_peak_gyr,
        "age_median_gyr": age_median_gyr,
        "age_lo_gyr":     age_lo_gyr,
        "age_hi_gyr":     age_hi_gyr,
        # [Fe/H]
        "feh_peak":   feh_peak,
        "feh_median": feh_med,
        "feh_lo":     feh_lo,
        "feh_hi":     feh_hi,
        # AV
        "AV_peak":   AV_peak,
        "AV_median": AV_med,
        "AV_lo":     AV_lo,
        "AV_hi":     AV_hi,
    }

    return results, samples


def plot_posteriors(samples: pd.DataFrame, host_name: str) -> None:
    """
    Three-panel plot: Age (Gyr), [Fe/H], AV
    """
    log_age = samples["age"].values
    age_gyr = 10**log_age / 1e9

    param_data = [
        (age_gyr,                "Age (Gyr)"),
        (samples["feh"].values,  "[Fe/H]"),
        (samples["AV"].values,   "AV (mag)"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f"Posterior Distributions — {host_name}", fontsize=13)

    for ax, (data, label) in zip(axes, param_data):
        ax.hist(data, bins=40, density=True,
                alpha=0.45, color="steelblue", label="Posterior")

        kde  = gaussian_kde(data, bw_method="scott")
        grid = np.linspace(data.min(), data.max(), 1000)
        ax.plot(grid, kde(grid), "k-", lw=2, label="KDE")

        peak = float(grid[np.argmax(kde(grid))])
        ax.axvline(peak, color="red", linestyle="--",
                   label=f"Mode:   {peak:.3f}")

        lo, median, hi = np.percentile(data, [16, 50, 84])
        ax.axvline(median, color="royalblue", linestyle=":",
                   label=f"Median: {median:.3f}")
        ax.axvspan(lo, hi, alpha=0.15, color="royalblue", label="68% CI")

        ax.set_xlabel(label, fontsize=11)
        ax.set_ylabel("Density", fontsize=11)
        ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(f"posteriors_{host_name}.png")


# ── Main ──────────────────────────────────────────────────────────────────────

mist  = get_ichrone("mist")
stars = ["TOI-6016", "WASP-96"]

all_results = []

for host_name in stars:
    results, samples = fit_star(host_name, mist, sigma_parallax=0.2)
    all_results.append(results)

    print(f"\nResults for {host_name}:")
    print(
        f"  Age    : {results['age_peak_gyr']:.2f} Gyr (mode)  |  "
        f"median {results['age_median_gyr']:.2f} "
        f"+{results['age_hi_gyr'] - results['age_median_gyr']:.2f} "
        f"/ -{results['age_median_gyr'] - results['age_lo_gyr']:.2f}"
    )
    print(
        f"  [Fe/H] : {results['feh_peak']:.3f} (mode)  |  "
        f"median {results['feh_median']:.3f} "
        f"+{results['feh_hi'] - results['feh_median']:.3f} "
        f"/ -{results['feh_median'] - results['feh_lo']:.3f}"
    )
    print(
        f"  AV     : {results['AV_peak']:.3f} (mode)  |  "
        f"median {results['AV_median']:.3f} "
        f"+{results['AV_hi'] - results['AV_median']:.3f} "
        f"/ -{results['AV_median'] - results['AV_lo']:.3f}"
    )

    plot_posteriors(samples, host_name)

# ── Save ──────────────────────────────────────────────────────────────────────
out_path = "age_fit_results_singlestarmodel.csv"
pd.DataFrame(all_results).set_index("Star").to_csv(out_path)
print(f"\nResults written to {out_path}")
    