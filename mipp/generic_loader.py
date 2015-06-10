# -*- coding: utf-8 -*-
# Copyright (c) 2015

# Author(s):

#   Adam Dybbroe
#   Ioan Ferencik
#   Lars Orum Rasmussen

# This file is part of mipp.

# mipp is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# mipp is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with
# mipp.  If not, see <http://www.gnu.org/licenses/>.
"""
Replacing xrit.sat and xrit.loader
"""
import os

import numpy
import glob
import imp
import types
import re
from mipp import cfg
import logging
logger = logging.getLogger('mipp')

PPP_CFG_VARNAME = 'PPP_CONFIG_DIR'


class GenericLoader(object):

    """ Generic loader for geostationary satellites
    """

    def __init__(self, channels, satid=None, timeslot=None, files=None):
        """ Locate files and read metadata.
            There
        """
        self.channels = channels
        self.image = None
        if files is not None:
            try:
                files[0]
            except TypeError:
                raise TypeError(
                    'Files argument has to be an iterable containing string ' +
                    'elements representing full path to HRIT files')
            self.files = sorted(files)

        else:

            if timeslot:
                # Get list of files from the timeslot
                # 1 read config
                ####
                if not PPP_CFG_VARNAME in os.environ.keys():
                    raise RuntimeError(
                        'Could not find the pytroll config directory environmet variable "%s" ' % (PPP_CFG_VARNAME))
                if satid is None:
                    raise ValueError(
                        'satid argument can not be omitted or be None')
                # get the config

                # Note: use trollsift (in new satellite config files) ?
                
                config = cfg.read_config(satid)
                # some confusin exists about the levels in the config file
                # it seeme level1 corresponds to mipp and level2 corresponds to mpop. when reaodin data from mipp level 1 is used when reading data from
                # mpop level 2 is used. unde the hood mpop uses mpip so this
                # all ends in mipp
                level = [e for e in config.sections if 'level1' in e][0]
                cfg_level1 = config(level)
                print cfg_level1
                data_dir = cfg_level1['dir']
                filename = cfg_level1['filename']
                print filename

                # 2 filter the files for this specific date
                # set the files attribute

            else:
                raise IOError("Either files or timeslot needs to be provided!")
        self.image_filenames = self.files
        self.mda = self._get_metadata()

    def __getitem__(self, slice):
        #from mipp.xrit.loader import ImageLoader
        #return ImageLoader(self.mda, self.image_filenames).__getitem__(slice)
        print self.mda
        rows, columns = self._handle_slice(slice)
        img = self._read(rows, columns)

    def _handle_slice(self, item):
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
                raise IndexError, "can only handle two indexes, not %d" % len(
                    item)
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

    def _read(self, rows, columns):
        """Here we need the following metadata:

        .image_size
        .data_type (8, 10, 16 ...)
        .first_pixel
        .no_data_value
        .line_offset
        """
        shape = (rows.stop - rows.start, columns.stop - columns.start)
        if (columns.start < 0 or
                columns.stop > self.mda.image_size[0] or
                rows.start < 0 or
                rows.stop > self.mda.image_size[1]):
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
        ncols = s.structure.nc
        segment_nlines = s.structure.nl

        #
        # Data type
        #
        converter = _null_converter
        if self.mda.data_type == 8:
            data_type = numpy.uint8
            data_type_len = 8
        elif self.mda.data_type == 10:
            converter = convert.dec10216
            data_type = numpy.uint16
            data_type_len = 16
        elif self.mda.data_type == 16:
            data_type = numpy.uint16
            data_type_len = 16
        else:
            raise mipp.ReaderError, "unknown data type: %d bit per pixel"\
                % self.mda.data_type

        #
        # Calculate initial and final line and column.
        # The interface 'load(..., center, size)' will produce
        # correct values relative to the image orientation.
        # line_init, line_end : 1-based
        #
        line_init = rows.start + 1
        line_end = line_init + rows.stop - rows.start - 1
        col_count = shape[1]
        col_offset = (columns.start) * data_type_len // 8

        #
        # Calculate initial and final segments
        # depending on the image orientation.
        # seg_init, seg_end : 1-based.
        #
        seg_init = ((line_init - 1) // segment_nlines) + 1
        seg_end = ((line_end - 1) // segment_nlines) + 1

        #
        # Calculate initial line in image, line increment
        # offset for columns and factor for columns,
        # and factor for columns, depending on the image
        # orientation
        #
        if self.mda.first_pixel == 'north west':
            first_line = 0
            increment_line = 1
            factor_col = 1
        elif self.mda.first_pixel == 'north east':
            first_line = 0
            increment_line = 1
            factor_col = -1
        elif self.mda.first_pixel == 'south west':
            first_line = shape[0] - 1
            increment_line = -1
            factor_col = 1
        elif self.mda.first_pixel == 'south east':
            first_line = shape[0] - 1
            increment_line = -1
            factor_col = -1
        else:
            raise mipp.ReaderError, "unknown geographical orientation of " + \
                "first pixel: '%s'" % self.mda.first_pixel

        #
        # Generate final image with no data
        #
        image = numpy.zeros(shape, dtype=data_type) + self.mda.no_data_value

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
                                        - (segment_nlines * (seg_init - 1)))
            else:
                init_line_in_segment = 1

            #
            # Calculate final line in actual segment.
            #
            if seg_no == seg_end:
                end_line_in_segment = line_end - \
                    (segment_nlines * (seg_end - 1))
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
                logger.warning("Segment number %d not found" % seg_no)

                # all image lines are already set to no-data count.
                line_in_segment = init_line_in_segment
                while line_in_segment <= end_line_in_segment:
                    line_in_segment += 1
                    line_in_image += increment_line
            else:
                #
                # Data for this segment.
                #
                logger.info("Read %s" % seg_file)
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
                    line = seg.readline()[self.mda.line_offset:]
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

        mask = (image == self.mda.no_data_value)

        #
        # With or without mask ?
        #
        if self.do_mask and not isinstance(image, numpy.ma.core.MaskedArray):
            image = numpy.ma.array(image, mask=mask, copy=False)
        elif ((not self.do_mask) and
                isinstance(image, numpy.ma.core.MaskedArray)):
            image = image.filled(self.mda.no_data_value)

        return image

    def load(self, area_extent=None, calibrate=1):
        """Specific loader will overwrite this
        """
        pass
        #self.mda.area_extent = area_extent
        #return self.__getitem__(self._get_slice_obj())


    def _get_metadata(self):
        pass

