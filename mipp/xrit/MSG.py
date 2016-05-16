#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2010, 2011, 2012, 2013, 2014

# Author(s):

#   Martin Raspaud <martin.raspaud@smhi.se>
#   Lars Ø. Rasmusen <ras@dmi.dk>
#   Esben S. Nielsen <esn@dmi.dk>

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

"""This module will read MSG level1.5 files, format documented in: 
'MSG Level 1.5 Image Data Format Description', EUM/MSG/ICD/105, v5A, 22 August 2007
"""
#raise NotImplementedError
import logging
logger = logging.getLogger(__name__)

import sys
import numpy as np
from StringIO import StringIO

from mipp import CalibrationError
from mipp.xrit import _xrit
from mipp.xrit import Metadata
from mipp.xrit import bin_reader as rbin

__all__ = ['read_metadata']

eval_np = eval
log = np.log
no_data_value = 0

if sys.version_info[0] >= 2 and sys.version_info[1] >= 5:
    try:
        # Use numexpr if available
        import numexpr
        eval_np = numexpr.evaluate
        logger.info('Using numexpr for fast numpy evaluation')
    except ImportError:
        logger.warning('Module numexpr not found. Performance will be slower.')
else:
    logger.warning('Older version of python. Module numexpr not used. '
                   'Performance will be slower.')


# Reflectance factor for visible bands
HRV_F = 25.15
VIS006_F = 20.76
VIS008_F = 23.30
IR_016_F = 19.73

SATNUM = {321: "08",
          322: "09",
          323: "10",
          324: "11"}

# Calibration coefficients from
# 'A Planned Change to the MSG Level 1.5 Image Product Radiance Definition',
# "Conversion from radiances to reflectances for SEVIRI warm channels"
# EUM/MET/TEN/12/0332 , and "The Conversion from Effective Radiances to
# Equivalent Brightness Temperatures" EUM/MET/TEN/11/0569

CALIB = {}


# Meteosat 8

CALIB[321] = {'HRV': {'F': 78.7599 / np.pi},
              'VIS006': {'F': 65.2296 / np.pi},
              'VIS008': {'F': 73.0127 / np.pi},
              'IR_016': {'F': 62.3715 / np.pi},
              'IR_039': {'VC': 2567.33,
                         'ALPHA': 0.9956,
                         'BETA': 3.41},
              'WV_062': {'VC': 1598.103,
                         'ALPHA': 0.9962,
                         'BETA': 2.218},
              'WV_073': {'VC': 1362.081,
                         'ALPHA': 0.9991,
                         'BETA': 0.478},
              'IR_087': {'VC': 1149.069,
                         'ALPHA': 0.9996,
                         'BETA': 0.179},
              'IR_097': {'VC': 1034.343,
                         'ALPHA': 0.9999,
                         'BETA': 0.06},
              'IR_108': {'VC': 930.647,
                         'ALPHA': 0.9983,
                         'BETA': 0.625},
              'IR_120': {'VC': 839.66,
                         'ALPHA': 0.9988,
                         'BETA': 0.397},
              'IR_134': {'VC': 752.387,
                         'ALPHA': 0.9981,
                         'BETA': 0.578}}

# Meteosat 9

CALIB[322] = {'HRV': {'F': 79.0113 / np.pi},
              'VIS006': {'F': 65.2065 / np.pi},
              'VIS008': {'F': 73.1869 / np.pi},
              'IR_016': {'F': 61.9923 / np.pi},
              'IR_039': {'VC': 2568.832,
                         'ALPHA': 0.9954,
                         'BETA': 3.438},
              'WV_062': {'VC': 1600.548,
                         'ALPHA': 0.9963,
                         'BETA': 2.185},
              'WV_073': {'VC': 1360.330,
                         'ALPHA': 0.9991,
                         'BETA': 0.47},
              'IR_087': {'VC': 1148.620,
                         'ALPHA': 0.9996,
                         'BETA': 0.179},
              'IR_097': {'VC': 1035.289,
                         'ALPHA': 0.9999,
                         'BETA': 0.056},
              'IR_108': {'VC': 931.7,
                         'ALPHA': 0.9983,
                         'BETA': 0.64},
              'IR_120': {'VC': 836.445,
                         'ALPHA': 0.9988,
                         'BETA': 0.408},
              'IR_134': {'VC': 751.792,
                         'ALPHA': 0.9981,
                         'BETA': 0.561}}

