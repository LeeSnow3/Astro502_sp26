import pandas as pd
import numpy as np

def read_star_row_from_csv(
    host_name: str,
    sigma_mag: bool = True,
    sigma_parallax: float = 0.1,
):
    master_csv_path = "mega_target_list.csv"
    master_phot_csv_path = "master_photometrylist.csv"
    
    master_df = pd.read_csv(master_csv_path)
    phot_df = pd.read_csv(master_phot_csv_path)
    index = master_df[master_df["hostname"] == host_name].index[0]
    phot_index = phot_df[phot_df["hostname"] == host_name].index[0]
    # Select row
    row = master_df.iloc[index]
    phot_row = phot_df.iloc[phot_index]

    # Build props dict
    props = {}

    # --- Parallax (required) ---
    if not np.isnan(row["st_parallax_mas"]):
        props["parallax"] = (row["st_parallax_mas"], sigma_parallax)
    
    #Teff
    if not np.isnan(row["st_teff"]):
        props["Teff"] = row["st_teff"]
        props["Teff_err"] = 100  

    #feh
    if not np.isnan(row["st_met"]):
        props["feh"] = row["st_met"]
        props["feh_err"] = 0.1  # placeholder error (0.1 dex)
    
    #age
    if not np.isnan(row["st_age"]):
        props["age_gyr"] = row["st_age"]
        props["age_gyr_err"] = row["st_ageerr1"] if not np.isnan(row["st_ageerr1"]) else row["st_ageerr2"] if not np.isnan(row["st_ageerr2"]) else 0.5  # use err1 if available, else err2, else default to 0.5 Gyr
   
    # band map from master_phot_csv to MIST keys
    band_map = {
        "gaiaGmag": "G_mag",
        "gaiaBPmag": "BP_mag",
        "gaiaRPmag": "RP_mag",
        "Jmag": "J_mag",
        "Hmag": "H_mag",
        "Kmag": "K_mag",
    }
    #get photometry from phot_df
    for csv_col, iso_key in band_map.items():
        if csv_col in phot_row and not np.isnan(phot_row[csv_col]):
            sigmamag = 0.02 if sigma_mag is False else phot_row[f"e_{csv_col}"]
            props[iso_key] = phot_row[csv_col]
            props[f"{iso_key}_err"] = sigmamag

    print(len(props))
    return props
