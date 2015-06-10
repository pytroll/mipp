#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013, 2014 Martin Raspaud

# Author(s):

#   Martin Raspaud <martin.raspaud@smhi.se>

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

"""Reader for eumetsat's native format.

TODO:
 - Add IMPFConfiguration Record
 - Make it an mpop reader (with geo info)
 - Make it work on a subset of channels
 - Put the hrv inside a square image (for not subsetted cases)
 - cleanup
"""

import sys
import numpy as np

def dec10to16(data):
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

def show(data):
    """Show the stetched data.
    """
    import Image as pil
    img = pil.fromarray(np.array((data - data.min()) * 255.0 /
                                 (data.max() - data.min()), np.uint8))
    img.show()

umarf = {}

with open(sys.argv[1]) as fp_:
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

    from pprint import pprint
    pprint(umarf)

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

    # read header
    
    from mipp.xrit.MSG import read_proheader, read_epiheader

    pk_header = np.fromfile(fp_, pk_head, count=1)
    print pk_header
    hdr_version = ord(fp_.read(1))
    hdr = read_proheader(fp_)

    # FIXME: read impf configuration here


    # read line data

    cols_visir = np.ceil(int(umarf["NumberColumnsVISIR"]) * 5.0 / 4) # 4640
    if (int(umarf['WestColumnSelectedRectangle'])
        - int(umarf['EastColumnSelectedRectangle'])) < 3711:
        cols_hrv = np.ceil(int(umarf["NumberColumnsHRV"]) * 5.0 / 4) # 6960
    else:
        cols_hrv = np.ceil(5568 * 5.0 / 4) # 6960
    #'WestColumnSelectedRectangle' - 'EastColumnSelectedRectangle'
    #'NorthLineSelectedRectangle' - 'SouthLineSelectedRectangle'

    area_extent = ((1856 - int(umarf["WestColumnSelectedRectangle"]) - 0.5) * hdr["ReferenceGridVIS_IR"]["ColumnDirGridStep"],
                   (1856 - int(umarf["NorthLineSelectedRectangle"]) + 0.5) * hdr["ReferenceGridVIS_IR"]["LineDirGridStep"],
                   (1856 - int(umarf["EastColumnSelectedRectangle"]) + 0.5) * hdr["ReferenceGridVIS_IR"]["ColumnDirGridStep"],
                   (1856 - int(umarf["SouthLineSelectedRectangle"]) + 1.5) * hdr["ReferenceGridVIS_IR"]["LineDirGridStep"])



    fp_.seek(450400)

    linetype = np.dtype([("visir", [("gp_pk", pk_head),
                                    ("version", ">u1"),
                                    ("satid", ">u2"),
                                    ("time", ">u2", (5, )),
                                    ("lineno", ">u4"),
                                    ("chan_id", ">u1"),
                                    ("acq_time", ">u2", (3, )),
                                    ("line_validity", ">u1"),
                                    ("line_rquality", ">u1"),
                                    ("line_gquality", ">u1"),
                                    ("line_data", ">u1", (cols_visir, ))],
                         (11, )),
                         ("hrv",  [("gp_pk", pk_head),
                                   ("version", ">u1"),
                                   ("satid", ">u2"),
                                   ("time", ">u2", (5, )),
                                   ("lineno", ">u4"),
                                   ("chan_id", ">u1"),
                                   ("acq_time", ">u2", (3, )),
                                   ("line_validity", ">u1"),
                                   ("line_rquality", ">u1"),
                                   ("line_gquality", ">u1"),
                                   ("line_data", ">u1", (cols_hrv, ))],
                          (3, ))])

    data_len = int(umarf["NumberLinesVISIR"])

    # read everything in memory
    #res = np.fromfile(fp_, dtype=linetype, count=data_len)
    
    # lazy reading
    res = np.memmap(fp_, dtype=linetype, shape=(data_len, ), offset=450400, mode="r")

    # read trailer
    #pk_header = np.fromfile(fp_, pk_head, count=1)
    #ftr = read_epiheader(fp_)

    # display the data
    show(dec10to16(res["visir"]["line_data"][:, 1, :])[::-1, ::-1])
    #show(dec10to16(res["hrv"]["line_data"]).reshape((int(umarf["NumberLinesHRV"]), -1))[::-1, ::-1])