# Meteosat 10

CALIB[323] = {'HRV': {'F': 78.9416 / np.pi},
              'VIS006': {'F': 65.5148 / np.pi},
              'VIS008': {'F': 73.1807 / np.pi},
              'IR_016': {'F': 62.0208 / np.pi},
              'IR_039': {'VC': 2547.771,
                         'ALPHA': 0.9915,
                         'BETA': 2.9002},
              'WV_062': {'VC': 1595.621,
                         'ALPHA': 0.9960,
                         'BETA': 2.0337},
              'WV_073': {'VC': 1360.337,
                         'ALPHA': 0.9991,
                         'BETA': 0.4340},
              'IR_087': {'VC': 1148.130,
                         'ALPHA': 0.9996,
                         'BETA': 0.1714},
              'IR_097': {'VC': 1034.715,
                         'ALPHA': 0.9999,
                         'BETA': 0.0527},
              'IR_108': {'VC': 929.842,
                         'ALPHA': 0.9983,
                         'BETA': 0.6084},
              'IR_120': {'VC': 838.659,
                         'ALPHA': 0.9988,
                         'BETA': 0.3882},
              'IR_134': {'VC': 750.653,
                         'ALPHA': 0.9982,
                         'BETA': 0.5390}}

# Meteosat 11

CALIB[324] = {'HRV': {'F': 79.0035 / np.pi},
              'VIS006': {'F': 65.2656 / np.pi},
              'VIS008': {'F': 73.1692 / np.pi},
              'IR_016': {'F': 61.9416 / np.pi},
              'IR_039': {'VC': 2555.280,
                         'ALPHA': 0.9916,
                         'BETA': 2.9438},
              'WV_062': {'VC': 1596.080,
                         'ALPHA': 0.9959,
                         'BETA': 2.0780},
              'WV_073': {'VC': 1361.748,
                         'ALPHA': 0.9990,
                         'BETA': 0.4929},
              'IR_087': {'VC': 1147.433,
                         'ALPHA': 0.9996,
                         'BETA': 0.1731},
              'IR_097': {'VC': 1034.851,
                         'ALPHA': 0.9998,
                         'BETA': 0.0597},
              'IR_108': {'VC': 931.122,
                         'ALPHA': 0.9983,
                         'BETA': 0.6256},
              'IR_120': {'VC': 839.113,
                         'ALPHA': 0.9988,
                         'BETA': 0.4002},
              'IR_134': {'VC': 748.585,
                         'ALPHA': 0.9981,
                         'BETA': 0.5635}}

# Polynomial coefficients for spectral-effective BT fits
BTFIT_A_IR_039 = 0.0
BTFIT_A_WV_062 = 0.00001805700
BTFIT_A_WV_073 = 0.00000231818
BTFIT_A_IR_087 = -0.00002332000
BTFIT_A_IR_097 = -0.00002055330
BTFIT_A_IR_108 = -0.00007392770
BTFIT_A_IR_120 = -0.00007009840
BTFIT_A_IR_134 = -0.00007293450

BTFIT_B_IR_039 = 1.011751900
BTFIT_B_WV_062 = 1.000255533
BTFIT_B_WV_073 = 1.000668281
BTFIT_B_IR_087 = 1.011803400
BTFIT_B_IR_097 = 1.009370670
BTFIT_B_IR_108 = 1.032889800
BTFIT_B_IR_120 = 1.031314600
BTFIT_B_IR_134 = 1.030424800

