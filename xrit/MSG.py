#
# $Id$
#
"""This module will read MSG level1.5 files, format documented in: 
'MSG Level 1.5 Image Data Format Description', EUM/MSG/ICD/105, v5A, 22 August 2007
"""
#raise NotImplementedError
import xrit
import xrit.mda
import sys
from StringIO import StringIO
from xrit.bin_reader import *
import numpy as np

#Reflectance factor for visible bands
HRV_F    = 25.15
VIS006_F = 20.76
VIS008_F = 23.30
IR_016_F = 19.73

#Central wavenumber (in cm-1) values for conversion between radiances to bt
VC_IR_039 = 2568.832
VC_WV_062 = 1600.548
VC_WV_073 = 1360.330
VC_IR_087 = 1148.620
VC_IR_097 = 1035.289
VC_IR_108 =  931.700
VC_IR_120 =  836.445
VC_IR_134 =  751.792

#ALPHA values for conversion between radiances to bt
ALPHA_IR_039 = 0.9954  
ALPHA_WV_062 = 0.9963
ALPHA_WV_073 = 0.9991
ALPHA_IR_087 = 0.9996
ALPHA_IR_097 = 0.9999
ALPHA_IR_108 = 0.9983
ALPHA_IR_120 = 0.9988
ALPHA_IR_134 = 0.9981

#BETA values for conversion between radiances to bt
BETA_IR_039 = 3.438
BETA_WV_062 = 2.185
BETA_WV_073 = 0.470
BETA_IR_087 = 0.179
BETA_IR_097 = 0.056
BETA_IR_108 = 0.640
BETA_IR_120 = 0.408
BETA_IR_134 = 0.561

#Polynomial coefficients for spectral-effective BT fits
BTFIT_A_IR_039 =  0.0
BTFIT_A_WV_062 =  0.00001805700
BTFIT_A_WV_073 =  0.00000231818
BTFIT_A_IR_087 = -0.00002332000
BTFIT_A_IR_097 = -0.00002055330 
BTFIT_A_IR_108 = -0.00007392770
BTFIT_A_IR_120 = -0.00007009840
BTFIT_A_IR_134 = -0.00007293450

BTFIT_B_IR_039 =  1.011751900
BTFIT_B_WV_062 =  1.000255533 
BTFIT_B_WV_073 =  1.000668281
BTFIT_B_IR_087 =  1.011803400
BTFIT_B_IR_097 =  1.009370670  
BTFIT_B_IR_108 =  1.032889800 
BTFIT_B_IR_120 =  1.031314600
BTFIT_B_IR_134 =  1.030424800

BTFIT_C_IR_039 =  -3.550400
BTFIT_C_WV_062 =  -1.790930
BTFIT_C_WV_073 =  -0.456166
BTFIT_C_IR_087 =  -1.507390
BTFIT_C_IR_097 =  -1.030600
BTFIT_C_IR_108 =  -3.296740
BTFIT_C_IR_120 =  -3.181090
BTFIT_C_IR_134 =  -2.645950


C1 = 1.19104273e-16
C2 = 0.0143877523


