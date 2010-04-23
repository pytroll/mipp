#
# $Id$ 
#

"""This module will read satellit data files in OpenMTP format (eg. Meteosat-7 prolog file). Format described in:
'The Meteosat Archive; Format Guide No. 1; Basic Imagery: OpenMTP Format'; EUM FG 1; Rev 2.1; April 2000
"""

import sys
from StringIO import StringIO

import xrit
import xrit.mda
from xrit.bin_reader import *

__all__ = ['read_metadata',]

ASCII_HEADER_LEN = 1345
BINARY_HEADER_LEN = 144515
BINARY_HEADER_LEN_VISCOMP = 192999

def _read_ascii_header(fp):    
    fp = StringIO(fp.read(ASCII_HEADER_LEN)) # Don't mix iteration and read method.
    hdr = dict()
    for line in fp:
        k = line[:14].strip()
        v = line[15:].strip()
        hdr[k] = v
    return hdr

def _read_binary_header(fp, product_type):
    hdr = dict()
    hdr['fname'] =  fp.read(8)
    hdr['year'] = read_int4(fp.read(4))
    hdr['jday'] = read_int4(fp.read(4))
    hdr['slot'] = read_int4(fp.read(4))
    hdr['dtype'] = read_int4(fp.read(4))
    hdr['date'] = read_int4(fp.read(4))
    hdr['time'] = read_int4(fp.read(4))
    hdr['pltfrm'] = fp.read(2)
    fp.read(2) # spares
    hdr['proc'] = read_int4(fp.read(4))
    hdr['chan'] = read_int4(fp.read(4))
    hdr['calco'] = fp.read(5)
    hdr['space'] = fp.read(3)
    hdr['caltim'] = fp.read(5)
    fp.read(3) # spares
    hdr['rec2siz'] = read_int4(fp.read(4))
    hdr['lrecsiz'] = read_int4(fp.read(4))
    hdr['loffset'] = read_int4(fp.read(4))
    hdr['rtmet'] = fp.read(15)
    hdr['dmmod'] = read_int4(fp.read(4))
    hdr['rsmod'] = read_int4(fp.read(4))
    hdr['ssp'] = read_float4(fp.read(4))
    fp.read(12)
    fp.read(4)
    fp.read(8)
    hdr['line1'] = read_int4(fp.read(4))
    hdr['pixel1'] = read_int4(fp.read(4))
    hdr['nlines'] = read_int4(fp.read(4))
    hdr['npixels'] = read_int4(fp.read(4))
    fp.read(16)
    #hdr['mlt1'] = fp.read(2500)
    #hdr['mlt2'] = fp.read(2500)
    hdr['imgqua'] = read_int4(fp.read(4))
    fp.read(16)
    fp.read(2636) # only present for unrectified images
    hdr['ndgrp'] = read_int4(fp.read(4))
    hdr['dmstrt'] = read_int4(fp.read(4))
    hdr['dmend'] = read_int4(fp.read(4))
    hdr['dmstep'] = read_int4(fp.read(4))
    fp.read(8*105*105)
    hdr['ncor'] = read_int4(fp.read(4))
    hdr['chid1'] = read_int4(fp.read(4))
    fp.read(16*3030)
    if product_type == 'PVISBAN':
        hdr['chid2'] = read_int4(fp.read(4))
        fp.read(16*3030)
    return hdr


def read_metadata(prologue, image_files):
    """ Selected items from the Meteosat-7 prolog file.
    """
    md = xrit.mda.Metadata()
    fp = StringIO(prologue.data)
    asc_hdr = _read_ascii_header(fp)
    bin_hdr = _read_binary_header(fp, asc_hdr['ProductType'])
    md.product_name = prologue.product_id
    pf = asc_hdr['Platform']
    if pf == 'M7':
        pf = 'MET7'
    md.satname = pf.lower()
    md.channel = prologue.product_name[:4]
    md.product_type = asc_hdr['ProductType']
    md.region_name = 'full disc'
    md.sublon = bin_hdr['ssp']
    md.first_pixel = asc_hdr['FirstPixelOri']
    md.data_type = bin_hdr['dtype']*8
    md.image_size = (int(asc_hdr['NumberOfPixels']), int(asc_hdr['NumberOfLines']))
    md.line_offset = int(asc_hdr['LineOffset'])
    md.time_stamp = datetime.strptime(asc_hdr['Date'] + asc_hdr['Time'], "%y%m%d%H%M")
    md.production_time = datetime.strptime(asc_hdr['ProdDate'] + asc_hdr['ProdTime'], "%y%m%d%H:%M:%S")
    md.calibration_name = ''
    md.calibration_unit = ''
    md.calibration_table = None
    return md

if __name__ == '__main__':
    import xrit
    p = xrit.read_prologue(sys.argv[1])
    print read_metadata(p, sys.argv[2:])
