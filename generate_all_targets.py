import pyvo as vo
import pandas as pd
import io

# 1. Setup
# Use the synchronous TAP service endpoint
service = vo.dal.TAPService("https://exoplanetarchive.ipac.caltech.edu/TAP")

# 2. The "Mega-Scoop" Query
# We use 'run_sync' below to bypass local parsing errors.
query = """
SELECT 
    pl_name, hostname, 
    gaia_id,                
    tic_id,                 
    hd_name,                
    ra, dec, 
    sy_vmag, sy_jmag, sy_kmag,
    sy_tmag,                
    sy_kepmag,              
    sy_gaiamag,             
    st_teff, st_logg, st_met, 
    st_mass, st_rad,        
    st_spectype,            
    st_lum,                 
    st_age, st_ageerr1, st_ageerr2,
    st_rotp,                
    st_refname,             
    pl_refname,             
    pl_orbper, pl_rade, pl_trandur,
    disc_facility, disc_year
FROM pscomppars
WHERE 
    tran_flag = 1
ORDER BY ra
"""

print("Querying NASA Exoplanet Archive for the MEGA list...")

try:
    # FIX: Use run_sync() instead of search().
    # This bypasses the client-side ADQL parser that was causing the "No table name" error.
    result = service.run_sync(query)
    
    # Convert to DataFrame
    df = result.to_table().to_pandas()

    # 3. Clean Strings (TAP returns byte-strings for text columns)
    str_cols = ['pl_name', 'hostname', 'disc_facility', 'st_spectype', 
                'st_refname', 'pl_refname', 'hd_name', 'gaia_id', 'tic_id']
    
    for col in str_cols:
        if col in df.columns:
            # Decode bytes to strings
            df[col] = df[col].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
            # Fill NaNs with empty strings
            df[col] = df[col].fillna('')

    # 4. Tagging
    df['mission_source'] = 'Other'
    
    # Handle NaNs in disc_facility before tagging
    df['disc_facility'] = df['disc_facility'].fillna('')

    # Space Missions
    df.loc[df['disc_facility'].str.contains('Kepler', case=False), 'mission_source'] = 'Kepler'
    df.loc[df['disc_facility'].str.contains('K2', case=False), 'mission_source'] = 'K2'
    df.loc[df['disc_facility'].str.contains('TESS', case=False), 'mission_source'] = 'TESS'
    df.loc[df['disc_facility'].str.contains('CoRoT', case=False), 'mission_source'] = 'CoRoT'
    
    # Ground-Based Surveys
    df.loc[df['disc_facility'].str.contains('WASP', case=False), 'mission_source'] = 'WASP'
    df.loc[df['disc_facility'].str.contains('HAT', case=False), 'mission_source'] = 'HAT'
    df.loc[df['disc_facility'].str.contains('KELT', case=False), 'mission_source'] = 'KELT'
    df.loc[df['disc_facility'].str.contains('TRAPPIST', case=False), 'mission_source'] = 'TRAPPIST'
    df.loc[df['disc_facility'].str.contains('NGTS', case=False), 'mission_source'] = 'NGTS'

    # 5. Save
    filename = "ASTR502_Mega_Target_List.csv"
    df.to_csv(filename, index=False)

    print(f"Success! Downloaded {len(df)} planets.")
    print(f"Saved to {filename}")
    
    # Verification
    print("\nTop 5 Spectral Types found:")
    print(df['st_spectype'].value_counts().head())

except Exception as e:
    print(f"PyVO Error: {e}")
    print("Attempting fallback with Astroquery...")
    
    # Fallback method if PyVO continues to struggle
    try:
        from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
        # Astroquery handles the connection differently and is often more robust
        table = NasaExoplanetArchive.query_adql(query)
        df = table.to_pandas()
        
        # Save (skipping the full cleanup for brevity, but it usually returns strings)
        filename = "ASTR502_Mega_Target_List_Astroquery.csv"
        df.to_csv(filename, index=False)
        print(f"Success with Astroquery! Saved to {filename}")
        
    except ImportError:
        print("Astroquery not installed.")
    except Exception as e2:
        print(f"Fallback failed: {e2}")