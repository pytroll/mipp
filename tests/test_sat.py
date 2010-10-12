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
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(img.shape == (200, 200), msg='GOES image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, goes_sum, 3, msg='GOES image reading/slicing failed')

    def test_mtsat(self):
        loader = xrit.sat.load_files(mtsat_files[0], mtsat_files[1:], calibrate=True)
        mda, img = loader[1276:1476,1276:1476]
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(img.shape == (200, 200), msg='MTSAT image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, mtsat_sum, 3, msg='MTSAT image reading/slicing failed')

    def test_met7(self):
        loader = xrit.sat.load_files(met7_files[0], met7_files[1:], calibrate=False)
        mda, img = loader[2300:2900,2000:3000]
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(img.shape == (600, 1000), msg='MET7 image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, met7_sum, 3, msg='MET7 image reading/slicing failed')

    def test_msg(self):
        loader = xrit.sat.load_files(msg_files[0], msg_files[1:-1], epilogue=msg_files[-1], calibrate=True)
        mda, img = loader[1756:2056,1056:1956]
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(img.shape == (300, 900), msg='MSG image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, msg_sum, 3, msg='MSG image reading/slicing failed')

    def test_hrv(self):
        loader = xrit.sat.load_files(hrv_files[0], hrv_files[1:-1], epilogue=hrv_files[-1], calibrate=True)
        mda, img = loader[5368:5968,5068:6068]
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(img.shape == (600, 1000), msg='MSG-HRV image reading/slicing failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, hrv_sum, 3, msg='MSG-HRV image reading/slicing failed')

if __name__ == '__main__':
    import nose
    nose.run()
