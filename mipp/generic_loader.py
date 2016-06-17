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
import glob
import numpy as np
import logging

LOG = logging.getLogger(__name__)

from mipp import satellite_config

PPP_CFG_VARNAME = 'PPP_CONFIG_DIR'


class GenericLoader(object):

    """ Generic loader for geostationary satellites
    """

    def __init__(self, platform_name=None, channels=None, timeslot=None, files=None):
        """ Locate files and read metadata.
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
                self.files = sorted(self._get_files(platform_name, channels, timeslot))
            else:
                raise IOError("Either files or timeslot needs to be provided!")
        self.mda = self._get_metadata()

    def __getitem__(self, item):
        """Slicing
        @args:
        @item, a tuple (or not) for two, one or zero slices
        """
        do_mask = True
        rows, columns = self._item_to_slice(item)

        try:
            #
            # To specific (for msg_hrit)
            # This should go into a general methode, which is overwritten in the
            # specific loader
            #
            # *_handle_rotation*
            #
            ns_, ew_ = self.mda.first_pixel.split()
            # Rotated image ?
            LOG.info("Rotating image")
            if ns_ == 'south':
                rows = slice(self.mda.number_of_lines - rows.stop,
                             self.mda.number_of_lines - rows.start)
                if ew_ == 'east':
                    columns = slice(self.mda.number_of_columns - columns.stop,
                                    self.mda.number_of_columns - columns.start)
                rows, columns = self._item_to_slice((rows, columns))
        except AttributeError:
            pass

        if not hasattr(self.mda, "boundaries"):
            img = self._read(rows, columns)

        else:
            #
            # To specific (for msg_hrit)
            # This should go into a general methode, which is overwritten in the
            # specific loader
            #
            # *_handle_boundaries*
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
                    img = (np.zeros((rows.stop - rows.start, columns.stop - columns.start),
                                    dtype=rdata.dtype)
                           + self.mda.no_data_value)
                    if do_mask:
                        img = np.ma.masked_all_like(img)

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
            LOG.warning("Produced no image")
            return None, None

        #
        # Update meta-data
        #
        self.mda.area_extent = np.array(
            self._slice2extent(rows, columns, rotated=True), dtype=np.float64)

        if ((rows != slice(0, self.mda.number_of_columns)) or
            (columns != slice(0, self.mda.number_of_columns))):
            self.mda.region_name = 'sliced'

        self.mda.number_of_lines = img.shape[0]
        self.mda_number_of_coloumns = img.shape[1]
        self.mda.image_size = np.array([self.mda.number_of_columns, self.mda.number_of_lines])

        # return metadata and image
        return self.mda, img

    def _item_to_slice(self, item):
        """Transform item into slice object(s)
        """

        # full disc and square
        allrows = slice(0, self.mda.number_of_columns)  # !!!
        allcolumns = slice(0, self.mda.number_of_columns)

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
                raise IndexError("can only handle two indexes, not %d" % len(item))
        elif item is None:
            # full disc
            rows, columns = allrows, allcolumns
        else:
            raise IndexError("don't understand the indexes")

        # take care of [:]
        if rows.start is None:
            rows = allrows
        if columns.start is None:
            columns = allcolumns

        if ((rows.step != 1 and rows.step is not None) or
            (columns.step != 1 and columns.step is not None)):
            raise IndexError("Currently we don't support steps different from one")

        return rows, columns

    def _get_files(self, platform_name, channels, timeslot):
        # Get list of files from the timeslot
        # 1 read config
        ####
        if PPP_CFG_VARNAME not in os.environ.keys():
            raise RuntimeError(
                'Could not find the pytroll config directory environmet variable "%s" ' % (PPP_CFG_VARNAME))
        if platform_name is None:
            raise ValueError(
                'platform_name argument can not be omitted or be None')
        # get the config

        # Note: use trollsift (in new satellite config files) ? YES

        config = satellite_config.read_config(platform_name)

        # some confusion exists about the levels in the config file
        # it seems level1 corresponds to mipp and level2 corresponds to mpop.
        # when reaodin data from mipp level 1 is used when reading data from
        # mpop level 2 is used. unde the hood mpop uses mpip so this
        # all ends in mipp
        level = [e for e in config.sections if 'level1' in e][0]
        cfg_level1 = config(level)
        data_dir = cfg_level1['dir']
        filename = cfg_level1['filename']
        files = []
        d = {}
        if channels:
            for channel in channels:
                chn = config.channels.get(channel, None)
                if chn:
                    d['channel'] = channel
                    patt = os.path.join(data_dir, timeslot.strftime(filename) % d)
                    files += glob.glob(patt)
        else:
            d['channel'] = '*'
            patt = os.path.join(data_dir, timeslot.strftime(filename) % d)
            files += glob.glob(patt)

        # 2 filter the files for this specific date
        # set the files attribute
        return files

    def _read(self, rows, columns):
        """
            read data, specific to format
        """
        raise NotImplementedError('Subclasses should implementet this method!')

    def load(self, area_extent=None, calibrate=1):
        """Specific loader will overwrite this
        """
        raise NotImplementedError('Subclasses should implementet this method!')


if __name__ == "__main__":

    from datetime import datetime
    #tslot = datetime(2010, 10, 11, 14, 0)
    tslot = datetime(2007, 06, 01, hour=02, minute=30)
    #this = GenericLoader(platform_name='Meteosat-9', timeslot=tslot)
    this = GenericLoader(platform_name='Himawari-7', timeslot=tslot, )
