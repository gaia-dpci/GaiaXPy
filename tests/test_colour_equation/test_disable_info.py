"""Check the public colour-equation function's information controls."""
import unittest
from importlib import import_module
from unittest.mock import patch

import pandas as pd


class TestColourEquationDisableInfo(unittest.TestCase):
    def test_public_option_reaches_reader_progress_and_writer(self):
        module = import_module('gaiaxpy.colour_equation.xp_filter_system_colour_equation')
        photometry = pd.DataFrame({'source_id': [123]})
        for options, expected in (({}, False), ({'disable_info': False}, False),
                                  ({'disable_info': True}, True)):
            with self.subTest(options=options):
                with patch.object(module, 'DataFrameReader') as reader, \
                        patch.object(module, '__get_systems_to_correct', return_value=[]) as select, \
                        patch.object(module, '__fill_systems_details', return_value={}), \
                        patch.object(module, '__generate_output_df', return_value=photometry) as generate, \
                        patch.object(module, 'PhotometryData') as output, \
                        patch.object(module, 'cast_output', return_value=photometry):
                    reader.return_value.read.return_value = (photometry, 'csv')
                    result = module.apply_colour_equation(photometry, photometric_system=[], save_file=False,
                                                          overwrite='ask', **options)
                    reader.assert_called_once_with(photometry, module.apply_colour_equation, False,
                                                   disable_info=expected)
                    select.assert_called_once_with([])
                    generate.assert_called_once_with(photometry, {}, disable_info=expected)
                    output.return_value.save.assert_called_once_with(False, '.', 'corrected_photometry', None, 'csv',
                                                                     disable_info=expected, overwrite='ask')
                    self.assertIs(result, photometry)
