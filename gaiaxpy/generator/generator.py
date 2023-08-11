from pathlib import Path
from typing import Union

import pandas as pd

from gaiaxpy.colour_equation.xp_filter_system_colour_equation import _apply_colour_equation
from gaiaxpy.core.generic_functions import cast_output, validate_arguments
from gaiaxpy.error_correction.error_correction import _apply_error_correction
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.photometry_data import PhotometryData
from .multi_synthetic_photometry_generator import MultiSyntheticPhotometryGenerator
from .photometric_system import PhotometricSystem


def generate(input_object: Union[list, Path, str], photometric_system: Union[list, PhotometricSystem],
             output_path: Union[Path, str] = '.', output_file: str = 'output_synthetic_photometry',
             output_format: str = None, save_file: bool = True, error_correction: bool = False,
             username: str = None, password: str = None) -> pd.DataFrame:
    """
    Synthetic photometry utility: generates synthetic photometry in a set of available systems from the input
    internally-calibrated continuously-represented mean spectra.
    Some standardised photometric systems include a colour-correction to the U bands which will be applied
    automatically when generating the corresponding synthetic photometry.

    Args:
        input_object (list/Path/str): Path to the file containing the mean spectra as downloaded from the archive in
            their continuous representation, a list of sources ids (string or long), or a pandas DataFrame.
        photometric_system (list/PhotometricSystem): Desired photometric system or list of photometric systems.
        output_path (Path/str): Path where to save the output data.
        output_file (str): Name of the output file without extension (e.g. 'my_file').
        output_format (str): Desired output format. If no format is given, the output file format will be the same as
            the input file (e.g. 'csv').
        save_file (bool): Whether to save the output in a file or not. If false, output_format and output_file_name will
            be ignored.
        error_correction (bool): Whether to apply to the photometric errors the tabulated factors to mitigate
            underestimated errors (see Montegriffo et al., 2022, for more details).
        username (str): Cosmos username, only suggested when input_object is a list or ADQL query.
        password (str): Cosmos password, only suggested when input_object is a list or ADQL query.

    Returns:
        DataFrame: A DataFrame of all synthetic photometry results.
    """

    def is_gaia_initially_in_systems(_internal_photometric_system: list,
                                     _gaia_system: PhotometricSystem = PhotometricSystem.Gaia_DR3_Vega):
        """
        Check whether Gaia DR3 is originally in the input photometric systems.

        Args:
            _internal_photometric_system (list): List of photometric systems.
            _gaia_system (PhotometricSystem): Gaia DR3 system.

        Returns:
            bool: True if Gaia DR3 is in the list, False otherwise.
        """
        return _gaia_system in _internal_photometric_system

    # colour_equation should be always true as it is part of the definition of standardised systems.
    colour_equation = True
    if photometric_system in (None, [], ''):
        raise ValueError('At least one photometric system is required as input.')
    validate_arguments(generate.__defaults__[1], output_file, save_file)
    parsed_input_data, extension = InputReader(input_object, generate, user=username, password=password).read()
    # Prepare systems, keep track of original systems
    internal_photometric_system = photometric_system.copy() if isinstance(photometric_system, list) else \
        [photometric_system].copy()
    gaia_system = PhotometricSystem.Gaia_DR3_Vega
    # Create multi generator
    gaia_initially_in_systems = is_gaia_initially_in_systems(internal_photometric_system)
    if error_correction and not gaia_initially_in_systems:
        internal_photometric_system.append(gaia_system)
    if isinstance(internal_photometric_system, list):
        generator = MultiSyntheticPhotometryGenerator(internal_photometric_system, bp_model='v375wi', rp_model='v142r')
    else:
        raise ValueError('Photometry generation not implemented for the input type.')
    photometry_df = generator.generate(parsed_input_data, extension, output_file=None, output_format=None,
                                       save_file=False)
    if colour_equation:
        photometry_df = _apply_colour_equation(photometry_df, photometric_system=internal_photometric_system,
                                               save_file=False, disable_info=True)
    if error_correction:
        photometry_df = _apply_error_correction(photometry_df, photometric_system=photometric_system, save_file=False,
                                                disable_info=True)
    if not gaia_initially_in_systems:
        # Remove Gaia_DR3_Vega system from the final result
        gaia_label = gaia_system.get_system_label()
        gaia_columns = [column for column in photometry_df if column.startswith(gaia_label)]
        photometry_df = photometry_df.drop(columns=gaia_columns)
    photometry_df = cast_output(photometry_df)
    output_data = PhotometryData(photometry_df)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return photometry_df
