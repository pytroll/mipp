import sys
import os
import unittest
import cStringIO

import buildpath_to_syspath
print sys.path
from xrit import cfg

datadir = os.path.dirname(__file__) + '/data'

class Test(unittest.TestCase):

    def test_config_parser(self):
        cfgfile = 'msg2'        
        os.environ['PPP_CONFIG_DIR'] = datadir
        c = cfg.read_config(cfgfile)
        fp = cStringIO.StringIO()
        for name in ('satellite', 'level1', 'level2'):
            h = c(name)
            print >>fp, name
            for k in sorted(h.keys()):
                print >>fp, '    ', k + ':',  h[k]
        print >>fp, cfg._Channel(c(1).items())
        print >>fp, cfg._Channel(c(2).items())
        print >>fp, cfg._Channel(c(3).items())
        for name in c.channel_names:
            print >>fp, c.get_channel(name)
        text1 = fp.getvalue().strip()
        fp.close()
        fp = open(datadir + '/' + cfgfile + '.cfg.out')
        text2 = fp.read().strip()
        fp.close()
        self.assertTrue(text1 == text2, msg='Reading %s.cfg failed'%cfgfile)

if __name__ == '__main__':
    import nose
    nose.main()
