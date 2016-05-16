#
# $Id$ 
#

"""This module will read satellit data files in JMA-HRIT format (eg. HIMAWARI-8).
Format described in:
JMA HRIT Mission Specific Implementation (Issue 1.2, 1 January, 2003)
http://www.data.jma.go.jp/mscweb/en/operation/type/HRIT/JMA_HRIT_Issue1.2.pdf
"""

import sys
import numpy

from mipp.xrit import _xrit
from mipp.xrit import Metadata
from mipp.xrit import bin_reader as rbin

no_data_value = 0

__all__ = ['read_metadata']

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
            cal = cal[:, 1]  # nasty !!!
            cal[int(no_data_value)] = no_data_value
            image = cal[image] # this does not work on masked arrays !!!
        elif cal.shape == (2, 2):
            scale = (cal[1][1] - cal[0][1])/(cal[1][0] - cal[0][0])
            offset = cal[0][1] - cal[0][0]*scale
            image = numpy.select([image == no_data_value*scale], [no_data_value], default=offset + image*scale)
        else:
            image = numpy.interp(image.ravel(), cal[:, 0], cal[:, 1]).reshape(image.shape)

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
    #md.product_name = im.product_id
    md.channel = im.product_name
    #ssp = float(im.product_name[5:-1].replace('_','.'))
    #if im.product_name[-1].lower() == 'w':
    #    ssp *= -1
    ssp = im.navigation.ssp
    md.sublon = ssp
    md.first_pixel = 'north west'
    md.data_type = -im.structure.nb
    nseg = im.segment.planned_end_seg_no - im.segment.planned_start_seg_no + 1
    #nseg = im.segment.total_seg_no
    md.image_size = (im.structure.nc, im.structure.nl*nseg) # !!!
    md.line_offset = 0
    #md.time_stamp = im.time_stamp
    md.production_time = im.production_time
    md.calibration_unit = ""

    # Calibration table
    dd = []
    for k in sorted(hdr.keys()):
        if isinstance(k, int):
            v = hdr[k]
            dd.append([float(k), v])

    try:
        md.calibration_table = dict((('name', im.data_function.data_definition['_NAME']),
                                     ('unit', im.data_function.data_definition['_UNIT']),
                                     ('table', numpy.array(dd, dtype=numpy.float32))))
    except KeyError:
        md.calibration_table = dict((('unit', im.data_function.data_definition['_UNIT']),
                                     ('table', numpy.array(dd, dtype=numpy.float32))))
    md.no_data_value = no_data_value

    segment_size = im.structure.nl

    #md.loff = im.navigation.loff + segment_size * (im.segment.seg_no - 1)
    md.loff = im.navigation.loff
    md.coff = im.navigation.coff

    return md

class EncryptionKeyMessageHeader(object):
    hdr_type = 129
    hdr_name = 'EncryptionKey'

    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.station_id = rbin.read_uint2(fp.read(2))

    def __str__(self):
        return  "hdr_type:%d, rec_len:%d"%\
               (self.hdr_type, self.rec_len)

class ImageCompensationInformationHeader(object):
    hdr_type = 130
    hdr_name = 'ImageCompensation'

    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.text = fp.read(self.rec_len-3).strip()

    def __str__(self):
        return  "hdr_type:%d, rec_len:%d"%\
               (self.hdr_type, self.rec_len)

class ImageObservationTimeHeader(object):
    hdr_type = 131
    hdr_name = 'ImageObservationTime'

    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.text = fp.read(self.rec_len-3).strip()

    def __str__(self):
        return  "hdr_type:%d, rec_len:%d"%\
               (self.hdr_type, self.rec_len)

class ImageQualityInformationHeader(object):
    hdr_type = 132
    hdr_name = 'ImageQuality'

    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.text = fp.read(self.rec_len-3).strip()

    def __str__(self):
        return  "hdr_type:%d, rec_len:%d"%\
               (self.hdr_type, self.rec_len)

class AnnotationHeader(object):
    hdr_type = 4
    hdr_name = 'annotation'
    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.text = fp.read(self.rec_len-3).strip()
        # a = [x.strip('_') for x in self.text.split('-')]
        # self.xrit_channel_id = a[0]
        # self.dissemination_id = int(a[1])
        # self.dissemination_sc = a[2]
        # self.platform = a[3]
        self.product_name = self.text[8:11]
        self.platform = "Himawari-8"
        # self.segment_name = a[5]
        # self.time_stamp = mipp.strptime(a[6], "%Y%m%d%H%M")
        # self.flags = a[7]
        # self.segment_id = a[3] + '_' + a[4] + '_' + a[5] + '_' + self.time_stamp.strftime("%Y%m%d_%H%M")
        # self.product_id = a[3] + '_' + a[4] + '_' + self.time_stamp.strftime("%Y%m%d_%H%M")

class SegmentIdentification(object):
    hdr_type = 128
    hdr_name = 'segment'
    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.seg_no = rbin.read_uint1(fp.read(1))
        self.planned_end_seg_no = rbin.read_uint1(fp.read(1))
        self.planned_start_seg_no = 1
        self.seg_line_no = rbin.read_uint2(fp.read(2))

    def __str__(self):
        return  "hdr_type:%d, rec_len:%d seg_no:%d, total_seg_no:%d, " \
                "seg_line_no:%d,"%\
               (self.hdr_type, self.rec_len, self.seg_no, self.planned_end_seg_no,\
                self.seg_line_no)


header_map = {0: _xrit.PrimaryHeader,
                    1: _xrit.ImageStructure,
                    2: _xrit.ImageNavigation,
                    3: _xrit.ImageDataFunction,
                    4: AnnotationHeader,
                    5: _xrit.TimeStampRecord,
                    128: SegmentIdentification,
                    129: EncryptionKeyMessageHeader,
                    130: ImageCompensationInformationHeader,
                    131: ImageObservationTimeHeader,
                    132: ImageQualityInformationHeader}

header_types = tuple(sorted(header_map.keys()))


if __name__ == '__main__':
    print read_metadata(None, sys.argv[1:])
