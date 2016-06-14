#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <adam.dybbroe@smhi.se>
#   Lars Ørum Rasmussen <ras@dmi.dk>

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

"""Convertion functions taken from old convert.py inside xrit directory
"""

from datetime import datetime, timedelta
import numpy as np

def get_cds_time(days, msecs):
    """Get the datetime object of the time since epoch given in days and
    milliseconds of day
    """
    return datetime(1958, 1, 1) + timedelta(days=float(days),
                                            milliseconds=float(msecs))


def dec10to16(data):
    """Unpacking the 10 bit data to 16 bit"""

    if isinstance(data, str):
        data = np.fromstring(data, dtype=np.uint8)

    arr10 = data.astype(np.uint16).flat
    new_shape = list(data.shape[:-1]) + [(data.shape[-1] * 8) / 10]
    arr16 = np.zeros(new_shape, dtype=np.uint16)
    arr16.flat[::4] = np.left_shift(arr10[::5], 2) + \
        np.right_shift((arr10[1::5]), 6)
    arr16.flat[1::4] = np.left_shift((arr10[1::5] & 63), 4) + \
        np.right_shift((arr10[2::5]), 4)
    arr16.flat[2::4] = np.left_shift(arr10[2::5] & 15, 6) + \
        np.right_shift((arr10[3::5]), 2)
    arr16.flat[3::4] = np.left_shift(arr10[3::5] & 3, 8) + \
        arr10[4::5]
    return arr16


