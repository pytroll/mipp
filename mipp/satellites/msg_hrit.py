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
"""

from mipp.xrit import _xrit
from mipp.xrit import bin_reader as rbin
from mipp.generic_loader import GenericLoader
from mipp.metadata import Metadata
import os.path
from StringIO import StringIO
import numpy as np
import logging
logger = logging.getLogger(__name__)

NO_DATA_VALUE = 0


SATNUM = {321: "08",
          322: "09",
          323: "10",
          324: "11"}


class MSGHRITLoader(GenericLoader):

    """Loader for MSG data"""

    def __init__(self, satid, timeslot=None, files=None):

        self.image_filenames = []
        self.prologue_filename = None
        self.epilogue_filename = None

        super(MSGHRITLoader, self).__init__(
            satid, timeslot=timeslot, files=files)

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
        prologue = read_proheader(fp)

        fp = StringIO(epilogue.data)
        epilogue = read_epiheader(fp)

        im = _xrit.read_imagedata(self.image_filenames[0])

        md = Metadata()
        #md.calibrate = _Calibrator(prologue, im.product_name)

        md.projection = im.navigation.proj_name.lower()
        md.sublon = prologue["ProjectionDescription"]["LongitudeOfSSP"]
        md.proj4_str = "proj=geos lon_0=%.2f lat_0=0.00 a=6378169.00 b=6356583.80 h=35785831.00" % md.sublon
        md.product_name = im.product_id
        md.channel_id = im.product_name
        if md.channel_id == "HRV":
            md.number_of_columns = prologue[
                "ReferenceGridHRV"]["NumberOfColumns"]
            md.number_of_lines = prologue["ReferenceGridHRV"]["NumberOfLines"]
        else:
            md.number_of_columns = prologue[
                "ReferenceGridVIS_IR"]["NumberOfColumns"]
            md.number_of_lines = prologue[
                "ReferenceGridVIS_IR"]["NumberOfLines"]

        md.image_size = np.array((md.number_of_columns,
                                  md.number_of_lines))

        md.satname = im.platform.lower()
        md.satnumber = SATNUM[prologue["SatelliteDefinition"]["SatelliteId"]]
        logger.debug("%s %s", md.satname, md.satnumber)
        md.product_type = 'full disc'
        md.region_name = 'full disc'
        if md.channel_id == "HRV":
            md.first_pixel = prologue["ReferenceGridHRV"]["GridOrigin"]
            dummy, ew_ = md.first_pixel.split()
            md.boundaries = np.array([[
                epilogue["LowerSouthLineActual"],
                epilogue["LowerNorthLineActual"],
                epilogue["LowerEastColumnActual"],
                epilogue["LowerWestColumnActual"]],
                [epilogue["UpperSouthLineActual"],
                 epilogue["UpperNorthLineActual"],
                 epilogue["UpperEastColumnActual"],
                 epilogue["UpperWestColumnActual"]]])

            md.coff = (epilogue["Lower" + ew_.capitalize() + "ColumnActual"]
                       + im.navigation.coff - 1)
            md.loff = im.navigation.loff + \
                segment_size * (im.segment.seg_no - 1)

        else:
            md.first_pixel = prologue["ReferenceGridVIS_IR"]["GridOrigin"]
            dummy, ew_ = md.first_pixel.split()
            md.boundaries = np.array([[
                epilogue["SouthernLineActual"],
                epilogue["NorthernLineActual"],
                epilogue["EasternColumnActual"],
                epilogue["WesternColumnActual"]]])

            md.coff = im.navigation.coff
            md.loff = im.navigation.loff + \
                segment_size * (im.segment.seg_no - 1)

        md.data_type = im.structure.nb
        md.no_data_value = NO_DATA_VALUE
        md.line_offset = 0
        md.time_stamp = im.time_stamp
        md.production_time = im.production_time
        md.calibration_unit = ""

        return md

    def load(self, channels, area_extent=None, calibrate='1'):
        """Load the data"""

        if len(channels) != 1:
            raise IOError(
                'Data loading requires one channel only at the moment!')


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


if __name__ == '__main__':
    import sys

    files = sys.argv[1:]
    this = MSGHRITLoader('meteosat10', files=files)
