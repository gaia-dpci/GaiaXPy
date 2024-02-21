from pathlib import Path
from typing import Union, Optional

import pandas as pd

from gaiaxpy.colour_equation.xp_filter_system_colour_equation import _apply_colour_equation
from gaiaxpy.core.generic_functions import cast_output, format_additional_columns, validate_photometric_system, \
    validate_error_correction
from gaiaxpy.error_correction.error_correction import _apply_error_correction
from gaiaxpy.input_reader.input_reader import InputReader
from gaiaxpy.output.photometry_data import PhotometryData
from .multi_synthetic_photometry_generator import MultiSyntheticPhotometryGenerator
from .photometric_system import PhotometricSystem
from ..core.input_validator import validate_save_arguments
from ..file_parser.cast import _cast


def generate(input_object: Union[list, Path, str], photometric_system: Union[list, PhotometricSystem],
             output_path: Union[Path, str] = '.', output_file: str = 'output_synthetic_photometry',
             output_format: str = None, save_file: bool = True, error_correction: bool = False,
             additional_columns: Optional[Union[dict, list, str]] = None, username: str = None, password: str = None) \
        -> pd.DataFrame:
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
        additional_columns (str/list): List of additional columns to include in the output. The columns must be requested
            columns must be available in the input (files, DataFrames) or in the Archive response (lists, queries).
        username (str): Cosmos username, only suggested when input_object is a list or ADQL query.
        password (str): Cosmos password, only suggested when input_object is a list or ADQL query.

    Returns:
        DataFrame: A DataFrame of all synthetic photometry results.
    """
    return _generate(input_object=input_object, photometric_system=photometric_system, output_path=output_path,
                     output_file=output_file, output_format=output_format, save_file=save_file,
                     error_correction=error_correction, additional_columns=additional_columns, username=username,
                     password=password)


def _generate(input_object: Union[list, Path, str], photometric_system: Union[list, PhotometricSystem],
              output_path: Union[Path, str] = '.', output_file: str = 'output_synthetic_photometry',
              output_format: str = None, save_file: bool = True, error_correction: bool = False,
              additional_columns: Optional[Union[dict, list, str]] = None, selector=None, username: str = None,
              password: str = None, bp_model: str = 'v375wi', rp_model: str = 'v142r') -> pd.DataFrame:
    """
    Internal function of the calibration utility. Refer to "generate".

    Args:
        selector (function): Function to filter AVRO records. The records returned will be the ones for which the
        function returns True. The field names used in the selector function should match the ones in the AVRO schema
        as the filter is run before any column renaming happens. If selector is not None and the input is not an AVRO
        file, a SelectorNotImplementedError will be raised.
        bp_model (str): The bp model.
        rp_model (str): The rp model.
    """

    def __is_gaia_initially_in_systems(_internal_photometric_system: list,
                                       _gaia_system: PhotometricSystem = PhotometricSystem.Gaia_DR3_Vega):
        """
        Check whether Gaia DR3 is originally in the input photometric systems.

        Args:
            _internal_photometric_system (list): List of photometric systems.
            _gaia_system (PhotometricSystem): Gaia DR3 system.

        Returns:
            bool: True if Gaia DR3 is in the list, False otherwise.
        """
        gaia_system_name = _gaia_system.get_system_name()
        return any([item.get_system_name() == gaia_system_name for item in _internal_photometric_system])

    validate_photometric_system(photometric_system)
    validate_save_arguments(generate.__defaults__[1], output_file, generate.__defaults__[2], output_format, save_file)
    # Prepare systems, keep track of original systems (especially required for error_correction)
    internal_phot_system = photometric_system.copy() if isinstance(photometric_system, list) else (
        [photometric_system].copy())
    validate_error_correction(internal_phot_system, error_correction)
    gaia_system = PhotometricSystem.Gaia_DR3_Vega
    is_gaia_in_input = __is_gaia_initially_in_systems(internal_phot_system)
    if error_correction and not is_gaia_in_input:
        internal_phot_system.append(gaia_system)
    additional_columns = format_additional_columns(additional_columns)
    # Read input data
    parsed_input_data, extension = InputReader(input_object, generate, False, additional_columns=additional_columns,
                                               selector=selector, user=username, password=password).read()
    additional_data = parsed_input_data[list(additional_columns.keys())]
    # Generate photometry
    phot_generator = MultiSyntheticPhotometryGenerator(internal_phot_system, bp_model=bp_model, rp_model=rp_model)
    photometry_df = phot_generator.generate(parsed_input_data, extension, output_file=None, output_format=None,
                                            save_file=False)
    photometry_df = _apply_colour_equation(photometry_df, photometric_system=internal_phot_system,
                                           save_file=False, disable_info=True)
    if error_correction:
        photometry_df = _apply_error_correction(photometry_df, photometric_system=photometric_system, save_file=False,
                                                disable_info=True)
        if not is_gaia_in_input:  # Remove Gaia_DR3_Vega system from the final result
            gaia_label = gaia_system.get_system_label()
            gaia_columns = [column for column in photometry_df if column.startswith(gaia_label)]
            photometry_df = photometry_df.drop(columns=gaia_columns)
    additional_data = additional_data[[c for c in additional_data.columns if c not in photometry_df.columns]]
    photometry_df = pd.concat([photometry_df, additional_data], axis=1)
    photometry_df = cast_output(photometry_df)
    # Save data
    output_data = PhotometryData(photometry_df)
    output_data.save(save_file, output_path, output_file, output_format, extension)
    return _cast(photometry_df)
