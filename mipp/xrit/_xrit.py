#
# $Id$ 
#

"""This module will read LRIT/HRIT headers. Format described in:
"LRIT/HRIT Global Specification"; CGMS 03; Issue 2.6; 12 August 1999
"MSG Ground Segment LRIT/HRIT Mission Specific Implementation"; EUM/MSG/SPE/057; Issue 6; 21 June 2006
"""

import sys
import os
from StringIO import StringIO 

import mipp
from mipp.xrit import bin_reader as rbin

__all__ = ['read_prologue',
           'read_epilogue',
           'read_imagedata',
           'read_gts_message',
           'read_mpef',
           'read_mpef_clm',
           'decompress',
           'list']

def decompress(infile, outdir='.'):
    """Will decompress an XRIT data file and return the path to the
    decompressed file. It expect to find Eumetsat's xRITDecompress through the
    environment variable XRIT_DECOMPRESS_PATH
    """
    from subprocess import Popen, PIPE
    cmd = os.environ.get('XRIT_DECOMPRESS_PATH', None)
    if not cmd:
        raise IOError("XRIT_DECOMPRESS_PATH is not defined" +
                      " (complete path to xRITDecompress)")

    infile = os.path.abspath(infile)
    cwd = os.getcwd()
    os.chdir(outdir)

    question = ("Did you set the environment variable " +
                "XRIT_DECOMPRESS_PATH correctly?")
    if not os.path.exists(cmd):
        raise IOError(str(cmd) + " does not exist!\n" + question)
    elif os.path.isdir(cmd):
        raise IOError(str(cmd) + " is a directory!\n" + question)

    p = Popen([cmd, infile], stdout=PIPE)
    stdout = StringIO(p.communicate()[0])
    status = p.returncode
    os.chdir(cwd)
    
    outfile = ''
    for line in stdout:
        try:
            k, v = [x.strip() for x in line.split(':', 1)]
        except ValueError:
            break
        if k == 'Decompressed file':
            outfile = v
            break
    
    if status != 0:
        raise mipp.DecodeError("xrit_decompress '%s', failed, status=%d"%(infile, status))
    if not outfile:
        raise mipp.DecodeError("xrit_decompress '%s', failed, no output file is generated"%infile)
    return outdir + '/' + outfile    
    
#-----------------------------------------------------------------------------
#
# XRIT header records
#
#-----------------------------------------------------------------------------
class PrimaryHeader(object):
    hdr_type = 0
    hdr_name = 'primary_header'    
    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.file_type = rbin.read_uint1(fp.read(1))
        self.total_hdr_len = rbin.read_uint4(fp.read(4))
        self.data_field_len = rbin.read_uint8(fp.read(8))
        
    def __str__(self):
        return  "hdr_type:%d, rec_len:%d, file_type:%d, total_hdr_len:%d, data_field_len:%d"%\
               (self.hdr_type, self.rec_len, self.file_type, self.total_hdr_len, self.data_field_len)

class ImageStructure(object):
    hdr_type = 1
    hdr_name = 'structure'    
    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.nb = rbin.read_uint1(fp.read(1))
        self.nc = rbin.read_uint2(fp.read(2))
        self.nl = rbin.read_uint2(fp.read(2))
        self.compress_flag = rbin.read_uint1(fp.read(1))
        
    def __str__(self):
        return  "hdr_type:%d, rec_len:%d, nb:%d, nc:%d, nl:%d, compress_flag:%d"%\
               (self.hdr_type, self.rec_len, self.nb, self.nc, self.nl, self.compress_flag)

class ImageNavigation(object):
    hdr_type = 2
    hdr_name = 'navigation'    
    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.proj_name = fp.read(32).strip()
        self.cfac = rbin.read_int4(fp.read(4))
        self.lfac = rbin.read_int4(fp.read(4))
        self.coff = rbin.read_int4(fp.read(4))
        self.loff = rbin.read_int4(fp.read(4))
        i1 = self.proj_name.find('(')
        i2 = self.proj_name.find(')')
        if i1 != -1 and i2 != -1:
            self.ssp = float(self.proj_name[i1+1:i2])
        else:
            self.ssp = None
        
    def __str__(self):
        return  "hdr_type:%d, rec_len:%d, proj_name:'%s', cfac:%d, lfac:%d. coff:%d, loff:%d"%\
               (self.hdr_type, self.rec_len, self.proj_name, self.cfac, self.lfac, self.coff, self.loff)

