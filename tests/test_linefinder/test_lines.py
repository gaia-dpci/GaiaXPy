import unittest

import numpy as np
import numpy.testing as npt

from gaiaxpy.core.satellite import BANDS
from gaiaxpy.linefinder.lines import Lines
from tests.files.paths import file_lines_example_path

bp_true = (np.array(['H_beta', 'He I_1', 'He I_2'], dtype='<U7'), np.array([24.42300844, 28.392607, 17.449061]))
rp_true = (np.array(['H_alpha', 'He I_3'], dtype='<U7'), np.array([15.73198734, 22.367717]))
bp_true_zet = (np.array(['C III]', 'Mg II'], dtype='<U8'), np.array([38.18102116, 19.02020368]))
rp_true_zet = (np.array(['H_beta'], dtype='<U8'), np.array([45.71770448]))
bp_true_list = (np.array(['H_beta'], dtype='<U7'), np.array([24.42300844]))
rp_true_list = (np.array(['H_alpha'], dtype='<U7'), np.array([15.73198734]))
xp_empty = (np.array([], dtype='<U7'), np.array([], dtype=np.float64))


class TestLines(unittest.TestCase):

    def test_lines_default_star(self):
        bpl = Lines(BANDS.bp, 'star')
        rpl = Lines(BANDS.rp, 'star')
        npt.assert_array_equal(bpl.get_lines_pwl()[0], bp_true[0])
        npt.assert_array_equal(rpl.get_lines_pwl()[0], rp_true[0])
        npt.assert_allclose(bpl.get_lines_pwl()[1], bp_true[1])
        npt.assert_allclose(rpl.get_lines_pwl()[1], rp_true[1])

    def test_lines_default_qso(self):
        bpl = Lines(BANDS.bp, 'qso')
        rpl = Lines(BANDS.rp, 'qso')
        npt.assert_array_equal(bpl.get_lines_pwl(zet=1.)[0], bp_true_zet[0])
        npt.assert_array_equal(rpl.get_lines_pwl(zet=1.)[0], rp_true_zet[0])
        npt.assert_allclose(bpl.get_lines_pwl(zet=1.)[1], bp_true_zet[1])
        npt.assert_allclose(rpl.get_lines_pwl(zet=1.)[1], rp_true_zet[1])

    def test_lines_list_star(self):
        user_list = [(656.461, 486.268), ('H_alpha', 'H_beta')]
        bpl = Lines(BANDS.bp, 'star', user_lines=user_list)
        rpl = Lines(BANDS.rp, 'star', user_lines=user_list)
        npt.assert_array_equal(bpl.get_lines_pwl()[0], bp_true_list[0])
        npt.assert_array_equal(rpl.get_lines_pwl()[0], rp_true_list[0])
        npt.assert_allclose(bpl.get_lines_pwl()[1], bp_true_list[1])
        npt.assert_allclose(rpl.get_lines_pwl()[1], rp_true_list[1])

    def test_lines_file_star(self):
        bpl = Lines(BANDS.bp, 'star', user_lines=file_lines_example_path)
        rpl = Lines(BANDS.rp, 'star', user_lines=file_lines_example_path)
        npt.assert_array_equal(bpl.get_lines_pwl()[0], bp_true_list[0])
        npt.assert_array_equal(rpl.get_lines_pwl()[0], rp_true_list[0])
        npt.assert_allclose(bpl.get_lines_pwl()[1], bp_true_list[1])
        npt.assert_allclose(rpl.get_lines_pwl()[1], rp_true_list[1])

    def test_lines_list_star_outsiderange(self):
        user_list = [(65.6461, 48.6268, 6560.461, 4860.268), ('Line1', 'Line2', 'Line3', 'Line4')]
        bpl = Lines(BANDS.bp, 'star', user_lines=user_list)
        rpl = Lines(BANDS.rp, 'star', user_lines=user_list)
        npt.assert_array_equal(bpl.get_lines_pwl()[0], xp_empty[0])
        npt.assert_array_equal(rpl.get_lines_pwl()[0], xp_empty[0])
        npt.assert_array_equal(bpl.get_lines_pwl()[1], xp_empty[1])
        npt.assert_array_equal(rpl.get_lines_pwl()[1], xp_empty[1])
