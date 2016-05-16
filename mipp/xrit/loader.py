#
# $id$
#
# Inspired by NWCLIB
#
import numpy
import types
import copy

import logging
logger = logging.getLogger('mipp')

import mipp
from mipp.xrit import _xrit, convert

__all__ = ['ImageLoader']

def _null_converter(blob):
    return blob

class ImageLoader(object):
    
    def __init__(self, mda, image_files, mask=False, calibrate=False):
        self.mda = mda
        self.image_files = image_files
        self.do_mask = mask        
        self.do_calibrate = calibrate
        # full disc and square
        self._allrows = slice(0, self.mda.image_size[0]) # !!!
        self._allcolumns = slice(0, self.mda.image_size[0])        

    def raw_slicing(self, item):
        """Raw slicing, no rotation of image.
        """
        # All data reading should end up here.

        # Don't mess with callers metadata.
        mda = copy.copy(self.mda)
        rows, columns = self._handle_item(item)

        ns_, ew_ = mda.first_pixel.split()

        if not hasattr(mda, "boundaries"):
            image = self._read(rows, columns, mda)

        else:
            #
            # Here we handle the case of partly defined channels.
            # (for example MSG's HRV channel)
            #
            image = None

            for region in (mda.boundaries - 1):
                rlines = slice(region[0], region[1] + 1)
                rcols = slice(region[2], region[3] + 1)

                # check is we are outside the region
                if (rows.start > rlines.stop or
                    rows.stop < rlines.start or
                    columns.start > rcols.stop or
                    columns.stop < rcols.start):
                    continue

                lines = slice(max(rows.start, rlines.start),
                              min(rows.stop, rlines.stop))
                cols =  slice(max(columns.start, rcols.start) - rcols.start,
                              min(columns.stop, rcols.stop) - rcols.start)
                rdata = self._read(lines, cols, mda)
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
                        image = numpy.ma.masked_all_like(image)

                if ns_ == "south":
                    lines = slice(image.shape[0] - lines.stop,
                                  image.shape[0] - lines.start)
                if ew_ == "east":
                    cols = slice(image.shape[1] - cols.stop,
                                 image.shape[1] - cols.start)
                if self.do_mask:
                    image.mask[lines, cols] = rdata.mask
                image[lines, cols] = rdata

        if not hasattr(image, 'shape'):
            logger.warning("Produced no image")
            return None, None

        #
        # Update meta-data
        #
        mda.area_extent = numpy.array(self._slice2extent(rows, columns, rotated=True), dtype=numpy.float64)

        if (rows != self._allrows) or (columns != self._allcolumns):
            mda.region_name = 'sliced'

        mda.data_type = 8*image.itemsize
        mda.image_size = numpy.array([image.shape[1], image.shape[0]])

        return mipp.mda.mslice(mda), image
    
    def __getitem__(self, item):
        """Default slicing, handles rotated images.
        """
        rows, columns = self._handle_item(item)
        ns_, ew_ = self.mda.first_pixel.split()
        if ns_ == 'south':
            rows = slice(self.mda.image_size[1] - rows.stop,
                         self.mda.image_size[1] - rows.start)
        if ew_ == 'east':
            columns = slice(self.mda.image_size[0] - columns.stop,
                            self.mda.image_size[0] - columns.start)
        return self.raw_slicing((rows, columns))

    def __call__(self, area_extent=None):
        """Slice according to (ll_x, ll_y, ur_x, ur_y) or read full disc.
        """
        if area_extent == None:
            # full disc
            return self[:]
            
        # slice
        area_extent = tuple(area_extent)
        if len(area_extent) != 4:
            raise TypeError, "optional argument must be an area_extent"

        ns_, ew_ = self.mda.first_pixel.split()

        if ns_ == "south":
            loff = self.mda.image_size[0] - self.mda.loff - 1
        else:
            loff = self.mda.loff - 1

        if ew_ == "east":
            coff = self.mda.image_size[1] - self.mda.coff - 1
        else:
            coff = self.mda.coff - 1

            
        row_size = self.mda.pixel_size[0]
        col_size = self.mda.pixel_size[1]

        logger.debug('area_extent: %.2f, %.2f, %.2f, %.2f'%tuple(area_extent))
        logger.debug('area_extent: resolution %.2f, %.2f'%(row_size, col_size))
        logger.debug('area_extent: loff, coff %d, %d'%(loff, coff))
        logger.debug('area_extent: expected size %d, %d'%\
                         (int(numpy.round((area_extent[2] - area_extent[0])/col_size)),\
                         int(numpy.round((area_extent[3] - area_extent[1])/row_size))))
        
        col_start = int(numpy.round(area_extent[0] / col_size + coff + 0.5))
        row_stop = int(numpy.round(area_extent[1] / -row_size + loff - 0.5))
        col_stop = int(numpy.round(area_extent[2] / col_size + coff - 0.5))
        row_start = int(numpy.round(area_extent[3] / -row_size + loff + 0.5))

        row_stop += 1
        col_stop += 1

        logger.debug('area_extent: computed size %d, %d'%(col_stop - col_start, row_stop - row_start))

        return self[row_start:row_stop, col_start:col_stop]

    def _handle_item(self, item):
        """Transform item into slice(s).
        """
        if isinstance(item, slice):
            # specify rows and all columns
            rows, columns = item, self._allcolumns
        elif isinstance(item, int):
            # specify one row and all columns
            rows, columns = slice(item, item + 1), self._allcolumns
        elif isinstance(item, tuple):
            if len(item) == 2:
                # both row and column are specified 
                rows, columns = item
                if isinstance(rows, int):
                    rows = slice(item[0], item[0] + 1)
                if isinstance(columns, int):
                    columns = slice(item[1], item[1] + 1)
            else:
                raise IndexError, "can only handle two indexes, not %d"%len(item)
        elif item is None:
            # full disc
            rows, columns = self._allrows, self._allcolumns            
        else:
            raise IndexError, "don't understand the indexes"

        # take care of [:]
        if rows.start == None:
            rows = self._allrows
        if columns.start == None:
            columns = self._allcolumns
            
        if (rows.step != 1 and rows.step != None) or \
               (columns.step != 1 and columns.step != None):
            raise IndexError, "Currently we don't support steps different from one"

        return rows, columns

    def _slice2extent(self, rows, columns, rotated=True):
        """ Calculate area extent.
        If rotated=True then rows and columns are reflecting the actual rows and columns.
        """
        ns_, ew_ = self.mda.first_pixel.split()

        loff = self.mda.loff
        coff = self.mda.coff
        if ns_ == "south":
            loff = self.mda.image_size[0] - loff - 1
            if rotated:
                rows = slice(self.mda.image_size[1] - rows.stop,
                             self.mda.image_size[1] - rows.start)
        else:
            loff -= 1
        if ew_ == "east":
            coff = self.mda.image_size[1] - coff - 1
            if rotated:
                columns = slice(self.mda.image_size[0] - columns.stop,
                                self.mda.image_size[0] - columns.start)
        else:
            coff -= 1

        logger.debug('slice2extent: size %d, %d'% \
                         (columns.stop - columns.start, rows.stop - rows.start))
        rows = slice(rows.start, rows.stop - 1)
        columns = slice(columns.start, columns.stop - 1)

        row_size = self.mda.pixel_size[0]
        col_size = self.mda.pixel_size[1]
      
        ll_x = (columns.start - coff - 0.5)*col_size
        ll_y = -(rows.stop - loff + 0.5)*row_size
        ur_x = (columns.stop - coff + 0.5)*col_size
        ur_y = -(rows.start - loff - 0.5)*row_size

        logger.debug('slice2extent: computed extent %.2f, %.2f, %.2f, %.2f'% \
                         (ll_x, ll_y, ur_x, ur_y))
        logger.debug('slice2extent: computed size %d, %d'% \
                         (int(numpy.round((ur_x - ll_x)/col_size)), \
                              int(numpy.round((ur_y - ll_y)/row_size))))

        return [ll_x, ll_y, ur_x, ur_y]

    def _read(self, rows, columns, mda):
        shape = (rows.stop - rows.start, columns.stop - columns.start)
        if (columns.start < 0 or
            columns.stop > mda.image_size[0] or
            rows.start < 0 or
            rows.stop > mda.image_size[1]):
            raise IndexError, "index out of range"

        image_files = self.image_files
        
        #
        # Order segments
        #
        segments = {}
        for f in image_files:
            s = _xrit.read_imagedata(f)
            segments[s.segment.seg_no] = f
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
            converter = convert.dec10216
            data_type = numpy.uint16
            data_type_len = 16
        elif mda.data_type == 16:
            data_type = numpy.uint16
            data_type_len = 16
        elif mda.data_type == -16:
            data_type = '>u2'
            data_type_len = 16
        else:
            raise mipp.ReaderError, "unknown data type: %d bit per pixel"\
                %mda.data_type

        #
        # Calculate initial and final line and column.
        # The interface 'load(..., center, size)' will produce
        # correct values relative to the image orientation. 
        # line_init, line_end : 1-based
        #
        line_init = rows.start + 1
        line_end = line_init + rows.stop - rows.start - 1
        col_count = shape[1]
        col_offset = (columns.start)*data_type_len//8

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
            first_line = shape[0] - 1
            increment_line = -1
            factor_col = 1
        elif mda.first_pixel == 'south east':
            first_line = shape[0] - 1
            increment_line = -1
            factor_col = -1
        else:
            raise mipp.ReaderError, "unknown geographical orientation of " + \
                "first pixel: '%s'"%mda.first_pixel

        #
        # Generate final image with no data
        #
        image = numpy.zeros(shape, dtype=data_type) + mda.no_data_value
    
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
                logger.info("Read %s"%seg_file)
                seg = _xrit.read_imagedata(seg_file)
            
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
        # Compute mask before calibration
        #

        mask = (image == mda.no_data_value)

        #
        # Calibrate ?
        #
        mda.is_calibrated = False
        if self.do_calibrate:
            # do this before masking.
            calibrate = self.do_calibrate
            if isinstance(calibrate, bool):
                # allow boolean True/False for 1/0
                calibrate = int(calibrate)
            image, mda.calibration_unit = mda.calibrate(image, calibrate=calibrate)
            mda.is_calibrated = True
        else:
            mda.calibration_unit = ""

        #
        # With or without mask ?
        #
        if self.do_mask and not isinstance(image, numpy.ma.core.MaskedArray):
            image = numpy.ma.array(image, mask=mask, copy=False)
        elif ((not self.do_mask) and 
                isinstance(image, numpy.ma.core.MaskedArray)):
            image = image.filled(mda.no_data_value)
            
        return image

