import numpy as np
import numpy.testing as npt

from gaiaxpy import calibrate
from gaiaxpy.core.config import load_xpmerge_from_file, load_xpsampling_from_file
from gaiaxpy.core.config_dispatcher import CalibratorDispatcher
from gaiaxpy.core.generic_variables import INV_BASIS_TYPES, RELEASES
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from tests.files.continuous import dr3_with_missing_bp_csv_file
from tests.reference.calibrator import sol_with_covariance_sampling_array
from tests.utils.utils import assert_dfs_equal


def test_with_covariance():
    kwargs = dict(save_file=False, release=RELEASES.dr3)
    with_correlation, sampling = calibrate(dr3_with_missing_bp_csv_file, with_correlation=True, **kwargs)
    without_correlation, _ = calibrate(dr3_with_missing_bp_csv_file, **kwargs)
    npt.assert_array_equal(sampling, sol_with_covariance_sampling_array)
    assert_dfs_equal(with_correlation.drop(columns=['correlation']), without_correlation, atol=0, rtol=0)

    inputs, _ = InternalContinuousParser().parse_file(dr3_with_missing_bp_csv_file)
    config = CalibratorDispatcher().build(sampling=None, parsed_input_data=inputs, release=RELEASES.dr3,
                                          basis_type=INV_BASIS_TYPES.basic)
    design = load_xpsampling_from_file(config)
    _, merge = load_xpmerge_from_file(config)

    for row, spectrum in zip(inputs.itertuples(index=False), with_correlation.itertuples(index=False), strict=True):
        assert row.source_id == spectrum.source_id
        available_bands = [band for band in BANDS
                           if isinstance(getattr(row, f'{band}_covariance_matrix'), np.ndarray)]
        expected = np.zeros((len(sampling), len(sampling)))
        for band in available_bands:
            coefficient_covariance = getattr(row, f'{band}_covariance_matrix') * (
                    getattr(row, f'{band}_standard_deviation') ** 2)
            projection = design[band].T
            if len(available_bands) == 2:
                projection = merge[band][:, None] * projection
            expected += projection @ coefficient_covariance @ projection.T

        # Check correlation values are in the expected range
        correlation = np.abs(spectrum.correlation)
        np.testing.assert_array_less(correlation[~np.isnan(correlation)], 1 + 1e-20)
        # A missing band leaves wavelengths outside its coverage masked.
        masked = np.isnan(spectrum.flux_error)
        expected[masked, :] = np.nan
        expected[:, masked] = np.nan
        i, j = np.tril_indices(len(sampling), k=-1)
        actual = np.diag(spectrum.flux_error ** 2)
        actual[i, j] = spectrum.correlation * spectrum.flux_error[i] * spectrum.flux_error[j]
        actual[j, i] = actual[i, j]

        npt.assert_allclose(actual, expected, rtol=1e-11,
                            atol=np.nanmax(np.abs(expected)) * 1e-13)
