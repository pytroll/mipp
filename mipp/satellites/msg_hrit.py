#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c20671.ad.smhi.se>

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

"""A reader for the MSG HRIT (EUMETCast disseminated) data
"""

from mipp.xrit import _xrit
from mipp.generic_loader import GenericLoader
import os.path


class MSGHRITLoader(GenericLoader):

    """Loader for MSG data"""

    def __init__(self, satid, timeslot=None, files=None):
        super(MSGHRITLoader, self).__init__(satid, timeslot=None, files=None)

        self.imagefiles = []
        self.prologue_filename = None
        self.epilogue_filename = None

        self._identify_files()

    def _identify_files(self):
        """Find the epilogue and the prologue files from the set of files provided 
        from outside"""

        for filename in self.files:
            if '-EPI' in os.path.basename(filename):
                self.epilogue_filename = filename
            elif '-PRO' in os.path.basename(filename):
                self.prologue_filename = filename
            else:
                self.imagefiles.append(filename)

    def _get_metadata(self):
        """ Selected items from the MSG prologue file.
        """
        segment_size = 464  # number of lines in a segment

        # Read the prologue:
        prologue = _xrit.read_prologue(self.prologue_filename)
        # Read the epilogue:

        fp = StringIO(prologue.data)
        hdr = read_proheader(fp)

        fp = StringIO(epilogue.data)
        ftr = read_epiheader(fp)

        im = _xrit.read_imagedata(image_files[0])

        md = Metadata()
        md.calibrate = _Calibrator(hdr, im.product_name)

        md.sublon = hdr["ProjectionDescription"]["LongitudeOfSSP"]
        md.product_name = im.product_id
        md.channel = im.product_name
        if md.channel == "HRV":
            md.image_size = np.array((hdr["ReferenceGridHRV"]["NumberOfLines"],
                                      hdr["ReferenceGridHRV"]["NumberOfColumns"]))
        else:
            md.image_size = np.array((hdr["ReferenceGridVIS_IR"]["NumberOfLines"],
                                      hdr["ReferenceGridVIS_IR"]["NumberOfColumns"]))

        md.satname = im.platform.lower()
        md.satnumber = SATNUM[hdr["SatelliteDefinition"]["SatelliteId"]]
        logger.debug("%s %s", md.satname, md.satnumber)
        md.product_type = 'full disc'
        md.region_name = 'full disc'
        if md.channel == "HRV":
            md.first_pixel = hdr["ReferenceGridHRV"]["GridOrigin"]
            ns_, ew_ = md.first_pixel.split()
            md.boundaries = np.array([[
                ftr["LowerSouthLineActual"],
                ftr["LowerNorthLineActual"],
                ftr["LowerEastColumnActual"],
                ftr["LowerWestColumnActual"]],
                [ftr["UpperSouthLineActual"],
                 ftr["UpperNorthLineActual"],
                 ftr["UpperEastColumnActual"],
                 ftr["UpperWestColumnActual"]]])

            md.coff = (ftr["Lower" + ew_.capitalize() + "ColumnActual"]
                       + im.navigation.coff - 1)
            md.loff = im.navigation.loff + \
                segment_size * (im.segment.seg_no - 1)

        else:
            md.first_pixel = hdr["ReferenceGridVIS_IR"]["GridOrigin"]
            ns_, ew_ = md.first_pixel.split()
            md.boundaries = np.array([[
                ftr["SouthernLineActual"],
                ftr["NorthernLineActual"],
                ftr["EasternColumnActual"],
                ftr["WesternColumnActual"]]])

            md.coff = im.navigation.coff
            md.loff = im.navigation.loff + \
                segment_size * (im.segment.seg_no - 1)

        md.data_type = im.structure.nb
        md.no_data_value = no_data_value
        md.line_offset = 0
        md.time_stamp = im.time_stamp
        md.production_time = im.production_time
        md.calibration_unit = ""

        return md