class _Calibrator:
    def __init__(self, hdr, md):
        self.hdr = hdr
        self.md = md
        
    def __call__(self, image, calibrate=1):
        """Computes the radiances and reflectances/bt of a given channel.
        """
        hdr = self.hdr
        
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
        chn_nb = channels[self.md.channel] - 1

        img = np.ma.MaskedArray(image,
                                mask=(image == self.md.no_data_value))

        radiances = (img *
                     hdr["Level1_5ImageCalibration"][chn_nb]['Cal_Slope'] +
                     hdr["Level1_5ImageCalibration"][chn_nb]['Cal_Offset'])
        radiances = np.where(radiances < 0.0, 0.0, radiances)

        if self.md.channel in ["HRV", "VIS006", "VIS008", "IR_016"]:
            solar_irradiance = eval(self.md.channel + "_F")
            return radiances / solar_irradiance * 100.

        wavenumber = eval("VC_" + self.md.channel)
        if cal_type[chn_nb] == 2:
            #computation based on effective radiance
            alpha = eval("ALPHA_" + self.md.channel)
            beta = eval("BETA_" + self.md.channel)
            cal_data = (((C2 * 100. * wavenumber /
                          np.log(C1 * 1.0e6 * wavenumber ** 3 /
                                 (1.0e-5 * radiances) + 1)) -
                         beta) / alpha)
            
        elif cal_type[chn_nb] == 1:
            #computation based on spectral radiance
            cal_data = (C2 * 100. * wavenumber /
                        np.log(C1 * 1.0e6 * wavenumber ** 3 /
                               (1.0e-5 * radiances) + 1))
            coef_a = eval("BTFIT_A_" + self.md.channel)
            coef_b = eval("BTFIT_B_" + self.md.channel)
            coef_c = eval("BTFIT_C_" + self.md.channel)
            cal_data = cal_data ** 2 * coef_a + cal_data * coef_b + coef_c

        else:
            raise RuntimeError("Something is seriously wrong in the metadata.")

        return cal_data

