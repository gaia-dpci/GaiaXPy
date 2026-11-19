from importlib import import_module

import numpy as np
import pytest

from gaiaxpy import PhotometricSystem
from gaiaxpy.core.input_validator import validate_explicit_save_options


@pytest.mark.parametrize('module, operation, args, options, message', [
    ('calibrator.calibrator', 'calibrate', (), {'sampling': np.array([400., 600., 500.])}, 'ascending order'),
    ('calibrator.calibrator', 'calibrate', (), {'sampling': np.array([400., np.nan, 500.])}, 'finite real numbers'),
    ('calibrator.calibrator', 'calibrate', (), {'sampling': np.array([400., 1100., 1200.])}, 'between 330 and 1050'),
    ('calibrator.calibrator', 'calibrate', (), {'sampling': np.array([])}, 'non-empty one-dimensional array'),
    ('converter.converter', 'convert', (), {'sampling': np.array(2.)}, 'non-empty one-dimensional array'),
    ('calibrator.calibrator', 'calibrate', (), {'basis_type': 'unknown'}, 'Basis type')
])
def test_invalid_processing_options_fail_before_reading(module, operation, args, options, message, mocker):
    module = import_module(f'gaiaxpy.{module}')
    reader = mocker.patch.object(module, 'InputReader')
    with pytest.raises(ValueError, match=message):
        getattr(module, operation)(None, *args, save_file=False, **options)
    reader.assert_not_called()


@pytest.mark.parametrize('module, operation, reader_name, args, options', [
    ('calibrator.calibrator', 'calibrate', 'InputReader', (), {}),
    ('converter.converter', 'convert', 'InputReader', (), {}),
    ('generator.generator', 'generate', 'InputReader', (PhotometricSystem.DR3_DECam,), {}),
    ('error_correction.error_corrector', 'apply_error_correction', 'InputReader', (), {'release': 'dr3'}),
    ('colour_equation.xp_filter_system_colour_equation', 'apply_colour_equation', 'DataFrameReader', (), {}),
])
@pytest.mark.parametrize('invalid, message', [
    ({'save_file': 0}, 'save_file.*boolean'),
    ({'output_format': 'unsupported'}, "output format 'unsupported' is not supported"),
    ({'output_file': 'photometry.csv'}, "use output_file='photometry' and output_format='csv'")
])
def test_invalid_saving_options_fail_before_reading(module, operation, reader_name, args, options, invalid, message,
                                                    mocker):
    module = import_module(f'gaiaxpy.{module}')
    reader = mocker.patch.object(module, reader_name)
    with pytest.raises(ValueError, match=message):
        getattr(module, operation)(None, *args, **options, **invalid)
    reader.assert_not_called()


@pytest.mark.parametrize('save_file, output_file', [(True, 'photometry.v2'),
                                                    (False, 'photometry.csv')])
def test_output_file_allows_dotted_stems_or_disabled_saving(save_file, output_file):
    validate_explicit_save_options(save_file, output_file, 'csv')


def test_output_file_detects_case_insensitive_extension_after_dotted_stem():
    with pytest.raises(ValueError, match=r"use output_file='photometry\.v2' and output_format='fits'"):
        validate_explicit_save_options(True, 'photometry.v2.FITS', 'csv')
