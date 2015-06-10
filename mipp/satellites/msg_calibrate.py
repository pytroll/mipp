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

import numpy as np

NO_DATA_VALUE = 0
EVAL_NP = eval

class CalibrationError(Exception):
    pass

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


class Calibrator(object):

    def __init__(self, hdr, channel_name):
        """Initialze a calibrator with a prolog header object and 
        channel name.
        """

        self.hdr = hdr
        self.channel_name = channel_name

    def __call__(self, image, calibrate=1):

        """Computes the radiances and reflectances/bt of a given channel.  The
        *calibrate* argument should be set to 0 for no calibration, 1 for
        default reflectances/bt calibration, and 2 for returning radiances. The
        default value is 1.

        Return calibrated (or not) image and corresponding physical unit.
        """

        hdr = self.hdr
        channel_name = self.channel_name

        if calibrate == 0:
            return (image, "counts")

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

        mask = (image == NO_DATA_VALUE)

        cslope = hdr["Level1_5ImageCalibration"][chn_nb]['Cal_Slope']
        coffset = hdr["Level1_5ImageCalibration"][chn_nb]['Cal_Offset']

        radiances = EVAL_NP('image * cslope + coffset')
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
            reflectance = EVAL_NP('(radiances / solar_irradiance) * 100.')
            return (np.ma.MaskedArray(reflectance, mask=mask),
                    "%")

        wavenumber = CALIB[sat][channel_name]["VC"]
        if cal_type[chn_nb] == 2:
            # computation based on effective radiance
            alpha = CALIB[sat][channel_name]["ALPHA"]
            beta = CALIB[sat][channel_name]["BETA"]

            cal_data = EVAL_NP(('((C2 * 100. * wavenumber / '
                                'np.log(C1 * 1.0e6 * wavenumber ** 3 / '
                                '(1.0e-5 * radiances) + 1)) - beta) / alpha'))

        elif cal_type[chn_nb] == 1:
            # computation based on spectral radiance
            cal_data = EVAL_NP(('C2 * 100. * wavenumber / '
                                'np.log(C1 * 1.0e6 * wavenumber ** 3 / '
                                '(1.0e-5 * radiances) + 1))'))

            coef_a = eval("BTFIT_A_" + channel_name)
            coef_b = eval("BTFIT_B_" + channel_name)
            coef_c = eval("BTFIT_C_" + channel_name)

            cal_data = EVAL_NP(('cal_data ** 2 * coef_a + '
                                'cal_data * coef_b + coef_c'))

        else:
            raise RuntimeError("Something is seriously wrong in the metadata.")

        mask = mask | np.isnan(cal_data) | np.isinf(cal_data)
        cal_data = np.ma.MaskedArray(cal_data, mask=mask)
        return (cal_data,
                "K")


