import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from gaiaxpy.output.output_data import OutputData


class CsvOutput(OutputData):
    _sampling_companion_formats = ('csv',)

    def __init__(self):
        super().__init__(pd.DataFrame(), None)
        self.writes = 0

    def _save_csv(self, output_path, output_file):
        self.writes += 1
        Path(output_path).mkdir(parents=True, exist_ok=True)
        for suffix in ('.csv', '_sampling.csv', '_metadata.csv'):
            (Path(output_path) / f'{output_file}{suffix}').write_text('new', encoding='utf-8')


class TestOverwritePolicy(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.output = CsvOutput()

    def save(self, *, save_file=True, disable_info=True, **kwargs):
        return self.output.save(save_file, self.path, 'result', None, 'csv',
                                disable_info=disable_info, **kwargs)

    def test_yes_aliases_replace_existing_files(self):
        for value in ('yes', 'y', 'YES', 'Y', 'YeS'):
            with self.subTest(value=value):
                main = self.path / 'result.csv'
                main.write_text('old', encoding='utf-8')
                with patch('builtins.input', side_effect=AssertionError('Unexpected prompt')):
                    self.save(overwrite=value)
                self.assertEqual(main.read_text(encoding='utf-8'), 'new')

    def test_default_replaces_existing_file(self):
        main = self.path / 'result.csv'
        main.write_text('old', encoding='utf-8')
        self.save()
        self.assertEqual(main.read_text(encoding='utf-8'), 'new')

    def test_no_aliases_protect_each_companion(self):
        for value in ('no', 'n', 'NO', 'N', 'No'):
            for suffix in ('.csv', '_sampling.csv', '_metadata.csv'):
                with self.subTest(value=value, suffix=suffix):
                    existing = self.path / f'result{suffix}'
                    existing.write_text('old', encoding='utf-8')
                    with self.assertRaises(FileExistsError):
                        self.save(overwrite=value)
                    self.assertEqual(list(self.path.iterdir()), [existing])
                    self.assertEqual(existing.read_text(encoding='utf-8'), 'old')
                    existing.unlink()
        self.assertEqual(self.output.writes, 0)

    def test_no_and_ask_allow_new_output_without_prompting(self):
        for value in ('no', 'n', 'ask', 'ASK'):
            with self.subTest(value=value):
                with patch('builtins.input', side_effect=AssertionError('Unexpected prompt')):
                    self.save(overwrite=value)
                self.assertEqual(len(list(self.path.iterdir())), 3)
                for path in self.path.iterdir():
                    path.unlink()

    def test_ask_confirms_entire_group_once(self):
        for suffix in ('.csv', '_sampling.csv', '_metadata.csv'):
            (self.path / f'result{suffix}').write_text('old', encoding='utf-8')
        with patch('builtins.input', return_value='YES') as prompt:
            self.save(overwrite='AsK')
        prompt.assert_called_once()
        self.assertTrue(all(path.read_text(encoding='utf-8') == 'new'
                            for path in self.path.iterdir()))

    def test_writer_receives_original_destination(self):
        for value in ('yes', 'no', 'ask'):
            with self.subTest(value=value):
                for path in self.path.iterdir():
                    path.unlink()
                if value == 'ask':
                    (self.path / 'result_metadata.csv').write_text('old', encoding='utf-8')
                with patch.object(self.output, '_save_csv', wraps=self.output._save_csv) as writer:
                    with patch('builtins.input', return_value='yes'):
                        self.save(overwrite=value)
                writer.assert_called_once_with(self.path, 'result')

    def test_directory_collision_is_rejected_before_writing(self):
        for value in ('no', 'ask'):
            for suffix in ('.csv', '_sampling.csv', '_metadata.csv'):
                with self.subTest(value=value, suffix=suffix):
                    existing = self.path / f'result{suffix}'
                    existing.mkdir()
                    with patch('builtins.input', side_effect=AssertionError('Unexpected prompt')):
                        with self.assertRaises(IsADirectoryError):
                            self.save(overwrite=value)
                    self.assertEqual(list(self.path.iterdir()), [existing])
                    existing.rmdir()
        self.assertEqual(self.output.writes, 0)

    def test_decline_or_unavailable_input_preserves_output(self):
        existing = self.path / 'result_metadata.csv'
        existing.write_text('old', encoding='utf-8')
        for answer in ('n', '', 'unexpected', EOFError(), OSError()):
            with self.subTest(answer=answer):
                options = {'side_effect': answer} if isinstance(answer, Exception) else {'return_value': answer}
                with patch('builtins.input', **options):
                    self.save(overwrite='ask')
                self.assertEqual(list(self.path.iterdir()), [existing])
                self.assertEqual(existing.read_text(encoding='utf-8'), 'old')
        self.assertEqual(self.output.writes, 0)

    def test_ask_warns_when_saving_is_disabled(self):
        for value in ('ask', 'ASK'):
            with self.subTest(value=value):
                with patch('builtins.input', side_effect=AssertionError('Unexpected prompt')):
                    with redirect_stderr(StringIO()) as stderr:
                        self.save(save_file=False, overwrite=value, disable_info=False)
                    self.assertEqual(
                        stderr.getvalue(),
                        "UserWarning: overwrite='ask' is ignored because save_file=False.\n"
                    )
        self.assertEqual(self.output.writes, 0)
        self.assertEqual(list(self.path.iterdir()), [])

    def test_disable_info_suppresses_ignored_ask_notice(self):
        with redirect_stderr(StringIO()) as stderr:
            self.save(save_file=False, overwrite='ask', disable_info=True)
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(self.output.writes, 0)

    def test_other_valid_values_are_silent_when_saving_is_disabled(self):
        with redirect_stderr(StringIO()) as stderr:
            self.save(save_file=False, disable_info=False)
            for value in ('yes', 'y', 'no', 'n'):
                self.save(save_file=False, overwrite=value, disable_info=False)
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(self.output.writes, 0)

    def test_invalid_values_are_rejected(self):
        for value in (True, False, None, 0, 1, '', 'always', ' yes ', [], {}):
            for save_file in (True, False):
                with self.subTest(value=value, save_file=save_file):
                    with self.assertRaisesRegex(ValueError, 'overwrite must be'):
                        self.save(save_file=save_file, overwrite=value)
        self.assertEqual(self.output.writes, 0)

    def test_invalid_policy_fails_before_reader_for_all_table_operations(self):
        from importlib import import_module

        operations = (
            ('calibrator.calibrator', 'calibrate', '_calibrate', (None,)),
            ('converter.converter', 'convert', '_convert', (None,)),
            ('generator.generator', 'generate', '_generate', (None, None)),
            ('error_correction.error_corrector', 'apply_error_correction', None, (None,)),
            ('colour_equation.xp_filter_system_colour_equation',
             'apply_colour_equation', '_apply_colour_equation', (None,))
        )
        for path, public, internal, args in operations:
            module = import_module(f'gaiaxpy.{path}')
            private = (getattr(module, internal) if internal else
                       module.ErrorCorrector.__new__(module.ErrorCorrector).apply_correction)
            reader_name = 'DataFrameReader' if path.startswith('colour_equation.') else 'InputReader'
            for name, function in ((public, getattr(module, public)), (internal, private)):
                for value in (True, False, 'invalid'):
                    with self.subTest(function=name, overwrite=value):
                        with patch.object(module, reader_name,
                                          side_effect=AssertionError('Reader was called')) as reader:
                            with self.assertRaisesRegex(ValueError, 'overwrite must be'):
                                function(*args, overwrite=value)
                            reader.assert_not_called()
