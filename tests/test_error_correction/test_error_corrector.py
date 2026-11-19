import numpy as np
import numpy.testing as npt
import pandas as pd
import pytest

from gaiaxpy import PhotometricSystem, apply_error_correction, generate
from gaiaxpy.core.generic_functions import extract_systems_from_data
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.error_correction.error_corrector import ErrorCorrector
from tests.files.continuous import dr3_mean_spectra_csv_file
from tests.files.generator import no_correction_solution_path
from tests.utils.utils import assert_dfs_equal


@pytest.mark.parametrize('kwargs', [{}, {'release': None}])
def test_apply_error_correction_defaults_to_dr3(mocker, kwargs):
    corrector = mocker.patch('gaiaxpy.error_correction.error_corrector.ErrorCorrector')
    input_df = pd.DataFrame({'source_id': [1]})

    apply_error_correction(input_df, save_file=False, **kwargs)

    corrector.assert_called_once_with(RELEASES.dr3)
    corrector.return_value.apply_correction.assert_called_once()
    assert corrector.return_value.apply_correction.call_args.args == (input_df,)


lists_of_systems_dr3 = ([PhotometricSystem.DR3_HST_ACSWFC], [PhotometricSystem.DR3_Gaia_Vega],
                        [PhotometricSystem.DR3_Euclid_VIS, PhotometricSystem.DR3_Gaia_2],
                        [PhotometricSystem.DR3_Gaia_Vega, PhotometricSystem.DR3_Euclid_VIS],
                        [PhotometricSystem.DR3_JKC, PhotometricSystem.DR3_Gaia_Vega])

requires_correction_values = [True, False]


@pytest.fixture
def err_corr_dr3():
    return ErrorCorrector(RELEASES.dr3)


@pytest.fixture
def dr3_input_df():
    input_df = pd.read_csv(no_correction_solution_path, **CSV_FLOAT_PRECISION_KWARGS)
    return input_df


required_addition_solution = [True, False, True, False, False]


@pytest.mark.parametrize('err_corr_fixture, lists_of_systems', [('err_corr_dr3', lists_of_systems_dr3)])
def test_requires_gaia_system_addition(request, err_corr_fixture, lists_of_systems):
    err_corr = request.getfixturevalue(err_corr_fixture)
    for systems, expected in zip(lists_of_systems, required_addition_solution):
        assert err_corr.requires_gaia_system_addition(systems) == expected, (f'Failed for fixture: {err_corr_fixture}, '
                                                                             f'systems: {systems}')


@pytest.mark.parametrize(
    'err_corr_fixture, gaia_system, lists_of_systems',
    [('err_corr_dr3', PhotometricSystem.DR3_Gaia_Vega, lists_of_systems_dr3)]
)
@pytest.mark.parametrize('corr_requested', requires_correction_values)
def test_get_required_systems(request, err_corr_fixture, gaia_system, lists_of_systems, corr_requested):
    err_corr = request.getfixturevalue(err_corr_fixture)
    for systems in lists_of_systems:
        requires_addition = err_corr.requires_gaia_system_addition(systems)
        expected_systems = err_corr.get_required_systems(error_correction=corr_requested,
                                                         requires_gaia_addition=requires_addition,
                                                         phot_systems=systems)
        if not corr_requested or not requires_addition:
            assert expected_systems == systems
        else:
            assert expected_systems == systems.copy() + [gaia_system], (f'Test failed for fixture: {err_corr_fixture}, '
                                                                        f'corr: {corr_requested}, addition: '
                                                                        f'{requires_addition}, and initial systems '
                                                                        f'{systems}.')


@pytest.mark.parametrize('err_corr_fixture, gaia_system', [('err_corr_dr3', PhotometricSystem.DR3_Gaia_Vega)])
def test_get_gaia_system(request, err_corr_fixture, gaia_system):
    err_corr = request.getfixturevalue(err_corr_fixture)
    assert gaia_system.get_system_name() == err_corr.get_gaia_system().get_system_name()
    assert gaia_system.get_system_full_label() == err_corr.get_gaia_system().get_system_full_label()


