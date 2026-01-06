import requests
import pandas as pd
import io

# 1. Define the Query (One single line, no comments, correct columns)
query_text = """
SELECT pl_name, hostname, gaia_dr3_id, gaia_dr2_id, tic_id, hd_name, ra, dec, sy_vmag, sy_jmag, sy_kmag, sy_tmag, sy_kepmag, sy_gaiamag, st_teff, st_logg, st_met, st_mass, st_rad, st_spectype, st_lum, st_age, st_ageerr1, st_ageerr2, st_rotp, pl_orbper, pl_rade, pl_trandur, disc_facility, disc_year FROM pscomppars WHERE tran_flag = 1 ORDER BY ra
"""

# Flatten just in case copy-pasting introduced breaks
query_clean = " ".join(query_text.split())

print("Querying NASA Exoplanet Archive (Direct HTTP / Flattened)...")

# 2. Send Request
url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
payload = {
    "query": query_clean,
    "format": "csv"
}

try:
    response = requests.post(url, data=payload)
    response.raise_for_status() 
    
    # 3. Load into Pandas
    df = pd.read_csv(io.StringIO(response.text))

    # 4. Clean Strings
    str_cols = ['pl_name', 'hostname', 'disc_facility', 'st_spectype', 
                'hd_name', 'tic_id', 'gaia_dr3_id', 'gaia_dr2_id']
    
    for col in str_cols:
        if col in df.columns:
            # Force to string, remove byte artifacts, handle nan
            df[col] = df[col].astype(str).str.replace("b'", "").str.replace("'", "")
            df[col] = df[col].replace('nan', '')
            df[col] = df[col].replace('<NA>', '')

    # 5. Tagging Logic
    df['mission_source'] = 'Other'
    df['disc_facility'] = df['disc_facility'].fillna('')

    # Space
    df.loc[df['disc_facility'].str.contains('Kepler', case=False), 'mission_source'] = 'Kepler'
    df.loc[df['disc_facility'].str.contains('K2', case=False), 'mission_source'] = 'K2'
    df.loc[df['disc_facility'].str.contains('TESS', case=False), 'mission_source'] = 'TESS'
    df.loc[df['disc_facility'].str.contains('CoRoT', case=False), 'mission_source'] = 'CoRoT'
    
    # Ground
    df.loc[df['disc_facility'].str.contains('WASP', case=False), 'mission_source'] = 'WASP'
    df.loc[df['disc_facility'].str.contains('HAT', case=False), 'mission_source'] = 'HAT'
    df.loc[df['disc_facility'].str.contains('KELT', case=False), 'mission_source'] = 'KELT'
    df.loc[df['disc_facility'].str.contains('TRAPPIST', case=False), 'mission_source'] = 'TRAPPIST'
    df.loc[df['disc_facility'].str.contains('NGTS', case=False), 'mission_source'] = 'NGTS'

    # 6. Save
    filename = "ASTR502_Mega_Target_List.csv"
    df.to_csv(filename, index=False)

    # 7. Final Statistics
    num_planets = len(df)
    num_stars = df['hostname'].nunique()
    
    print("-" * 30)
    print(f"Success! Data saved to {filename}")
    print("-" * 30)
    print(f"Total Planets found:      {num_planets}")
    print(f"Total Unique Stars:       {num_stars}")
    print("-" * 30)
    print("Breakdown by Mission Source (Planets):")
    print(df['mission_source'].value_counts())

except Exception as e:
    print(f"Error: {e}")