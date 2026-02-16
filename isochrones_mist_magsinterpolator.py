from __future__ import annotations

from typing import Iterable, Dict, Any
from isochrones.mist import MIST_EvolutionTrack
from isochrones import get_ichrone


def mist_mags_from_mass_age_feh(
    mass: float,
    age: float,
    feh: float,
    *,
    bands: Iterable[str] = ("G_mag", "BP_mag", "RP_mag", "J_mag", "H_mag", "K_mag"),
    distance: float = 10.0,
    AV: float = 0.0,
    use_track_feh: str = "initial_feh",  # "initial_feh" (recommended) or "feh"
) -> Dict[str, Any]:
    """
    Workflow:
      (mass, age, feh) -> EEP via MIST evolutionary track -> evaluate MIST isochrone at (EEP, age, feh).

    Parameters
    ----------
    mass : Msun
    age  : log10(age/yr), as used by isochrones/MIST (e.g. 9.75)
    feh  : [Fe/H] input
    bands: keys to return (must exist in the MIST grid)
    distance : pc (apparent mags)
    AV : mag (V-band extinction)
    use_track_feh : which metallicity to pass to the isochrone evaluation:
        - "initial_feh": use the input feh (best matches grid parameterization)
        - "feh": use the track's returned surface feh (if present)

    Returns
    -------
    dict with eep, plus requested bands and a few useful stellar params.
    """

    # 1) Track: get EEP and (optionally) consistent metallicity
    track = MIST_EvolutionTrack()
    t = track.generate(mass, age, feh, distance=distance, AV=AV, return_dict=True)

    if "eep" not in t:
        raise RuntimeError("Track generate() did not return an 'eep' field.")

    eep = float(t["eep"])

    # Choose which feh to pass forward
    feh_for_iso = float(feh)
    if use_track_feh == "feh" and "feh" in t:
        feh_for_iso = float(t["feh"])

    # 2) Isochrone: evaluate at (eep, age, feh)
    mist = get_ichrone("mist")
    print(type(mist))
    print([a for a in dir(mist) if "eep" in a.lower()])
    print([a for a in dir(mist) if "interp" in a.lower()])

    # Try a few common call signatures; isochrones has changed a bit across versions.
    # We'll attempt the most common ones first.
    def _eval_iso() -> Dict[str, Any]:
        # Signature A (common): mist.interp_value(eep, age, feh, param)
        out: Dict[str, Any] = {}
        for key in set(bands) | {"Teff", "logg", "logL", "radius", "mass"}:
            try:
                out[key] = float(mist.interp_value(eep, age, feh_for_iso, key))
            except Exception:
                # Signature B: mist(eep, age, feh, distance=..., AV=...) returning dict/series
                pass
        if len(out) >= 1:
            return out

        # Try calling the model directly (many versions support this)
        try:
            row = mist(eep, age, feh_for_iso, distance=distance, AV=AV)
            # row might be a pandas Series-like or dict-like
            return {k: float(row[k]) for k in row.keys()}
        except Exception:
            pass

        # Try evaluate() if available
        if hasattr(mist, "evaluate"):
            row = mist.evaluate(eep, age, feh_for_iso, distance=distance, AV=AV)
            return {k: float(row[k]) for k in row.keys()}

        raise RuntimeError(
            "Couldn't evaluate the MIST isochrone at (eep, age, feh). "
            "Your isochrones version may use a different API."
        )

    iso_vals = _eval_iso()

    # 3) Package results: EEP + requested outputs
    result = {
        "eep": eep,
        "age": float(age),
        "feh": float(feh_for_iso),
        "distance": float(distance),
        "AV": float(AV),
        # some helpful core params if present
        "Teff": iso_vals.get("Teff"),
        "logg": iso_vals.get("logg"),
        "logL": iso_vals.get("logL"),
        "radius": iso_vals.get("radius"),
        "mass_current": iso_vals.get("mass"),
    }

    for b in bands:
        if b not in iso_vals:
            raise KeyError(f"Band '{b}' not found from isochrone evaluation outputs.")
        result[b] = iso_vals[b]

    return result


if __name__ == "__main__":
    mass, age, feh = 1.0, 9.75, -0.05
    out = mist_mags_from_mass_age_feh(
        mass, age, feh,
        bands=("G_mag", "BP_mag", "RP_mag", "J_mag", "H_mag", "K_mag"),
        distance=100.0,
        AV=0.02,
        use_track_feh="initial_feh",
    )

    # Pretty-print
    from pprint import pprint
    pprint(out, sort_dicts=False)
