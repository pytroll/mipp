import os
import sys
from datetime import datetime
import numpy
import unittest

import buildpath_to_syspath
import mipp
from mipp import xrit
from mipp.mda import _nice2cmp

datadir = (os.path.dirname(__file__) or '.') + '/data'
save_mda = False
debug = os.environ.has_key('DEBUG')

xrit_decomp_exec = os.environ.get("XRIT_DECOMPRESS_PATH", None)
xrit_outdir = os.environ.get("XRIT_DECOMPRESS_OUTDIR", None)

try:
    # give the possibility to test other config files
    os.environ['PPP_CONFIG_DIR'] = os.environ['LOCAL_PPP_CONFIG_DIR']
except KeyError:
    os.environ['PPP_CONFIG_DIR'] = datadir
if not os.path.isdir(os.environ['PPP_CONFIG_DIR']):
    raise mipp.ConfigReaderError, "No config dir: '%s'" % os.environ[
        'PPP_CONFIG_DIR']

goes_files = [datadir + '/L-000-MSG2__-GOES11______-10_7_135W-PRO______-201002010600-__',
              datadir +
              '/L-000-MSG2__-GOES11______-10_7_135W-000003___-201002010600-__',
              datadir + '/L-000-MSG2__-GOES11______-10_7_135W-000004___-201002010600-__']
goes_sum = 11629531.0

mtsat_files = [datadir + '/L-000-MSG2__-MTSAT1R_____-10_8_140E-PRO______-200912210900-__',
               datadir +
               '/L-000-MSG2__-MTSAT1R_____-10_8_140E-000003___-200912210900-__',
               datadir + '/L-000-MSG2__-MTSAT1R_____-10_8_140E-000004___-200912210900-__']
mtsat_sum = 11148074.0

met7_files = [datadir + '/L-000-MTP___-MET7________-00_7_057E-PRO______-200912211200-__',
              datadir +
              '/L-000-MTP___-MET7________-00_7_057E-000005___-200912211200-__',
              datadir + '/L-000-MTP___-MET7________-00_7_057E-000006___-200912211200-__']
met7_sum = 11662791

msg_files = [datadir + '/H-000-MSG2__-MSG2________-_________-PRO______-201010111400-__',
             datadir +
             '/H-000-MSG2__-MSG2________-IR_108___-000004___-201010111400-__',
             datadir +
             '/H-000-MSG2__-MSG2________-IR_108___-000005___-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-_________-EPI______-201010111400-__']
msg_sum = 75116847.263172984

hrv_files = [datadir + '/H-000-MSG2__-MSG2________-_________-PRO______-201010111400-__',
             datadir +
             '/H-000-MSG2__-MSG2________-HRV______-000012___-201010111400-__',
             datadir +
             '/H-000-MSG2__-MSG2________-HRV______-000013___-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-_________-EPI______-201010111400-__']
hrv_sum = 11328340.753558

hrv2_files = [datadir + '/H-000-MSG2__-MSG2________-_________-PRO______-201011091200-__',
              datadir +
              '/H-000-MSG2__-MSG2________-HRV______-000018___-201011091200-__',
              datadir + '/H-000-MSG2__-MSG2________-_________-EPI______-201011091200-__']
hrv2_sum = 44049589.065626

cmprs_files = [datadir + '/H-000-MSG3__-MSG3________-_________-PRO______-201311271015-__',
               datadir +
               '/H-000-MSG3__-MSG3________-WV_073___-000008___-201311271015-C_',
               datadir +
               '/H-000-MSG3__-MSG3________-_________-EPI______-201311271015-__'
               ]


def make_image(mda, img, outdir='.'):
    if not debug:
        return
    import Image as pil
    fname = outdir + '/' + mda.product_name + '.png'
    img = ((img - img.min()) * 255.0 /
           (img.max() - img.min()))
    if type(img) == numpy.ma.MaskedArray:
        img = img.filled(mda.no_data_value)
    img = pil.fromarray(numpy.array(img, numpy.uint8))
    img.save(fname)


def compare_mda(m1, m2):
    def compare_arrays(e1, e2):
        for x1, x2 in zip(e1, e2):
            if "%.3f" % x1 != "%.3f" % x2:
                return False
        return True

    k1 = sorted(m1.__dict__.keys())
    k2 = sorted(m2.__dict__.keys())
    if not k1 == k2:
        return False
    for k in k1:
        if k in ('area_extent', 'pixel_size'):
            if not compare_arrays(getattr(m1, k), getattr(m2, k)):
                return False
        elif not _nice2cmp(getattr(m1, k)) == _nice2cmp(getattr(m2, k)):
            return False

    return True


