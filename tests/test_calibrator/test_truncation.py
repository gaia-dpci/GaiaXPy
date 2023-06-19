import unittest
from os.path import join

import numpy.testing as npt
import pandas as pd
from pandas import testing as pdt

from gaiaxpy import calibrate
from gaiaxpy.calibrator.calibrator import _create_spectrum
from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.core.generic_functions import str_to_array
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from tests.test_calibrator.calibrator_paths import mean_spectrum_csv, mean_spectrum_fits, mean_spectrum_xml,\
    mean_spectrum_xml_plain
from tests.files.paths import files_path
from tests.utils.utils import pos_file_to_array

# TODO: Add tests for AVRO format

parser = InternalContinuousParser()

# Load variables
label = 'calibrator'
bp_model = 'v211w'  # Alternative bp model
xp_sampling_grid, xp_merge = load_xpmerge_from_xml(bp_model=bp_model)
xp_design_matrices = load_xpsampling_from_xml(bp_model=bp_model)

# Path to solution files
calibrator_sol_path = join(files_path, 'calibrator_solution')

# Calibrate data in files
spectra_df_fits, _ = calibrate(mean_spectrum_fits, save_file=False, truncation=True)
spectra_df_xml, _ = calibrate(mean_spectrum_xml, save_file=False, truncation=True)
spectra_df_xml_plain, _ = calibrate(mean_spectrum_xml_plain, save_file=False, truncation=True)

# Generate converters
columns_to_parse = ['flux', 'flux_error']
converters = dict([(column, lambda x: str_to_array(x)) for column in columns_to_parse])

# Load solution files, default model
solution_default_sampling = pos_file_to_array(join(calibrator_sol_path, 'calibrator_solution_default_sampling.csv'))
truncation_default_solution_df = pd.read_csv(join(calibrator_sol_path, 'calibrator_solution_truncation_default.csv'),
                                             float_precision='high', converters=converters)

_rtol, _atol = 1e-22, 1e-22


class TestCalibratorTruncation(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser._parse(mean_spectrum_csv)
        # Create sampled basis functions
        sampled_basis_func = {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_design_matrices[band])
                              for band in BANDS}
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, truncation=True, design_matrix=sampled_basis_func, merge=xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model_csv(self):
        # Default sampling and default calibration sampling
        spectra_df_csv, positions = calibrate(mean_spectrum_csv, truncation=True, save_file=False)
        npt.assert_array_equal(positions, solution_default_sampling)
        pdt.assert_frame_equal(spectra_df_csv, truncation_default_solution_df, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(spectra_df_fits, truncation_default_solution_df, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(spectra_df_xml, truncation_default_solution_df, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(spectra_df_xml_plain, truncation_default_solution_df, rtol=_rtol, atol=_atol)
