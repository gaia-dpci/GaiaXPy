import matplotlib.pyplot as plt

col = ['tab:green', 'tab:orange', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:olive', 'tab:cyan', 'tab:grey']


def plot_spectra_with_lines(source_id, sampling, bpflux, rpflux, wavelength, flux, continuum, bplines, rplines,
                            save_plots):
    fig = plt.figure(figsize=(8, 8), layout='tight')
    fig.suptitle(str(source_id), fontsize=14)

    # bp
    ax1 = plt.subplot(221)
    if bpflux is not None:
        ax1.plot(sampling, bpflux, c='tab:blue')
        for i, line in enumerate(bplines):
            name, line_pwl, i_line, line_root, line_wv, line_flux, line_depth, line_width, line_sig, line_continuum, line_sig_pwl, line_continuum_pwl, line_width_pwl = line
            ax1.axvline(line_root, ls='--', c=col[i % len(col)], label=name)
            ax1.plot([line_root - line_width_pwl * 0.5, line_root + line_width_pwl * 0.5],
                     [line_continuum_pwl, line_continuum_pwl], c='black', alpha=0.3)
        ax1.set_xlabel('Pseudo-wavelength')
        ax1.set_ylabel('Flux [e-/s]')
        if 0 < len(bplines) < 9:
            ax1.legend()
        elif len(bplines) > 8:
            ax1.legend(fontsize=6)

    # rp
    ax2 = plt.subplot(222)
    ax2.plot(sampling, rpflux, c='tab:red')
    for i, line in enumerate(rplines):
        name, line_pwl, i_line, line_root, line_wv, line_flux, line_depth, line_width, line_sig, line_continuum, line_sig_pwl, line_continuum_pwl, line_width_pwl = line
        ax2.axvline(line_root, ls='--', c=col[(i + len(bplines)) % len(col)], label=name)
        ax2.plot([line_root - line_width_pwl * 0.5, line_root + line_width_pwl * 0.5],
                 [line_continuum_pwl, line_continuum_pwl], c='black', alpha=0.3)
    ax2.set_xlabel('Pseudo-wavelength')
    ax2.set_ylabel('Flux [e-/s]')
    if 0 < len(rplines) < 9:
        ax2.legend()
    elif len(rplines) > 8:
        ax2.legend(fontsize=6)

    # total
    ax3 = plt.subplot(212)
    ax3.plot(wavelength, flux, c='black')
    # ax3.plot(wavelength, continuum, c='black', ls='--')
    for i, line in enumerate(bplines):
        name, line_pwl, i_line, line_root, line_wv, line_flux, line_depth, line_width, line_sig, line_continuum, line_sig_pwl, line_continuum_pwl, line_width_pwl = line
        ax3.axvline(line_wv, ls='-.', c=col[i % len(col)], label=name)
        ax3.plot([line_wv - line_width * 0.5, line_wv + line_width * 0.5], [line_continuum, line_continuum], c='black',
                 alpha=0.3)
    for i, line in enumerate(rplines):
        name, line_pwl, i_line, line_root, line_wv, line_flux, line_depth, line_width, line_sig, line_continuum, line_sig_pwl, line_continuum_pwl, line_width_pwl = line
        ax3.axvline(line_wv, ls=':', c=col[(i + len(bplines)) % len(col)], label=name)
        ax3.plot([line_wv - line_width * 0.5, line_wv + line_width * 0.5], [line_continuum, line_continuum], c='black',
                 alpha=0.3)
    ax3.set_xlabel('Wavelength [nm]')
    ax3.set_ylabel('Flux [W nm^-1 m^-2]')
    if 0 < len(bplines + rplines) < 13:
        ax3.legend()
    elif len(bplines + rplines) > 12:
        ax3.legend(fontsize=4)

    if save_plots:
        plt.savefig(str(source_id) + '.png', bbox_inches='tight', dpi=300)
    else:
        plt.show()
    return fig
