#
# $Id$ 
#

"""This module will read satellit data files in SGS (Support Ground Segments) format (eg. GOES, MTSAT).
Format described in:
'MSG Ground Segment LRIT/HRIT Mission Specific Implementation'; EUM/MSG/SPE/057; Issue 6; 21 June 2006
"""

import sys
import numpy

import xrit
from xrit.bin_reader import *

__all__ = ['read_metadata',]

class SGSDecodeError(Exception):
    pass

def _read_sgs_common_header(fp):
    hdr = dict()
    hdr['CommonHeaderVersion'] = read_uint1(fp.read(1))
    fp.read(3)
    hdr['NominalSGSProductTime'] = read_cds_time(fp.read(6))
    hdr['SGSProductQuality'] = read_uint1(fp.read(1))
    hdr['SGSProductCompleteness'] = read_uint1(fp.read(1))
    hdr['SGSProductTimeliness'] = read_uint1(fp.read(1))
    hdr['SGSProcessingInstanceId'] = read_uint1(fp.read(1))
    hdr['BaseAlgorithmVersion'] = fp.read(16).strip()
    hdr['ProductAlgorithmVersion'] = fp.read(16).strip()
    return hdr
    
def _read_sgs_product_header(fp):
    hdr = dict()
    hdr['ImageProductHeaderVersion'] = read_uint1(fp.read(1))
    fp.read(3)
    hdr['ImageProductHeaderLength'] = read_uint4(fp.read(4))
    hdr['ImageProductVersion'] = read_uint1(fp.read(1))
    #hdr['ImageProductHeaderData'] = fp.read()
    return hdr

def read_metadata(prologue, image_files):
    """ Selected items from the GOES image data files (not much information in prologue).
    """
    im = xrit.read_imagedata(image_files[0])
    md = xrit.mda.Metadata()
    md.satname = im.platform.lower()
    md.product_type = 'full disc'
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
    md.calibration_name = im.data_function.data_definition['_NAME']
    md.calibration_unit = im.data_function.data_definition['_UNIT']
    md.calibration_table = dict()
    dd = []
    keys = sorted(im.data_function.data_definition.keys())
    for k in keys:
        if type(k) == type(1):
            v = im.data_function.data_definition[k]
            dd.append([float(k), v])
    md.calibration_table = numpy.array(dd, dtype=numpy.float32)
    return md

def read_prologue_headers(fp):
    hdr = _read_sgs_common_header(fp)
    hdr.update(_read_sgs_product_header(fp))
    return hdr
    
if __name__ == '__main__':
    print read_metadata(xrit.read_prologue(sys.argv[1]), sys.argv[2:])
