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

    gp_pk_header = np.dtype([
        ("HeaderVersionNo", ">i1"),
        ("PacketType", ">i1"),
        ("SubHeaderType", ">i1"),
        ("SourceFacilityId", ">i1"),
        ("SourceEnvId", ">i1"),
        ("SourceInstanceId", ">i1"),
        ("SourceSUId", ">i4"),
        ("SourceCPUId", ">i1", (4, )),
        ("DestFacilityId", ">i1"),
        ("DestEnvId", ">i1"),
        ("SequenceCount", ">u2"),
        ("PacketLength", ">i4"),
    ])

    gp_pk_subheader = np.dtype([
        ("SubHeaderVersionNo", ">i1"),
        ("ChecksumFlag", ">i1"),
        ("Acknowledgement", ">i1", (4, )),
        ("ServiceType", ">i1"),
        ("ServiceSubtype", ">i1"),
        ("PacketTime", ">i1", (6, )),
        ("SpacecraftId", ">i2"),
    ])

    pk_head = np.dtype([("gp_pk_header", gp_pk_header),
                        ("gp_pk_sh1", gp_pk_subheader)])

    print pk_head.itemsize

    fp_ = open(filename, 'r')
    fp_.seek(offset)
    pk_header = np.fromfile(fp_, pk_head, count=1)
    fp_.close()
    pos = offset + pk_header.itemsize

    return pk_header, pos


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
