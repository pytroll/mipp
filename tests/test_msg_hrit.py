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

"""Test the reading of the MSG HRIT formatet (EUMETCast disseminated) data
"""

import unittest
import os.path
from datetime import datetime
from mipp.satellites.msg_hrit import MSGHRITLoader
import logging

DATADIR = (os.path.dirname(__file__) or '.') + '/data'

MSG_FILES = [DATADIR + '/H-000-MSG2__-MSG2________-_________-PRO______-201010111400-__',
             DATADIR +
             '/H-000-MSG2__-MSG2________-IR_108___-000004___-201010111400-__',
             DATADIR +
             '/H-000-MSG2__-MSG2________-IR_108___-000005___-201010111400-__',
             DATADIR + '/H-000-MSG2__-MSG2________-_________-EPI______-201010111400-__']
MSG_SUM_CALIB = 75116847.263172984
MSG_SUM_NOCALIB = 121795059

HRV_FILES = [DATADIR + '/H-000-MSG2__-MSG2________-_________-PRO______-201010111400-__',
             DATADIR +
             '/H-000-MSG2__-MSG2________-HRV______-000012___-201010111400-__',
             DATADIR +
             '/H-000-MSG2__-MSG2________-HRV______-000013___-201010111400-__',
             DATADIR + '/H-000-MSG2__-MSG2________-_________-EPI______-201010111400-__']
HRV_SUM = 11328340.753558

PROJ4_STRING = "proj=geos lon_0=0.00 lat_0=0.00 a=6378169.00 b=6356583.80 h=35785831.00"


class TestReadData(unittest.TestCase):

    def setUp(self):
        self.decompressed_msg_files = []

    def test_msg_nocalib(self):
        """Test read some msg image data"""

        loader = MSGHRITLoader(channels=[''], files=MSG_FILES)
        mda, img = loader.load(calibrate=0)
        arr = img[1656:1956, 1756:2656]
        self.assertTrue(arr.shape == (300, 900))
        self.assertEqual(arr.sum(), MSG_SUM_NOCALIB)

    def test_msg_calib(self):
        """Test read some msg image data"""

        loader = MSGHRITLoader(channels=[''], files=MSG_FILES)
        mda, img = loader.load(calibrate=1)
        arr = img[1656:1956, 1756:2656]
        self.assertTrue(arr.shape == (300, 900))
        print arr.sum()
        self.assertAlmostEqual(arr.sum(), MSG_SUM_CALIB, 3)

    def test_msg_hrv(self):
        """Test read some msg image data"""

        loader = MSGHRITLoader(channels=[''], files=HRV_FILES)
        mda, img = loader[5168:5768, 5068:6068] #.load(calibrate=1)

        from mipp.satellites.msg_calibrate import Calibrator
        img, unit = Calibrator(loader.prologue, loader.mda.channel_id)(
            img, calibrate=1)
        mda.calibration_unit = unit

        print img.shape
        self.assertTrue(img.shape == (600, 1000))
        print img.sum()
        self.assertAlmostEqual(img.sum(), HRV_SUM, 3)
        print mda

    def tearDown(self):
        """Clean up"""
        pass


class TestReadMetaData(unittest.TestCase):

    def setUp(self):
        self.timestamp = datetime(2010, 10, 11, 14, 0, 0)

    def test_read_metadata(self):
        """Test read msg metadata"""

        loader = MSGHRITLoader('meteosat10', files=MSG_FILES)
        self.assertEqual(loader.mda.coff, 1856)
        self.assertEqual(loader.mda.loff, 1856)
        self.assertEqual(loader.mda.image_size[0], 3712)
        self.assertEqual(loader.mda.image_size[1], 3712)
        self.assertEqual(loader.mda.number_of_columns, 3712)
        self.assertEqual(loader.mda.proj4_str, PROJ4_STRING)
        self.assertAlmostEqual(loader.mda.sublon, 0.0, 4)
        self.assertEqual(loader.mda.satname, 'msg2')
        self.assertEqual(loader.mda.satnumber, '09')
        self.assertEqual(loader.mda.timestamp, self.timestamp)

        ##print loader.mda

    def tearDown(self):
        """Clean up"""
        pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
