#
# $Id$ 
#
# Unpack binary data, all in network (big-endian) byte order.
#
import struct
from datetime import datetime, timedelta

def read_uint1(buf):
    return struct.unpack("!B", buf)[0]

def read_uint2(buf):
    return struct.unpack("!H", buf)[0]

def read_uint4(buf):
    return struct.unpack("!I", buf)[0]

def read_uint8(buf):
    v = struct.unpack("!2I", buf)
    return v[0]*pow(2L, 32) + v[1]

def read_int2(buf):
    return struct.unpack("!h", buf)[0]

def read_int4(buf):
    return struct.unpack("!i", buf)[0]

def read_float4(buf):
    return struct.unpack("!f", buf)[0]

def read_float8(buf):
    return struct.unpack("!d", buf)[0]


def read_cds_time(buf):
    days = read_uint2(buf[:2])
    msecs = read_uint4(buf[2:6])
    return datetime(1958, 1, 1) + timedelta(days=days, milliseconds=msecs)

def read_cds_expanded_time(buf):
    days = read_uint2(buf[:2])
    msecs = read_uint4(buf[2:6])
    usecs = read_uint2(buf[6:8])
    nsecs = read_uint2(buf[8:10])
    return datetime(1958, 1, 1) + timedelta(days=days, milliseconds=msecs, microseconds=(usecs+nsecs/1000.))

def read_cuc_time(buf, coarce, fine):
    ctime = 0
    ftime = 0
    for i in range(coarce - 1, -1, -1):
        ctime += ord(buf[coarce - i - 1]) * 2 ** (i * 8)
    for i in range(fine):
        ftime += ord(buf[coarce + i]) * 2 ** ((i + 1) * -8)
    return datetime(1958, 1, 1) + timedelta(seconds=ctime + ftime) 