@pytest.mark.parametrize('err_corr_fixture, release', [('err_corr_dr3', RELEASES.dr3)])
def test_get_release(request, err_corr_fixture, release):
    err_corr = request.getfixturevalue(err_corr_fixture)
    assert err_corr.get_release() == release


@pytest.mark.parametrize('err_corr_fixture, csv_path, photometric_systems', [(
        'err_corr_dr3', no_correction_solution_path, [PhotometricSystem.DR3_Els_Custom_W09_S2,
                                                      PhotometricSystem.DR3_Euclid_VIS,
                                                      PhotometricSystem.DR3_Gaia_2,
                                                      PhotometricSystem.DR3_Gaia_Vega,
                                                      PhotometricSystem.DR3_Halpha_Custom_AB,
                                                      PhotometricSystem.DR3_H_Custom,
                                                      PhotometricSystem.DR3_Hipparcos_Tycho,
                                                      PhotometricSystem.DR3_HST_ACSWFC,
                                                      PhotometricSystem.DR3_HST_HUGS_Std,
                                                      PhotometricSystem.DR3_HST_WFC3UVIS,
                                                      PhotometricSystem.DR3_HST_WFPC2,
                                                      PhotometricSystem.DR3_IPHAS,
                                                      PhotometricSystem.DR3_JKC,
                                                      PhotometricSystem.DR3_JKC_Std,
                                                      PhotometricSystem.DR3_JPAS,
                                                      PhotometricSystem.DR3_JPLUS,
                                                      PhotometricSystem.DR3_JWST_NIRCAM,
                                                      PhotometricSystem.DR3_LSST,
                                                      PhotometricSystem.DR3_PanSTARRS1,
                                                      PhotometricSystem.DR3_PanSTARRS1_Std,
                                                      PhotometricSystem.DR3_Pristine,
                                                      PhotometricSystem.DR3_SDSS,
                                                      PhotometricSystem.DR3_SDSS_Std,
                                                      PhotometricSystem.DR3_Stromgren,
                                                      PhotometricSystem.DR3_Stromgren_Std,
                                                      PhotometricSystem.DR3_WFIRST])])
def test_extract_systems_from_data_dr3(request, err_corr_fixture, csv_path, photometric_systems):
    err_corr = request.getfixturevalue(err_corr_fixture)
    df = pd.read_csv(csv_path, **CSV_FLOAT_PRECISION_KWARGS)
    extracted_from_df = extract_systems_from_data(df, release=err_corr.get_release())
    extracted_from_list = extract_systems_from_data(df, release=err_corr.get_release(),
                                                    photometric_system=photometric_systems)
    assert set(extracted_from_df) == set(
        extracted_from_list), f'Failed for fixture: {err_corr_fixture}, csv: {csv_path}'


expected_dr3 = {'DR3_ElsCustomW09S2', 'DR3_EuclidVis', 'DR3_Gaia2', 'DR3_GaiaVega', 'DR3_HipparcosTycho',
                'DR3_HipparcosTycho', 'DR3_HstAcswfc', 'DR3_HstHugsStd', 'DR3_HstWfc3uvis', 'DR3_HstWfpc2',
                'DR3_Iphas', 'DR3_Jkc', 'DR3_JkcStd', 'DR3_Jpas', 'DR3_Jplus', 'DR3_JwstNircam', 'DR3_Panstarrs1',
                'DR3_Panstarrs1Std', 'DR3_Pristine', 'DR3_Sdss', 'DR3_SdssStd', 'DR3_SkyMapper', 'DR3_Stromgren',
                'DR3_StromgrenStd', 'DR3_Wfirst'}


@pytest.mark.parametrize('err_corr_fixture, expected', [('err_corr_dr3', expected_dr3)])
def test_get_correctable_systems(request, err_corr_fixture, expected):
    err_corr = request.getfixturevalue(err_corr_fixture)
    assert set(err_corr.get_correctable_systems()) == expected


