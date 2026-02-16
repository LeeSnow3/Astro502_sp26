from isochrones import get_ichrone

# Build once (cache it) so you don't reload grids every call.
_TRACKS = get_ichrone("mist", tracks=True)

def get_model_mag(mass: float, age: float, feh: float,
                  distance: float = 10.0, AV: float = 0.0) -> dict:

    print(f"available bands: {_TRACKS.bands}")
    #bands = ["G", "BP", "RP", "J", "H", "K"]
    bands = ["BP_mag", "G_mag", "RP_mag"]

    # tracks.generate returns a dict with physical params + band mags
    out = _TRACKS.generate(mass, age, feh, distance=distance, AV=AV, return_dict=True)

    missing = [b for b in bands if b not in out]
    if missing:
        raise KeyError(f"{sorted(out.keys())}")

    return {b: float(out[b]) for b in bands}


if __name__ == "__main__":
    mags = get_model_mag(1.03, 9.72, -0.11)
    print(mags)


