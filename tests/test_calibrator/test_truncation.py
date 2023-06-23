import unittest

import numpy.testing as npt
from pandas import testing as pdt

from gaiaxpy import calibrate
from gaiaxpy.calibrator.calibrator import _create_spectrum
from gaiaxpy.core.config import load_xpmerge_from_xml, load_xpsampling_from_xml
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from tests.files.paths import mean_spectrum_fits_file, mean_spectrum_csv_file, mean_spectrum_xml_file,\
    mean_spectrum_xml_plain_file
from tests.test_calibrator.calibrator_solutions import sol_default_sampling_array, truncation_default_solution_df

# TODO: Add tests for AVRO format

parser = InternalContinuousParser()

# Load variables
label = 'calibrator'
bp_model = 'v211w'  # Alternative bp model
xp_sampling_grid, xp_merge = load_xpmerge_from_xml(bp_model=bp_model)
xp_design_matrices = load_xpsampling_from_xml(bp_model=bp_model)

# Calibrate data in files
spectra_df_fits, _ = calibrate(mean_spectrum_fits_file, save_file=False, truncation=True)
spectra_df_xml, _ = calibrate(mean_spectrum_xml_file, save_file=False, truncation=True)
spectra_df_xml_plain, _ = calibrate(mean_spectrum_xml_plain_file, save_file=False, truncation=True)


_rtol, _atol = 1e-22, 1e-22


class TestCalibratorTruncation(unittest.TestCase):

    def test_create_spectrum(self):
        # Read mean Spectrum
        parsed_spectrum_file, extension = parser._parse(mean_spectrum_csv_file)
        # Create sampled basis functions
        sampled_basis_func = {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_design_matrices[band])
                              for band in BANDS}
        first_row = parsed_spectrum_file.iloc[0]
        spectrum = _create_spectrum(first_row, truncation=True, design_matrix=sampled_basis_func, merge=xp_merge)
        self.assertIsInstance(spectrum, AbsoluteSampledSpectrum)

    def test_calibrate_both_bands_default_calibration_model_csv(self):
        # Default sampling and default calibration sampling
        spectra_df_csv, positions = calibrate(mean_spectrum_csv_file, truncation=True, save_file=False)
        npt.assert_array_equal(positions, sol_default_sampling_array)
        pdt.assert_frame_equal(spectra_df_csv, truncation_default_solution_df, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(spectra_df_fits, truncation_default_solution_df, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(spectra_df_xml, truncation_default_solution_df, rtol=_rtol, atol=_atol)
        pdt.assert_frame_equal(spectra_df_xml_plain, truncation_default_solution_df, rtol=_rtol, atol=_atol)
