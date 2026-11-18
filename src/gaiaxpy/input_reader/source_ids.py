"""Validate source ID selections before Archive retrieval."""

import re

import numpy as np


def validate_source_ids(sources):
    """Validate and normalise source IDs to a list of Python integers.

    Args:
        sources (iterable of int or str): Non-empty selection of Python or NumPy
            integers, decimal integer strings, or a mixture. Strings may have
            an optional sign and surrounding whitespace. NumPy arrays must be
            one-dimensional. Booleans, floats and masked or missing IDs are rejected.

    Returns:
        list[int]: Normalised IDs in their original order, including duplicates.
        The input selection is not modified.

    Raises:
        TypeError: The selection contains invalid IDs or an array has an
            unsupported shape or dtype.
        ValueError: The selection is empty.

    Notes:
        Validation checks the integer representation, not whether an ID exists
        in the Archive or falls within a particular release's source-ID range.
        A single string is not a selection; place it in a list or tuple.
    """
    error = 'An Archive source ID selection must contain only integers or strings representing decimal integers.'
    if isinstance(sources, (str, bytes)):
        raise TypeError('A source ID selection must be an iterable of IDs, not a single string.')
    if isinstance(sources, np.ndarray):
        if sources.ndim != 1:
            raise TypeError('An Archive source ID selection must be one-dimensional.')
        if np.ma.isMaskedArray(sources) and np.any(np.ma.getmask(sources)):
            raise TypeError(error)
        if sources.size == 0:
            raise ValueError('Input list cannot be empty.')
        if sources.dtype.kind in 'iu':
            return sources.tolist()
        if sources.dtype.kind not in 'OU':
            raise TypeError(error)

    identifiers = sources if isinstance(sources, list) else list(sources)
    if not identifiers:
        raise ValueError('Input list cannot be empty.')
    normalised = []
    for source in identifiers:
        if isinstance(source, (int, np.integer)) and not isinstance(source, (bool, np.bool_)):
            normalised.append(int(source))
        elif isinstance(source, str) and re.fullmatch(r'[+-]?[0-9]+', source.strip()):
            normalised.append(int(source.strip()))
        else:
            raise TypeError(error)
    return normalised
