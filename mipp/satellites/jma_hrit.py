#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Adam.Dybbroe

# Author(s):

#   ioan.ferencik <a000680@c20671.ad.smhi.se>

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

"""A reader for the MSG
"""

from mipp.generic_loader import GenericLoader
from mipp.metadata import Metadata
from collections import OrderedDict
import struct
import datetime
import numpy as np

import logging
logger = logging.getLogger(__name__)



# a MTSAT HRIT image can have only following number of lines
HRIT_IMAGE_NLINES = 11000, 11000//2, 11000//4, 11000//8

#the number of lines in a full disk MTSAT HROIT image
HRIT_FDIMAGE_NLINES = 11000

HRIT_BYTE_ORDER = '>' # the byte order ot MTSAT HRIT files, BIG endian

#the scene types of an MTSAT HRIT image
HRIT_SCENE_TYPES= {'DK01':'FD', 'DK02':'NH', 'DK03':'SH'}
# an explicit dictionary with all HRIT records as defined by JMA mission specific implementatation
#NB: some of the records have a variable length therefore the size of thse records has to be computed at runtime.as
# those
RECORDS = {

    0: ('Primary Header', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'), ('File_Type_Code', 'B'), ('Total_Header_Length', 'I'), ('Data_Field_Length', 'Q')))),
    1: ('Image Structure', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'), ('NB','B'), ('NC', 'H'), ('NL', 'H'), ('Compression_Flag', 'B')))),
    2: ('Image Navigation', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'), ('Projection_Name','32s'), ('CFAC', 'I'), ('LFAC', 'I'), ('COFF', 'I'), ('LOFF', 'I')))),
    3: ('Image Data Function', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'), ('Data_Definition_Block', '%ss')))),
    4: ('Annotation', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'), ('Annotation_Text', '%ss')))),
    5: ('Time Stamp', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'), ('CDS_P_Field', 'B'), ('CDS_T_Field', '6s')))),
    6: ('Ancillary text', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'), ('Ancillary_Text','%ss')))),
    7: ('Key header', OrderedDict((('Header_Type', 'I'), ('Header_Record_Length', 'I'), ('Key_Number','I')))),
    128: ('Image Segment Identification', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'), ('Image_Segm_Seq_No','B'), ('Total_No_Image_Segm', 'B'), ('Line_No_Image_Segm', 'H')))),
    129: ('Encryption Key Message Header', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'),  ('Station_Number', 'H')))),
    130: ('Image Compensation Information Header', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'),  ('Image_Compensation_Information', '%ss')))),
    131: ('Image Observation Time Header', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'), ('Image_Observation_Time', '%ss')))),
    132: ('Image Quality Information Header', OrderedDict((('Header_Type', 'B'), ('Header_Record_Length', 'H'), ('Image_Quality_Information', '%ss'))))
}

class HRITHeader(object):
    """
        JMA mission specific Header Object.
        While the document mixes sometimes ambiguously/interchangeably to the concepts of Header and Record
        this module distinguishes them clearly. A HRIT Header consists of reader Records. While a Record can have a name that contains word Header
        it is still a record, respectively an dictionary.
        A header is therefore a sum of records, some of them general and some mission specific.
        Simple as that.

        The Header is dynamic, that is it can adapt and read Unknown records.
        At runtime te RECORDS dictionary controls the exact structure of each record.
        One can distinguish two


    """

    def __init__(self, buffer=None, byte_order=None):
        if buffer is None:
            raise ValueError, 'Can not create a Header object without a buffer'
        try:
            iter(buffer)
        except TypeError:
            raise TypeError, 'buffer argument is not iterable'
        if not isinstance(buffer, basestring):
            raise TypeError, 'buffer argument should be a string'
        if byte_order is None:
            raise ValueError, 'Can not create a Header object without knowing the byte order'

        htype_fmt = '%sB' % byte_order
        hlen_fmt = '%sH' % byte_order
        i = 0
        self.records = {}
        while i < len(buffer):
            #compute header type
            rec_type = struct.unpack(htype_fmt, buffer[i])[0]
            #compute record length
            rec_len_start = i + 1
            rec_len_end = rec_len_start + 2
            rec_len = struct.unpack(hlen_fmt,buffer[rec_len_start:rec_len_end])[0]
            rec_start = i
            rec_end = i + rec_len
            #extract the bytes corresponding to the record
            rec_buffer = buffer[rec_start:rec_end]

            #fetch the format and element names of the recpords, altough they are called headers they are records in the header.
            #I am following  strictly http://www.jma.go.jp/jma/jma-eng/satellite/introduction/4_2HRIT.pdf

            hitems = RECORDS.get(rec_type, ('UnknownHeader', OrderedDict([('Content', '%ss')])))
            hname, records = hitems
            #compute format string. because certain records have a variable length, the format string contains a format charater "%s"
            #the value of this format charater has to be computed dynamically and filled in
            fmt = '%s%s' % (byte_order, ''.join(records.values()))
            fchar = '%s'
            if fchar in fmt: # the records length is variable
                #get the  known part and variable part
                known_part, variable_part = fmt.split(fchar)
                #compute the size of the known part
                sz = struct.Struct(known_part).size
                #substract the  size of the known part from the record length to get the size of the variable part
                diff = rec_len - sz
                #compute the format string
                fmt = known_part + fchar % diff + variable_part

            rec_data = dict(zip(records.keys(), struct.unpack(fmt, rec_buffer)))

            #handle specifics
            #extract subsatellite point
            if rec_type == 2:
                proj_str = rec_data['Projection_Name'].strip()
                rec_data['SSP'] = float(proj_str.split('(')[1][:-1])
                rec_data['Projection_Name'] = proj_str
            #convert CDS_T_Field bytes into datetime according to CCSDS
            if rec_type == 5:
                t_field_buffer = rec_data['CDS_T_Field']
                days = struct.unpack('%sH'% byte_order, t_field_buffer[:2])[0]
                msecs = struct.unpack('%sI'% byte_order, t_field_buffer[2:])[0]
                rec_data['CDS_T_Field'] = datetime.datetime(1958, 1, 1) + datetime.timedelta(days=days, milliseconds=msecs)
            # store the COFFs and LOFFs into an array
            if rec_type == 130:
                data = rec_data['Image_Compensation_Information'].strip().split('\r')
                ic = np.zeros((len(data)/3), dtype=[('LINE', np.uint16), ('COFF', np.float32), ('LOFF', np.float32)])
                for j in range(0, len(data), 3):
                    linestr = data[j]
                    coffstr = data[j+1]
                    loffstr = data[j+2]
                    _line, lv = linestr.split(':=')
                    _coff, coffv = coffstr.split(':=')
                    _loff, loffv = loffstr.split(':=')
                    ic[j//3] = int(lv), float(coffv), float(loffv)

                rec_data['Image_Compensation_Information'] = ic
            if rec_type == 131:
                data = rec_data['Image_Observation_Time'].strip().split('\r')
                io = np.zeros((len(data)/2), dtype=[('LINE', np.uint16), ('TIME', np.float32)] )
                for j in range(0, len(data), 2):
                    linestr = data[j]
                    timestr = data[j + 1]
                    _line, lv = linestr.split(':=')
                    _time, timev = timestr.split(':=')
                    io[j//2] = int(lv),float(timev)

                rec_data['Image_Observation_Time'] = io

            #store the record data
            self.records[hname] = rec_data
            i += rec_len

    def __iter__(self):
        return iter(self.records.items())
    def __str__(self):

        return str(self.records)

class HRITSegment(object):
    """
        Represents a JMA HRIT Image segment.
        Consists of a header and data
    """
    byte_order = HRIT_BYTE_ORDER
    def __init__(self, fpath=None):
        """

        :param fpath, str, path to the :
        :return:
        """
        self._fpath = fpath
        f = open(self._fpath)
        #establish endiannes by extracting number of lines and cols and comparing with NLINES
        f.seek(20) #jump to byte 20 (size of primary header + Heaer type, record length and NB
        buf = f.read(2)
        #BIG endian
        nl = struct.unpack('%sH' % self.byte_order, buf)[0]

        if nl not in HRIT_IMAGE_NLINES:
            raise ValueError, '%s has wrong byte order. Expected big endian' % self.__class__.__name__
        #set pointer to byte 4, and read byte 5 to find out the total header length
        f.seek(4)
        self.header_length = struct.unpack('%sI' % self.byte_order, f.read(4))[0]
        #reset pointer
        f.seek(0)

        #1 create header
        self.header = HRITHeader(buffer=f.read(self.header_length), byte_order=self.byte_order)
        self.NL = self.header.records['Image Structure']['NL']
        self.NC = self.header.records['Image Structure']['NC']
        self.NB = self.header.records['Image Structure']['NB']
        self.SEG_NUM = self.header.records['Image Segment Identification']['Image_Segm_Seq_No']
        self.is_compressed = bool(self.header.records['Image Structure']['Compression_Flag'])

        self.ssp = self.header.records['Image Navigation']['SSP']
        self.CFAC = self.header.records['Image Navigation']['CFAC']
        self.LFAC = self.header.records['Image Navigation']['LFAC']
        self.COFF = self.header.records['Image Navigation']['COFF']
        self.LOFF = self.header.records['Image Navigation']['LOFF']



        self.shape = self.NL, self.NC


        self.size = self.NL*self.NC

        self._data = None

        f.close()

    @property
    def data(self):
        if self._data is None:
            self._data = np.zeros(self.shape, dtype=np.uint16)
            block = np.memmap(self._fpath, dtype='%su2' % self.byte_order, mode='r', offset=self.header_length,shape=self.shape)
            self._data = block.copy()
            del block
            return self._data
        else:
            return self._data




class JMAHRITLoader(GenericLoader):

    """Loader for JMA data"""



    def __init__(self, platform_name=None, channels=None, timeslot=None, files=None):
        #call the superclass constructor
        super(JMAHRITLoader, self).__init__(platform_name=platform_name, channels=channels, timeslot=timeslot, files=files)

    def _get_metadata(self):
        """
            Read the metadata from the header as per JMA mission specific LRIT/HRIT specs
        """
        #JMA specific attributes
        self.basename = self.files[0].split('/')[-1][:-4]
        self.segments = []
        self.NL = None
        self.NC = None
        self.NB = None
        self.SSP = None
        self.is_compressed = None
        self.seg_lines = []
        self.nsegs = 0
        ICOLINES = []
        COFFS = []
        LOFFS = []
        IOTLINES = []
        TIMES = []
        for f in  self.files:
            s = HRITSegment(fpath=f)
            seg_header = s.header
            self.CFAC = s.CFAC
            self.LFAC = s.CFAC
            self.COFF = s.COFF
            self.LOFF = s.LOFF
            if self.SSP is None:
                self.SSP = s.ssp
            else:
                if self.SSP != s.ssp:
                    raise ValueError, 'Invalid segment %s. SSP is not consistent %s, %s' % (f, self.SSP, s.ssp)

            if self.NC is None:
                self.NC = s.NC
            else:
                if self.NC != s.NC:
                    raise ValueError, 'Invalid segment %s. NC is not consistent %s, %s' % (f,self.NC, s.NC)
            if self.NL is None:
                self.NL = s.NL
            else:
                self.NL += s.NL
            if self.NB is None:
                self.NB = s.NB
            else:
                if self.NB != s.NB:
                    raise ValueError, 'Invalid segment %s. NB is not consistent %s, %s' % (f, self.NB, s.NB)
            self.nsegs+=1
            self.seg_lines.append(s.header.records['Image Segment Identification']['Line_No_Image_Segm'])
            self.segments.append(s)
            #avoid the last element because it is redundant. the next segment start with the next line
            ICOLINES += seg_header.records['Image Compensation Information Header']['Image_Compensation_Information']['LINE'].tolist()
            COFFS += seg_header.records['Image Compensation Information Header']['Image_Compensation_Information']['COFF'].tolist()
            LOFFS += seg_header.records['Image Compensation Information Header']['Image_Compensation_Information']['LOFF'].tolist()

            IOTLINES += seg_header.records['Image Observation Time Header']['Image_Observation_Time']['LINE'].tolist()[:-1]
            TIMES += seg_header.records['Image Observation Time Header']['Image_Observation_Time']['TIME'].tolist()[:-1]

        self.resolution = (HRIT_IMAGE_NLINES[0]/self.NC)*1000
        self.proj4_str = '+proj=geos +a=6378169.0 +b=6356583.8 +h=35785831.0 +lon_0=%.2f +units=m' % self.SSP

        t_ = self.basename.split('_')[1]
        self.scene_type = HRIT_SCENE_TYPES[t_[:4]]
        self.band = t_[4:]
        self.ICOLINES = np.array(ICOLINES, dtype=np.uint16)
        self.COFFS = np.array(COFFS, dtype=np.float32)
        self.LOFFS = np.array(LOFFS, dtype=np.float32)
        self.TIMES = np.array(TIMES, dtype=np.float32)
        self.IOTLINES = np.array(IOTLINES, dtype=np.uint16)
        self.size = self.NL*self.NC
        self.shape = self.NL, self.NC
        self._data = None
        if np.all(self.LOFF == self.LOFFS) and np.all(self.COFF == self.COFFS):
            self.is_shifted = False
        else:
            self.is_shifted = True

        self.ico_offsets = np.zeros(shape=(self.NL,), dtype=[('COFF',np.float32), ('LOFF', np.float32)])
        for i in range(self.ICOLINES.size-1):
            start, end = self.ICOLINES[i]-1, self.ICOLINES[i+1]-1
            if i == self.ICOLINES.size - 2:
                end +=1
            j=i+1
            step_l = end-start
            if step_l == 1:
                ratio = 0
            else:
                ratio = np.arange(step_l) / float(step_l - 1)
            self.ico_offsets['COFF'][start:end] = self.COFFS[i] + ratio * (self.COFFS[j] - self.COFFS[i])
            self.ico_offsets['LOFF'][start:end] = self.LOFFS[i] + ratio * (self.LOFFS[j] - self.LOFFS[i])
        #compose the calibration table
        cdata = self.segments[0].header.records['Image Data Function']['Data_Definition_Block'].strip().split('\r')
        sctable = []
        for e in cdata:
            n, v = e.split(':=')
            if '$' in n:
                pass
            else:
                try:
                    int(n)
                    sctable.append((int(n), v))
                except ValueError:
                    pass
        dt =[('count', np.int32), ('value', np.float32)]
        self.ctable = np.array(sctable, dtype=dt )
        max_ind = sctable[-1][0]
        self.calibration_table = np.zeros(max_ind+1, dtype=dt)
        self.calibration_table['count'][:] = np.arange(max_ind+1)

        #find the designated count index
        dup_mask = self.ctable['value'][1:] == self.ctable['value'][:-1]
        if self.ctable[dup_mask].size > 1 or self.ctable.size <3: # we are not able to fetch the designated count point for some reason so no calibration shall be performed
            self.ca_be_calibrated = False
            self.designated_point = None
        else:
            self.can_be_calibrated = True
            self.designated_point = self.ctable[dup_mask].item()
            #interpolate the calibration table
            self.calibration_table['value'] = np.interp(np.arange(max_ind+1),self.ctable['count'], self.ctable['value'])

        #mipp metadata

        mda = Metadata()
        mda.coff = self.COFF
        mda.loff = self.LOFF
        mda.cfac = self.CFAC
        mda.lfac = self.LFAC
        mda.shifted = self.is_shifted
        mda.number_of_columns = self.NC
        mda.number_of_lines = self.NL
        mda.timestamp = self.segments[0].header.records['Time Stamp']['CDS_T_Field']
        mda.number_of_segments = self.nsegs
        mda.proj4_str = self.proj4_str
        mda.projection = self.segments[0].header.records['Image Navigation']['Projection_Name']
        mda.xscale = self.resolution
        mda.yscale = self.resolution
        mda.sublon = self.SSP
        mda.calibration_unit = 'counts'
        mda.platform_name = 'Himawari_?'
        return mda

    def _read(self, rows, columns):
        """
            @rags:
                @rows, a slice object with start and stop for rows(axis0)
                @columns, a slice object with start and stop for cols(axis1)

        """
        #unpack the slices
        row_start, row_stop = rows.start, rows.stop
        col_start, col_stop = columns.start, columns.stop
        #need to collect the segments that are intersecting the area defined by the slices
        lines_in_segment = self.NL//self.nsegs

        ##compute the segment indices (start, stop) that needs to be collected
        start_seg, end_seg = int(np.ceil(float(row_start)//lines_in_segment)), int(np.ceil(float(row_stop)/lines_in_segment))

        #filter the segments
        filtered_segs = self.segments[start_seg:end_seg]
        #prepare soem metadata to compute the array size
        first_seg = filtered_segs[0]
        segnl, segnc,  = first_seg.NL, first_seg.NC
        segn = first_seg.SEG_NUM-1
        #allocate the array
        _data = np.zeros((segnl*len(filtered_segs), segnc), dtype='u2')
        for j, seg in enumerate(filtered_segs):
            seg_start_line = j*seg.NL
            seg_end_line = seg_start_line + seg.NL
            #push segment data into array
            _data[seg_start_line:seg_end_line,:] = seg.data
        #compute relative row indices because we have reduced  the space by filtering the segments
        rel_row_start, rel_row_stop = row_start-segnl*segn, row_stop-segn*segnl

        return _data[rel_row_start:rel_row_stop,col_start:col_stop]

    def load(self, area_extent=None, calibrate=1):
        """

        """
        if area_extent:
            col_start = int(round(area_extent[0] / self.mda.xscale + self.mda.coff + 0.5))
            row_stop = int(round(area_extent[1] / - self.mda.yscale + self.mda.loff - 0.5))
            col_stop = int(round(area_extent[2] / self.mda.xscale + self.mda.coff - 0.5))+1
            row_start = int(round(area_extent[3] / -self.mda.yscale + self.mda.loff + 0.5))+1
            rows = slice(row_start, row_stop)
            columns = slice(col_start, col_stop)
        else:
            rows = slice(self.mda.number_of_lines)
            columns = slice(self.mda.number_of_columns)

        data = self[rows, columns]
        return self.mda, data





if __name__ == '__main__':
    import glob
    import datetime
    #fp = '/home/jano/pytroll/data/IMG_DK01VIS_200703220030_001'
    fp = '/home/jano/pytroll/data/IMG_DK01VIS_200706010230_001'
    hrit_files = glob.glob(fp.replace('001', '*'))
    hf = JMAHRITLoader(files=hrit_files)
    #hf = JMAHRITLoader(satid='mtsat2', timeslot=datetime.datetime(2007, 03, 22, hour=00, minute=30 ))
    md, d = hf.load(area_extent=(-1987889.062, 185264.062, 203310.938, 4765664.062))
    print d.shape
    md, d = hf.load()
    print d.shape
    md, d = hf.load(area_extent=(-2661089,-2845580 , -2189189,-2484642))
    print d.shape
    md, d = hf.load(area_extent=(-3100607.812,1874039.062 , -2772257.812,2142576.562))
    print d.shape
    md, d = hf.load(area_extent=(-1051852,3116321 , 579034,4363721))
    print d.shape
    #print md
    print d.shape
    from pylab import imshow, show
    imshow(d, cmap='gray', interpolation='nearest')
    show()