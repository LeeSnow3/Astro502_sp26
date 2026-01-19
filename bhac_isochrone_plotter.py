import numpy as np
import matplotlib.pyplot as plt
import os

def read_bhac15_file(filepath):
    """
    Read a BHAC15 ASCII table file.

    Parameters:
    filepath (str): Path to the .dat file

    Returns:
    dict: Dictionary with column names as keys and numpy arrays as values
    """
    # Read the file, skipping the comment line
    data = np.loadtxt(filepath, comments='#')

    # Column names from the header
    columns = ['t', 'm', 'teff', 'logg', 'logL', 'Lum', 'R']

    # Create dictionary
    result = {}
    for i, col in enumerate(columns):
        result[col] = data[:, i]

    return result

def plot_bhac15_data():
    """
    Read and plot the BHAC data from the bhac15 folder.
    """
    # Files to read
    file1 = ['bhac15/bhac15_t_1.dat']
    file2 = ['bhac15/bhac15_t_5.dat']
    # Read data
    data1 = read_bhac15_file(file1[0])
    teff1 = data1["teff"]
    logL1 = data1['logL']
    mass_range1 = (data1['m'][0], data1['m'][-1])
    data2 = read_bhac15_file(file2[0])
    teff2 = data2["teff"]
    logL2 = data2['logL']
    mass_range2 = (data2['m'][0], data2['m'][-1])
    print(f"mass ranges: {mass_range1}, {mass_range2}")
    #plot isochrones
    plt.figure(figsize=(8, 6))
    plt.title('Bhac15 1 Gyr 5 Gyr Isochrones', fontsize=16)
    plt.scatter(teff1, logL1, label='1 Gyr')
    plt.scatter(teff2, logL2, label='5 Gyr')
    plt.xlabel('Effective Temperature (K)')
    plt.ylabel('log(L/L⊙)')
    plt.gca().invert_xaxis()  # Cooler stars on the right
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig('bhac_isochrones.png', dpi=150, bbox_inches='tight')
    plt.show()  


if __name__ == "__main__":
    plot_bhac15_data()