def read_proheader(fp):
    """Read the msg header.
    """
    hdr = dict()

    # Satellite definition

    satdef = {}
    satdef["SatelliteId"] = read_uint2(fp.read(2))
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
    attitude["PeriodStartTime"] = read_cds_time(fp.read(6))
    attitude["PeriodEndTime"] =  read_cds_time(fp.read(6))
    attitude["PrincipleAxisOffsetAngle"] = read_float8(fp.read(8))
    attitudecoef = np.dtype(">u2, >u4, >u2, >u4, (8,)>f8, (8,)>f8, (8,)>f8")
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

    # PlannedAcquisitionTime

    pat = {}
    pat["TrueRepeatCycleStart"] = read_cds_expanded_time(fp.read(10))
    pat["PlannedForwardScanEnd"] = read_cds_expanded_time(fp.read(10))
    pat["PlannedRepeatCycleEnd"] = read_cds_expanded_time(fp.read(10))

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
    radiosettings["HRVFrameOffsets"]["MDUNomHRVDelay1"] = read_uint2(fp.read(2))
    radiosettings["HRVFrameOffsets"]["MDUNomHRVDelay2"] = read_uint2(fp.read(2))
    radiosettings["HRVFrameOffsets"]["Spare"] = read_uint2(fp.read(2))
    radiosettings["HRVFrameOffsets"]["MDUNomHRVBreakline"] = read_uint2(fp.read(2))
    radiosettings["DHSSSynchSelection"] = ord(fp.read(1))
    radiosettings["MDUOutGain"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["MDUCourseGain"] = np.fromstring(fp.read(42), dtype=np.uint8)
    radiosettings["MDUFineGain"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["MDUNumericalOffset"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["PUGain"] = np.fromstring(fp.read(42 * 2), dtype=">u2")
    radiosettings["PUOffset"] = np.fromstring(fp.read(27 * 2), dtype=">u2")
    radiosettings["PUBias"] = np.fromstring(fp.read(15 * 2), dtype=">u2")
    radiosettings["OperationParameters"] = {}
    radiosettings["OperationParameters"]["L0_LineCounter"] = read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["K1_RetraceLines"] = read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["K2_PauseDeciseconds"] = read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["K3_RetraceLines"] = read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["K4_PauseDeciseconds"] = read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["K5_RetraceLines"] = read_uint2(fp.read(2))
    radiosettings["OperationParameters"]["X_DeepSpaceWindowPosition"] = ord(fp.read(1))
    radiosettings["RefocusingLines"] = read_uint2(fp.read(2))
    radiosettings["RefocusingDirection"] = ord(fp.read(1))
    radiosettings["RefocusingPosition"] = read_uint2(fp.read(2))
    radiosettings["ScanRefPosFlag"] = ord(fp.read(1)) > 0
    radiosettings["ScanRefPosNumber"] = read_uint2(fp.read(2))
    radiosettings["ScanRefPosVal"] = read_float4(fp.read(4))
    radiosettings["ScanFirstLine"] = read_uint2(fp.read(2))
    radiosettings["ScanLastLine"] = read_uint2(fp.read(2))
    radiosettings["RetraceStartLine"] = read_uint2(fp.read(2))

    hdr["RadiometerSettings"] = radiosettings

    # RadiometerOperations

    radiooper = {}

    radiooper["LastGainChangeFlag"] = ord(fp.read(1)) > 0
    radiooper["LastGainChangeTime"] = read_cds_time(fp.read(6))
    radiooper["Decontamination"] = {}
    radiooper["Decontamination"]["DecontaminationNow"] = ord(fp.read(1)) > 0
    radiooper["Decontamination"]["DecontaminationStart"] = read_cds_time(fp.read(6))
    radiooper["Decontamination"]["DecontaminationEnd"] = read_cds_time(fp.read(6))


    radiooper["BBCalScheduled"] = ord(fp.read(1)) > 0
    radiooper["BBCalibrationType"] = ord(fp.read(1))
    radiooper["BBFirstLine"] = read_uint2(fp.read(2))
    radiooper["BBLastLine"] = read_uint2(fp.read(2))
    radiooper["ColdFocalPlaneOpTemp"] = read_uint2(fp.read(2))
    radiooper["WarmFocalPlaneOpTemp"] = read_uint2(fp.read(2))


    hdr["RadiometerOperations"] = radiooper

    ## CelestialEvents
    # CelestialBodiesPosition

    celbodies = {}
    celbodies["PeriodTimeStart"] = read_cds_time(fp.read(6))
    celbodies["PeriodTimeEnd"] = read_cds_time(fp.read(6))
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
    reltoim["EclipseStartTime"] = read_cds_time(fp.read(6))
    reltoim["EclipseEndTime"] = read_cds_time(fp.read(6))
    reltoim["VisibleBodiesInImage"] = ord(fp.read(1))
    reltoim["BodiesClosetoFOV"] = ord(fp.read(1))
    reltoim["ImpactOnImageQuality"] = ord(fp.read(1))

    hdr["RelationToImage"] = reltoim

    ## ImageDescriptionRecord

    grid_origin = ["north west", "south west", "south east", "north east"]

    # ProjectionDescription

    projdes = {}
    projdes["TypeOfProjection"] = ord(fp.read(1))
    projdes["LongitudeOfSSP"] = read_float4(fp.read(4))

    hdr["ProjectionDescription"] = projdes

    # ReferenceGridVIS_IR

    refvisir = {}
    refvisir["NumberOfLines"] = read_int4(fp.read(4))
    refvisir["NumberOfColumns"] = read_int4(fp.read(4))
    refvisir["LineDirGridStep"] = read_float4(fp.read(4))
    refvisir["ColumnDirGridStep"] = read_float4(fp.read(4))
    refvisir["GridOrigin"] = grid_origin[ord(fp.read(1))]

    hdr["ReferenceGridVIS_IR"] = refvisir

    # ReferenceGridHRV

    refhrv = {}
    refhrv["NumberOfLines"] = read_int4(fp.read(4))
    refhrv["NumberOfColumns"] = read_int4(fp.read(4))
    refhrv["LineDirGridStep"] = read_float4(fp.read(4))
    refhrv["ColumnDirGridStep"] = read_float4(fp.read(4))
    refhrv["GridOrigin"] = grid_origin[ord(fp.read(1))]

    hdr["ReferenceGridHRV"] = refhrv

    # PlannedCoverageVIS_IR

    covvisir = {}
    covvisir["SouthernLinePlanned"] = read_int4(fp.read(4))
    covvisir["NorthernLinePlanned"] = read_int4(fp.read(4))
    covvisir["EasternColumnPlanned"] = read_int4(fp.read(4))
    covvisir["WesternColumnPlanned"] = read_int4(fp.read(4))

    hdr["PlannedCoverageVIS_IR"] = covvisir

    
    # PlannedCoverageHRV

    covhrv = {}
    
    covhrv["LowerSouthLinePlanned"] = read_int4(fp.read(4))
    covhrv["LowerNorthLinePlanned"] = read_int4(fp.read(4))
    covhrv["LowerEastColumnPlanned"] = read_int4(fp.read(4))
    covhrv["LowerWestColumnPlanned"] = read_int4(fp.read(4))
    covhrv["UpperSouthLinePlanned"] = read_int4(fp.read(4))
    covhrv["UpperNorthLinePlanned"] = read_int4(fp.read(4))
    covhrv["UpperEastColumnPlanned"] = read_int4(fp.read(4))
    covhrv["UpperWestColumnPlanned"] = read_int4(fp.read(4))

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


    ## RadiometricProcessing

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

    bbdu["BBObservationUTC"] = read_cds_expanded_time(fp.read(10))
    bbdu["BBRelatedData"] = {}
    bbdu["BBRelatedData"]["OnBoardBBTime"] = read_cuc_time(fp.read(7), 4, 3)
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
    data[::3] = data[::3]*256 + data[1::3] // 16
    data[1::3] = (data[1::3] & 0x0f)*16 + data[2::3]
    result = np.ravel(data.reshape(-1,3)[:,:2])
    bbdu["BBRelatedData"]["DCRValues"] = result
    bbdu["BBRelatedData"]["X_DeepSpaceWindowPosition"] = ord(fp.read(1))
    bbdu["BBRelatedData"]["ColdFPTemperature"] = {}
    bbdu["BBRelatedData"]["ColdFPTemperature"]["FCUNominalColdFocalPlaneTemp"] = read_uint2(fp.read(2)) / 100.
    bbdu["BBRelatedData"]["ColdFPTemperature"]["FCURedundantColdFocalPlaneTemp"] = read_uint2(fp.read(2)) / 100.
    bbdu["BBRelatedData"]["WarmFPTemperature"] = {}
    bbdu["BBRelatedData"]["WarmFPTemperature"]["FCUNominalWarmFocalPlaneVHROTemp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["WarmFPTemperature"]["FCURedundantWarmFocalPlaneVHROTemp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"] = {}
    bbdu["BBRelatedData"]["ScanMirrorTemperature"]["FCUNominalScanMirrorSensor1Temp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"]["FCURedundantScanMirrorSensor1Temp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"]["FCUNominalScanMirrorSensor2Temp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["ScanMirrorTemperature"]["FCURedundantScanMirrorSensor2Temp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"] = {}
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCUNominalM1MirrorSensor1Temp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCURedundantM1MirrorSensor1Temp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCUNominalM1MirrorSensor2Temp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCURedundantM1MirrorSensor2Temp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCUNominalM23AssemblySensor1Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCURedundantM23AssemblySensor1Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCUNominalM23AssemblySensor2Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["M1M2M3Temperature"]["FCURedundantM23AssemblySensor2Temp"] = ord(fp.read(1)) / 4. + 265
    bbdu["BBRelatedData"]["BaffleTemperature"] = {}
    bbdu["BBRelatedData"]["BaffleTemperature"]["FCUNominalM1BaffleTemp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["BaffleTemperature"]["FCURedundantM1BaffleTemp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["BlackBodyTemperature"] = {}
    bbdu["BBRelatedData"]["BlackBodyTemperature"]["FCUNominalBlackBodySensorTemp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["BlackBodyTemperature"]["FCURedundantBlackBodySensorTemp"] = read_uint2(fp.read(2)) / 100. + 250
    bbdu["BBRelatedData"]["FCUMode"] = {}
    bbdu["BBRelatedData"]["FCUMode"]["FCUNominalSMMStatus"] = read_uint2(fp.read(2))
    bbdu["BBRelatedData"]["FCUMode"]["FCURedundantSMMStatus"] = read_uint2(fp.read(2))
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
                                            dtype=">f4").reshape((42,64))
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
    geoproc["EarthModel"]["EquatorialRadius"] = read_float8(fp.read(8))
    geoproc["EarthModel"]["NorthPolarRadius"] = read_float8(fp.read(8))
    geoproc["EarthModel"]["SouthPolarRadius"] = read_float8(fp.read(8))
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
    ftr["SateliteID"] = read_uint2(fp.read(2))
    ftr["NominalImageScanning"] = ord(fp.read(1)) > 0
    ftr["ReducedScan"] = ord(fp.read(1)) > 0
    ftr["ForwardScanStart"] = read_cds_time(fp.read(6))
    ftr["ForwardScanEnd"] = read_cds_time(fp.read(6))
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

    ftr["SouthernLineActual"] = read_int4(fp.read(4))
    ftr["NorthernLineActual"] = read_int4(fp.read(4))
    ftr["EasternColumnActual"] = read_int4(fp.read(4))
    ftr["WesternColumnActual"] = read_int4(fp.read(4))
    ftr["LowerSouthLineActual"] = read_int4(fp.read(4))
    ftr["LowerNorthLineActual"] = read_int4(fp.read(4))
    ftr["LowerEastColumnActual"] = read_int4(fp.read(4))
    ftr["LowerWestColumnActual"] = read_int4(fp.read(4))
    ftr["UpperSouthLineActual"] = read_int4(fp.read(4))
    ftr["UpperNorthLineActual"] = read_int4(fp.read(4))
    ftr["UpperEastColumnActual"] = read_int4(fp.read(4))
    ftr["UpperWestColumnActual"] = read_int4(fp.read(4))

    return ftr

def read_metadata(prologue, image_files, epilogue):
    """ Selected items from the Meteosat-7 prolog file.
    """
    md = xrit.mda.Metadata()

    fp = StringIO(prologue.data)
    hdr = read_proheader(fp)

    fp = StringIO(epilogue.data)
    ftr = read_epiheader(fp)
    
    md.sublon = hdr["SatelliteDefinition"]["NominalLongitude"]
    im = xrit.read_imagedata(image_files[0])
    md.product_name = str(im)
    md.channel = im.product_name
    if md.channel == "HRV":
        md.image_size = np.array((hdr["ReferenceGridHRV"]["NumberOfLines"],
                                  hdr["ReferenceGridHRV"]["NumberOfColumns"]))
    else:
        md.image_size = np.array((hdr["ReferenceGridVIS_IR"]["NumberOfLines"],
                                  hdr["ReferenceGridVIS_IR"]["NumberOfColumns"]))
        

    md.satname = im.platform.lower()
    md.product_type = 'full disc'
    md.region_name = 'full disc'
    if md.channel == "HRV":
        md.first_pixel = hdr["ReferenceGridHRV"]["GridOrigin"]
        md.boundaries = np.array([[
            ftr["LowerSouthLineActual"],
            ftr["LowerNorthLineActual"],
            ftr["LowerEastColumnActual"],
            ftr["LowerWestColumnActual"]],
           [ftr["UpperSouthLineActual"],
            ftr["UpperNorthLineActual"],
            ftr["UpperEastColumnActual"],
            ftr["UpperWestColumnActual"]]])
    else:
        md.first_pixel = hdr["ReferenceGridVIS_IR"]["GridOrigin"]
        md.boundaries = np.array([[
            ftr["SouthernLineActual"],
            ftr["NorthernLineActual"],
            ftr["EasternColumnActual"],
            ftr["WesternColumnActual"]]])

    if md.channel in ["HRV", "VIS006", "VIS008", "IR_016"]:
        md.calibration_unit = "%"
    else:
        md.calibration_unit = "K"
    
    md.data_type = im.structure.nb
    md.no_data_value = 0
    md.line_offset = 0
    md.time_stamp = im.time_stamp
    md.production_time = im.production_time
    md.calibrate = _Calibrator(hdr, md)


    return md

if __name__ == '__main__':
    import xrit
    p = xrit.read_prologue(sys.argv[1])
    print dir(p)
    print p.platform
    print p.segment_id
    print p.is_compressed
    #print read_metadata(p, sys.argv[2:])
