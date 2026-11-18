"""Source identification shared by spectrum representations."""
from typing import Union


class Spectrum:
    """Store the identifier associated with a spectrum."""

    def __init__(self, source_id: Union[str, int]):
        """Store a source identifier without converting or validating it.

        Args:
            source_id (int or str): Gaia source ID or another identifier.
        """
        self.source_id = source_id

    def get_source_id(self):
        """Return the source identifier in its original type.

        Returns:
            int or str: Identifier supplied at construction.
        """
        return self.source_id