BTFIT_C_IR_039 = -3.550400
BTFIT_C_WV_062 = -1.790930
BTFIT_C_WV_073 = -0.456166
BTFIT_C_IR_087 = -1.507390
BTFIT_C_IR_097 = -1.030600
BTFIT_C_IR_108 = -3.296740
BTFIT_C_IR_120 = -3.181090
BTFIT_C_IR_134 = -2.645950


C1 = 1.19104273e-16
C2 = 0.0143877523


class _Calibrator(object):

    def __init__(self, hdr, channel_name, bits_per_pixel):
        self.hdr = hdr
        self.channel_name = channel_name
        self.bits_per_pixel = bits_per_pixel

    def __call__(self, image, calibrate=1):
        """Computes the radiances and reflectances/bt of a given channel.  The
        *calibrate* argument should be set to 0 for no calibration, 1 for
        default reflectances/bt calibration, and 2 for returning radiances. The
        default value is 1.
        """
        hdr = self.hdr

        channel_name = self.channel_name

        if calibrate == 0:
            return (image,
                    "counts")

        channels = {"VIS006": 1,
                    "VIS008": 2,
                    "IR_016": 3,
                    "IR_039": 4,
                    "WV_062": 5,
                    "WV_073": 6,
                    "IR_087": 7,
                    "IR_097": 8,
                    "IR_108": 9,
                    "IR_120": 10,
                    "IR_134": 11,
                    "HRV": 12}

        cal_type = (hdr["Level 1_5 ImageProduction"]["PlannedChanProcessing"])
        chn_nb = channels[channel_name] - 1

        mask = (image == no_data_value)
        if self.bits_per_pixel == 8:
            logger.info("8 bits per pixel adjusted to 10 bits for calibration.")
            image = image.astype(np.uint16) * 4

        cslope = hdr["Level1_5ImageCalibration"][chn_nb]['Cal_Slope']
        coffset = hdr["Level1_5ImageCalibration"][chn_nb]['Cal_Offset']

        radiances = eval_np('image * cslope + coffset')
        radiances[radiances < 0] = 0

        if calibrate == 2:
            return (np.ma.MaskedArray(radiances, mask=mask),
                    "mW m-2 sr-1 (cm-1)-1")

        sat = hdr["SatelliteDefinition"]["SatelliteId"]
        if sat not in CALIB:
            raise CalibrationError("No calibration coefficients available for "
                                   + "this satellite (" + str(sat) + ")")

        if channel_name in ["HRV", "VIS006", "VIS008", "IR_016"]:
            solar_irradiance = CALIB[sat][channel_name]["F"]
            reflectance = eval_np('(radiances / solar_irradiance) * 100.')
            return (np.ma.MaskedArray(reflectance, mask=mask),
                    "%")

        wavenumber = CALIB[sat][channel_name]["VC"]
        if cal_type[chn_nb] == 2:
            # computation based on effective radiance
            alpha = CALIB[sat][channel_name]["ALPHA"]
            beta = CALIB[sat][channel_name]["BETA"]

            cal_data = eval_np(('((C2 * 100. * wavenumber / '
                                'log(C1 * 1.0e6 * wavenumber ** 3 / '
                                '(1.0e-5 * radiances) + 1)) - beta) / alpha'))

        elif cal_type[chn_nb] == 1:
            # computation based on spectral radiance
            cal_data = eval_np(('C2 * 100. * wavenumber / '
                                'log(C1 * 1.0e6 * wavenumber ** 3 / '
                                '(1.0e-5 * radiances) + 1)'))
            
            coef_a = eval("BTFIT_A_" + channel_name)
            coef_b = eval("BTFIT_B_" + channel_name)
            coef_c = eval("BTFIT_C_" + channel_name)

            cal_data = eval_np(('cal_data ** 2 * coef_a + '
                                'cal_data * coef_b + coef_c'))

        else:
            raise RuntimeError("Something is seriously wrong in the metadata.")

        mask = mask | np.isnan(cal_data) | np.isinf(cal_data)
        cal_data = np.ma.MaskedArray(cal_data, mask=mask)
        return (cal_data,
                "K")


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
    radiosettings["MDUSamplingDelays"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["HRVFrameOffsets"] = {}
    radiosettings["HRVFrameOffsets"]["MDUNomHRVDelay1"] = rbin.read_uint2(fp.read(2))
    radiosettings["HRVFrameOffsets"]["MDUNomHRVDelay2"] = rbin.read_uint2(fp.read(2))
    radiosettings["HRVFrameOffsets"]["Spare"] = rbin.read_uint2(fp.read(2))
    radiosettings["HRVFrameOffsets"]["MDUNomHRVBreakline"] = rbin.read_uint2(fp.read(2))
    radiosettings["DHSSSynchSelection"] = ord(fp.read(1))
    radiosettings["MDUOutGain"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["MDUCourseGain"] = np.fromstring(fp.read(42), dtype=np.uint8)
    radiosettings["MDUFineGain"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["MDUNumericalOffset"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["PUGain"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["PUOffset"] = np.fromstring(fp.read(27 * 2), dtype=">u2")
    radiosettings["PUBias"] = np.fromstring(fp.read(15 * 2), dtype=">u2")
    radiosettings["OperationParameters"] = {}
    radiosettings["OperationParameters"]["L0_LineCounter"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["K1_RetraceLines"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["K2_PauseDeciseconds"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["K3_RetraceLines"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["K4_PauseDeciseconds"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["K5_RetraceLines"] = rbin.read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["X_DeepSpaceWindowPosition"] = ord(fp.read(1))
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
    radiooper["Decontamination"]["DecontaminationStart"] = rbin.read_cds_time(fp.read(6))
    radiooper["Decontamination"]["DecontaminationEnd"] = rbin.read_cds_time(fp.read(6))

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
    rpsummary["RadianceLinearization"] = np.fromstring(fp.read(12), dtype=np.bool)

    rpsummary["DetectorEqualization"] = np.fromstring(fp.read(12), dtype=np.bool)
    rpsummary["OnboardCalibrationResult"] = np.fromstring(fp.read(12), dtype=np.bool)
    rpsummary["MPEFCalFeedback"] = np.fromstring(fp.read(12), dtype=np.bool)
    rpsummary["MTFAdaptation"] = np.fromstring(fp.read(12), dtype=np.bool)
    rpsummary["StraylightCorrectionFlag"] = np.fromstring(fp.read(12), dtype=np.bool)

    hdr["RPSummary"] = rpsummary

    # Level1_5ImageCalibration

    caltype = np.dtype([('Cal_Slope', '>f8'), ('Cal_Offset', '>f8')])

    hdr["Level1_5ImageCalibration"] = np.fromstring(fp.read(192), dtype=caltype)

    # BlackBodyDataUsed

    bbdu = {}

    bbdu["BBObservationUTC"] = rbin.read_cds_expanded_time(fp.read(10))
    bbdu["BBRelatedData"] = {}
    bbdu["BBRelatedData"]["OnBoardBBTime"] = rbin.read_cuc_time(fp.read(7), 4, 3)
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
    bbdu["BBRelatedData"]["ColdFPTemperature"]["FCUNominalColdFocalPlaneTemp"] = rbin.read_uint2(fp.read(2)) / 100.
    bbdu["BBRelatedData"]["ColdFPTemperature"]["FCURedundantColdFocalPlaneTemp"] = rbin.read_uint2(fp.read(2)) / 100.
    bbdu["BBRelatedData"]["WarmFPTemperature"] = {}
    bbdu["BBRelatedData"]["WarmFPTemperature"]["FCUNominalWarmFocalPlaneVHROTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["WarmFPTemperature"]["FCURedundantWarmFocalPlaneVHROTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"] = {}
    bbdu["BBRelatedData"]["ScanMirrorTemperature"]["FCUNominalScanMirrorSensor1Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"]["FCURedundantScanMirrorSensor1Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"]["FCUNominalScanMirrorSensor2Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"]["FCURedundantScanMirrorSensor2Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"] = {}
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCUNominalM1MirrorSensor1Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCURedundantM1MirrorSensor1Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCUNominalM1MirrorSensor2Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCURedundantM1MirrorSensor2Temp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCUNominalM23AssemblySensor1Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCURedundantM23AssemblySensor1Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCUNominalM23AssemblySensor2Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCURedundantM23AssemblySensor2Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["BaffleTemperature"] = {}
    bbdu["BBRelatedData"]["BaffleTemperature"]["FCUNominalM1BaffleTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["BaffleTemperature"]["FCURedundantM1BaffleTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["BlackBodyTemperature"] = {}
    bbdu["BBRelatedData"]["BlackBodyTemperature"]["FCUNominalBlackBodySensorTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["BlackBodyTemperature"]["FCURedundantBlackBodySensorTemp"] = rbin.read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["FCUMode"] = {}
    bbdu["BBRelatedData"]["FCUMode"]["FCUNominalSMMStatus"] = rbin.read_uint2(fp.read(2))
    bbdu["BBRelatedData"]["FCUMode"]["FCURedundantSMMStatus"] = rbin.read_uint2(fp.read(2))
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
                              ("GSICSCalCoeff", ">f4"),
                              ("GSICSCalError", ">f4"),
                              ("GSICSOffsetCount", ">f4")])

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
    ftr = dict()
    ftr["15TRAILERVersion"] = ord(fp.read(1))
    ftr["SateliteID"] = rbin.read_uint2(fp.read(2))
    ftr["NominalImageScanning"] = ord(fp.read(1)) > 0
    ftr["ReducedScan"] = ord(fp.read(1)) > 0
    ftr["ForwardScanStart"] = rbin.read_cds_time(fp.read(6))
    ftr["ForwardScanEnd"] = rbin.read_cds_time(fp.read(6))
    ftr["NominalBehaviour"] = ord(fp.read(1)) > 0
    ftr["RadScanIrregularity"] = ord(fp.read(1)) > 0
    ftr["RadStoppage"] = ord(fp.read(1)) > 0
    ftr["RepeatCycleNotCompleted"] = ord(fp.read(1)) > 0
    ftr["GainChangeTookPlace"] = ord(fp.read(1)) > 0
    ftr["DecontaminationTookPlace"] = ord(fp.read(1)) > 0
    ftr["NoBBCalibrationAchieved"] = ord(fp.read(1)) > 0
    ftr["IncorrectTemperature"] = ord(fp.read(1)) > 0
    ftr["InvalidBBData"] = ord(fp.read(1)) > 0
    ftr["InvalidAuxOrHKTMData"] = ord(fp.read(1)) > 0
    ftr["RefocusingMechanismActuated"] = ord(fp.read(1)) > 0
    ftr["MirrorBackToReferencePos"] = ord(fp.read(1)) > 0
    ftr["PlannedNumberOfL10Lines"] = np.fromstring(fp.read(12 * 4),
                                                   dtype=">u4")
    ftr["NumberOfMissingL10Lines"] = np.fromstring(fp.read(12 * 4),
                                                   dtype=">u4")
    ftr["NumberOfCorruptedL10Lines"] = np.fromstring(fp.read(12 * 4),
                                                     dtype=">u4")
    ftr["NumberOfReplacedL10Lines"] = np.fromstring(fp.read(12 * 4),
                                                    dtype=">u4")
    validitytype = np.dtype([('NominalImage', '>u1'),
                             ('NonNominalBecauseIncomplete', '>u1'),
                             ('NonNominalRadiometricQuality', '>u1'),
                             ('NonNominalGeometricQuality', '>u1'),
                             ('NonNominalTimeliness', '>u1'),
                             ('IncompleteL15', '>u1')])
    ftr["L15ImageValidity"] = np.fromstring(fp.read(12 * 6),
                                            dtype=validitytype)

    ftr["SouthernLineActual"] = rbin.read_int4(fp.read(4))
    ftr["NorthernLineActual"] = rbin.read_int4(fp.read(4))
    ftr["EasternColumnActual"] = rbin.read_int4(fp.read(4))
    ftr["WesternColumnActual"] = rbin.read_int4(fp.read(4))
    ftr["LowerSouthLineActual"] = rbin.read_int4(fp.read(4))
    ftr["LowerNorthLineActual"] = rbin.read_int4(fp.read(4))
    ftr["LowerEastColumnActual"] = rbin.read_int4(fp.read(4))
    ftr["LowerWestColumnActual"] = rbin.read_int4(fp.read(4))
    ftr["UpperSouthLineActual"] = rbin.read_int4(fp.read(4))
    ftr["UpperNorthLineActual"] = rbin.read_int4(fp.read(4))
    ftr["UpperEastColumnActual"] = rbin.read_int4(fp.read(4))
    ftr["UpperWestColumnActual"] = rbin.read_int4(fp.read(4))

    return ftr


def read_metadata(prologue, image_files, epilogue):
    """ Selected items from the MSG prologue file.
    """
    segment_size = 464  # number of lines in a segment

    fp = StringIO(prologue.data)
    hdr = read_proheader(fp)

    fp = StringIO(epilogue.data)
    ftr = read_epiheader(fp)

    im = _xrit.read_imagedata(image_files[0])

    md = Metadata()
    md.calibrate = _Calibrator(hdr, im.product_name, bits_per_pixel=im.structure.nb)

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
                   + im.navigation.coff + 1)
        md.loff = im.navigation.loff + segment_size * (im.segment.seg_no - 1) + 2

    else:
        md.first_pixel = hdr["ReferenceGridVIS_IR"]["GridOrigin"]
        ns_, ew_ = md.first_pixel.split()
        md.boundaries = np.array([[
            ftr["SouthernLineActual"],
            ftr["NorthernLineActual"],
            ftr["EasternColumnActual"],
            ftr["WesternColumnActual"]]])

        md.coff = im.navigation.coff
        md.loff = im.navigation.loff + segment_size * (im.segment.seg_no - 1)

    md.data_type = im.structure.nb
    md.no_data_value = no_data_value
    md.line_offset = 0
    md.time_stamp = im.time_stamp
    md.production_time = im.production_time
    md.calibration_unit = ""

    return md


def read_obstimes(epilogue):
    """Get the start and end full disk scan times from the Epilogue file."""
    epi = _xrit.read_epilogue(epilogue)
    fpt = StringIO(epi.data)
    ftr = read_epiheader(fpt)
    return (ftr['ForwardScanStart'], ftr['ForwardScanEnd'])


def read_scanline_quality(segment_filename):
    """Get the line quality data from the segment file. This is from the
    ImageSegmentLineQuality class of the _xrit module, which maps the Header
    Type 129 - Image Segment Line Quality as decribed in the 'MSG Ground
    Segment LRIT/HRIT Mission Specific Implementation, EUM/MSG/SPE/057'
    document, see reference below.

    This record contains the scan line mean acquisition times

    http://www.eumetsat.int/website/wcm/idc/idcplg?IdcService=GET_FILE&dDocName=PDF_TEN_05057_SPE_MSG_LRIT_HRI&RevisionSelectionMethod=LatestReleased&Rendition=Web

    """
    imgdata = _xrit.read_imagedata(segment_filename)
    return imgdata.image_quality.line_quality


if __name__ == '__main__':
    p = _xrit.read_prologue(sys.argv[1])
    e = _xrit.read_epilogue(sys.argv[-1])
    print read_metadata(p, sys.argv[2:-1], e)
