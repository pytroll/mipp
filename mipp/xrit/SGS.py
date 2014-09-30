#
# $Id$ 
#

"""This module will read satellit data files in SGS (Support Ground Segments) format (eg. GOES, MTSAT).
Format described in:
'MSG Ground Segment LRIT/HRIT Mission Specific Implementation'; EUM/MSG/SPE/057; Issue 6; 21 June 2006
"""

import sys
import numpy

from mipp.xrit import _xrit
from mipp.xrit import Metadata
from mipp.xrit import bin_reader as rbin

no_data_value = 0

__all__ = ['read_metadata']

def _read_sgs_common_header(fp):
    hdr = dict()
    hdr['CommonHeaderVersion'] = rbin.read_uint1(fp.read(1))
    fp.read(3)
    hdr['NominalSGSProductTime'] = rbin.read_cds_time(fp.read(6))
    hdr['SGSProductQuality'] = rbin.read_uint1(fp.read(1))
    hdr['SGSProductCompleteness'] = rbin.read_uint1(fp.read(1))
    hdr['SGSProductTimeliness'] = rbin.read_uint1(fp.read(1))
    hdr['SGSProcessingInstanceId'] = rbin.read_uint1(fp.read(1))
    hdr['BaseAlgorithmVersion'] = fp.read(16).strip()
    hdr['ProductAlgorithmVersion'] = fp.read(16).strip()
    return hdr
    
def _read_sgs_product_header(fp):
    hdr = dict()
    hdr['ImageProductHeaderVersion'] = rbin.read_uint1(fp.read(1))
    fp.read(3)
    hdr['ImageProductHeaderLength'] = rbin.read_uint4(fp.read(4))
    hdr['ImageProductVersion'] = rbin.read_uint1(fp.read(1))
    #hdr['ImageProductHeaderData'] = fp.read()
    return hdr

class _Calibrator(object):
    def __init__(self, hdr):
        self.hdr = hdr

        dd = []
        for k in sorted(hdr.keys()):
            if isinstance(k, int):
                v = hdr[k]
                dd.append([float(k), v])
        self.calibration_table = numpy.array(dd, dtype=numpy.float32)

    def __call__(self, image, calibrate=1):
        cal = self.calibration_table

        if type(cal) != numpy.ndarray:
            cal = numpy.array(cal)

        if cal.shape == (256, 2):
            cal = cal[:,1] # nasty !!!
            cal[int(no_data_value)] = no_data_value
            image = cal[image] # this does not work on masked arrays !!!
        elif cal.shape == (2, 2):
            scale = (cal[1][1] - cal[0][1])/(cal[1][0] - cal[0][0])
            offset = cal[0][1] - cal[0][0]*scale
            image = numpy.select([image == no_data_value*scale], [no_data_value], default=offset + image*scale)
        else:
            raise mipp.DecodeError("Could not recognize the shape %s of the calibration table"%str(cal.shape))

        return (image,
                self.hdr['_UNIT'])

def read_metadata(prologue, image_files):
    """ Selected items from the GOES image data files (not much information in prologue).
    """
    im = _xrit.read_imagedata(image_files[0])
    hdr = im.data_function.data_definition
    md = Metadata()
    md.calibrate = _Calibrator(hdr)
    md.satname = im.platform.lower()
    md.product_type = 'full disc'
    md.region_name = 'full disc'
    md.product_name = prologue.product_id
    md.channel = prologue.product_name[:4]
    ssp = float(im.product_name[5:-1].replace('_','.'))
    if im.product_name[-1].lower() == 'w':            
        ssp *= -1
    md.sublon = ssp
    md.first_pixel = 'north west'
    md.data_type = im.structure.nb
    nseg = im.segment.planned_end_seg_no - im.segment.planned_start_seg_no + 1
    md.image_size = (im.structure.nc, im.structure.nl*nseg) # !!!
    md.line_offset = 0
    md.time_stamp = im.time_stamp
    md.production_time = im.production_time
    md.calibration_unit = ""

    # Calibration table
    dd = []
    for k in sorted(hdr.keys()):
        if isinstance(k, int):
            v = hdr[k]
            dd.append([float(k), v])

    md.calibration_table = dict((('name', im.data_function.data_definition['_NAME']),
                                 ('unit', im.data_function.data_definition['_UNIT']),
                                 ('table', numpy.array(dd, dtype=numpy.float32))))

    md.no_data_value = no_data_value

    segment_size = im.structure.nl
    md.loff = im.navigation.loff + segment_size * (im.segment.seg_no - 1)
    md.coff = im.navigation.coff

    return md

def read_prologue_headers(fp):
    hdr = _read_sgs_common_header(fp)
    hdr.update(_read_sgs_product_header(fp))
    return hdr
    
if __name__ == '__main__':
    print read_metadata(_xrit.read_prologue(sys.argv[1]), sys.argv[2:])
