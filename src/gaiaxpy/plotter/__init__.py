"""Plot sampled spectra returned by calibrate and convert.

The public entry point is gaiaxpy.plot_spectra. Supply the sampled-spectrum
DataFrame and its sampling array. Plot rows separately with flux-error shading,
or combine them without error shading. Axis labels come from the spectrum
class stored in the DataFrame's data_type attribute.
"""
