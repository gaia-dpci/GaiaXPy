
def _validate_source_type(source_type):
    if not isinstance(source_type, str):
        raise ValueError('The variable source_type must be a string.')
    source_type = source_type.lower()
    if source_type not in ['qso', 'star']:
        raise ValueError("Unknown source type. Available source types: 'qso' and 'star'.")
    return source_type
