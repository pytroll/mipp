#
# $Id$
#
"""This module will read MSG level1.5 files, format documented in: 
'MSG Level 1.5 Image Data Format Description', EUM/MSG/ICD/105, v5A, 22 August 2007
"""
#raise NotImplementedError
import xrit.mda
import sys
from StringIO import StringIO
from xrit.bin_reader import *
import numpy as np

def read_header(fp):
    """Read the msg header.
    """
    hdr = dict()

    # Satellite definition

    satdef = {}
    satdef["SatelliteId"] = read_int2(fp.read(2))
    satdef["NominalLongitude"] = read_float4(fp.read(4))
    satdef["SatelliteStatus"] = ord(fp.read(1))

    hdr["SatelliteDefinition"] = satdef
    del satdef

    # Satellite operations

    satop = {}
    satop["LastManoeuvreFlag"] = ord(fp.read(1)) > 0
    satop["LastManoeuvreStartTime"] = read_cds_time(fp.read(6))
    satop["LastManoeuvreEndTime"] = read_cds_time(fp.read(6))
    satop["LastManoeuvreType"] =  ord(fp.read(1))
    satop["NextManoeuvreFlag"] = ord(fp.read(1)) > 0
    satop["NextManoeuvreStartTime"] = read_cds_time(fp.read(6))
    satop["NextManoeuvreEndTime"] = read_cds_time(fp.read(6))
    satop["NextManoeuvreType"] =  ord(fp.read(1))

    hdr["SatelliteOperations"] = satop
    del satop

    # Orbit

    orbit = {}
    orbit["PeriodStartTime"] = read_cds_time(fp.read(6))
    orbit["PeriodEndTime"] = read_cds_time(fp.read(6))
    orbitcoef = np.dtype("u2, u4, u2, u4,"
                         " (8,)f8, (8,)f8, (8,)f8,"
                         " (8,)f8, (8,)f8, (8,)f8")
    orbit["OrbitPolynomial"] = np.fromstring(fp.read(39600),
                                             dtype=orbitcoef,
                                             count=100)

    hdr["Orbit"] = orbit
    del orbit

    # Attitude

    attitude = {}
    attitude["PeriodStartTime"] = read_cds_time(fp.read(6))
    attitude["PeriodEndTime"] =  read_cds_time(fp.read(6))
    attitude["PrincipleAxisOffsetAngle"] = read_float8(fp.read(8))
    attitudecoef = np.dtype("u2, u4, u2, u4, (8,)f8, (8,)f8, (8,)f8")
    attitude["AttitudePolynomial"] = np.fromstring(fp.read(20400),
                                                   dtype=attitudecoef,
                                                   count=100)

    hdr["Attitude"] = attitude
    del attitude
    
    # SpinRateatRCStart
    
    hdr["SpinRateatRCStart"] = read_float8(fp.read(8))

    # UTCCorrelation

    utccor = {}
    
    utccor["PeriodStartTime"] = read_cds_time(fp.read(6))
    utccor["PeriodEndTime"] = read_cds_time(fp.read(6))
    utccor["OnBoardTimeStart"] = read_cuc_time(fp.read(7), 4, 3)
    utccor["VarOnBoardTimeStart"] = read_float8(fp.read(8))
    utccor["A1"] = read_float8(fp.read(8))
    utccor["VarA1"] = read_float8(fp.read(8))
    utccor["A2"] = read_float8(fp.read(8))
    utccor["VarA2"] = read_float8(fp.read(8))

    hdr["UTCCorrelation"] = utccor
    del utccor

    pat = {}
    pat["TrueRepeatCycleStart"] = read_cds_expanded_time(fp.read(10))
    pat["PlannedForwardScanEnd"] = read_cds_expanded_time(fp.read(10))
    pat["PlannedRepeatCycleEnd"] = read_cds_expanded_time(fp.read(10))

    print 'PAT', pat

    return hdr


def read_metadata(prologue, image_files):
    """ Selected items from the Meteosat-7 prolog file.
    """
    md = xrit.mda.Metadata()
    fp = StringIO(prologue.data)

    hdr = read_header(fp)
    md.sublon = hdr["SatelliteDefinition"]["NominalLongitude"]
    im = xrit.read_imagedata(image_files[0])
    md.product_name = str(im)
    md.channel = im.product_name
    nseg = im.segment.planned_end_seg_no - im.segment.planned_start_seg_no + 1
    md.image_size = (im.structure.nc, im.structure.nl*nseg) # !!!  get it from "Image Description Record"


    md.satname = im.platform.lower()
    md.product_type = 'full disc'
    md.region_name = 'full disc'
    md.first_pixel = 'south east' # get it from "Image Description Record"
    md.data_type = im.structure.nb
    md.line_offset = 0
    md.time_stamp = im.time_stamp
    md.production_time = im.production_time

    return md

if __name__ == '__main__':
    import xrit
    p = xrit.read_prologue(sys.argv[1])
    print dir(p)
    print p.platform
    print p.segment_id
    print p.is_compressed
    #print read_metadata(p, sys.argv[2:])
