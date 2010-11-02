#
# $id$
#
# Inspired by NWCLIB
#
import numpy
import types
import copy

import xrit
import xrit.convert
from xrit import logger

__all__ = ['ImageLoader',]

class _Region(object):
    def __init__(self, rows, columns):
        self.rows = rows
        self.columns = columns
        self.shape = (rows.stop - rows.start, columns.stop - columns.start)
    def __str__(self):
        return 'rows:%s, columns:%s'%(str(self.rows), str(self.columns))

def _null_converter(blob):
    return blob
        
class ImageLoader(object):
    
    def __init__(self, mda, image_files, mask=False, calibrate=False):
        self.mda = copy.copy(mda)
        self.image_files = image_files
        self.do_mask = mask        
        self.do_calibrate = calibrate
        # full disc and square
        self._allrows = slice(0, self.mda.image_size[0]) # !!!
        self._allcolumns = slice(0, self.mda.image_size[0])        
        self.region = _Region(self._allrows, self._allcolumns)

    def __getitem__(self, item):
        if isinstance(item, slice):
            # specify rows and all columns
            rows, columns = item, self._allcolumns
        elif isinstance(item, int):
            # specify one row and all columns
            rows, columns = slice(item, item + 1), self._allcolumns
        elif isinstance(item, tuple):
            # both row and column are specified 
            if len(item) != 2:
                raise IndexError("too many indexes")
            rows, columns = item
            if isinstance(rows, int):
                rows = slice(item[0], item[0] + 1)
            if isinstance(columns, int):
                columns = slice(item[1], item[1] + 1)
        else:
            raise IndexError("don't understand the indexes")

        # take care of [:]
        if rows.start == None:
            rows = self._allrows
        if columns.start == None:
            columns = self._allcolumns
            
        if (rows.step != 1 and rows.step != None) or \
               (columns.step != 1 and columns.step != None):
            raise IndexError("Currently we don't support steps different from one")
        

        ns_ = self.mda.first_pixel.split()[0]
        ew_ = self.mda.first_pixel.split()[1]

        if not hasattr(self.mda, "boundaries"):
            mda, image = self._read(_Region(rows, columns))

        else:
            #
            # Here we handle the case of partly defined channels.
            # (for example MSG's HRV channel)
            #
            image = None

            offset = 0
            offset_position = 0

            for region in (self.mda.boundaries - 1):
                offset += region[0] - offset_position
                offset_position = region[1] + 1

                rlines = slice(region[0], region[1] + 1)
                rcols = slice(region[2], region[3] + 1)

                # check is we are outside the region
                if (rows.start > rlines.stop or
                    rows.stop < rlines.start or
                    columns.start > rcols.stop or
                    columns.stop < rcols.start):
                    continue

                lines = slice(max(rows.start, rlines.start) - offset,
                              min(rows.stop, rlines.stop) - offset)
                cols =  slice(max(columns.start, rcols.start) - rcols.start,
                              min(columns.stop, rcols.stop) - rcols.start)
                mda, rdata = self._read(_Region(lines, cols))
                lines = slice(max(rows.start, rlines.start) - rows.start,
                              min(rows.stop, rlines.stop) - rows.start)
                cols =  slice(max(columns.start, rcols.start) - columns.start,
                              min(columns.stop, rcols.stop) - columns.start)
                if image is None:
                    image = (numpy.zeros((rows.stop - rows.start,
                                          columns.stop - columns.start),
                                         dtype=rdata.dtype)
                             + mda.no_data_value)
                    if self.do_mask:
                        image = numpy.ma.array(image)

                if ns_ == "south":
                    lines = slice(image.shape[0] - lines.stop,
                                  image.shape[0] - lines.start)
                if ew_ == "east":
                    cols = slice(image.shape[1] - cols.stop,
                                 image.shape[1] - cols.start)

                image[lines, cols] = rdata

        #
        # Update meta-data
        #

        if (rows != self._allrows) or (columns != self._allcolumns):
            mda.region_name = 'sliced'

        mda.image_size = numpy.array([image.shape[1], image.shape[0]])
        mda.navigation.loff -= rows.start
        mda.navigation.coff -= columns.start
        if ew_ == "east":
            # rotate 180 degrees
            mda.navigation.loff = mda.image_size[1] - mda.navigation.loff
            mda.navigation.coff = mda.image_size[0] - mda.navigation.coff
            mda.navigation.cfac *= -1
            mda.navigation.lfac *= -1

        #
        # New center
        #
        try:
            mda.center = mda.navigation.lonlat((mda.image_size[0]//2,
                                                mda.image_size[1]//2))
        except xrit.NavigationError:
            # this is OK, but maybe not expected
            logger.warning("Image slice center is outside earth disc")
            mda.center = None


        delattr(mda, 'line_offset')
        delattr(mda, 'first_pixel')

        return mda, image
    
    def __call__(self, center=None, size=None):
        if center and size:
            try:
                px = self.mda.navigation.pixel(center)
            except xrit.NavigationError:
                raise xrit.SatReaderError("center for slice is outside image")
            columns = slice(px[0] - (size[0]+1)//2, px[0] + (size[0]+1)//2)
            rows = slice(px[1] - (size[1]+1)//2, px[1] + (size[1]+1)//2)
        elif bool(center) ^ bool(size):
            raise xrit.SatReaderError("when slicing, if center or size are"
                                      " specified, both has to be specified"
                                      " ... please")
        else:
            rows = self._allrows
            columns = self._allcolumns

        return self[rows, columns]


    def _read(self, region):
        if (region.columns.start < 0 or
            region.columns.stop > self.mda.image_size[0] or
            region.rows.start < 0 or
            region.rows.stop > self.mda.image_size[1]):
            raise IndexError("index out of range")
            
        mda = self.mda
        image_files = self.image_files
        
        #
        # Order segments
        #
        segments = {}
        nlines = 0
        for f in image_files:
            s = xrit.read_imagedata(f)
            segments[s.segment.seg_no] = f
            nlines += s.structure.nl
        start_seg_no = s.segment.planned_start_seg_no
        end_seg_no = s.segment.planned_end_seg_no
        ncols =  s.structure.nc
        segment_nlines = s.structure.nl

        #
        # Data type
        #
        converter = _null_converter
        if mda.data_type == 8:        
            data_type = numpy.uint8
            data_type_len = 8
        elif mda.data_type == 10:
            converter = xrit.convert.dec10216
            data_type = numpy.uint16
            data_type_len = 16
        elif mda.data_type == 16:
            data_type = numpy.uint16
            data_type_len = 16
        else:
            raise xrit.SatReaderError("unknown data type: %d bit per pixel"
                                      %mda.data_type)
        mda.data_type = data_type_len

        #
        # Calculate initial and final line and column.
        # The interface 'load(..., center, size)' will produce
        # correct values relative to the image orientation. 
        # line_init, line_end : 1-based
        #
        line_init = region.rows.start + 1
        line_end = line_init + region.rows.stop - region.rows.start - 1
        col_count = region.shape[1]
        col_offset = (region.columns.start)*data_type_len//8

        #
        # Calculate initial and final segments
        # depending on the image orientation.
        # seg_init, seg_end : 1-based.
        #
        seg_init = ((line_init-1)//segment_nlines) + 1
        seg_end = ((line_end-1)//segment_nlines) + 1

        #
        # Calculate initial line in image, line increment
        # offset for columns and factor for columns,
        # and factor for columns, depending on the image
        # orientation
        #
        if mda.first_pixel == 'north west':
            first_line = 0
            increment_line = 1
            factor_col = 1
        elif mda.first_pixel == 'north east':
            first_line = 0
            increment_line = 1
            factor_col = -1
        elif mda.first_pixel == 'south west':
            first_line = region.shape[0] - 1
            increment_line = -1
            factor_col = 1
        elif mda.first_pixel == 'south east':
            first_line = region.shape[0] - 1
            increment_line = -1
            factor_col = -1
        else:
            raise xrit.SatReaderError("unknown geographical orientation of "
                                      "first pixel: '%s'"%mda.first_pixel)

        #
        # Generate final image with no data
        #
        image = numpy.zeros(region.shape, dtype=data_type) + mda.no_data_value
    
        #
        # Begin the segment processing.
        #
        seg_no = seg_init
        line_in_image = first_line
        while seg_no <= seg_end:
            line_in_segment = 1
      
            #
            # Calculate initial line in actual segment.
            #
            if seg_no == seg_init:
                init_line_in_segment = (line_init
                                        - (segment_nlines*(seg_init - 1)))
            else:
                init_line_in_segment = 1

            #
            # Calculate final line in actual segment.
            #
            if seg_no == seg_end:
                end_line_in_segment = line_end - (segment_nlines*(seg_end - 1))
            else:
                end_line_in_segment = segment_nlines

            #
            # Open segment file.
            #
            seg_file = segments.get(seg_no, None)
            if not seg_file:
                #
                # No data for this segment.
                #
                logger.warning("Segment number %d not found"%seg_no)

                # all image lines are already set to no-data count.
                line_in_segment = init_line_in_segment
                while line_in_segment <= end_line_in_segment:
                    line_in_segment += 1
                    line_in_image += increment_line
            else:
                #
                # Data for this segment.
                #
                seg = xrit.read_imagedata(seg_file)
            
                #
                # Skip lines not processed.
                #
                while line_in_segment < init_line_in_segment:
                    line = seg.readline()
                    line_in_segment += 1

                #
                # Reading and processing segment lines.
                #
                while line_in_segment <= end_line_in_segment:
                    line = seg.readline()[mda.line_offset:]
                    line = converter(line)

                    line = (numpy.frombuffer(line,
                                             dtype=data_type,
                                             count=col_count,
                                             offset=col_offset)[::factor_col])
                
                    #
                    # Insert image data.
                    #
                    image[line_in_image] = line
                
                    line_in_segment += 1
                    line_in_image += increment_line
            
                seg.close()

            seg_no += 1

        #
        # Calibrate ?
        #
        mda.is_calibrated = False
        if self.do_calibrate:
            # do this before masking.
            calibrate = self.do_calibrate
            if type(calibrate) == types.BooleanType:
                # allow boolean True/False for 1/0
                calibrate = int(calibrate)
            image = mda.calibrate(image, calibrate=calibrate)
            mda.is_calibrated = True

        #
        # With or without mask ?
        #
        if self.do_mask:
            image = numpy.ma.masked_equal(image,
                                          mda.no_data_value,
                                          copy=False)
        return mda, image