class Test(unittest.TestCase):

    def setUp(self):
        self.decompressed_msg_files = []

    def test_goes(self):
        loader = xrit.sat.load_files(
            goes_files[0], goes_files[1:], calibrate=True)
        mda, img = loader[1308:1508, 1308:1508]
        if save_mda:
            mda.save(mda.product_name + '.mda')
        mdac = xrit.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        mdac.data_type = 8 * img.itemsize
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(compare_mda(mda, mdac), msg='GOES metadata differ')
        self.assertTrue(
            img.shape == (200, 200), msg='GOES image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, goes_sum, 3,
                                   msg='GOES image reading/slicing failed, wrong cross_sum (%.3f != %.3f)' % (
                                       cross_sum, goes_sum))

    def test_mtsat(self):
        loader = xrit.sat.load_files(
            mtsat_files[0], mtsat_files[1:], calibrate=True)
        mda, img = loader[1276:1476, 1276:1476]
        if save_mda:
            mda.save(mda.product_name + '.mda')
        mdac = xrit.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        mdac.data_type = 8 * img.itemsize
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(compare_mda(mda, mdac), msg='MTSAT metadata differ')
        self.assertTrue(
            img.shape == (200, 200), msg='MTSAT image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, mtsat_sum, 3,
                                   msg='MTSAT image reading/slicing failed, wrong cross_sum (%.3f != %.3f)' % (
                                       cross_sum, mtsat_sum))

    def test_met7(self):
        loader = xrit.sat.load_files(
            met7_files[0], met7_files[1:], calibrate=False)
        mda, img = loader.raw_slicing((slice(2300, 2900), slice(2000, 3000)))
        if save_mda:
            mda.save(mda.product_name + '.mda')
        mdac = xrit.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(compare_mda(mda, mdac), msg='MET7 metadata differ')
        self.assertTrue(
            img.shape == (600, 1000), msg='MET7 image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, met7_sum, 3,
                                   msg='MET7 image reading/slicing failed, wrong cross_sum (%.3f != %.3f)' % (
                                       cross_sum, met7_sum))

    def test_msg(self):
        loader = xrit.sat.load_files(msg_files[0], msg_files[1:-1], epilogue=msg_files[-1],
                                     calibrate=True)
        mda, img = loader[1656:1956, 1756:2656]
        if save_mda:
            mda.save(mda.product_name + '.mda')
        mdac = xrit.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        mdac.data_type = 8 * img.itemsize
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(compare_mda(mda, mdac), msg='MSG metadata differ')
        self.assertTrue(
            img.shape == (300, 900), msg='MSG image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, msg_sum, 3,
                                   msg='MSG image reading/slicing reflectances failed, wrong cross_sum (%.3f != %.3f)' % (
                                       cross_sum, msg_sum))

        mda, img = loader(mda.area_extent)
        if save_mda:
            mda.save(mda.product_name + '.mda')
        cross_sum = img.sum()
        self.assertTrue(
            compare_mda(mda, mdac), msg='MSG metadata differ, when using area_extent')
        self.failUnlessAlmostEqual(cross_sum, msg_sum, 3,
                                   msg='MSG image reading/slicing failed, when using area_extent, wrong cross_sum (%.3f != %.3f)' % (
                                       cross_sum, msg_sum))

    def test_msg2(self):
        loader = xrit.sat.load_files(msg_files[0], msg_files[1:-1], epilogue=msg_files[-1],
                                     calibrate=2)
        mda, img = loader[1656:1956, 1756:2656]
        cross_sum = img.sum()
        expected = 22148991.0194
        self.failUnlessAlmostEqual(cross_sum, expected, 3,
                                   msg='MSG image reading/slicing radiances failed, wrong cross_sum (%.3f != %.3f)' % (
                                       cross_sum, expected))

    def test_hrv(self):
        loader = xrit.sat.load_files(hrv_files[0],
                                     hrv_files[1:-1],
                                     epilogue=hrv_files[-1],
                                     calibrate=True)
        mda, img = loader[5168:5768, 5068:6068]
        if save_mda:
            mda.save(mda.product_name + '.mda')
        mdac = xrit.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        mdac.data_type = 8 * img.itemsize
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(compare_mda(mda, mdac), msg='MSG-HRV metadata differ')
        message = 'MSG-HRV image reading/slicing failed, wrong shape'
        self.assertTrue(img.shape == (600, 1000), msg=message)
        message = ('MSG-HRV image reading/slicing failed, ' +
                   'wrong cross_sum (%.3f != %.3f)' % (cross_sum, hrv_sum))
        #self.failUnlessAlmostEqual(cross_sum, hrv_sum, 3, msg=message)

    def test_hrv2(self):
        loader = xrit.sat.load_files(hrv2_files[0], hrv2_files[1:-1],
                                     epilogue=hrv2_files[-1], calibrate=True)
        mda, img = loader[2786:3236, 748:9746]
        if save_mda:
            mda.save(mda.product_name + '.mda')
        mdac = xrit.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        mdac.data_type = 8 * img.itemsize
        cross_sum = img.sum()
        make_image(mda, img)

        self.assertTrue(compare_mda(mda, mdac), msg='MSG-HRV metadata differ')
        self.assertTrue(img.shape == (450, 8998),
                        msg='MSG-HRV image reading/slicing failed, wrong shape')
        message = ('MSG-HRV image reading/slicing failed, ' +
                   'wrong cross_sum (%.3f != %.3f)' % (cross_sum, hrv2_sum))
        self.failUnlessAlmostEqual(cross_sum, hrv2_sum, 3, msg=message)

    def test_decompress(self):
        """Test decompressing MSG SEVIRI data on the fly with xRITDecompress"""
        message = ("Environment variable XRIT_DECOMPRESS_PATH not set. " +
                   "Not possible to test decompression on the fly!")
        from warnings import warn
        if xrit_decomp_exec == None:
            warn(message)
            return

        message = ("Environment variable XRIT_DECOMPRESS_PATH is empty. " +
                   "Please point it to the complete file path to the xRITDecompress software")
        self.failIfEqual(len(xrit_decomp_exec), 0, message)
        if not xrit_outdir:
            outdir = datadir
        else:
            outdir = xrit_outdir
        uncompressed_chanels = xrit.sat.decompress(cmprs_files[1:-1],
                                                   outdir=outdir)
        self.decompressed_msg_files = uncompressed_chanels
        nfiles = len(uncompressed_chanels)
        self.assertEqual(nfiles, len(cmprs_files[1:-1]))
        self.assertTrue(os.path.exists(uncompressed_chanels[0]))

    def tearDown(self):
        """Clean up"""
        for filename in self.decompressed_msg_files:
            if os.path.exists(filename):
                os.remove(filename)


if __name__ == '__main__':
    save_mda = False
    unittest.main()