class ImageDataFunction(object):
    hdr_type = 3
    hdr_name = 'data_function'    
    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.data_definition = _decode_data_definition(fp.read(self.rec_len-3))
        
    def __str__(self):
        return  "hdr_type:%d, rec_len:%d, data_definition:'%s'"%\
               (self.hdr_type, self.rec_len, self.data_definition)

class AnnotationHeader(object):
    hdr_type = 4
    hdr_name = 'annotation'
    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.text = fp.read(self.rec_len-3).strip()
        a = [x.strip('_') for x in self.text.split('-')]
        self.xrit_channel_id = a[0]
        self.dissemination_id = int(a[1])
        self.dissemination_sc = a[2]
        self.platform = a[3]
        self.product_name = a[4]
        self.segment_name = a[5]
        self.time_stamp = mipp.strptime(a[6], "%Y%m%d%H%M")
        self.flags = a[7]
        self.segment_id = a[3] + '_' + a[4] + '_' + a[5] + '_' + self.time_stamp.strftime("%Y%m%d_%H%M")
        self.product_id = a[3] + '_' + a[4] + '_' + self.time_stamp.strftime("%Y%m%d_%H%M")

    def __str__(self):
        return  "hdr_type:%d, rec_len:%d, text:%s"%\
               (self.hdr_type, self.rec_len, self.text)

class TimeStampRecord(object):
    hdr_type = 5
    hdr_name = 'time_stamp'    
    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.cds_p_field = rbin.read_uint1(fp.read(1))
        self.time_stamp = rbin.read_cds_time(fp.read(6))

    def __str__(self):
        return  "hdr_type:%d, rec_len:%d, time_stamp:%s"%\
               (self.hdr_type, self.rec_len, str(self.time_stamp))

class SegmentIdentification(object):
    hdr_type = 128
    hdr_name = 'segment'    
    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        self.gp_sc_id = rbin.read_uint2(fp.read(2))
        self.spectral_channel_id = rbin.read_uint1(fp.read(1))
        self.seg_no = rbin.read_uint2(fp.read(2))
        self.planned_start_seg_no = rbin.read_uint2(fp.read(2))
        self.planned_end_seg_no = rbin.read_uint2(fp.read(2))
        self.data_field_repr = rbin.read_uint1(fp.read(1))

    def __str__(self):
        return  "hdr_type:%d, rec_len:%d gp_sc_id:%d, spectral_channel_id:%d, seg_no:%d, planned_start_seg_no:%d, planned_end_seg_no:%d, data_field_repr:%d"%\
               (self.hdr_type, self.rec_len, self.gp_sc_id, self.spectral_channel_id,\
                self.seg_no, self.planned_start_seg_no, self.planned_end_seg_no, self.data_field_repr)

class ImageSegmentLineQuality(object):
    hdr_type = 129
    hdr_name = 'image_quality'
    
    def __init__(self, fp):
        self.rec_len = rbin.read_uint2(fp.read(2))
        a = []
        nb = 3
        while nb < (self.rec_len):
            ln = rbin.read_int4(fp.read(4))
            stamp = rbin.read_cds_time(fp.read(6))
            lv = rbin.read_uint1(fp.read(1))
            lr = rbin.read_uint1(fp.read(1))
            lg = rbin.read_uint1(fp.read(1))
            a.append((ln, stamp, lv, lr, lg))
            nb += 13
        self.line_quality = a        

    def __str__(self):
        return  "hdr_type:%d, rec_len:%d"%\
               (self.hdr_type, self.rec_len)

class UnknownHeader(object):
    hdr_name = 'unknown'    
    def __init__(self, hdr_type, fp):
        self.hdr_type = hdr_type
        self.rec_len = rbin.read_uint2(fp.read(2))        
        self.data = fp.read(self.rec_len-3)
    def __str__(self):
        return  "hdr_type:%d, rec_len:%d"%\
               (self.hdr_type, self.rec_len)

def _decode_data_definition(buf):
    dd = dict()
    lines = [x.strip() for x in buf.strip().split('\r')]
    for a in lines:
        k, v = [x.strip() for x in a.split(':=')]
        if k[0] == '$':
            dd[k] = int(v)
        elif k[0] == '_':
            dd[k] = v
        elif k.isdigit():
            dd[int(k)] = float(v)
        else:
            raise mipp.DecodeError("could not decode data definition: '%s'"%a)
    return dd
    
base_header_map = {0: PrimaryHeader,
              1: ImageStructure,
              2: ImageNavigation,
              3: ImageDataFunction,
              4: AnnotationHeader,
              5: TimeStampRecord,
              128: SegmentIdentification,
              129: ImageSegmentLineQuality}
