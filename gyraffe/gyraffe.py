import os, argparse, logging
import numpy as np
import pandas as pd

from multiprocessing import Pool
from ast import literal_eval
from tqdm import tqdm

from .io import read_mesa_profile

# MAKE_PLOTS = False
LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_version():
    with open(os.path.join(PACKAGE_DIR, 'version.txt')) as file:
        version = literal_eval(file.readline())
    return version
    
def smooth(x, window):
    """Smooth y using a box kernel of size window."""
    LOGGER.debug(f'Smooth input with a window width of {window}')
    box = np.ones(window)/window
    x_smooth = np.convolve(x, box, mode='same')
    return x_smooth

def cumulative_trapz(y, x):
    """1D cumulative trapezium method for numerical integration"""
    LOGGER.debug('Comute cumulative integral using trapezium method')
    y = np.array(y)
    x = np.array(x)
    res = np.zeros_like(y)
    res[1:] = np.cumsum(0.5 * np.diff(x) * (y[1:] + y[:-1]))
    return res

def sound_speed(profile):
    """Calculates the adiabatic speed of sound across the profile."""
    LOGGER.debug('Calculate sound speed')
    if 'Gamma_1' not in profile.columns:
        raise KeyError('First adiabatic exponant Gamma_1 must be present in the input file.')
    return np.sqrt(profile['Gamma_1'] * profile['P'] / profile['rho'])

def acoustic_depth(profile):
    """Cumulatively integrates the acoustic depth, $tau = - \int_R^r dr/c$.
    
    Note:
        The profile goes radially out from the centre of the star, and thus must be reversed.
        Acoustic depth increases radially from the stellar surface.
    """
    return - cumulative_trapz(1/profile['c'].iloc[::-1], profile['r'].iloc[::-1])[::-1]

def plot_gamma(ax, profile, tau, tau_he, gamma_he, delta_he, tau_cz, gamma_cz):
    """Plot the first adiabatic exponant with the locations of the BCZ and HeII zones."""
    profile.plot(x='tau', y='Gamma_1', ax=ax)
    ax.plot(tau_cz, gamma_cz, linestyle='none', marker='o', label='BCZ')
    ax.plot(tau_he, gamma_he, marker='o', linestyle='none', label='HeII')
    ax.axvspan(tau.iloc[-1], tau.iloc[0], edgecolor='C0', facecolor='none', alpha=0.5, 
               hatch='//', label='4e4 < T/K < 2e5')
    ax.axvspan(tau_he-delta_he, tau_he+delta_he, color='C2', alpha=0.2, label=r'$2\Delta$')
    
    ax.set_xlabel('acoustic depth (s)')
    ax.set_ylabel('first adiabatic exponant')
    ax.legend()
    return ax

def plot_n2(ax, profile):
    """Plot the Brunt-Väisälä frequency squared."""
    profile.plot(x='tau', y='N^2', ax=ax)
    ax.set_xlabel('acoustic depth (s)')
    ax.set_ylabel('Brunt-Väisälä frequency squared (s-2)')
    ax.set_yscale('log')
#     ax.set_xscale('log')

def get_delta_cz(profile, tau, window_width=200.):
    """Gets the delta term for the BCZ from the max-min of d2ln(rho)/dr2 about tau_cz.
    TODO!
    """
    drho_dr = np.gradient(np.log(profile['rho']), profile['r'])
    d2rho_dr2 = np.gradient(drho_dr, profile['r'])
#     mask = (profile['tau'] > tau - window_width) & (profile['tau'] < tau + window_width)
#     diff = d2rho_dr2[mask]
    cz = profile['tau'] == tau
    sound_speed = profile.loc[cz, 'c'].iloc[0]
    # tau_cz will always be below true tau_cz due to methods above
    # Thus we can take the difference between the max and the gradient at tau_cz
#     delta = (diff.max() - d2rho_dr2[cz][0])
    
    g = np.gradient(d2rho_dr2*1e20, profile['r'])
    cond = np.abs(g) < 1e-9

    pre_cz = (profile['tau'] < tau) & (profile['tau'] > tau - window_width)
    p1 = np.polyfit(profile.loc[pre_cz & cond, 'r'], drho_dr[pre_cz & cond], 1)

    post_cz = (profile['tau'] > tau) & (profile['tau'] < tau + window_width)
    p2 = np.polyfit(profile.loc[post_cz & cond, 'r'], drho_dr[post_cz & cond], 1)
    
    delta = p2[0] - p1[0]
    return sound_speed, delta, 0.5 * sound_speed**2 * delta

