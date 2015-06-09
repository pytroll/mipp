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
from mipp.satellites.msg_hrit import MSGHRITLoader

DATADIR = (os.path.dirname(__file__) or '.') + '/data'

MSG_FILES = [DATADIR + '/H-000-MSG2__-MSG2________-_________-PRO______-201010111400-__',
             DATADIR +
             '/H-000-MSG2__-MSG2________-IR_108___-000004___-201010111400-__',
             DATADIR +
             '/H-000-MSG2__-MSG2________-IR_108___-000005___-201010111400-__',
             DATADIR + '/H-000-MSG2__-MSG2________-_________-EPI______-201010111400-__']


class TestReadData(unittest.TestCase):

    def setUp(self):
        self.decompressed_msg_files = []

    def test_msg(self):
        """Test read some msg image data"""

        #loader = msg_hrit.load(files=msg_files, calibrate=2)
        #mda, img = loader[1656:1956, 1756:2656]
        pass

    def tearDown(self):
        """Clean up"""
        pass


class TestReadMetaData(unittest.TestCase):

    def setUp(self):
        pass

    def test_read_metadata(self):
        """Test read msg metadata"""

        loader = MSGHRITLoader('meteosat10', files=MSG_FILES)
        print loader.mda

    def tearDown(self):
        """Clean up"""
        pass

if __name__ == "__main__":
    unittest.main()
