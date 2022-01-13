import logging
import pandas as pd

LOGGER = logging.getLogger(__name__)

# Column names for each file version number
COLUMN_NAMES = {
    1: ['k',
        'r',
        'M_r/(M-M_r)',
        'L_r',
        'P',
        'T',
        'rho',
        'nabla',
        'N^2',
        'c_V',
        'c_P',
        'chi_T',
        'chi_rho',
        'kap',
        'kap_T',
        'kap_rho',
        'eps',
        'eps_nuc*eps_T',
        'eps_nuc*eps_rho'],
    19: ['k',
         'r',
         'M_r/(M-M_r)',
         'L_r',
         'P',
         'T',
         'rho',
         'nabla',
         'N^2',
         'Gamma_1',
         'nabla_ad',
         'delta',
         'kap',
         'kap_T',
         'kap_rho',
         'eps',
         'eps_nuc*eps_T',
         'eps_nuc*eps_rho',
         'Omega_rot'],
    100: ['k',
          'r',
          'M_r',
          'L_r',
          'P',
          'T',
          'rho',
          'nabla',
          'N^2',
          'Gamma_1',
          'nabla_ad',
          'delta',
          'kap',
          'kap kap_T',
          'kap kap_rho',
          'eps',
          'eps_nuc*eps_T',
          'eps_nuc*eps_rho',
          'Omega_rot'],
    101: ['k',
          'r',
          'M_r',
          'L_r',
          'P',
          'T',
          'rho',
          'nabla',
          'N^2',
          'Gamma_1',
          'nabla_ad',
          'delta',
          'kap',
          'kap kap_T',
          'kap kap_rho',
          'eps_nuc',
          'eps_nuc*eps_T',
          'eps_nuc*eps_rho',
          'Omega_rot'],
}

def read_mesa_profile(filename):
    """Read MESA profile and return """
    # Adapted from PyGYRE with speed improvement using pandas.read_table
    # Read data from the file

    LOGGER.debug(f"Open file '{filename}'")
    
    if isinstance(filename, str):
        filename = open(filename, 'r')
    
    with filename as file:
        
        LOGGER.debug("Parse header")
        header = file.readline().split()
        if len(header) == 4:
            version = 1
        elif len(header) == 5:
            version = int(header[-1])
        else:
            # Basic header validation
            raise ValueError(f"Invalid header line in file '{filename:s}'")
        
        LOGGER.debug(f"Get column names for version {version:d}")
        names = COLUMN_NAMES.get(version, None)
        if names is None:
            raise ValueError(f"Invalid header line in file '{filename:s}': {version:d}")
        
        LOGGER.debug("Read table")
        profile = pd.read_table(file, delimiter='\s+', names=names)

    return profile
