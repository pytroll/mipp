import sys
import os
import unittest
import cStringIO

import buildpath_to_syspath
print sys.path
from xrit import cfg, geosnav

datadir = os.path.dirname(__file__) + '/data'

class Test(unittest.TestCase):

    def test_config_parser(self):
        cfgfile = 'meteosat09'        
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

    def test_navigation(self):
        expected = ((57.0, -0.0),
                    (2500, 2500),
                    (57.0, 76.504177857169125),
                    (2500, 100),
                    (313, 2500))
        nav = geosnav.GeosNavigation(57.0, 18204444, 18204444, 2500, 2500)
        values = (nav.lonlat((2500, 2500)),
                  nav.pixel((57.0, 0)),
                  nav.lonlat((2500, 100)),               
                  nav.pixel(nav.lonlat((2500, 100))),
                  nav.pixel((0,0)))
        self.assertTrue(values == expected, msg='Error in navigation')
               
if __name__ == '__main__':
    import nose
    nose.main()
