import numpy as np
import matplotlib.pyplot as plt
from isochrones import get_ichrone
import inspect
import isochrones.models
from isochrones.mist import MISTIsochroneGrid, MISTEvolutionTrackGrid

def patch_dm_deep():
    # Find any class inside isochrones.models that has a get_dm_deep method
    candidates = []
    for name, obj in vars(isochrones.models).items():
        if inspect.isclass(obj) and hasattr(obj, "get_dm_deep"):
            candidates.append(obj)

    if not candidates:
        raise RuntimeError("Could not find any class with get_dm_deep() in isochrones.models")

    # Patch ALL of them (safe), since only the relevant one will be used.
    for cls in candidates:
        orig = cls.get_dm_deep

        def make_safe(orig_func):
            def safe(self, *args, **kwargs):
                try:
                    return orig_func(self, *args, **kwargs)
                except KeyError:
                    # dm_deep is not needed for basic isochrone plotting, so return a benign value
                    return 0.0
            return safe

        cls.get_dm_deep = make_safe(orig)

    print("Patched get_dm_deep on:", [c.__name__ for c in candidates])

patch_dm_deep()

df = MISTIsochroneGrid().df

def nearest(val, grid):
    grid = np.asarray(grid, dtype=float)
    return float(grid[np.argmin(np.abs(grid - val))])

def get_iso_df(age_gyr, feh):
    log_age_target = np.log10(age_gyr * 1e9)
    ages = df.index.levels[df.index.names.index("log10_isochrone_age_yr")].values
    fehs = df.index.levels[df.index.names.index("feh")].values
    log_age = nearest(log_age_target, ages)
    feh_use = nearest(feh, fehs)
    iso = df.xs((log_age, feh_use), level=("log10_isochrone_age_yr", "feh")).copy()
    iso.attrs["log_age_used"] = log_age
    iso.attrs["feh_used"] = feh_use
    return iso


iso_1 = get_iso_df(1.0, -0.25)
iso_5 = get_iso_df(5.0, -0.25)
print(iso_1.columns)
logL1 = iso_1["logL"]
logL5 = iso_5["logL"]
logteff1 = iso_1["logTeff"]
logteff5 = iso_5["logTeff"]

fig, ax = plt.subplots()
plt.plot(logteff1, logL1, label = "1 Gyr")
plt.plot(logteff5, logL5, label = "5 Gyr")
plt.xlabel("Log Teff")
plt.ylabel("Log L")
plt.title("MIST 1 Gyr vs 5 Gyr Isochrones")
plt.legend()
plt.savefig("mist_isochrones_1Gyr_5Gyr.png")