base_header_types = tuple(sorted(base_header_map.keys()))

def read_header(fp):
    hdr_type = rbin.read_uint1(fp.read(1))
    if hdr_type != 0:
        raise mipp.DecodeError("first header has to be a Primary Header, this one is of type %d"%hdr_type)
    phdr = PrimaryHeader(fp)
    yield phdr
    current_size = phdr.rec_len
    while current_size < phdr.total_hdr_len:
        hdr_type = rbin.read_uint1(fp.read(1))
        cls = header_map.get(hdr_type, None)
        if cls:
            hdr = cls(fp)
        else:
            hdr = UnknownHeader(hdr_type, fp)
        yield hdr
        current_size += hdr.rec_len

def read_headers(fp):
    return [h for h in read_header(fp)]

#-----------------------------------------------------------------------------
#
# File level
#
#-----------------------------------------------------------------------------
class Segment(object):
    def __init__(self, file_name):
        self.file_name = file_name
        fp = open(file_name)
        for h in read_header(fp):
            if h.hdr_type == 0:
                self.file_type = h.file_type
            elif h.hdr_type == 4:
                self.platform = h.platform
                self.product_name = h.product_name
                self.segment_name = getattr(h, "segment_name", None)
                self.time_stamp = getattr(h, "time_stamp", None)
                self.product_id = getattr(h, "product_id", None)
                self.segment_id = getattr(h, "segment_id", None)
            elif h.hdr_type == 5:
                self.production_time = h.time_stamp
            elif h.hdr_type in header_types:
                setattr(self, h.hdr_name, h)
        fp.close()
        try:
            self.is_compressed = bool(self.structure.compress_flag)
        except AttributeError:
            self.is_compressed = False
        # lazy reading of data
        self._blob = None

    @property
    def data(self):
        if not self._blob:
            fp = open(self.file_name)
            read_headers(fp)
            self._blob = fp.read()
            fp.close()
        return self._blob

    def pprint(self):
        keys = self.__dict__.keys()
        keys.sort()
        for k in keys:
            if not k.startswith('_'):
                print k + ':', self.__dict__[k]

    def __str__(self):
        return str(self.segment_id)

class ImageSegment(Segment):

    def __init__(self, file_name):
        Segment.__init__(self, file_name)
        self.bytes_per_line = (self.structure.nc*self.structure.nb)/8
        self.fp = None
    
    def readline(self, nlines=1):
        if not self.fp:
            self.fp = open(self.file_name)
            read_headers(self.fp)
        data = self.fp.read(self.bytes_per_line*nlines)
        if not data:
            raise mipp.DecodeError("could not read", self.bytes_per_line*nlines, "bytes")
        return data
    
    def close(self):
        if self.fp:
            self.fp.close()
            self.fp = None

def read_prologue(file_name):
    s = Segment(file_name)
    if s.file_type == 128:
        return s
    else:
        raise mipp.DecodeError("this is no 'prologue' file: '%s'"%file_name)

def read_epilogue(file_name):
    s = Segment(file_name)
    if s.file_type == 129:
        return s
    else:
        raise mipp.DecodeError("this is no 'epilogue' file: '%s'"%file_name)

def read_imagedata(file_name):
    s = Segment(file_name)
    if s.file_type == 0:
        return ImageSegment(file_name)
    else:
        raise mipp.DecodeError("this is no 'image data' file: '%s'"%file_name)
    
    
def read_gts_message(file_name):
    s = Segment(file_name)
    if s.file_type == 1:
        return s
    else:
        raise mipp.DecodeError("this is no 'GTS Message' file: '%s'"%file_name)

def read_mpef(file_name):
    s = Segment(file_name)
    if s.file_type == 144:
        return s
    else:
        raise mipp.DecodeError("this is no 'MPEF (type=144)' file: '%s'"%file_name)

# Backward compatible
read_mpef_clm = read_mpef

def list(file_name, dump_data=False):
    fname = 'xrit.dat'
    fp = open(file_name)
    for hdr in read_header(fp):
        if hdr.hdr_name == 'annotation':
            fname = hdr.segment_id
    data = fp.read()
    fp.close()
    if dump_data:
        print 'Writing', fname
        fp = open(fname, 'wb')
        fp.write(data)
        fp.close()
    
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) > 1:
        if args[0] == '-d':
            dump_data = True
        filename = args[1]
    else:
        dump_data = False
        filename = args[0]
        
    list(filename, dump_data)
