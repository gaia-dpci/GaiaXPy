import importlib

import numpy as np
import pandas as pd
import pytest

from gaiaxpy import PhotometricSystem, apply_error_correction, calibrate, convert, generate
from gaiaxpy.core.generic_variables import RELEASES
from gaiaxpy.core.pandas_compat import CSV_FLOAT_PRECISION_KWARGS
from gaiaxpy.error_correction.error_corrector import ErrorCorrector
from gaiaxpy.output import read_output_metadata
from tests.files.continuous import dr3_mean_spectra_csv_file


@pytest.mark.parametrize('function', [calibrate, convert, generate])
@pytest.mark.parametrize('as_file', [False, True])
def test_mean_spectra_quiet_mode_preserves_returned_and_saved_results(function, as_file, tmp_path, capfd):
    frame = pd.read_csv(dr3_mean_spectra_csv_file, **CSV_FLOAT_PRECISION_KWARGS).iloc[:1]
    if as_file:
        selection = tmp_path / 'input.csv'
        frame.to_csv(selection, index=False)
    else:
        selection = frame
    kwargs = {'save_file': True, 'output_format': 'csv', 'output_path': tmp_path}
    if function is generate:
        kwargs.update(photometric_system=PhotometricSystem.DR3_SDSS, error_correction=True)
    expected = function(selection, output_file='normal', **kwargs)
    capfd.readouterr()
    actual = function(selection, output_file='quiet', disable_info=True, **kwargs)
    printed = capfd.readouterr()
    assert printed.out == ''
    assert printed.err == ''
    if function is not generate:
        np.testing.assert_array_equal(actual[1], expected[1])
        actual, expected = actual[0], expected[0]
    pd.testing.assert_frame_equal(actual, expected)
    assert actual.attrs == expected.attrs
    assert (tmp_path / 'quiet.csv').read_bytes() == (tmp_path / 'normal.csv').read_bytes()
    assert read_output_metadata(tmp_path / 'quiet.csv') == actual.attrs['gaiaxpy_metadata']


def test_public_error_correction_quiet_mode_preserves_results(tmp_path, capfd):
    frame = pd.read_csv(dr3_mean_spectra_csv_file).iloc[:1]
    original = generate(frame, [PhotometricSystem.DR3_SDSS, PhotometricSystem.DR3_Gaia_Vega],
                        save_file=False, disable_info=True)
    expected = apply_error_correction(original, release=RELEASES.dr3, save_file=False)
    capfd.readouterr()
    actual = apply_error_correction(original, release=RELEASES.dr3, disable_info=True,
                                    output_path=tmp_path, output_format='csv')
    printed = capfd.readouterr()
    assert printed.out == printed.err == ''
    pd.testing.assert_frame_equal(actual, expected)
    assert actual.attrs == expected.attrs


def test_quiet_mode_keeps_unsupported_system_warnings(capfd):
    ErrorCorrector.display_skipped_systems(['Example'], [], disable_info=True)
    printed = capfd.readouterr()
    assert printed.out == ''
    assert 'UserWarning: System Example does not have a correction table' in printed.err


@pytest.mark.parametrize('module_name,public,internal,args', [
    ('calibrator.calibrator', 'calibrate', '_calibrate', ('input',)),
    ('converter.converter', 'convert', '_convert', ('input',)),
    ('generator.generator', 'generate', '_generate', ('input', 'systems'))])
@pytest.mark.parametrize('quiet', [False, True])
def test_public_wrappers_forward_disable_info(mocker, module_name, public, internal, args, quiet):
    module = importlib.import_module('gaiaxpy.' + module_name)
    implementation = mocker.patch.object(module, internal)
    getattr(module, public)(*args, disable_info=quiet)
    assert implementation.call_args.kwargs['disable_info'] is quiet
