import matplotlib.pyplot as plt

col = ['tab:green','tab:orange','tab:purple','tab:brown','tab:pink','tab:olive','tab:cyan','tab:grey']

def plot_spectra_with_lines(source_id, sampling, bpflux, rpflux, wavelength, flux, continuum, bplines, rplines):

    fig = plt.figure(figsize=(8,8), layout='tight')
    fig.suptitle(str(source_id), fontsize=14)
   
    # bp
    ax1 = plt.subplot(221)
    ax1.plot(sampling, bpflux, c='tab:blue')
    for i,line in enumerate(bplines):
        name,line_pwl,i_line,line_root,line_wv,line_flux,line_depth,line_width = line
        ax1.axvline(line_root, ls='--', c=col[i%len(col)], label = name)
    ax1.set_xlabel('Pseudo-wavelength')
    ax1.set_ylabel('Flux [e-/s]')
    if len(bplines)>0: ax1.legend()
   
    # rp
    ax2 = plt.subplot(222)
    ax2.plot(sampling, rpflux, c='tab:red')
    for i,line in enumerate(rplines):
        name,line_pwl,i_line,line_root,line_wv,line_flux,line_depth,line_width = line
        ax2.axvline(line_root, ls='--', c=col[i%len(col)+len(bplines)], label = name)
    ax2.set_xlabel('Pseudo-wavelength')
    ax2.set_ylabel('Flux [e-/s]')
    if len(rplines)>0: ax2.legend()
   
    # total
    ax3 = plt.subplot(212)
    ax3.plot(wavelength, flux, c='black')
    ax3.plot(wavelength, continuum, c='black', ls='--')
    for i,line in enumerate(bplines+rplines):
        name,line_pwl,i_line,line_root,line_wv,line_flux,line_depth,line_width = line
        ax3.axvline(line_wv, ls='-.', c=col[i%len(col)], label = name)
    ax3.set_xlabel('Wavelength [nm]')
    ax3.set_ylabel('Flux [W nm^-1 m^-2]')
    if len(bplines+rplines)>0: ax3.legend()
   
    plt.show()


