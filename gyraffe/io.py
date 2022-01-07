import pandas as pd

def read_mesa_profile(file):
    # Adapted from PyGYRE with speed improvement using pandas.read_table
    # Read data from the file

    with open(file, 'r') as f:

        header = f.readline().split()
        if len(header) == 4:
            version = 1
        elif len(header) == 5:
            version = int(header[-1])
        else:
            raise ValueError("Invalid header line in file '{:s}'".format(file))
        
        if version == 1:
            col_keys = ['k',
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
                        'eps_nuc*eps_rho']
        elif version == 19:
            col_keys = ['k',
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
                        'Omega_rot']
        elif version == 100:
            col_keys = ['k',
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
                        'Omega_rot']
        elif version == 101:
            col_keys = ['k',
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
                        'Omega_rot']
        else:
            raise ValueError("Invalid header line in file '{:s}': {:d}".format(file, version))
        
        table = pd.read_table(f, delimiter='\s+', names=col_keys)

    return table
