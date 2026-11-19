"""Save GaiaXPy results and read their output metadata.

The public read_output_metadata helper retrieves GaiaXPy metadata from a saved
output or a CSV metadata companion. Writer classes are used internally to write
the computed results to files.
"""

from .metadata import read_output_metadata
