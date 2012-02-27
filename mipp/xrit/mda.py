#
# $Id$
#
import mipp.mda

class Metadata(mipp.mda.Metadata):
    token = ':'
    ignore_attributes = ('line_offset', 'first_pixel',
                         'coff', 'loff',
                         'image_data', 'boundaries')
if __name__ == '__main__':
    import sys
    print Metadata().read(sys.argv[1])
