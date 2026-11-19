"""Describe applied flux-error corrections and preserve prior output provenance.

Only tables associated with corrected passbands are recorded. Public correction
calls append operation-history entries rather than replacing metadata from the
original photometry-generation call.
"""
from copy import deepcopy
from pathlib import Path

from gaiaxpy.core.output_metadata import OUTPUT_METADATA_KEY, collect_config_metadata, collect_output_metadata
from gaiaxpy.core.version import __version__


def collect_error_correction_metadata(error_corrector, requested=True):
    """Describe requested correction status and the tables/passbands actually used.

    Args:
        error_corrector (ErrorCorrector): Corrector holding applied_corrections
            records from its latest call.
        requested (bool): Whether correction was requested; defaults to True.

    Returns:
        dict: requested, status, files and systems, plus a reason when requested
        correction had no applicable passbands. Status is disabled when not
        requested, applied when records exist, otherwise not_applied. System
        records are sorted by label and contain corrected passbands and output
        file labels. Configuration-file entries are deduplicated by resolved path.
    """
    records = sorted(error_corrector.applied_corrections, key=lambda record: record['system'])
    correction_paths = list(dict.fromkeys(Path(record['file']).resolve() for record in records))
    correction_files = collect_config_metadata(correction_paths)
    correction_labels = {path: entry['file'] for path, entry in zip(correction_paths, correction_files, strict=True)}
    correction = {'requested': bool(requested),
                  'status': 'disabled' if not requested else 'applied' if records else 'not_applied'}
    if requested and not records:
        correction['reason'] = 'No requested passbands had an applicable error-correction table.'
    correction['files'] = correction_files
    correction['systems'] = [{**record, 'file': correction_labels[Path(record['file']).resolve()]}
                             for record in records]
    return correction


def append_error_correction_metadata(data, error_corrector):
    """Append a correction operation to the table's metadata without replacing its origin.

    Args:
        data (pandas.DataFrame): Corrected table whose attrs are updated in place.
        error_corrector (ErrorCorrector): Corrector recording the release and
            applied correction tables/passbands.

    Raises:
        ValueError: Existing gaiaxpy_metadata is not a dictionary, or its
            operations field is not a list.

    Notes:
        Deep-copy existing GaiaXPy metadata before appending. Keep earlier
        correction records, including any top-level generation correction record.
        Each new operation records its function, GaiaXPy version, release and
        correction details. Without existing metadata, create provenance for
        apply_error_correction only; do not infer the input's filters or history.
    """
    if OUTPUT_METADATA_KEY in data.attrs:
        original = data.attrs[OUTPUT_METADATA_KEY]
        if not isinstance(original, dict):
            raise ValueError('Output gaiaxpy_metadata must be a dictionary.')
        metadata = deepcopy(original)
    else:
        metadata = collect_output_metadata('apply_error_correction', error_corrector.get_release(), [])
    operations = metadata.setdefault('operations', [])
    if not isinstance(operations, list):
        raise ValueError('Output metadata operations must be a list.')
    operations.append({'function': 'apply_error_correction', 'gaiaxpy_version': __version__,
                       'data_release': error_corrector.get_release(),
                       'error_correction': collect_error_correction_metadata(error_corrector)})
    data.attrs[OUTPUT_METADATA_KEY] = metadata
