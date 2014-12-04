#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c14526.ad.smhi.se>

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

"""Unit testing the (10 to 16 bit) conversion functions
"""

import unittest

from mipp import convert
from mipp import xrit
import os
from mipp.xrit import _xrit
import numpy as np


class ConvertTest(unittest.TestCase):

    """Unit testing the functions to get the old flag palettes etc"""

    def setUp(self):
        """Set up"""
        return

    def test_10to16(self):
        """Test 10 to 16 bit conversion"""

        datadir = (os.path.dirname(__file__) or '.') + '/data'
        msg_files = [datadir + '/H-000-MSG2__-MSG2________-_________-PRO______-201010111400-__',
                     datadir + '/H-000-MSG2__-MSG2________-IR_108___-000004___-201010111400-__',
                     datadir + '/H-000-MSG2__-MSG2________-IR_108___-000005___-201010111400-__',
                     datadir + '/H-000-MSG2__-MSG2________-_________-EPI______-201010111400-__']

        
        EXPECTED_SUM = 1578433028

        # 
        # Raw reading
        #
        fp = open(msg_files[1], 'r')
        _xrit.read_headers(fp)
        s = fp.read()
        fp.close()

        fp = open(msg_files[2], 'r')
        _xrit.read_headers(fp)
        s2 = fp.read()
        fp.close()
        s = s + s2

        #
        # Do conversion
        #
        x = convert.dec10216(s)
        this = np.frombuffer(x, dtype=np.uint16)

        #
        # Validate conversion through known sum
        #
        self.assertEqual(this.sum(), EXPECTED_SUM)



    def tearDown(self):
        """Clean up"""
        return

if __name__ == '__main__':
    unittest.main()
