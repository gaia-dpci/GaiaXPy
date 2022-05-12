"""
satellite.py
====================================
Module to hold satellite-related constants.
"""

from collections import namedtuple

# Satellite-related parameters
TELESCOPE_PUPIL_AREA = 0.7278

WLRange = namedtuple('WLRange', 'low high')

# Wavelength range covered by the BP spectrum
BP_WL = WLRange(330, 643)

# Wavelength range covered by the RP spectrum
RP_WL = WLRange(635, 1020)

# Bands
Bands = namedtuple('Bands', 'bp rp')
BANDS = Bands('bp', 'rp')
