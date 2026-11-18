from gaiaxpy.core.config import load_xpmerge_from_file, load_xpsampling_from_file
from gaiaxpy.core.config_dispatcher import CalibratorDispatcher
from gaiaxpy.core.generic_variables import RELEASES, INV_BASIS_TYPES
from gaiaxpy.core.satellite import BANDS
from gaiaxpy.file_parser.parse_internal_continuous import InternalContinuousParser
from gaiaxpy.spectrum.absolute_sampled_spectrum import AbsoluteSampledSpectrum
from gaiaxpy.spectrum.sampled_basis_functions import SampledBasisFunctions
from gaiaxpy.spectrum.utils import correlation_to_covariance_dr3int5
from gaiaxpy.spectrum.xp_continuous_spectrum import XpContinuousSpectrum

from tests.files.continuous import dr3_mean_spectra_csv_file


def test_init_truncation():
    parser = InternalContinuousParser()
    parsed_correlation, _ = parser.parse_file(dr3_mean_spectra_csv_file)
    config_file = CalibratorDispatcher().build(parsed_input_data=parsed_correlation, sampling=None, bp_model='v375wi',
                                               rp_model='v142r', release=RELEASES.dr3, basis_type=INV_BASIS_TYPES.basic)
    xp_sampling_grid, xp_merge = load_xpmerge_from_file(config_file)
    xp_design_matrices = load_xpsampling_from_file(config_file)

    # Create sampled basis functions
    sampled_basis_func = {band: SampledBasisFunctions.from_design_matrix(xp_sampling_grid, xp_design_matrices[band])
                          for band in BANDS}
    truncations = [{}, {BANDS.bp: 50, BANDS.rp: 40}]
    for truncation in truncations:
        parsed_correlation_dict = parsed_correlation.to_dict('records')
        for row in parsed_correlation_dict:
            source_id = row['source_id']
            cont_dict = {}
            # Split both bands
            for _band in BANDS:
                covariance_matrix = correlation_to_covariance_dr3int5(row[f'{_band}_coefficient_correlations'],
                                                                      row[f'{_band}_coefficient_errors'],
                                                                      row[f'{_band}_standard_deviation'])
                continuous_object = XpContinuousSpectrum(source_id, _band, row[f'{_band}_coefficients'],
                                                         covariance_matrix, row[f'{_band}_standard_deviation'])
                cont_dict[_band] = continuous_object
            spectrum = AbsoluteSampledSpectrum(source_id, cont_dict, sampled_basis_func, xp_merge,
                                               truncation=truncation)
            assert isinstance(spectrum, AbsoluteSampledSpectrum)


def test_plot_labels():
    assert AbsoluteSampledSpectrum.get_flux_label() == 'Flux [W nm^-1 m^-2]'
    assert AbsoluteSampledSpectrum.get_position_label() == 'Wavelength [nm]'
    assert AbsoluteSampledSpectrum.get_flux_label(use_tex=True) == r'Flux [$\mathrm{W\,nm^{-1}\,m^{-2}}$]'
    assert AbsoluteSampledSpectrum.get_position_label(use_tex=True) == r'Wavelength [$\mathrm{nm}$]'