def test_get_systems_to_correct_dr3(err_corr_dr3, dr3_input_df):
    correctable_systems = err_corr_dr3.get_correctable_systems()
    extracted_from_df = extract_systems_from_data(dr3_input_df, release=err_corr_dr3.get_release())
    solution = ['DR3_HstWfc3uvis', 'DR3_Stromgren', 'DR3_Iphas', 'DR3_Wfirst', 'DR3_JwstNircam', 'DR3_Jkc',
                'DR3_SdssStd', 'DR3_JkcStd', 'DR3_Sdss', 'DR3_GaiaVega', 'DR3_EuclidVis', 'DR3_Jpas',
                'DR3_ElsCustomW09S2', 'DR3_HipparcosTycho', 'DR3_Pristine', 'DR3_Gaia2', 'DR3_Panstarrs1',
                'DR3_HstAcswfc', 'DR3_Jplus', 'DR3_StromgrenStd', 'DR3_HstHugsStd', 'DR3_Panstarrs1Std', 'DR3_HstWfpc2']
    systems_to_correct = err_corr_dr3.get_systems_to_correct(extracted_from_df, correctable_systems)
    set_systems_to_correct = set(systems_to_correct)
    # Check no duplicates
    assert len(set_systems_to_correct) == len(systems_to_correct)
    assert set_systems_to_correct == set(solution)


gaia_present_solution = [False, True, False, True, True]


@pytest.mark.parametrize('err_corr_fixture, lists_of_systems, expected', [('err_corr_dr3', lists_of_systems_dr3,
                                                                           gaia_present_solution)])
def test_check_gaia_is_present(request, err_corr_fixture, lists_of_systems, expected):
    err_corr = request.getfixturevalue(err_corr_fixture)
    for systems, expected_value in zip(lists_of_systems, expected):
        if expected_value:
            err_corr.check_gaia_is_present(systems)
        else:
            with pytest.raises(ValueError):
                err_corr.check_gaia_is_present(systems)


@pytest.mark.parametrize('err_corr_fixture, input_df_fixture, photometric_systems, needs_generate',
                         [('err_corr_dr3', 'dr3_input_df',
                           [PhotometricSystem.DR3_LSST, PhotometricSystem.DR3_Gaia_Vega], False)])
@pytest.mark.parametrize('required_addition', [True, False])
def test_format_error_output_has_gaia(request, err_corr_fixture, input_df_fixture, photometric_systems, needs_generate,
                                      required_addition):
    err_corr = request.getfixturevalue(err_corr_fixture)
    input_df = request.getfixturevalue(input_df_fixture)
    photometry_df = generate(input_df, photometric_systems, save_file=False) if needs_generate else input_df

    formatted_df = err_corr.format_error_output(photometry_df, required_addition)

    # Identify Gaia columns
    gaia_label = err_corr.get_gaia_full_label()
    gaia_columns = [c for c in photometry_df.columns if c.startswith(gaia_label)]

    if required_addition:
        # Gaia columns should have been dropped
        for c in gaia_columns:
            assert c not in formatted_df.columns, f'Gaia column {c} was not removed for fixture {err_corr_fixture}'
    else:
        # DataFrame should be unchanged
        assert_dfs_equal(formatted_df, photometry_df)


def test_read_system_table(err_corr_dr3):
    def __verify_systems(err_corr, release_systems, systems_with_tables):
        """
        Verify that systems with correction tables exist and can be read.
        """
        expected = set(systems_with_tables)
        for system in release_systems:
            label = system.get_system_full_label()
            should_have_table = label in expected
            try:
                table = err_corr._read_system_table(label)
            except FileNotFoundError:
                assert not should_have_table, (f'System {label} is expected to have a correction table, but the file '
                                               f'was not be found.')
            else:
                # Succeeded: should have a table, and it must be a DataFrame
                assert should_have_table, (f'System {label} is not expected to have a correction table, but one was '
                                           f'found and read successfully.')
                assert isinstance(table, pd.DataFrame), (f'System {label} returned {type(table).__name__} instead of '
                                                         f'a pandas DataFrame.')

    available_systems = [PhotometricSystem[ps.strip()] for ps in
                         PhotometricSystem.get_available_systems(grouped=False).split(',')]
    dr3_systems = [s for s in available_systems if s.get_system_name().startswith('DR3_')]
    assert len(dr3_systems) == 28  # Length of dr3_available_systems file


