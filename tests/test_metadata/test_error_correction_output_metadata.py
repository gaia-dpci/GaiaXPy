from copy import deepcopy

import pandas as pd
import pytest

from gaiaxpy import apply_error_correction, generate, PhotometricSystem
from gaiaxpy.core.generic_variables import RELEASES, VALID_EXTENSIONS
from gaiaxpy.core.output_metadata import OUTPUT_METADATA_KEY
from gaiaxpy.error_correction.error_corrector import ErrorCorrector
from gaiaxpy.output import read_output_metadata
from tests.test_metadata.test_saved_photometry_metadata import input_photometry, read_values, assert_values_equal


@pytest.fixture(params=RELEASES)
def photometry(request):
    frame, systems = input_photometry(request.param)
    gaia = PhotometricSystem.DR3_Gaia_Vega
    systems.append(gaia)
    original = generate(frame, systems, error_correction=False, save_file=False)
    expected = ErrorCorrector(request.param).apply_correction(original, save_file=False)
    return request.param, original, expected


def last_correction(output):
    operation = output.attrs[OUTPUT_METADATA_KEY]['operations'][-1]
    assert operation['function'] == 'apply_error_correction'
    assert operation['gaiaxpy_version']
    return operation['error_correction']


@pytest.mark.parametrize('existing_metadata', [False, True])
def test_existing_provenance_is_preserved_and_no_origin_is_inferred(photometry, existing_metadata):
    release, original, expected = photometry
    if not existing_metadata:
        original.attrs.pop(OUTPUT_METADATA_KEY)
    original.attrs['user_note'] = {'values': ['keep this value']}
    before = original.copy(deep=True)
    before.attrs = deepcopy(original.attrs)
    output = apply_error_correction(original, release=release, save_file=False)
    assert_values_equal(output, expected, 'csv')
    pd.testing.assert_frame_equal(original, before)
    assert original.attrs == before.attrs
    metadata = output.attrs[OUTPUT_METADATA_KEY]
    if existing_metadata:
        assert {key: value for key, value in metadata.items() if key != 'operations'} == before.attrs[
            OUTPUT_METADATA_KEY]
        assert metadata['error_correction']['status'] == 'disabled'
    else:
        assert metadata['function'] == 'apply_error_correction'
        assert metadata['configuration_files'] == []
        assert not {'photometric_systems', 'reference_photometric_systems', 'standardisation',
                    'input_correction', 'basis_type'} & metadata.keys()
    correction = last_correction(output)
    assert correction['status'] == 'applied'
    assert correction['files']
    assert all(entry['metadata']['data_release'] == release for entry in correction['files'])
    files = [entry['file'] for entry in correction['files']]
    assert len(files) == len(set(files))
    assert all(record['file'] in files and record['passbands'] for record in correction['systems'])
    for record in correction['systems']:
        assert all(f"{record['system']}_flux_error_{band}" in output for band in record['passbands'])
    output.attrs['user_note']['values'].append('output only')
    assert original.attrs == before.attrs
    if existing_metadata:
        metadata['configuration_files'][0]['metadata']['version'] = 'output only'
        assert original.attrs == before.attrs


def test_repeated_calls_keep_prior_corrections(photometry):
    release, _, _ = photometry
    frame, systems = input_photometry(release)
    systems.append(PhotometricSystem.DR3_Gaia_Vega)
    original = generate(frame, systems, error_correction=True, save_file=False)
    assert original.attrs[OUTPUT_METADATA_KEY]['error_correction']['status'] == 'applied'
    first = apply_error_correction(original, release=release, save_file=False)
    before = deepcopy(first.attrs)
    second = apply_error_correction(first, release=release, save_file=False)
    metadata = second.attrs[OUTPUT_METADATA_KEY]
    assert len(metadata['operations']) == 2
    assert metadata['operations'][0] == before[OUTPUT_METADATA_KEY]['operations'][0]
    assert metadata['error_correction'] == original.attrs[OUTPUT_METADATA_KEY]['error_correction']
    assert first.attrs == before
    second.attrs[OUTPUT_METADATA_KEY]['operations'][0]['error_correction']['files'].clear()
    assert first.attrs == before


