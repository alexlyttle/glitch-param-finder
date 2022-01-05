import argparse
import numpy as np
import pygyre as pg
import pandas as pd
import matplotlib.pyplot as plt

from scipy.integrate import cumtrapz

def load_profile(filepath):
    """Loads a GYRE profile and converts to pandas."""
    profile = pg.read_model(filepath).to_pandas()
    return profile

def sound_speed(profile):
    """Calculates the adiabatic speed of sound across the profile."""
    return np.sqrt(profile['Gamma_1'] * profile['P'] / profile['rho'])

def acoustic_depth(profile):
    """Cumulatively integrates the acoustic depth, $tau = - \int_R^r dr/c$.
    
    Note:
        The profile goes radially out from the centre of the star, and thus must be reversed.
        Acoustic depth increases radially from the stellar surface.
    """
    return - cumtrapz(1/profile['c'].iloc[::-1], profile['r'].iloc[::-1], initial=0)[::-1]

def smooth(x, window):
    """Smooth y using a box kernel of size window."""
    box = np.ones(window)/window
    x_smooth = np.convolve(x, box, mode='same')
    return x_smooth

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
    mult
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

def find_glitch_params(filepath, make_plots=False):
    profile = load_profile(filepath)
    profile['c'] = sound_speed(profile)
    profile['tau'] = acoustic_depth(profile)
    profile['gamma_smooth'] = smooth(profile['Gamma_1'], 50)
    
    he_cond = (profile['T'] > 4e4) & (profile['T'] < 2e5)
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
    
    idx_min = profile.loc[(profile['N^2'] > 0)].iloc[0].name  # First positive
#     dN2 = np.gradient(profile['N^2'])
    cz_cond = (profile['N^2'] < 0)  # & (dN2 < 0)
    
    tau_cz = profile[cz_cond].loc[idx_min:, 'tau'].iloc[0]
    gamma_cz = profile[cz_cond].loc[idx_min:, 'Gamma_1'].iloc[0]
#     c_cz, d_cz, delta_cz = get_delta_cz(profile, tau_cz)
#     amp_cz = delta_cz / 16 / np.pi**2 / T # see my derivation from Houdek & Gough (2007)
    # dnu_cz = amp_cz * delta_nu / nu**2 * sin(...)

#     tau_cz = profile.loc[cz_cond, 'tau'].iloc[0]
#     gamma_cz = profile.loc[cz_cond, 'Gamma_1'].iloc[0]
    
    if make_plots:
        fig, axes = plt.subplots(2, 1, figsize=(6.4, 8.0), sharex=True, gridspec_kw={'hspace': 0.05})
        plot_gamma(axes[0], profile, tau, tau_he, gamma_he, delta_he, tau_cz, gamma_cz)
        plot_n2(axes[1], profile)

    return pd.Series({
        'tau_he': tau_he,
        'delta_he': delta_he,
        'amp_he': amp_he,
        'tau_cz': tau_cz,
#         'delta_cz': delta_cz,
#         'amp_cz': amp_cz,
#         'c_cz': c_cz,
#         'd_cz': d_cz,
    })

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath', help='path to GYRE profile file')
    parser.add_argument('-p', '--plot', action='store_true',
                        help='make plots')
    args = parser.parse_args()
    out = find_glitch_params(args.filepath, make_plots=args.plot)
    print(out)
    if args.plot:
        plt.show()