def find_glitch_params(filename, make_plots=False):
    LOGGER.debug(f"Find glitch parameters for file '{filename}'")
    profile = read_mesa_profile(filename)
    
    profile['c'] = sound_speed(profile)
    profile['tau'] = acoustic_depth(profile)
    profile['gamma_smooth'] = smooth(profile['Gamma_1'], 50)
    
    tau_he, delta_he, gamma_he, amp_he = (np.nan, np.nan, np.nan, np.nan)
    he_cond = (profile['T'] > 4e4) & (profile['T'] < 2e5)
    
    if any(he_cond):
        tau = profile.loc[he_cond, 'tau']
        gamma = profile.loc[he_cond, 'gamma_smooth']
        dgamma = np.gradient(gamma)
        dgamma2 = np.gradient(dgamma)
        mask = (dgamma > 0) & (dgamma2 > 0)
        
        tau_he = tau[mask].iloc[0]
        delta_he = tau_he - tau[mask].iloc[-1]
        gamma_he = profile[he_cond].loc[mask, 'Gamma_1'].iloc[0]
        gamma0 = 1.651
        Gamma_he = 2* delta_he * np.sqrt(2*np.pi) * (gamma0 - gamma_he) / (gamma0 + gamma_he)
        
        T = profile['tau'].iloc[0]
        amp_he = np.pi * Gamma_he / T # equation (16) Houdek & Gough (2007)
    
    tau_cz, delta_cz, gamma_cz, amp_cz = (np.nan, np.nan, np.nan, np.nan)
    conv = profile['N^2'] < 0

    if any(conv):
        # if any part is convective look for the lower boundary of the
        # outermost convective zone
        conv_zone_start = conv.loc[conv == True].index[-1]
        conv = conv.loc[:conv_zone_start]  # trim up to conv zone start
        idx_cz = conv.loc[conv == False].index[-1]
        tau_cz = profile.loc[idx_cz, 'tau']
        gamma_cz = profile.loc[idx_cz, 'Gamma_1']
    
    # TODO: figure out all this stuff if needed
    #  c_cz, d_cz, delta_cz = get_delta_cz(profile, tau_cz)
    #  amp_cz = delta_cz / 16 / np.pi**2 / T # see my derivation from Houdek & Gough (2007)
    # dnu_cz = amp_cz * delta_nu / nu**2 * sin(...)

    #  tau_cz = profile.loc[cz_cond, 'tau'].iloc[0]
    #  gamma_cz = profile.loc[cz_cond, 'Gamma_1'].iloc[0]
    
    # if make_plots:
    # # TODO!
    #     _, axes = plt.subplots(2, 1, figsize=(6.4, 8.0), sharex=True, gridspec_kw={'hspace': 0.05})
    #     plot_gamma(axes[0], profile, tau, tau_he, gamma_he, delta_he, tau_cz, gamma_cz)
    #     plot_n2(axes[1], profile)
    #     plt.show()
    return pd.Series({
        'filename': filename,
        'tau_he': tau_he,
        'delta_he': delta_he,
        'amp_he': amp_he,
        'tau_cz': tau_cz,
#         'delta_cz': delta_cz,
#         'amp_cz': amp_cz,
#         'c_cz': c_cz,
#         'd_cz': d_cz,
    })

def pool_glitch_params(filenames, num_processes=1, chunksize_factor=4):
    
    chunksize, extra = divmod(len(filenames), num_processes * chunksize_factor)
    if extra:  # If leftover, add to chunksize
        chunksize += 1
        
    with Pool(num_processes) as pool:
        # Create iterator map
        # TODO need way to make plots
        imap = pool.imap_unordered(find_glitch_params, filenames, chunksize)
        outputs = [output for output in imap]
    return outputs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='+', 
                        help='GYRE profile filename(s)')
    # parser.add_argument('-p', '--plot', action='store_true',
    #                     help='make plots')
    parser.add_argument('-p', '--processes', type=int, default=1,
                        help='number of parallel processes (defaults to 1)')
    parser.add_argument('-o', '--output', type=str,
                        help='filename to which to output results')
    parser.add_argument('--log-file', type=str,
                        help='filename to which to output log')
    parser.add_argument('--log-level', type=str, default='WARNING',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        )

    args = parser.parse_args()
    
    root = logging.getLogger('gyraffe')  # Log all in gyraffe module
    
    if args.log_file is not None:
        formatter = logging.Formatter('%(asctime)s %(name)-15s %(levelname)-8s %(message)s')
        handler = logging.FileHandler(args.log_file)
        handler.setFormatter(formatter)
        root.addHandler(handler)
    
    root.setLevel(args.log_level)
    root.info(f'Using gyraffe v{get_version()}')
    
    if args.processes == 1:
        outputs = [find_glitch_params(filename) for filename in \
            tqdm(args.filenames, desc='Finding glitch parameters', unit='files')]
    else:
        outputs = pool_glitch_params(args.filenames, num_processes=args.processes)

    df = pd.DataFrame(outputs)
    if args.output is None:
        print('\nGlitch parameters:')
        print(df)
    else:
        root.debug(f'Save input to \'{args.output}\'')
        df.to_csv(args.output, index=False)
        root.info(f'Output saved as CSV to \'{args.output}\'')

if __name__ == '__main__':
    main()
