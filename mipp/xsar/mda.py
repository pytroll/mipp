#
# $Id$
#
import mipp.mda

class Metadata(mipp.mda.Metadata):
    token = ':'
    ignore_attributes = ('data',
                         'calibrate',
                         'tiepoints')

if __name__ == '__main__':
    import sys
    print Metadata().read(sys.argv[1])