@pytest.mark.parametrize(
    'err_corr, label, mags, expected_rows', [('err_corr_dr3', 'DR3_ElsCustomW09S2',
                                              pd.Series([3.0, 4.0, 12.0, 15.5, 20.9], name='DR3_ElsCustomW09S2'),
                                              [0, 0, 8, 11, 16])])
def test_get_correction_array(request, err_corr, label, mags, expected_rows):
    err_corr_instance = request.getfixturevalue(err_corr)
    # Read and process the table
    table = err_corr_instance._read_system_table(label)
    table = table.drop(columns=['min_Gmag_bin', 'max_Gmag_bin', 'bin_centre'])
    # Get correction arrays
    corr_arrays = err_corr_instance._get_correction_array(mags, label)
    # Compare expected rows
    for index, row in enumerate(expected_rows):
        npt.assert_array_equal(corr_arrays[index], table.iloc[row].values)


@pytest.mark.parametrize('err_corr, photometric_systems, sdss_system, prefix, filepath',
                         [('err_corr_dr3', [PhotometricSystem.DR3_SDSS, PhotometricSystem.DR3_Gaia_Vega],
                           PhotometricSystem.DR3_SDSS, 'DR3',
                           dr3_mean_spectra_csv_file)])
def test_apply_correction(request, err_corr, photometric_systems, sdss_system, prefix, filepath):
    err_corr_instance = request.getfixturevalue(err_corr)
    sdss_label = sdss_system.get_system_full_label()

    phot_df = generate(filepath, photometric_system=photometric_systems, save_file=False)
    corrected_df = err_corr_instance.apply_correction(phot_df.copy(), save_file=False,
                                                      photometric_system=photometric_systems)
    # Assert structure
    assert isinstance(corrected_df, pd.DataFrame)
    assert corrected_df.shape == phot_df.shape
    # Assert corrections
    sdss_bands = ['u', 'g', 'r', 'i', 'z']
    correction_arrays = err_corr_instance._get_correction_array(
        phot_df[f'{prefix}_GaiaVega_mag_G'], sdss_label).T

    for index, band in enumerate(sdss_bands):
        orig = phot_df[f'{prefix}_Sdss_flux_error_{band}'].values
        corr = corrected_df[f'{prefix}_Sdss_flux_error_{band}'].values
        expected = orig * correction_arrays[index]
        npt.assert_array_equal(corr, expected, err_msg=f'{prefix}: Correction mismatch for band {band}')


@pytest.mark.parametrize('release', [RELEASES.dr3])
@pytest.mark.parametrize('position', ['below', 'at', 'above'])
def test_error_correction_upper_table_boundary(release, position):
    """The last table row should also apply at its exact upper magnitude limit."""
    prefix = release.upper()
    table = ErrorCorrector(release)._read_system_table(f'{prefix}_Sdss')
    upper = table['max_Gmag_bin'].iloc[-1]
    magnitude = {'below': np.nextafter(upper, -np.inf),
                 'at': upper,
                 'above': np.nextafter(upper, np.inf)}[position]
    error_column = f'{prefix}_Sdss_flux_error_g'
    original = pd.DataFrame({f'{prefix}_GaiaVega_mag_G': [magnitude], error_column: [2.0]})

    output = apply_error_correction(original, release=release, save_file=False, disable_info=True)

    expected = 2.0 * table['factor_g'].iloc[-1]
    npt.assert_allclose(output[error_column].iloc[0], expected, rtol=1e-14, atol=0)
