#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Lars Orum Rasmussen, Adam.Dybbroe, Ioan Ferencik

# Author(s):

#   Adam.Dybbroe <adam.dybbroe@smhi.se>
#   Ioan Ferencik
#   Lars Orum Rasmussen

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

Interface for MPOP:
    other.load(...)

Inherit and define:
    other.load(...) (calling this.__getitem__(...), calling other._read(...)) hmm ?
    other._read(rows, columns)

class GenericLoader:

    def __init__(self, satid=None, channels=None, timeslot=None, files=None):
        # Definening:
        self.mda

        self.channels
        self.satid

        self.image_files
        self._get_metadata()

    def __getitem__(self, item):
        ...
        self._read(rows, columns)

class SpecificLoader(GenericLoader):

    def __init__(...):
        ...


    def load(area_extent, calibrate=1):
         self[slice_obj]
         ...
         return self.mda, image

    def _read(rows, columns):
        ....
    def _get_metadata()


Note: have a commen data container class between MPOP and MIPP

"""

import os
from StringIO import StringIO
import numpy as np

from mipp.satellites.msg_hrit import _xrit
from mipp.satellites.msg_hrit import bin_reader as rbin
from mipp.generic_loader import GenericLoader
from mipp.metadata import Metadata

import logging
LOG = logging.getLogger(__name__)

NO_DATA_VALUE = 0


SATNUM = {321: "08",
          322: "09",
          323: "10",
          324: "11"}


def _null_converter(blob):
    return blob


class MSGHRITLoader(GenericLoader):

    """Loader for MSG data"""

    def __init__(self, platform_name=None, channels=None, timeslot=None, files=None):

        self.image_filenames = []
        self.prologue_filename = None
        self.epilogue_filename = None
        self.prologue = None
        self.epilogue = None

        super(MSGHRITLoader, self).__init__(platform_name=platform_name,
                                            channels=channels, timeslot=timeslot, files=files)

    def _slice2extent(self, rows, columns, rotated=True):
        """ Calculate area extent.
        If rotated=True then rows and columns are reflecting the actual rows and columns.
        """
        ns_, ew_ = self.mda.first_pixel.split()

        loff = self.mda.loff
        coff = self.mda.coff
        if ns_ == "south":
            loff = self.mda.number_of_columns - loff - 1
            if rotated:
                rows = slice(self.mda.number_of_lines - rows.stop,
                             self.mda.number_of_lines - rows.start)
        else:
            loff -= 1
        if ew_ == "east":
            coff = self.mda.number_of_lines - coff - 1
            if rotated:
                columns = slice(self.mda.number_of_columns - columns.stop,
                                self.mda.number_of_columns - columns.start)
        else:
            coff -= 1

        LOG.debug('slice2extent: size %d, %d' %
                  (columns.stop - columns.start, rows.stop - rows.start))
        rows = slice(rows.start, rows.stop - 1)
        columns = slice(columns.start, columns.stop - 1)

        row_size = self.mda.xscale
        col_size = self.mda.yscale

        ll_x = (columns.start - coff - 0.5) * col_size
        ll_y = -(rows.stop - loff + 0.5) * row_size
        ur_x = (columns.stop - coff + 0.5) * col_size
        ur_y = -(rows.start - loff - 0.5) * row_size

        LOG.debug('slice2extent: computed extent %.2f, %.2f, %.2f, %.2f' %
                  (ll_x, ll_y, ur_x, ur_y))
        LOG.debug('slice2extent: computed size %d, %d' %
                  (int(np.round((ur_x - ll_x) / col_size)),
                   int(np.round((ur_y - ll_y) / row_size))))

        return [ll_x, ll_y, ur_x, ur_y]

    def _identify_files(self):
        """Find the epilogue and the prologue files from the set of files provided
        from outside"""

        for filename in self.files:
            if '-EPI' in os.path.basename(filename):
                self.epilogue_filename = filename
            elif '-PRO' in os.path.basename(filename):
                self.prologue_filename = filename
            else:
                self.image_filenames.append(filename)

        self.image_filenames.sort()

    def _get_metadata(self):
        """ Selected items from the MSG prologue file.
        """
        self._identify_files()

        segment_size = 464  # number of lines in a segment

        # Read the prologue:
        prologue = _xrit.read_prologue(self.prologue_filename)
        # Read the epilogue:
        epilogue = _xrit.read_epilogue(self.epilogue_filename)

        fp = StringIO(prologue.data)
        self.prologue = read_proheader(fp)

        fp = StringIO(epilogue.data)
        self.epilogue = read_epiheader(fp)

        im = _xrit.read_imagedata(self.image_filenames[0])

        self.channels = [im.product_name]

        md = Metadata()
        #md.calibrate = _Calibrator(self.prologue, im.product_name)

        if 'HRV' in im.product_name:
            md.xscale = 1000.134348869
            md.yscale = 1000.134348869
        else:
            md.xscale = 3000.403165817
            md.yscale = 3000.403165817

        md.projection = im.navigation.proj_name.lower()
        md.sublon = self.prologue["ProjectionDescription"]["LongitudeOfSSP"]
        md.proj4_str = "proj=geos lon_0=%.2f lat_0=0.00 a=6378169.00 b=6356583.80 h=35785831.00" % md.sublon
        md.product_name = im.product_id
        md.channel_id = im.product_name
        if md.channel_id == "HRV":
            md.number_of_columns = self.prologue[
                "ReferenceGridHRV"]["NumberOfColumns"]
            md.number_of_lines = self.prologue[
                "ReferenceGridHRV"]["NumberOfLines"]
        else:
            md.number_of_columns = self.prologue[
                "ReferenceGridVIS_IR"]["NumberOfColumns"]
            md.number_of_lines = self.prologue[
                "ReferenceGridVIS_IR"]["NumberOfLines"]

        md.image_size = np.array((md.number_of_columns,
                                  md.number_of_lines))

        md.satname = im.platform.lower()
        md.satnumber = SATNUM[
            self.prologue["SatelliteDefinition"]["SatelliteId"]]
        LOG.debug("%s %s", md.satname, md.satnumber)
        md.product_type = 'full disc'
        md.region_name = 'full disc'
        if md.channel_id == "HRV":
            md.first_pixel = self.prologue["ReferenceGridHRV"]["GridOrigin"]
            dummy, ew_ = md.first_pixel.split()
            md.boundaries = np.array([[
                self.epilogue["LowerSouthLineActual"],
                self.epilogue["LowerNorthLineActual"],
                self.epilogue["LowerEastColumnActual"],
                self.epilogue["LowerWestColumnActual"]],
                [self.epilogue["UpperSouthLineActual"],
                 self.epilogue["UpperNorthLineActual"],
                 self.epilogue["UpperEastColumnActual"],
                 self.epilogue["UpperWestColumnActual"]]])

            md.coff = (self.epilogue["Lower" + ew_.capitalize() + "ColumnActual"]
                       + im.navigation.coff - 1)
            md.loff = im.navigation.loff + \
                segment_size * (im.segment.seg_no - 1)

        else:
            md.first_pixel = self.prologue["ReferenceGridVIS_IR"]["GridOrigin"]
            dummy, ew_ = md.first_pixel.split()
            md.boundaries = np.array([[
                self.epilogue["SouthernLineActual"],
                self.epilogue["NorthernLineActual"],
                self.epilogue["EasternColumnActual"],
                self.epilogue["WesternColumnActual"]]])

            md.coff = im.navigation.coff
            md.loff = im.navigation.loff + \
                segment_size * (im.segment.seg_no - 1)

        md.data_type = im.structure.nb
        md.no_data_value = NO_DATA_VALUE
        md.line_offset = 0
        md.timestamp = im.time_stamp
        md.production_time = im.production_time
        md.calibration_unit = ""

        return md

    def load(self, area_extent=None, calibrate=1):
        """Load the data
        """

        if len(self.channels) != 1:
            raise IOError(
                'Data loading requires one channel only at the moment!')

        # Check if the files are xrit-compressed, and decompress them
        # accordingly:
        decomp_files = decompress(self.image_filenames)

        #
        # Call generic slicer
        #
        slice_obj = self._area_extent_to_slice(area_extent)

        # You can call __getitem__ or _read
        # mda, img = self[slice_obj]
        img = self._read(*slice_obj)
        mda = self.mda
        #
        # Calibrate
        #
        from mipp.satellites.msg_calibrate import Calibrator
        # Note: teach Calibrator to use mda instead of prologue
        img, unit = Calibrator(self.prologue, self.mda.channel_id)(
            img, calibrate=calibrate)
        mda.calibration_unit = unit
        return mda, img

    def _area_extent_to_slice(self, area_extent):
        """Slice according to (ll_x, ll_y, ur_x, ur_y) or read full disc.
        """
        if area_extent is None:
            # full disc
            return (slice(0, self.mda.number_of_lines),
                    slice(0, self.mda.number_of_columns))

        # slice
        area_extent = tuple(area_extent)
        if len(area_extent) != 4:
            raise TypeError("optional argument must be an area_extent")

        ns_, ew_ = self.mda.first_pixel.split()
        if ns_ == "south":
            loff = self.mda.number_of_columns - self.mda.loff - 1
        else:
            loff = self.mda.loff - 1

        if ew_ == "east":
            coff = self.mda.number_of_lines - self.mda.coff - 1
        else:
            coff = self.mda.coff - 1

        try:
            row_size = self.mda.xscale
            col_size = self.mda.yscale
        except AttributeError:
            row_size = self.mda.pixel_size[0]
            col_size = self.mda.pixel_size[1]

        LOG.debug('area_extent: %.2f, %.2f, %.2f, %.2f' %
                  tuple(area_extent))
        LOG.debug('area_extent: resolution %.2f, %.2f' %
                  (row_size, col_size))
        LOG.debug('area_extent: loff, coff %d, %d' % (loff, coff))
        LOG.debug('area_extent: expected size %d, %d' %
                  (int(np.round((area_extent[2] - area_extent[0]) / col_size)),
                   int(np.round((area_extent[3] - area_extent[1]) / row_size))))

        col_start = int(np.round(area_extent[0] / col_size + coff + 0.5))
        row_stop = int(np.round(area_extent[1] / -row_size + loff - 0.5))
        col_stop = int(np.round(area_extent[2] / col_size + coff - 0.5))
        row_start = int(np.round(area_extent[3] / -row_size + loff + 0.5))

        row_stop += 1
        col_stop += 1

        LOG.debug('Returning slices: (%d, %d), (%d, %d)' % (
            row_start, row_stop, col_start, col_stop))
        LOG.debug('area_extent: computed size %d, %d' %
                  (col_stop - col_start, row_stop - row_start))
        return (slice(row_start, row_stop), slice(col_start, col_stop))

    def _read(self, rows, columns):
        """Here we need the following metadata:

        .number_of_columns
        .number_of_lines
        .data_type (8, 10, 16 ...)
        .first_pixel
        .no_data_value
        .line_offset
        """
        import mipp.tools.convert

        shape = (rows.stop - rows.start, columns.stop - columns.start)
        if (columns.start < 0 or
                columns.stop > self.mda.number_of_columns or
                rows.start < 0 or
                rows.stop > self.mda.number_of_lines):
            raise IndexError("index out of range")

        image_files = self.image_filenames

        #
        # Order segments
        #
        segments = {}
        for f in image_files:
            s = _xrit.read_imagedata(f)
            segments[s.segment.seg_no] = f

        start_seg_no = s.segment.planned_start_seg_no
        end_seg_no = s.segment.planned_end_seg_no
        ncols = s.structure.nc
        segment_nlines = s.structure.nl

        #
        # Data type
        #
        converter = _null_converter
        if self.mda.data_type == 8:
            data_type = np.uint8
            data_type_len = 8
        elif self.mda.data_type == 10:
            converter = mipp.tools.convert.dec10to16
            data_type = np.uint16
            data_type_len = 16
        elif self.mda.data_type == 16:
            data_type = np.uint16
            data_type_len = 16
        else:
            raise IOError("unknown data type: %d" % self.mda.data_type +
                          " bit per pixel")

        #
        # Calculate initial and final line and column.
        # The interface 'load(..., center, size)' will produce
        # correct values relative to the image orientation.
        # line_init, line_end : 1-based
        #
        line_init = rows.start + 1
        line_end = line_init + rows.stop - rows.start - 1
        col_count = shape[1]
        col_offset = (columns.start) * data_type_len // 8

        #
        # Calculate initial and final segments
        # depending on the image orientation.
        # seg_init, seg_end : 1-based.
        #
        seg_init = ((line_init - 1) // segment_nlines) + 1
        seg_end = ((line_end - 1) // segment_nlines) + 1

        #
        # Calculate initial line in image, line increment
        # offset for columns and factor for columns,
        # and factor for columns, depending on the image
        # orientation
        #
        if self.mda.first_pixel == 'north west':
            first_line = 0
            increment_line = 1
            factor_col = 1
        elif self.mda.first_pixel == 'north east':
            first_line = 0
            increment_line = 1
            factor_col = -1
        elif self.mda.first_pixel == 'south west':
            first_line = shape[0] - 1
            increment_line = -1
            factor_col = 1
        elif self.mda.first_pixel == 'south east':
            first_line = shape[0] - 1
            increment_line = -1
            factor_col = -1
        else:
            raise IOError("unknown geographical orientation of " +
                          "first pixel: '%s'" % self.mda.first_pixel)

        #
        # Generate final image with no data
        #
        image = np.zeros(shape, dtype=data_type) + self.mda.no_data_value

        #
        # Begin the segment processing.
        #
        seg_no = seg_init
        line_in_image = first_line
        while seg_no <= seg_end:
            line_in_segment = 1

            #
            # Calculate initial line in actual segment.
            #
            if seg_no == seg_init:
                init_line_in_segment = (line_init
                                        - (segment_nlines * (seg_init - 1)))
            else:
                init_line_in_segment = 1

            #
            # Calculate final line in actual segment.
            #
            if seg_no == seg_end:
                end_line_in_segment = line_end - \
                    (segment_nlines * (seg_end - 1))
            else:
                end_line_in_segment = segment_nlines

            #
            # Open segment file.
            #
            seg_file = segments.get(seg_no, None)
            if not seg_file:
                #
                # No data for this segment.
                #
                LOG.warning("Segment number %d not found" % seg_no)

                # all image lines are already set to no-data count.
                line_in_segment = init_line_in_segment
                while line_in_segment <= end_line_in_segment:
                    line_in_segment += 1
                    line_in_image += increment_line
            else:
                #
                # Data for this segment.
                #
                LOG.info("Read %s" % seg_file)
                seg = _xrit.read_imagedata(seg_file)

                #
                # Skip lines not processed.
                #
                while line_in_segment < init_line_in_segment:
                    line = seg.readline()
                    line_in_segment += 1

                #
                # Reading and processing segment lines.
                #
                while line_in_segment <= end_line_in_segment:
                    line = seg.readline()[self.mda.line_offset:]
                    line = converter(line)

                    line = (np.frombuffer(line,
                                             dtype=data_type,
                                             count=col_count,
                                             offset=col_offset)[::factor_col])

                    #
                    # Insert image data.
                    #
                    image[line_in_image] = line

                    line_in_segment += 1
                    line_in_image += increment_line

                seg.close()

            seg_no += 1

        #
        # Compute mask before calibration
        #

        mask = (image == self.mda.no_data_value)

        #
        # With or without mask ?
        #
        do_mask = True
        if do_mask and not isinstance(image, np.ma.core.MaskedArray):
            image = np.ma.array(image, mask=mask, copy=False)
        elif ((not do_mask) and
                isinstance(image, np.ma.core.MaskedArray)):
            image = image.filled(self.mda.no_data_value)

        return image


def read_proheader(fp):
    """Read the msg header.
    """

    hdr = dict()

    # Satellite definition

    satdef = {}
    satdef["SatelliteId"] = rbin.read_uint2(fp.read(2))
    satdef["NominalLongitude"] = rbin.read_float4(fp.read(4))
    satdef["SatelliteStatus"] = ord(fp.read(1))

    hdr["SatelliteDefinition"] = satdef
    del satdef

    # Satellite operations

    satop = {}
    satop["LastManoeuvreFlag"] = ord(fp.read(1)) > 0
    satop["LastManoeuvreStartTime"] = rbin.read_cds_time(fp.read(6))
    satop["LastManoeuvreEndTime"] = rbin.read_cds_time(fp.read(6))
    satop["LastManoeuvreType"] = ord(fp.read(1))
    satop["NextManoeuvreFlag"] = ord(fp.read(1)) > 0
    satop["NextManoeuvreStartTime"] = rbin.read_cds_time(fp.read(6))
    satop["NextManoeuvreEndTime"] = rbin.read_cds_time(fp.read(6))
    satop["NextManoeuvreType"] = ord(fp.read(1))

    hdr["SatelliteOperations"] = satop
    del satop

    # Orbit

    orbit = {}
    orbit["PeriodStartTime"] = rbin.read_cds_time(fp.read(6))
    orbit["PeriodEndTime"] = rbin.read_cds_time(fp.read(6))
    orbitcoef = np.dtype(">u2, >u4, >u2, >u4,"
                         " (8,)>f8, (8,)>f8, (8,)>f8,"
                         " (8,)>f8, (8,)>f8, (8,)>f8")
    orbit["OrbitPolynomial"] = np.fromstring(fp.read(39600),
                                             dtype=orbitcoef,
                                             count=100)

    hdr["Orbit"] = orbit
    del orbit

    # Attitude

    attitude = {}
    attitude["PeriodStartTime"] = rbin.read_cds_time(fp.read(6))
    attitude["PeriodEndTime"] = rbin.read_cds_time(fp.read(6))
    attitude["PrincipleAxisOffsetAngle"] = rbin.read_float8(fp.read(8))
    attitudecoef = np.dtype(">u2, >u4, >u2, >u4, (8,)>f8, (8,)>f8, (8,)>f8")
    attitude["AttitudePolynomial"] = np.fromstring(fp.read(20400),
                                                   dtype=attitudecoef,
                                                   count=100)

    hdr["Attitude"] = attitude
    del attitude

    # SpinRateatRCStart

    hdr["SpinRateatRCStart"] = rbin.read_float8(fp.read(8))

    # UTCCorrelation

    utccor = {}

    utccor["PeriodStartTime"] = rbin.read_cds_time(fp.read(6))
    utccor["PeriodEndTime"] = rbin.read_cds_time(fp.read(6))
    utccor["OnBoardTimeStart"] = rbin.read_cuc_time(fp.read(7), 4, 3)
    utccor["VarOnBoardTimeStart"] = rbin.read_float8(fp.read(8))
    utccor["A1"] = rbin.read_float8(fp.read(8))
    utccor["VarA1"] = rbin.read_float8(fp.read(8))
    utccor["A2"] = rbin.read_float8(fp.read(8))
    utccor["VarA2"] = rbin.read_float8(fp.read(8))

    hdr["UTCCorrelation"] = utccor
    del utccor

    # PlannedAcquisitionTime

    pat = {}
    pat["TrueRepeatCycleStart"] = rbin.read_cds_expanded_time(fp.read(10))
    pat["PlannedForwardScanEnd"] = rbin.read_cds_expanded_time(fp.read(10))
    pat["PlannedRepeatCycleEnd"] = rbin.read_cds_expanded_time(fp.read(10))

    hdr["PlannedAcquisitionTime"] = pat

    # RadiometerStatus

    radiostatus = {}
    radiostatus["ChannelStatus"] = np.fromstring(fp.read(12), dtype=np.uint8)
    radiostatus["DetectorStatus"] = np.fromstring(fp.read(42), dtype=np.uint8)

    hdr["RadiometerStatus"] = radiostatus

    # RadiometerSettings

    radiosettings = {}
    radiosettings["MDUSamplingDelays"] = np.fromstring(
        fp.read(42 * 2), dtype=">u2")
    radiosettings["HRVFrameOffsets"] = {}
    radiosettings["HRVFrameOffsets"][
        "MDUNomHRVDelay1"] = rbin.read_uint2(fp.read(2))
    radiosettings["HRVFrameOffsets"][
        "MDUNomHRVDelay2"] = rbin.read_uint2(fp.read(2))
    radiosettings["HRVFrameOffsets"]["Spare"] = rbin.read_uint2(fp.read(2))
    radiosettings["HRVFrameOffsets"][
        "MDUNomHRVBreakline"] = rbin.read_uint2(fp.read(2))
    radiosettings["DHSSSynchSelection"] = ord(fp.read(1))
    radiosettings["MDUOutGain"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["MDUCourseGain"] = np.fromstring(fp.read(42), dtype=np.uint8)
    radiosettings["MDUFineGain"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["MDUNumericalOffset"] = np.fromstring(
        fp.read(42 * 2), dtype=">u2")
    radiosettings["PUGain"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["PUOffset"] = np.fromstring(fp.read(27 * 2), dtype=">u2")
    radiosettings["PUBias"] = np.fromstring(fp.read(15 * 2), dtype=">u2")
    radiosettings["OperationParameters"] = {}
    radiosettings["OperationParameters"][
        "L0_LineCounter"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"][
        "K1_RetraceLines"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"][
        "K2_PauseDeciseconds"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"][
        "K3_RetraceLines"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"][
        "K4_PauseDeciseconds"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"][
        "K5_RetraceLines"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"][
        "X_DeepSpaceWindowPosition"] = ord(fp.read(1))
    radiosettings["RefocusingLines"] = rbin.read_uint2(fp.read(2))
    radiosettings["RefocusingDirection"] = ord(fp.read(1))
    radiosettings["RefocusingPosition"] = rbin.read_uint2(fp.read(2))
    radiosettings["ScanRefPosFlag"] = ord(fp.read(1)) > 0
    radiosettings["ScanRefPosNumber"] = rbin.read_uint2(fp.read(2))
    radiosettings["ScanRefPosVal"] = rbin.read_float4(fp.read(4))
    radiosettings["ScanFirstLine"] = rbin.read_uint2(fp.read(2))
    radiosettings["ScanLastLine"] = rbin.read_uint2(fp.read(2))
    radiosettings["RetraceStartLine"] = rbin.read_uint2(fp.read(2))

    hdr["RadiometerSettings"] = radiosettings

    # RadiometerOperations

    radiooper = {}

    radiooper["LastGainChangeFlag"] = ord(fp.read(1)) > 0
    radiooper["LastGainChangeTime"] = rbin.read_cds_time(fp.read(6))
    radiooper["Decontamination"] = {}
    radiooper["Decontamination"]["DecontaminationNow"] = ord(fp.read(1)) > 0
    radiooper["Decontamination"][
        "DecontaminationStart"] = rbin.read_cds_time(fp.read(6))
    radiooper["Decontamination"][
        "DecontaminationEnd"] = rbin.read_cds_time(fp.read(6))

    radiooper["BBCalScheduled"] = ord(fp.read(1)) > 0
    radiooper["BBCalibrationType"] = ord(fp.read(1))
    radiooper["BBFirstLine"] = rbin.read_uint2(fp.read(2))
    radiooper["BBLastLine"] = rbin.read_uint2(fp.read(2))
    radiooper["ColdFocalPlaneOpTemp"] = rbin.read_uint2(fp.read(2))
    radiooper["WarmFocalPlaneOpTemp"] = rbin.read_uint2(fp.read(2))

    hdr["RadiometerOperations"] = radiooper

    # CelestialEvents
    # CelestialBodiesPosition

    celbodies = {}
    celbodies["PeriodTimeStart"] = rbin.read_cds_time(fp.read(6))
    celbodies["PeriodTimeEnd"] = rbin.read_cds_time(fp.read(6))
    celbodies["RelatedOrbitFileTime"] = fp.read(15)
    celbodies["RelatedAttitudeFileTime"] = fp.read(15)
    earthmoonsuncoef = np.dtype(">u2, >u4, >u2, >u4, (8,)>f8, (8,)>f8")
    celbodies["EarthEphemeris"] = np.fromstring(fp.read(14000),
                                                dtype=earthmoonsuncoef,
                                                count=100)
    celbodies["MoonEphemeris"] = np.fromstring(fp.read(14000),
                                               dtype=earthmoonsuncoef,
                                               count=100)
    celbodies["SunEphemeris"] = np.fromstring(fp.read(14000),
                                              dtype=earthmoonsuncoef,
                                              count=100)
    starcoef = np.dtype(">u2, >u2, >u4, >u2, >u4, (8,)>f8, (8,)>f8")
    starcoefs = np.dtype([('starcoefs', starcoef, (20,))])

    celbodies["StarEphemeris"] = np.fromstring(fp.read(284000),
                                               dtype=starcoefs,
                                               count=100)

    hdr["CelestialBodiesPosition"] = celbodies

    # RelationToImage

    reltoim = {}
    reltoim["TypeofEclipse"] = ord(fp.read(1))
    reltoim["EclipseStartTime"] = rbin.read_cds_time(fp.read(6))
    reltoim["EclipseEndTime"] = rbin.read_cds_time(fp.read(6))
    reltoim["VisibleBodiesInImage"] = ord(fp.read(1))
    reltoim["BodiesClosetoFOV"] = ord(fp.read(1))
    reltoim["ImpactOnImageQuality"] = ord(fp.read(1))

    hdr["RelationToImage"] = reltoim

    # ImageDescriptionRecord

    grid_origin = ["north west", "south west", "south east", "north east"]

    # ProjectionDescription

    projdes = {}
    projdes["TypeOfProjection"] = ord(fp.read(1))
    projdes["LongitudeOfSSP"] = rbin.read_float4(fp.read(4))

    hdr["ProjectionDescription"] = projdes

    # ReferenceGridVIS_IR

    refvisir = {}
    refvisir["NumberOfLines"] = rbin.read_int4(fp.read(4))
    refvisir["NumberOfColumns"] = rbin.read_int4(fp.read(4))
    refvisir["LineDirGridStep"] = rbin.read_float4(fp.read(4))
    refvisir["ColumnDirGridStep"] = rbin.read_float4(fp.read(4))
    refvisir["GridOrigin"] = grid_origin[ord(fp.read(1))]

    hdr["ReferenceGridVIS_IR"] = refvisir

    # ReferenceGridHRV

    refhrv = {}
    refhrv["NumberOfLines"] = rbin.read_int4(fp.read(4))
    refhrv["NumberOfColumns"] = rbin.read_int4(fp.read(4))
    refhrv["LineDirGridStep"] = rbin.read_float4(fp.read(4))
    refhrv["ColumnDirGridStep"] = rbin.read_float4(fp.read(4))
    refhrv["GridOrigin"] = grid_origin[ord(fp.read(1))]

    hdr["ReferenceGridHRV"] = refhrv

    # PlannedCoverageVIS_IR

    covvisir = {}
    covvisir["SouthernLinePlanned"] = rbin.read_int4(fp.read(4))
    covvisir["NorthernLinePlanned"] = rbin.read_int4(fp.read(4))
    covvisir["EasternColumnPlanned"] = rbin.read_int4(fp.read(4))
    covvisir["WesternColumnPlanned"] = rbin.read_int4(fp.read(4))

    hdr["PlannedCoverageVIS_IR"] = covvisir

    # PlannedCoverageHRV

    covhrv = {}

    covhrv["LowerSouthLinePlanned"] = rbin.read_int4(fp.read(4))
    covhrv["LowerNorthLinePlanned"] = rbin.read_int4(fp.read(4))
    covhrv["LowerEastColumnPlanned"] = rbin.read_int4(fp.read(4))
    covhrv["LowerWestColumnPlanned"] = rbin.read_int4(fp.read(4))
    covhrv["UpperSouthLinePlanned"] = rbin.read_int4(fp.read(4))
    covhrv["UpperNorthLinePlanned"] = rbin.read_int4(fp.read(4))
    covhrv["UpperEastColumnPlanned"] = rbin.read_int4(fp.read(4))
    covhrv["UpperWestColumnPlanned"] = rbin.read_int4(fp.read(4))

    hdr["PlannedCoverageHRV"] = covhrv

    # Level 1_5 ImageProduction

    image_proc_direction = ["North-South", "South-North"]
    pixel_gen_direction = ["East-West", "West-East"]

    l15prod = {}
    l15prod["ImageProcDirection"] = image_proc_direction[ord(fp.read(1))]
    l15prod["PixelGenDirection"] = pixel_gen_direction[ord(fp.read(1))]

    # 0: No processing, 1: Spectral radiance, 2: Effective radiance
    l15prod["PlannedChanProcessing"] = np.fromstring(fp.read(12),
                                                     dtype=np.uint8)

    hdr["Level 1_5 ImageProduction"] = l15prod

    # RadiometricProcessing

    # RPSummary

    rpsummary = {}
    rpsummary["RadianceLinearization"] = np.fromstring(
        fp.read(12), dtype=np.bool)

    rpsummary["DetectorEqualization"] = np.fromstring(
        fp.read(12), dtype=np.bool)
    rpsummary["OnboardCalibrationResult"] = np.fromstring(
        fp.read(12), dtype=np.bool)
    rpsummary["MPEFCalFeedback"] = np.fromstring(fp.read(12), dtype=np.bool)
    rpsummary["MTFAdaptation"] = np.fromstring(fp.read(12), dtype=np.bool)
    rpsummary["StraylightCorrectionFlag"] = np.fromstring(
        fp.read(12), dtype=np.bool)

    hdr["RPSummary"] = rpsummary

    # Level1_5ImageCalibration

    caltype = np.dtype([('Cal_Slope', '>f8'), ('Cal_Offset', '>f8')])

    hdr["Level1_5ImageCalibration"] = np.fromstring(
        fp.read(192), dtype=caltype)

    # BlackBodyDataUsed

    bbdu = {}

    bbdu["BBObservationUTC"] = rbin.read_cds_expanded_time(fp.read(10))
    bbdu["BBRelatedData"] = {}
    bbdu["BBRelatedData"][
        "OnBoardBBTime"] = rbin.read_cuc_time(fp.read(7), 4, 3)
    bbdu["BBRelatedData"]["MDUOutGain"] = np.fromstring(fp.read(42 * 2),
                                                        dtype=">u2")
    bbdu["BBRelatedData"]["MDUCoarseGain"] = np.fromstring(fp.read(42),
                                                           dtype=np.uint8)
    bbdu["BBRelatedData"]["MDUFineGain"] = np.fromstring(fp.read(42 * 2),
                                                         dtype=">u2")
    bbdu["BBRelatedData"]["MDUNumericalOffset"] = np.fromstring(fp.read(42 * 2),
                                                                dtype=">u2")
    bbdu["BBRelatedData"]["PUGain"] = np.fromstring(fp.read(42 * 2),
                                                    dtype=">u2")
    bbdu["BBRelatedData"]["PUOffset"] = np.fromstring(fp.read(27 * 2),
                                                      dtype=">u2")
    bbdu["BBRelatedData"]["PUBias"] = np.fromstring(fp.read(15 * 2),
                                                    dtype=">u2")
    # 12 bits bitstrings... convert to uint16
    data = np.fromstring(fp.read(int(42 * 1.5)),
                         dtype=np.uint8)
    data = data.astype(np.uint16)
    data[::3] = data[::3] * 256 + data[1::3] // 16
    data[1::3] = (data[1::3] & 0x0f) * 16 + data[2::3]
    result = np.ravel(data.reshape(-1, 3)[:, :2])
    bbdu["BBRelatedData"]["DCRValues"] = result
    bbdu["BBRelatedData"]["X_DeepSpaceWindowPosition"] = ord(fp.read(1))
    bbdu["BBRelatedData"]["ColdFPTemperature"] = {}
    bbdu["BBRelatedData"]["ColdFPTemperature"][
        "FCUNominalColdFocalPlaneTemp"] = rbin.read_uint2(fp.read(2)) / 100.
    bbdu["BBRelatedData"]["ColdFPTemperature"][
        "FCURedundantColdFocalPlaneTemp"] = rbin.read_uint2(fp.read(2)) / 100.
    bbdu["BBRelatedData"]["WarmFPTemperature"] = {}
    bbdu["BBRelatedData"]["WarmFPTemperature"][
        "FCUNominalWarmFocalPlaneVHROTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["WarmFPTemperature"][
        "FCURedundantWarmFocalPlaneVHROTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"] = {}
    bbdu["BBRelatedData"]["ScanMirrorTemperature"][
        "FCUNominalScanMirrorSensor1Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"][
        "FCURedundantScanMirrorSensor1Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"][
        "FCUNominalScanMirrorSensor2Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"][
        "FCURedundantScanMirrorSensor2Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"] = {}
    bbdu["BBRelatedData"]["M1M2M3Temperature"][
        "FCUNominalM1MirrorSensor1Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"][
        "FCURedundantM1MirrorSensor1Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"][
        "FCUNominalM1MirrorSensor2Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"][
        "FCURedundantM1MirrorSensor2Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"][
        "FCUNominalM23AssemblySensor1Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["M1M2M3Temperature"][
        "FCURedundantM23AssemblySensor1Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["M1M2M3Temperature"][
        "FCUNominalM23AssemblySensor2Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["M1M2M3Temperature"][
        "FCURedundantM23AssemblySensor2Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["BaffleTemperature"] = {}
    bbdu["BBRelatedData"]["BaffleTemperature"][
        "FCUNominalM1BaffleTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["BaffleTemperature"][
        "FCURedundantM1BaffleTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["BlackBodyTemperature"] = {}
    bbdu["BBRelatedData"]["BlackBodyTemperature"][
        "FCUNominalBlackBodySensorTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["BlackBodyTemperature"][
        "FCURedundantBlackBodySensorTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["FCUMode"] = {}
    bbdu["BBRelatedData"]["FCUMode"][
        "FCUNominalSMMStatus"] = rbin.read_uint2(fp.read(2))
    bbdu["BBRelatedData"]["FCUMode"][
        "FCURedundantSMMStatus"] = rbin.read_uint2(fp.read(2))
    extracted_data_type = np.dtype([('NumberOfPixelsUsed', '>u4'),
                                    ('MeanCount', '>f4'),
                                    ('RMS', '>f4'),
                                    ('MaxCount', '>u2'),
                                    ('MinCount', '>u2'),
                                    ('BB_Processing_Slope', '>f8'),
                                    ('BB_Processing_Offset', '>f8')])

    bbdu["BBRelatedData"]["ExtractedBBData"] = np.fromstring(fp.read(32 * 12),
                                                             dtype=extracted_data_type)
    impf_cal_type = np.dtype([("ImageQualityFlag", "u1"),
                              ("ReferenceDataFlag", "u1"),
                              ("AbsCalMethod", "u1"),
                              ("Pad1", "u1"),
                              ("AbsCalWeightVic", ">f4"),
                              ("AbsCalWeightXsat", ">f4"),
                              ("AbsCalCoeff", ">f4"),
                              ("AbsCalError", ">f4"),
                              ("CalMonBias", ">f4"),
                              ("CalMonRms", ">f4"),
                              ("OffsetCount", ">f4")])

    bbdu["MPEFCalFeedback"] = np.fromstring(fp.read(32 * 12),
                                            dtype=impf_cal_type)

    bbdu["RadTransform"] = np.fromstring(fp.read(42 * 64 * 4),
                                         dtype=">f4").reshape((42, 64))
    bbdu["RadProcMTFAdaptation"] = {}

    bbdu["RadProcMTFAdaptation"]["VIS_IRMTFCorrectionE_W"] = np.fromstring(fp.read(33 * 16 * 4),
                                                                           dtype=">f4").reshape((33, 16))
    bbdu["RadProcMTFAdaptation"]["VIS_IRMTFCorrectionN_S"] = np.fromstring(fp.read(33 * 16 * 4),
                                                                           dtype=">f4").reshape((33, 16))
    bbdu["RadProcMTFAdaptation"]["HRVMTFCorrectionE_W"] = np.fromstring(fp.read(9 * 16 * 4),
                                                                        dtype=">f4").reshape((9, 16))
    bbdu["RadProcMTFAdaptation"]["HRVMTFCorrectionN_S"] = np.fromstring(fp.read(9 * 16 * 4),
                                                                        dtype=">f4").reshape((9, 16))
    bbdu["RadProcMTFAdaptation"]["StraylightCorrection"] = np.fromstring(fp.read(12 * 8 * 8 * 4),
                                                                         dtype=">f4").reshape((12, 8, 8))

    hdr["BlackBodyDataUsed"] = bbdu

    # GeometricProcessing

    geoproc = {}
    geoproc["OptAxisDistances"] = {}
    geoproc["OptAxisDistances"]["E-WFocalPlane"] = np.fromstring(fp.read(42 * 4),
                                                                 dtype=">f4")
    geoproc["OptAxisDistances"]["N-SFocalPlane"] = np.fromstring(fp.read(42 * 4),
                                                                 dtype=">f4")

    geoproc["EarthModel"] = {}
    geoproc["EarthModel"]["TypeOfEarthModel"] = ord(fp.read(1))
    geoproc["EarthModel"]["EquatorialRadius"] = rbin.read_float8(fp.read(8))
    geoproc["EarthModel"]["NorthPolarRadius"] = rbin.read_float8(fp.read(8))
    geoproc["EarthModel"]["SouthPolarRadius"] = rbin.read_float8(fp.read(8))
    geoproc["AtmosphericModel"] = np.fromstring(fp.read(12 * 360 * 4),
                                                dtype=">f4").reshape((12, 360))
    geoproc["ResamplingFunctions"] = np.fromstring(fp.read(12),
                                                   dtype=np.uint8)

    hdr["GeometricProcessing"] = geoproc

    return hdr


def read_epiheader(fp):
    """Read the msg header.
    """
    epilogue = dict()
    epilogue["15TRAILERVersion"] = ord(fp.read(1))
    epilogue["SateliteID"] = rbin.read_uint2(fp.read(2))
    epilogue["NominalImageScanning"] = ord(fp.read(1)) > 0
    epilogue["ReducedScan"] = ord(fp.read(1)) > 0
    epilogue["ForwardScanStart"] = rbin.read_cds_time(fp.read(6))
    epilogue["ForwardScanEnd"] = rbin.read_cds_time(fp.read(6))
    epilogue["NominalBehaviour"] = ord(fp.read(1)) > 0
    epilogue["RadScanIrregularity"] = ord(fp.read(1)) > 0
    epilogue["RadStoppage"] = ord(fp.read(1)) > 0
    epilogue["RepeatCycleNotCompleted"] = ord(fp.read(1)) > 0
    epilogue["GainChangeTookPlace"] = ord(fp.read(1)) > 0
    epilogue["DecontaminationTookPlace"] = ord(fp.read(1)) > 0
    epilogue["NoBBCalibrationAchieved"] = ord(fp.read(1)) > 0
    epilogue["IncorrectTemperature"] = ord(fp.read(1)) > 0
    epilogue["InvalidBBData"] = ord(fp.read(1)) > 0
    epilogue["InvalidAuxOrHKTMData"] = ord(fp.read(1)) > 0
    epilogue["RefocusingMechanismActuated"] = ord(fp.read(1)) > 0
    epilogue["MirrorBackToReferencePos"] = ord(fp.read(1)) > 0
    epilogue["PlannedNumberOfL10Lines"] = np.fromstring(fp.read(12 * 4),
                                                        dtype=">u4")
    epilogue["NumberOfMissingL10Lines"] = np.fromstring(fp.read(12 * 4),
                                                        dtype=">u4")
    epilogue["NumberOfCorruptedL10Lines"] = np.fromstring(fp.read(12 * 4),
                                                          dtype=">u4")
    epilogue["NumberOfReplacedL10Lines"] = np.fromstring(fp.read(12 * 4),
                                                         dtype=">u4")
    validitytype = np.dtype([('NominalImage', '>u1'),
                             ('NonNominalBecauseIncomplete', '>u1'),
                             ('NonNominalRadiometricQuality', '>u1'),
                             ('NonNominalGeometricQuality', '>u1'),
                             ('NonNominalTimeliness', '>u1'),
                             ('IncompleteL15', '>u1')])
    epilogue["L15ImageValidity"] = np.fromstring(fp.read(12 * 6),
                                                 dtype=validitytype)

    epilogue["SouthernLineActual"] = rbin.read_int4(fp.read(4))
    epilogue["NorthernLineActual"] = rbin.read_int4(fp.read(4))
    epilogue["EasternColumnActual"] = rbin.read_int4(fp.read(4))
    epilogue["WesternColumnActual"] = rbin.read_int4(fp.read(4))
    epilogue["LowerSouthLineActual"] = rbin.read_int4(fp.read(4))
    epilogue["LowerNorthLineActual"] = rbin.read_int4(fp.read(4))
    epilogue["LowerEastColumnActual"] = rbin.read_int4(fp.read(4))
    epilogue["LowerWestColumnActual"] = rbin.read_int4(fp.read(4))
    epilogue["UpperSouthLineActual"] = rbin.read_int4(fp.read(4))
    epilogue["UpperNorthLineActual"] = rbin.read_int4(fp.read(4))
    epilogue["UpperEastColumnActual"] = rbin.read_int4(fp.read(4))
    epilogue["UpperWestColumnActual"] = rbin.read_int4(fp.read(4))

    return epilogue


def decompress(infiles, **options):
    """Check if the files are xrit-compressed, and decompress them
    accordingly:
    """
    if 'outdir' in options:
        cmd = options['outdir']
    else:
        cmd = os.environ.get('XRIT_DECOMPRESS_OUTDIR', None)

    if not cmd:
        LOG.info("XRIT_DECOMPRESS_OUTDIR is not defined. " +
                 "The decompressed files will be put in " +
                 "the same directory as compressed ones")

    decomp_files = []
    for filename in infiles:
        if filename.endswith('C_'):
            # Try decompress it:
            LOG.debug('Try decompressing ' + filename)
            if cmd:
                outdir = cmd
            else:
                outdir = os.path.dirname(filename)
            outfile = _xrit.decompress(filename, outdir)
            decomp_files.append(outfile)
        else:
            decomp_files.append(filename)

    return decomp_files


if __name__ == '__main__':
    import sys
    from glob import glob

    files = sys.argv[1:]
    files = (glob('/home/a000680/data/hrit/*IR_108*000008___-201504211100*') +
             glob('/home/a000680/data/hrit/*EPI*201504211100*') +
             glob('/home/a000680/data/hrit/*PRO*201504211100*'))
    this = MSGHRITLoader(channels=['HRV'], files=files)
    mda, img = this.load(calibrate=0)
    #mda, img = this.load(area_extent=[1000, 2000, 1200, 2200], calibrate=0)
