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

"""Tools to read MSG header information
"""

from mipp.header_records import Level15HeaderRecord
from mipp.header_records import GP_PK_HeaderRecord
import numpy as np


def read_umarf_header(filename):
    """Read the umarf header from file"""

    umarf = {}

    with open(filename) as fp_:
        for i in range(6):
            name = (fp_.read(30).strip("\x00"))[:-2].strip()
            umarf[name] = fp_.read(50).strip("\x00").strip()

        for i in range(27):
            name = fp_.read(30).strip("\x00")
            if name == '':
                fp_.read(32)
                continue
            name = name[:-2].strip()
            umarf[name] = {"size": fp_.read(16).strip("\x00").strip(),
                           "adress": fp_.read(16).strip("\x00").strip()}
        for i in range(19):
            name = (fp_.read(30).strip("\x00"))[:-2].strip()
            umarf[name] = fp_.read(50).strip("\x00").strip()

        for i in range(18):
            name = (fp_.read(30).strip("\x00"))[:-2].strip()
            umarf[name] = fp_.read(50).strip("\x00").strip()

        pos = fp_.tell()

    return umarf, pos


def read_pkhead(filename, offset):
    """Read the rest of the native header"""

    pkhrec = GP_PK_HeaderRecord().get()
    dt_ = np.dtype(pkhrec)
    dtl = dt_.newbyteorder('>')
    with open(filename) as fpt:
        data = np.memmap(fpt, dtype=dtl, shape=(1,), offset=offset, mode='r')

    return data, offset + dtl.itemsize


def read_level15header(filename, offset):
    """Read the level 1.5 SEVIRI header"""

    # Create the header record object:
    hrec = Level15HeaderRecord().get()
    dt_ = np.dtype(hrec)
    dtl = dt_.newbyteorder('>')
    with open(filename) as fpt:
        return np.memmap(fpt, dtype=dtl, shape=(1,), offset=offset, mode='r')

if __name__ == "__main__":
    import sys
    from datetime import datetime, timedelta

    FILE = sys.argv[1]
    umarfhd, offs = read_umarf_header(FILE)
    pkh, offs = read_pkhead(FILE, offs)
    hdr = read_level15header(FILE, offs)
