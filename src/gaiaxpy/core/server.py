gaia_server = 'https://gea.esac.esa.int/'


def get_server_for_archive(release):
    """Return the Archive server used for a Gaia data release."""
    return gaia_server


def get_release_for_archive(release):
    """Return the Archive data-release label used for a GaiaXPy release."""
    return f'Gaia {release.upper()}'


def get_retrieval_type_for_archive(release):
    """Return the mean XP spectrum DataLink retrieval type for a Gaia data release."""
    return 'XP_CONTINUOUS'