@pytest.mark.parametrize('existing_metadata', [False, True])
@pytest.mark.parametrize('extension', VALID_EXTENSIONS)
def test_saved_metadata_matches_returned_metadata(tmp_path, photometry, existing_metadata, extension):
    release, original, expected = photometry
    if not existing_metadata:
        original.attrs.pop(OUTPUT_METADATA_KEY)
    output = apply_error_correction(original, release=release, output_path=tmp_path, output_file='corrected',
                                    output_format=extension)
    path = tmp_path / f'corrected.{extension}'
    assert read_output_metadata(path) == output.attrs[OUTPUT_METADATA_KEY]
    assert_values_equal(read_values(path, extension), expected, extension)


@pytest.mark.parametrize('release', RELEASES)
def test_unavailable_systems_and_passbands_are_not_recorded(release):
    prefix = release.upper()
    original = pd.DataFrame({'source_id': [1], f'{prefix}_GaiaVega_mag_G': [15.], f'{prefix}_Sdss_flux_error_g': [2.],
                             f'{prefix}_Sdss_flux_error_unknown': [3.], f'{prefix}_Custom_flux_error_VIS': [4.]})
    output = apply_error_correction(original, release=release, save_file=False)
    records = last_correction(output)['systems']
    assert [(record['system'], record['passbands']) for record in records] == [(f'{prefix}_Sdss', ['g'])]
    assert output[f'{prefix}_Sdss_flux_error_unknown'].iloc[0] == 3.
    assert output[f'{prefix}_Custom_flux_error_VIS'].iloc[0] == 4.
    assert original[f'{prefix}_Sdss_flux_error_g'].iloc[0] == 2.


def test_no_applicable_passbands_records_not_applied():
    original = pd.DataFrame({'source_id': [1], 'DR3_GaiaVega_mag_G': [15.], 'DR3_Custom_flux_error_VIS': [4.]})
    output = apply_error_correction(original, release=RELEASES.dr3, save_file=False)
    correction = last_correction(output)
    assert correction['status'] == 'not_applied'
    assert correction['files'] == []
    assert correction['systems'] == []
    pd.testing.assert_frame_equal(output, original, check_dtype=False)


@pytest.mark.parametrize('metadata, message', [([], 'must be a dictionary'),
                                               ({'operations': {}}, 'operations must be a list')])
def test_malformed_existing_metadata_is_not_silently_replaced(tmp_path, metadata, message):
    original = pd.DataFrame({'source_id': [1], 'DR3_GaiaVega_mag_G': [15.]})
    original.attrs[OUTPUT_METADATA_KEY] = metadata
    before = deepcopy(original.attrs)
    with pytest.raises(ValueError, match=message):
        apply_error_correction(original, release=RELEASES.dr3, output_path=tmp_path)
    assert original.attrs == before
    assert not list(tmp_path.iterdir())


def test_user_metadata_and_existing_operations_are_preserved():
    original = pd.DataFrame({'source_id': [1], 'DR3_GaiaVega_mag_G': [15.], 'DR3_Sdss_flux_error_g': [2.]})
    original.attrs[OUTPUT_METADATA_KEY] = {'creator': 'user', 'description': 'Photometry desc.',
                                           'operations': [{'function': 'user_processing', 'settings': [1, 2]}]}
    before = deepcopy(original.attrs)
    output = apply_error_correction(original, release=RELEASES.dr3, save_file=False)
    metadata = output.attrs[OUTPUT_METADATA_KEY]
    assert set(metadata) == set(before[OUTPUT_METADATA_KEY])
    assert metadata['creator'] == 'user'
    assert metadata['description'] == 'Photometry desc.'
    assert metadata['operations'][0] == before[OUTPUT_METADATA_KEY]['operations'][0]
    assert len(metadata['operations']) == 2
    assert last_correction(output)['status'] == 'applied'
    metadata['operations'][0]['settings'].append(3)
    assert original.attrs == before
