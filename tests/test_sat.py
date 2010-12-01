import os
import sys
from datetime import datetime
import numpy
import unittest

import buildpath_to_syspath
import xrit

datadir = os.path.dirname(__file__) + '/data'
os.environ['PPP_CONFIG_DIR'] = os.path.abspath(os.path.dirname(__file__) + '/../etc')

goes_files = [datadir + '/L-000-MSG2__-GOES11______-10_7_135W-PRO______-201002010600-__',
              datadir + '/L-000-MSG2__-GOES11______-10_7_135W-000003___-201002010600-__',
              datadir + '/L-000-MSG2__-GOES11______-10_7_135W-000004___-201002010600-__']
goes_sum = 11629531.0

mtsat_files = [datadir + '/L-000-MSG2__-MTSAT1R_____-10_8_140E-PRO______-200912210900-__',
               datadir + '/L-000-MSG2__-MTSAT1R_____-10_8_140E-000003___-200912210900-__',
               datadir + '/L-000-MSG2__-MTSAT1R_____-10_8_140E-000004___-200912210900-__']
mtsat_sum = 11148074.0

met7_files = [datadir + '/L-000-MTP___-MET7________-00_7_057E-PRO______-200912211200-__',
              datadir + '/L-000-MTP___-MET7________-00_7_057E-000005___-200912211200-__',
              datadir + '/L-000-MTP___-MET7________-00_7_057E-000006___-200912211200-__']
met7_sum = 11662791

msg_files = [datadir + '/H-000-MSG2__-MSG2________-_________-PRO______-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-IR_108___-000004___-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-IR_108___-000005___-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-_________-EPI______-201010111400-__']
msg_sum = 75116847.263172984

hrv_files = [datadir + '/H-000-MSG2__-MSG2________-_________-PRO______-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-HRV______-000012___-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-HRV______-000013___-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-_________-EPI______-201010111400-__']
hrv_sum = 11328375.846757833

hrv2_files = [datadir + '/H-000-MSG2__-MSG2________-_________-PRO______-201011091200-__',
              datadir + '/H-000-MSG2__-MSG2________-HRV______-000018___-201011091200-__',
              datadir + '/H-000-MSG2__-MSG2________-_________-EPI______-201011091200-__']
hrv2_sum = 44049725.5234

def make_image(mda, img, outdir='.'):
    if not os.environ.has_key('DEBUG'):
        return
    import Image as pil
    fname = outdir + '/' + mda.product_name + '.png'
    img = ((img - img.min()) * 255.0 /
           (img.max() - img.min()))
    if type(img) == numpy.ma.MaskedArray:
        img = img.filled(mda.no_data_value)
    img = pil.fromarray(numpy.array(img, numpy.uint8))
    img.save(fname)

class Test(unittest.TestCase):

    def test_goes(self):
        loader = xrit.sat.load_files(goes_files[0], goes_files[1:], calibrate=True)
        mda, img = loader[1308:1508,1308:1508]
        mdac = xrit.mda.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        mdac.data_type = 8*img.itemsize
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(str(mda) == str(mdac), msg='GOES metadata differ')
        self.assertTrue(img.shape == (200, 200), msg='GOES image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, goes_sum, 3, msg='GOES image reading/slicing failed')

    def test_mtsat(self):
        loader = xrit.sat.load_files(mtsat_files[0], mtsat_files[1:], calibrate=True)
        mda, img = loader[1276:1476,1276:1476]
        mdac = xrit.mda.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        mdac.data_type = 8*img.itemsize
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(str(mda) == str(mdac), msg='MTSAT metadata differ')
        self.assertTrue(img.shape == (200, 200), msg='MTSAT image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, mtsat_sum, 3, msg='MTSAT image reading/slicing failed')

    def test_met7(self):
        loader = xrit.sat.load_files(met7_files[0], met7_files[1:], calibrate=False)
        print 'met7', loader.mda.first_pixel
        mda, img = loader._getitem((slice(2300,2900), slice(2000,3000)))
        mdac = xrit.mda.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(str(mda) == str(mdac), msg='MET7 metadata differ')
        self.assertTrue(img.shape == (600, 1000), msg='MET7 image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, met7_sum, 3, msg='MET7 image reading/slicing failed')

    def test_msg(self):
        loader = xrit.sat.load_files(msg_files[0], msg_files[1:-1], epilogue=msg_files[-1], calibrate=True)
        print 'msg', loader.mda.first_pixel
        mda, img = loader._getitem((slice(1756,2056), slice(1056,1956)))
        mdac = xrit.mda.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        mdac.data_type = 8*img.itemsize
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(str(mda) == str(mdac), msg='MSG metadata differ')
        self.assertTrue(img.shape == (300, 900), msg='MSG image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, msg_sum, 3, msg='MSG image reading/slicing failed')

    def test_hrv(self):
        loader = xrit.sat.load_files(hrv_files[0], hrv_files[1:-1], epilogue=hrv_files[-1], calibrate=True)
        print 'hrv', loader.mda.first_pixel
        mda, img = loader._getitem((slice(5368,5968), slice(5068,6068)))
        mdac = xrit.mda.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        mdac.data_type = 8*img.itemsize
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(str(mda) == str(mdac), msg='MSG-HRV metadata differ')
        self.assertTrue(img.shape == (600, 1000), msg='MSG-HRV image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, hrv_sum, 3, msg='MSG-HRV image reading/slicing failed')

    def test_hrv2(self):
        loader = xrit.sat.load_files(hrv2_files[0], hrv2_files[1:-1], epilogue=hrv2_files[-1], calibrate=True)
        mda, img = loader._getitem((slice(7900,8350), slice(1390,10388)))
        mdac = xrit.mda.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        mdac.data_type = 8*img.itemsize
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(str(mda) == str(mdac), msg='MSG-HRV metadata differ')
        self.assertTrue(img.shape == (450, 8998), msg='MSG-HRV image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, hrv2_sum, 3, msg='MSG-HRV image reading/slicing failed')

if __name__ == '__main__':
    import nose
    nose.run()
