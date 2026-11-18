"""Build photometry metadata from the filters and corrections actually used.

Requested output filters and internally required reference filters are recorded
separately. Additional-filter records include their versions, file checksums
and generated column names, alongside any embedded configuration metadata.
"""
from hashlib import file_digest
from pathlib import Path

from gaiaxpy.core.output_metadata import collect_output_metadata
from gaiaxpy.error_correction.metadata import collect_error_correction_metadata


def build_generator_metadata(release, reader, system_files, reference_files, standardisations,
                             error_corrector, error_correction_requested, *, columns=()):
    """Collect output provenance for one generation call.

    Args:
        release (str): Resolved Gaia release.
        reader (InputReader): Reader recording the input-correction request and
            correction files used.
        system_files (list[tuple]): Requested systems paired with filter paths.
        reference_files (list[tuple]): Reference systems paired with filter paths.
        standardisations (list[dict]): Applied standardisation records containing
            system, method and file.
        error_corrector (ErrorCorrector): Corrector recording applied tables and
            passbands.
        error_correction_requested (bool): Whether flux-error correction was
            requested, independently of whether a table applied.
        columns (iterable[str]): Generated photometry columns before extra input
            columns are appended. Defaults to an empty tuple.

    Returns:
        dict: Output metadata containing configuration metadata, requested and
        reference filter records, standardisation and correction information.
        Additional-system records include base name, release, selected version,
        version source, filename version, SHA-256 checksum and generated columns.

    Notes:
        Configuration paths are deduplicated and converted to output file labels.
        Column association matches complete names, avoiding overlap between
        system-name prefixes. Filename versions are recorded separately from
        embedded metadata; missing descriptive metadata is not invented.
        Reading or hashing a configuration file can raise a file-reading error.
    """
    paths = [path for _, path in system_files + reference_files]
    paths.extend(record['file'] for record in standardisations)
    paths = list(dict.fromkeys(Path(path).resolve() for path in paths))
    metadata = collect_output_metadata('generate', release, paths, reader.applied_correction_files)
    file_labels = {path: entry['file'] for path, entry in zip(paths, metadata['configuration_files'], strict=True)}

    def systems(files):
        """Build system records and map additional filters to their generated columns.

        Use the enclosing call's file labels and column selection. Hash each additional
        filter's file bytes to identify the configuration used.
        """
        records = []
        for system, path in files:
            label = system.get_system_full_label()
            record = {'system': label, 'file': file_labels[Path(path).resolve()]}
            if not system.value.is_builtin:
                # Match complete column names, avoiding ambiguous system-name prefixes.
                system_columns = {f'{label}_{quantity}_{band}'
                                  for quantity in ('mag', 'flux', 'flux_error', 'within_range')
                                  for band in system.get_bands()}
                with Path(path).open('rb') as stream:
                    checksum = file_digest(stream, 'sha256').hexdigest()
                record.update(name=system.value.get_system_name(), data_release=system.value.release,
                              version=system.get_version(), version_source=system.value.version_source,
                              filename_version=system.value.filename_version, sha256=checksum,
                              columns=[column for column in columns if column in system_columns])
            records.append(record)
        return records

    metadata['photometric_systems'] = systems(system_files)
    metadata['reference_photometric_systems'] = systems(reference_files)
    metadata['standardisation'] = [{**record, 'file': file_labels[Path(record['file']).resolve()]}
                                   for record in standardisations]

    metadata['error_correction'] = collect_error_correction_metadata(error_corrector, error_correction_requested)
    return metadata
