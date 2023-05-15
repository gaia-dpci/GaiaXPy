import matplotlib.pyplot as plt

colours = [f'tab:{colour}' for colour in ['green', 'orange', 'purple', 'brown', 'pink', 'olive', 'cyan', 'grey']]


def plot_spectra_with_lines(source_id, sampling, bp_flux, rp_flux, wavelength, flux, bp_lines, rp_lines, save_plots):
    fig = plt.figure(figsize=(8, 8), layout='tight')
    fig.suptitle(str(source_id), fontsize=14)

    # BP
    ax1 = plt.subplot(221)
    if bp_flux is not None:
        ax1.plot(sampling, bp_flux, c='tab:blue')
        for i, line in enumerate(bp_lines):
            name, _, _, line_root, _, _, _, _, _, _, _, line_continuum_pwl, line_width_pwl = line
            ax1.axvline(line_root, ls='--', c=colours[i % len(colours)], label=name)
            ax1.plot([line_root - line_width_pwl * 0.5, line_root + line_width_pwl * 0.5],
                     [line_continuum_pwl, line_continuum_pwl], c='black', alpha=0.3)
        ax1.set_xlabel('Pseudo-wavelength')
        ax1.set_ylabel('Flux [e-/s]')
        if 0 < len(bp_lines) < 9:
            ax1.legend()
        elif len(bp_lines) > 8:
            ax1.legend(fontsize=6)

    # RP
    ax2 = plt.subplot(222)
    ax2.plot(sampling, rp_flux, c='tab:red')
    for i, line in enumerate(rp_lines):
        name, _, _, line_root, _, _, _, _, _, _, _, line_continuum_pwl, line_width_pwl = line
        ax2.axvline(line_root, ls='--', c=colours[(i + len(bp_lines)) % len(colours)], label=name)
        ax2.plot([line_root - line_width_pwl * 0.5, line_root + line_width_pwl * 0.5],
                 [line_continuum_pwl, line_continuum_pwl], c='black', alpha=0.3)
    ax2.set_xlabel('Pseudo-wavelength')
    ax2.set_ylabel('Flux [e-/s]')
    if 0 < len(rp_lines) < 9:
        ax2.legend()
    elif len(rp_lines) > 8:
        ax2.legend(fontsize=6)

    # Total
    ax3 = plt.subplot(212)
    ax3.plot(wavelength, flux, c='black')

    for i, line in enumerate(bp_lines):
        name, _, _, _, line_wv, _, _, line_width, _, line_continuum, _, _, _ = line
        ax3.axvline(line_wv, ls='-.', c=colours[i % len(colours)], label=name)
        ax3.plot([line_wv - line_width * 0.5, line_wv + line_width * 0.5], [line_continuum, line_continuum], c='black',
                 alpha=0.3)

    for i, line in enumerate(rp_lines):
        name, _, _, _, line_wv, _, line_depth, line_width, _, line_continuum, _, _, _ = line
        ax3.axvline(line_wv, ls=':', c=colours[(i + len(bp_lines)) % len(colours)], label=name)
        ax3.plot([line_wv - line_width * 0.5, line_wv + line_width * 0.5], [line_continuum, line_continuum], c='black',
                 alpha=0.3)

    ax3.set_xlabel('Wavelength [nm]')
    ax3.set_ylabel('Flux [W nm^-1 m^-2]')

    if 0 < len(bp_lines + rp_lines) < 13:
        ax3.legend()
    elif len(bp_lines + rp_lines) > 12:
        ax3.legend(fontsize=4)

    if save_plots:
        plt.savefig(str(source_id) + '.png', bbox_inches='tight', dpi=300)
    else:
        plt.show()
    return fig
