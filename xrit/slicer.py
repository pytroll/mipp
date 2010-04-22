#
# $id$
#
# Inspired by NWCLIB
#
import numpy

import xrit
import xrit.convert
from xrit import logger

__all__ = ['ImageSlicer',]

class SatReaderError(Exception):
    pass

class _Region(object):
    def __init__(self, rows, columns):
        self.rows = rows
        self.columns = columns
        self.shape = (rows.stop - rows.start, columns.stop - columns.start)
    def __str__(self):
        return 'rows:%s, columns:%s'%(str(self.rows), str(self.columns))

def _null_converter(blob):
    return blob
        
class ImageSlicer(object):
    
    def __init__(self, mda, image_files, mask=False, calibrate=True):
        self.mda = mda
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
            raise xrit.SatReaderError("currently we don't support steps different from one")
        
        return self._read(_Region(rows, columns))
    
    def __call__(self, center=None, size=None):
        if center and size:
            try:
                px = self.mda.navigation.pixel(center)
            except xrit.NavigationError:
                raise xrit.SatReaderError("center for slice is outside image")                
            columns = slice(px[0] - (size[0]+1)//2, px[0] + (size[0]+1)//2)
            rows = slice(px[1] - (size[1]+1)//2, px[1] + (size[1]+1)//2)
        elif bool(center) ^ bool(size):
            raise xrit.SatReaderError("when slicing, both center and size has to be specified ... please")
        else:
            rows = self._allrows
            columns = self._allcolumns
            
        return self._read(_Region(rows, columns))

    def _read(self, region):
        if region.columns.start < 0 or region.columns.stop > self.mda.image_size[0] or \
               region.rows.start < 0 or region.rows.stop > self.mda.image_size[1]:
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
        elif mda.data_type == 10:
            converter = xrit.convert.dec10216
            data_type = numpy.uint16
            mda.data_type = 16
        elif mda.data_type == 16:
            data_type = numpy.uint16
        else:
            raise xrit.SatReaderError("unknown data type: %d bit per pixel"%mda.data_type)
        

        #
        # Calculate initial and final line and column.
        # The interface 'load(..., center, size)' will produce
        # correct values relative to the image orientation. 
        # line_init, line_end : 1-based
        #
        line_init = region.rows.start + 1
        line_end = line_init + region.rows.stop - region.rows.start - 1    
        col_count = region.shape[1]
        col_offset = (region.columns.start)*mda.data_type//8

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
            raise xrit.SatReaderError("unknown geographical orientation of first pixel: '%s'"%mda.first_pixel)
        
        #
        # Generate final image with no data
        #
        image = numpy.zeros(region.shape, dtype=data_type) + mda.no_data_value
    
        #
        # Begin the segment processing.
        #
        seg_no = seg_init
        line_in_image = first_line;
        while seg_no <= seg_end:
            line_in_segment = 1
      
            #
            # Calculate initial line in actual segment.
            #
            if seg_no == seg_init:
                init_line_in_segment = line_init - (segment_nlines*(seg_init - 1))
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
                line_in_segment = init_line_in_segment;
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
                
                    line = numpy.frombuffer(line, dtype=data_type, count=col_count, offset=col_offset)[::factor_col]
                
                    #
                    # Insert image data.
                    #
                    image[line_in_image] = line
                
                    line_in_segment += 1
                    line_in_image += increment_line
            
                seg.close()

            seg_no += 1

        #
        # Update meta-data
        #
        delattr(mda, 'line_offset')
        delattr(mda, 'first_pixel')
        mda.image_size = image.shape[1], image.shape[0]
        mda.navigation.loff -= region.rows.start
        mda.navigation.coff -= region.columns.start
        if factor_col == -1:
            # rotate 180 degrees
            mda.navigation.loff = mda.image_size[1] - mda.navigation.loff
            mda.navigation.coff = mda.image_size[0] - mda.navigation.coff
            mda.navigation.cfac *= -1
            mda.navigation.lfac *= -1

        #
        # New center
        #
        try:
            mda.center = mda.navigation.lonlat((mda.image_size[0]//2, mda.image_size[1]//2))
        except xrit.NavigationError:
            # this is OK, but maybe not expected
            logger.warning("Image slice center is outside earth disk")
            mda.center = None
        
        #
        # Calibrate ?
        #
        mda.calibrated = self.do_calibrate
        if self.do_calibrate:
            # do this before masking.
            image = self._calibrate(image)

        #
        # With ot without mask ?
        #
        if self.do_mask:
            image = numpy.ma.array(image, mask=(image == mda.no_data_value), copy=False)
            
        return mda, image

    def _calibrate(self, image):
        mda = self.mda
        mda.calibrated = False
        cal = mda.__dict__.pop('calibration_table', None)
    
        if cal == None or len(cal) == 0:
            return image
        if type(cal) != numpy.ndarray:
            cal = numpy.array(cal)

        if cal.shape == (256, 2):
            cal = cal[:,1] # nasty !!!
            cal[int(mda.no_data_value)] = mda.no_data_value
            image = cal[image] # this does not work on masked arrays !!!
        elif cal.shape ==(2, 2):
            scale = (cal[1][1] - cal[0][1])/(cal[1][0] - cal[0][0])
            offset = cal[0][1] - cal[0][0]*scale
            image = numpy.select([image == mda.no_data_value*scale], [mda.no_data_value], default=offset + image*scale)
        else:
            raise xrit.SatDecodeError("could not recognize the shape %s of the calibration table"%str(cal.shape))
        mda.calibrated = True
        return image
