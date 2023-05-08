import unittest
from os.path import join

import numpy as np
import numpy.testing as npt

from gaiaxpy.core.satellite import BANDS
from gaiaxpy.lines.lines import Lines

from tests.files.paths import files_path

lines_path = join(files_path, 'lines_files')
file_lines = join(lines_path, 'lines_example.txt')

bptrue = (np.array(['H_beta', 'He I_1', 'He I_2'], dtype='<U7'), np.array([24.42300844, 28.392607, 17.449061]))
rptrue = (np.array(['H_alpha', 'He I_3'], dtype='<U7'), np.array([15.73198734, 22.367717]))
bptruezet = (np.array(['C III]', 'Mg II'], dtype='<U8'), np.array([38.18102116, 19.02020368]))
rptruezet = (np.array(['H_beta'], dtype='<U8'), np.array([45.71770448]))
bptruelist = (np.array(['H_beta'], dtype='<U7'), np.array([24.42300844]))
rptruelist = (np.array(['H_alpha'], dtype='<U7'), np.array([15.73198734]))
xpempty = (np.array([], dtype='<U7'), np.array([], dtype=np.float64))

class TestLines(unittest.TestCase):

    def test_lines_default_star(self):
        bpl = Lines(BANDS.bp, 'star')
        rpl = Lines(BANDS.rp, 'star')
        npt.assert_array_equal(bpl.get_lines_pwl()[0], bptrue[0])
        npt.assert_array_equal(rpl.get_lines_pwl()[0], rptrue[0])
        npt.assert_allclose(bpl.get_lines_pwl()[1], bptrue[1])
        npt.assert_allclose(rpl.get_lines_pwl()[1], rptrue[1])

    def test_lines_default_qso(self):
        bpl = Lines(BANDS.bp, 'qso')
        rpl = Lines(BANDS.rp, 'qso')
        npt.assert_array_equal(bpl.get_lines_pwl(zet=1.)[0], bptruezet[0])
        npt.assert_array_equal(rpl.get_lines_pwl(zet=1.)[0], rptruezet[0])
        npt.assert_allclose(bpl.get_lines_pwl(zet=1.)[1], bptruezet[1])
        npt.assert_allclose(rpl.get_lines_pwl(zet=1.)[1], rptruezet[1])

    def test_lines_list_star(self):
        user_list = [(656.461, 486.268), ('H_alpha', 'H_beta')]
        bpl = Lines(BANDS.bp, 'star', user_lines=user_list)
        rpl = Lines(BANDS.rp, 'star', user_lines=user_list)
        npt.assert_array_equal(bpl.get_lines_pwl()[0], bptruelist[0])
        npt.assert_array_equal(rpl.get_lines_pwl()[0], rptruelist[0])
        npt.assert_allclose(bpl.get_lines_pwl()[1], bptruelist[1])
        npt.assert_allclose(rpl.get_lines_pwl()[1], rptruelist[1])

    def test_lines_file_star(self):
        bpl = Lines(BANDS.bp, 'star', user_lines=file_lines)
        rpl = Lines(BANDS.rp, 'star', user_lines=file_lines)
        npt.assert_array_equal(bpl.get_lines_pwl()[0], bptruelist[0])
        npt.assert_array_equal(rpl.get_lines_pwl()[0], rptruelist[0])
        npt.assert_allclose(bpl.get_lines_pwl()[1], bptruelist[1])
        npt.assert_allclose(rpl.get_lines_pwl()[1], rptruelist[1])

    def test_lines_list_star_outsiderange(self):
        user_list = [(65.6461, 48.6268, 6560.461, 4860.268), ('Line1', 'Line2', 'Line3', 'Line4')]
        bpl = Lines(BANDS.bp, 'star', user_lines=user_list)
        rpl = Lines(BANDS.rp, 'star', user_lines=user_list)
        npt.assert_array_equal(bpl.get_lines_pwl()[0], xpempty[0])
        npt.assert_array_equal(rpl.get_lines_pwl()[0], xpempty[0])
        npt.assert_array_equal(bpl.get_lines_pwl()[1], xpempty[1])
        npt.assert_array_equal(rpl.get_lines_pwl()[1], xpempty[1])

