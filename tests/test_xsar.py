import os
import sys
from datetime import datetime
import numpy
import unittest

import buildpath_to_syspath
import mipp
from mipp import xsar
from mipp.mda import _nice2cmp, mslice

datadir = (os.path.dirname(__file__) or '.') + '/data'
save_mda = False

try:
    # give the possibility to test other config files
    os.environ['PPP_CONFIG_DIR'] = os.environ['LOCAL_PPP_CONFIG_DIR']
except KeyError:
    os.environ['PPP_CONFIG_DIR'] = datadir
if not os.path.isdir(os.environ['PPP_CONFIG_DIR']):
    raise mipp.ConfigReaderError, "No config dir: '%s'"%os.environ['PPP_CONFIG_DIR']

txs1_file = datadir + '/TX01_SAR_SC_GEC_20110825T104705_20110825T104727_NSG_023264_8133_test.TSX.tar'
tsx1_sum = 3895.1342095

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

def compare_mda(m1, m2):
    m1 = mslice(m1)
    m2 = mslice(m2)
    k1 = sorted(m1.__dict__.keys())
    k2 = sorted(m2.__dict__.keys())
    if not k1 == k2:
        return False
    for k in k1:
        if not _nice2cmp(getattr(m1, k)) == _nice2cmp(getattr(m2, k)):
            return False           
    return True

class Test(unittest.TestCase):

    def test_tsx(self):
        mda, img = xsar.sat.load_file(txs1_file, 'sarx', calibrate=True)
        if save_mda:
            mda.save(mda.product_name + '.mda')
        mdac = xsar.Metadata().read(datadir + '/' + mda.product_name + '.mda')
        cross_sum = img.sum()
        make_image(mda, img)
        self.assertTrue(compare_mda(mda, mdac), msg='TSX metadata differ')
        self.assertTrue(img.shape == (512, 512), msg='TSX image reading failed, wrong shape')
        self.failUnlessAlmostEqual(cross_sum, tsx1_sum, 3, msg='TSX image reading failed')

if __name__ == '__main__':
    save_mda = False
    unittest.main()
