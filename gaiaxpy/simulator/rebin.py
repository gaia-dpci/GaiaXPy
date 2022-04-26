import numpy as np
from scipy.interpolate import interp1d

# TODO: use non-generic exceptions.
def _rebin(input_wavelength, tuple_flux_ferror, grid_wavelength):
    """
    PMN rebinning function, second version. Partially solves CB error issues.
    """
    input_values = tuple_flux_ferror[0]
    input_uncertainties = tuple_flux_ferror[1]
    size_input = len(input_wavelength)
    size_grid = len(grid_wavelength)
    grid_ranges = np.zeros(size_grid + 1)
    for i in range(1, size_grid):
        grid_ranges[i] = 0.5 * (grid_wavelength[i] + grid_wavelength[i - 1])
    grid_ranges[0] = grid_wavelength[0] - 0.5 * (grid_wavelength[1] - grid_wavelength[0])
    grid_ranges[size_grid] = grid_wavelength[size_grid - 1] + 0.5 * \
                            (grid_wavelength[size_grid - 1] - grid_wavelength[size_grid - 2])
    # Initialise the interpolators
    linear_flux = interp1d(input_wavelength, input_values, kind='linear')
    linear_error = interp1d(input_wavelength, input_uncertainties, kind='linear')
    extended_grid = []
    for i in range(size_input):
        extended_grid.append([input_wavelength[i], input_values[i], input_uncertainties[i]])
    for i in range(size_grid + 1):
        x = grid_ranges[i]
        y = 0; e = 0
        try:
            y = linear_flux(x)
        except Exception as err:
            print(err)
        try:
            e = linear_error(x)
        except Exception as err:
            print(err)
        extended_grid.append([x, y, e])
        extended_grid = sorted(extended_grid, key=lambda x: x[0])
    flux = []
    flux_error = []
    extended_grid_first_elements = [item[0] for item in extended_grid]
    for i in range(size_grid):
        i1 = extended_grid_first_elements.index(grid_ranges[i])
        i2 = extended_grid_first_elements.index(grid_ranges[i + 1])
        area = 0; error_correlated = 0
        for j in range(i1, i2):
            x_low = extended_grid[j][0]
            x_high = extended_grid[j+1][0]
            y_low = extended_grid[j][1]
            y_high = extended_grid[j+1][1]
            error_low = extended_grid[j][2]
            error_high = extended_grid[j+1][2]
            dx2 = 0.5 * (x_high - x_low)
            area += dx2 * (y_low + y_high)
            error_correlated += dx2 * (error_low + error_high)
        flux.append(area / (extended_grid[i2][0] - extended_grid[i1][0]))
        flux_error.append(error_correlated / (extended_grid[i2][0] - extended_grid[i1][0]))
    return flux, flux_error
