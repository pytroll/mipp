#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2012, 2013

# Author(s):

#   Martin Raspaud <martin.raspaud@smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Read Electro L N1 HRIT files.
"""
# comments on the document:
# - data is in little endian
# - geometric processing's TagChGroup should not be there.
# - can't read the satellite name
# - explanation on types ?

import logging

logger = logging.getLogger(__name__)

from mipp.xrit import bin_reader as rbin
from mipp.xrit import Metadata
from StringIO import StringIO
from mipp.xrit import _xrit
import numpy as np


class _Calibrator(object):
    def __init__(self, hdr, channel_name):
        self.hdr = hdr
        self.vis = channel_name.startswith("00_")
        channels = ["00_6",
                    "00_7",
                    "00_9",
                    "03_8",
                    "06_4",
                    "08_0",
                    "08_7",
                    "09_7",
                    "10_7",
                    "11_9"]
        chnb = channels.index(channel_name)
        self.calibration_table = hdr["ImageCalibration"][chnb, :]
        
    def __call__(self, image, calibrate=1):
        if calibrate == 0:
            return image
        if calibrate == 1:
            res = np.ma.masked_less_equal(self.calibration_table[image], 0)
            if self.vis:
                return (res, "%")
            else:
                return (res, "K")
    

def read_proheader(fp):
    hdr = {}

    satstatus = [("TagType", "<u4"),
                 ("TagLength", "<u4"),
                 ("SatelliteID", "<u8"),
                 ("SatelliteName", "S256"),
                 ("NominalLongitude", "<f8"),
                 ("SatelliteCondition", "<u4"),
                 ("TimeOffset", "<f8")]
    
    satstatus = np.dtype(satstatus)
    hdr["SatelliteStatus"] =  np.fromstring(fp.read(satstatus.itemsize),
                                            dtype=satstatus,
                                            count=1)[0]


    imaq = [("TagType", "<u4"),
            ("TagLength", "<u4"),
            ("Status", "<u4"),
            ("StartDelay", "<i4"),
            ("Cel", "<f8")]

    imaq = np.dtype(imaq)
    hdr["ImageAcqusition"] =  np.fromstring(fp.read(imaq.itemsize*10),
                                            dtype=imaq,
                                            count=10)


    imcal = np.dtype("(10, 1024)<i4")

    hdr["ImageCalibration"] = np.fromstring(fp.read(imcal.itemsize),
                                            dtype=imcal,
                                            count=1)[0] / 1000.0
    
    return hdr

def read_epiheader(fp):

    hdr = {}

    rproc = [("TagType", "<u4"),
             ("TagLength", "<u4"),
             ("RPSummary",
              [("Impulse", "<u4"),
               ("IsStrNoiseCorrection", "<u4"),
               ("IsOptic", "<u4"),
               ("IsBrightnessAligment", "<u4")]),
             ("OpticCorrection",
              [("Degree", "<i4"),
               ("A", "<f8", (16, ))]),
             ("RPQuality",
              [("EffDinRange", "<f8"),
               ("EathDarkening", "<f8"),
               ("Zone", "<f8"),
               ("Impulse", "<f8"),
               ("Group", "<f8"),
               ("DefectCount", "<u4"),
               ("DefectProcent", "<f8"),
               ("S_Noise_DT_Preflight", "<f8"),
               ("S_Noise_DT_Bort", "<f8"),
               ("S_Noise_DT_Video", "<f8"),
               ("S_Noise_DT_1_5", "<f8"),
               ("CalibrStability", "<f8"),
               ("TemnSKO", "<f8", (2, )),
               ("StructSKO", "<f8", (2, )),
               ("Struct_1_5", "<f8"),
               ("Zone_1_ 5", "<f8"),
               ("RadDif", "<f8")])]

    rproc = np.dtype(rproc)
    hdr["RadiometricProcessing"] =  np.fromstring(fp.read(rproc.itemsize*10),
                                                  dtype=rproc,
                                                  count=10)
    gproc =  [("TagType", "<u4"),
              ("TagLength", "<u4"),
              ("TGeomNormInfo",
               [("IsExist", "<u4"),
                ("IsNorm", "<u4"),
                ("SubLon", "<f8"),
                ("TypeProjection", "<u4"),
                ("PixInfo", "<f8", (4, ))]),
              ("SatInfo",
               [("TISO",
                 [("T0", "<f8"),
                  ("dT", "<f8"),
                  ("ASb", "<f8"),
                  ("Evsk", "<f8", (3, 3, 4)),
                  ("ARx", "<f8", (4, )),
                  ("ARy", "<f8", (4, )),
                  ("ARz", "<f8", (4, )),
                  ("AVx", "<f8", (4, )),
                  ("AVy", "<f8", (4, )),
                  ("AVz", "<f8", (4, ))]),
                ("Type", "<i4")]),
              ("TimeProcessing", "<f8"),
              ("ApriorAccuracy", "<f8"),
              ("RelativeAccuracy", "<f8", (2, ))]

    gproc = np.dtype(gproc)
    hdr["GeometricProcessing"] =  np.fromstring(fp.read(gproc.itemsize*10),
                                                dtype=gproc,
                                                count=10)
    
    
    
    return hdr

def read_metadata(prologue, image_files, epilogue):
    """ Selected items from the Electro L N1 prolog file.
    """

    segment_size = 464 # number of lines in a segment

    hdr = {}

    fp = StringIO(prologue.data)
    phdr = read_proheader(fp)
    fp = StringIO(epilogue.data)
    ehdr = read_epiheader(fp)

    hdr.update(phdr)
    hdr.update(ehdr)

    im = _xrit.read_imagedata(image_files[0])

    md = Metadata()

    md.sublon = np.rad2deg(hdr["SatelliteStatus"]["NominalLongitude"])

    md.image_size = (im.structure.nc, im.structure.nc)

    md.channel = im.product_name[:4]
    md.satname = im.platform.lower()
    md.line_offset = 0
    md.data_type = im.structure.nb
    md.no_data_value = 0
    md.first_pixel = "north west"
    md.calibrate = _Calibrator(hdr, md.channel)

    segment_size = im.structure.nl
    md.loff = im.navigation.loff + segment_size * (im.segment.seg_no - 1)
    md.coff = im.navigation.coff
    return md
