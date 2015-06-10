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

"""
"""


class Metadata(object):

    def __init__(self):

        self.coff = 0
        self.loff = 0
        self.cfac = 0
        self.lfac = 0
        self.shifted = False
        self.number_of_columns = 0
        self.number_of_lines = 0
        self.timestamp = None
        self.number_of_segments = 0
        self.resolution = None
        self.proj4_str = 'unknown'
        self.projection = 'unknown'
        self.sublon = None
        self.calibration_unit = 'unknown'
        self.channel_names = []
        self.satellite_id = ''
        self.sensor = 'unknown'

        self._info = {}

    def __str__(self):
        keys = sorted(self.__dict__.keys())
        strn = ''
        for key in keys:
            val = getattr(self, key)
            if (not key.startswith('_') and
                    not callable(val)):
                strn += key + ': ' + str(val) + '\n'
        return strn[:-1]
