import os
import sys
from datetime import datetime
import numpy
import hashlib
import unittest

import buildpath_to_syspath
import xrit

datadir = os.path.dirname(__file__) + '/data'
os.environ['PPP_CONFIG_DIR'] = os.path.abspath(os.path.dirname(__file__) + '/../etc')

goes_files = [datadir + '/L-000-MSG2__-GOES11______-10_7_135W-PRO______-201002010600-__',
              datadir + '/L-000-MSG2__-GOES11______-10_7_135W-000003___-201002010600-__',
              datadir + '/L-000-MSG2__-GOES11______-10_7_135W-000004___-201002010600-__']
goes_md5 = 'cdea6e4da3aa42b69f6d9898fe0fc53d'

mtsat_files = [datadir + '/L-000-MSG2__-MTSAT1R_____-10_8_140E-PRO______-200912210900-__',
               datadir + '/L-000-MSG2__-MTSAT1R_____-10_8_140E-000003___-200912210900-__',
               datadir + '/L-000-MSG2__-MTSAT1R_____-10_8_140E-000004___-200912210900-__']
mtsat_md5 = '25323150c00b3d1a2994ee3de28c83d7'

met7_files = [datadir + '/L-000-MTP___-MET7________-00_7_057E-PRO______-200912211200-__',
              datadir + '/L-000-MTP___-MET7________-00_7_057E-000005___-200912211200-__',
              datadir + '/L-000-MTP___-MET7________-00_7_057E-000006___-200912211200-__']
met7_md5 = '60ce1213182deeaff632ce06a108a435'

msg_files = [datadir + '/H-000-MSG2__-MSG2________-_________-PRO______-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-IR_108___-000004___-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-IR_108___-000005___-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-_________-EPI______-201010111400-__']
msg_md5 = '48cbed6aaabe8ba9c76127a96b64f4db'

hrv_files = [datadir + '/H-000-MSG2__-MSG2________-_________-PRO______-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-HRV______-000012___-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-HRV______-000013___-201010111400-__',
             datadir + '/H-000-MSG2__-MSG2________-_________-EPI______-201010111400-__']
hrv_md5 = '011cdc73e4c2ce2a542515847b4d1db1'

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
        md5 = hashlib.md5(img).hexdigest()
        make_image(mda, img)
        self.assertTrue(md5 == goes_md5, msg='GOES image md5 check failed')

    def test_mtsat(self):
        loader = xrit.sat.load_files(mtsat_files[0], mtsat_files[1:], calibrate=True)
        mda, img = loader[1276:1476,1276:1476]
        md5 = hashlib.md5(img).hexdigest()
        make_image(mda, img)
        self.assertTrue(md5 == mtsat_md5, msg='MTSAT image md5 check failed')

    def test_met7(self):
        loader = xrit.sat.load_files(met7_files[0], met7_files[1:], calibrate=False)
        mda, img = loader[2300:2900,2000:3000]
        md5 = hashlib.md5(img).hexdigest()
        make_image(mda, img)
        self.assertTrue(md5 == met7_md5, msg='MET7 image md5 check failed')

    def test_msg(self):
        loader = xrit.sat.load_files(msg_files[0], msg_files[1:-1], epilogue=msg_files[-1], calibrate=True)
        mda, img = loader[1756:2056,1056:1956]
        md5 = hashlib.md5(img).hexdigest()
        make_image(mda, img)
        self.assertTrue(md5 == msg_md5, msg='MSG image md5 check failed')

    def test_hrv(self):
        loader = xrit.sat.load_files(hrv_files[0], hrv_files[1:-1], epilogue=hrv_files[-1], calibrate=True)
        mda, img = loader[5368:5968,5068:6068]
        md5 = hashlib.md5(img).hexdigest()
        make_image(mda, img)
        self.assertTrue(md5 == hrv_md5, msg='HRV image md5 check failed')

if __name__ == '__main__':
    import nose
    nose.run()
