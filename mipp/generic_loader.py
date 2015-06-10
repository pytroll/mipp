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
        self.image_filenames = []

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
        self.mda = self._get_metadata()

    def __getitem__(self, item):
        """Default slicing, handles rotated images.
        """
        do_mask = True
        allrows = slice(0, self.mda.image_size[0])  # !!!
        allcolumns = slice(0, self.mda.image_size[0])


        # from mipp.xrit.loader import ImageLoader
        # return ImageLoader(self.mda, self.image_filenames).__getitem__(slice)
        rows, columns = self._handle_slice(item)
        ns_, ew_ = self.mda.first_pixel.split()
        if ns_ == 'south':
            rows = slice(self.mda.image_size[1] - rows.stop,
                         self.mda.image_size[1] - rows.start)
        if ew_ == 'east':
            columns = slice(self.mda.image_size[0] - columns.stop,
                            self.mda.image_size[0] - columns.start)

        rows, columns = self._handle_slice((rows, columns))
        if not hasattr(self.mda, "boundaries"):
            img = self._read(rows, columns)

        else:
            #
            # Here we handle the case of partly defined channels.
            # (for example MSG's HRV channel)
            #
            img = None

            for region in (self.mda.boundaries - 1):
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
                cols = slice(max(columns.start, rcols.start) - rcols.start,
                             min(columns.stop, rcols.stop) - rcols.start)
                rdata = self._read(lines, cols)
                lines = slice(max(rows.start, rlines.start) - rows.start,
                              min(rows.stop, rlines.stop) - rows.start)
                cols = slice(max(columns.start, rcols.start) - columns.start,
                             min(columns.stop, rcols.stop) - columns.start)
                if img is None:
                    img = (numpy.zeros((rows.stop - rows.start,
                                        columns.stop - columns.start),
                                       dtype=rdata.dtype)
                           + self.mda.no_data_value)
                    if do_mask:
                        img = numpy.ma.masked_all_like(img)

                if ns_ == "south":
                    lines = slice(img.shape[0] - lines.stop,
                                  img.shape[0] - lines.start)
                if ew_ == "east":
                    cols = slice(img.shape[1] - cols.stop,
                                 img.shape[1] - cols.start)
                if do_mask:
                    img.mask[lines, cols] = rdata.mask
                img[lines, cols] = rdata

        if not hasattr(img, 'shape'):
            logger.warning("Produced no image")
            return None, None

        #
        # Update meta-data
        #
        self.mda.area_extent = numpy.array(
            self._slice2extent(rows, columns, rotated=True), dtype=numpy.float64)

        if (rows != allrows) or (columns != allcolumns):
            self.mda.region_name = 'sliced'

        self.mda.image_size = numpy.array([img.shape[1], img.shape[0]])

        # return mipp.mda.mslice(mda), image
        return self.mda, img

    def _handle_slice(self, item):
        """Transform item into slice(s).
        """

        # full disc and square
        allrows = slice(0, self.mda.image_size[0])  # !!!
        allcolumns = slice(0, self.mda.image_size[0])

        if isinstance(item, slice):
            # specify rows and all columns
            rows, columns = item, allcolumns
        elif isinstance(item, int):
            # specify one row and all columns
            rows, columns = slice(item, item + 1), allcolumns
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
            rows, columns = allrows, allcolumns
        else:
            raise IndexError, "don't understand the indexes"

        # take care of [:]
        if rows.start == None:
            rows = allrows
        if columns.start == None:
            columns = allcolumns

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

        logger.debug('slice2extent: size %d, %d' %
                     (columns.stop - columns.start, rows.stop - rows.start))
        rows = slice(rows.start, rows.stop - 1)
        columns = slice(columns.start, columns.stop - 1)

        row_size = self.mda.xscale
        col_size = self.mda.yscale

        ll_x = (columns.start - coff - 0.5) * col_size
        ll_y = -(rows.stop - loff + 0.5) * row_size
        ur_x = (columns.stop - coff + 0.5) * col_size
        ur_y = -(rows.start - loff - 0.5) * row_size

        logger.debug('slice2extent: computed extent %.2f, %.2f, %.2f, %.2f' %
                     (ll_x, ll_y, ur_x, ur_y))
        logger.debug('slice2extent: computed size %d, %d' %
                     (int(numpy.round((ur_x - ll_x) / col_size)),
                      int(numpy.round((ur_y - ll_y) / row_size))))

        return [ll_x, ll_y, ur_x, ur_y]

    def load(self, area_extent=None, calibrate=1):
        """Specific loader will overwrite this
        """
        pass
        #self.mda.area_extent = area_extent
        # return self.__getitem__(self._get_slice_obj())

    def _get_metadata(self):
        pass
