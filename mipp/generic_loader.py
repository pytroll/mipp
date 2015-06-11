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
from mipp import satellite_config
import logging
logger = logging.getLogger('mipp')

PPP_CFG_VARNAME = 'PPP_CONFIG_DIR'


class GenericLoader(object):

    """ Generic loader for geostationary satellites
    """

    def __init__(self, platform_name=None, channels=None, timeslot=None, files=None):
        """ Locate files and read metadata.
            There
        """
        #self.channels = channels
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
                if platform_name is None:
                    raise ValueError(
                        'platform_name argument can not be omitted or be None')
                # get the config

                # Note: use trollsift (in new satellite config files) ? YES

                config = satellite_config.read_config(platform_name)

                # some confusion exists about the levels in the config file
                # it seeme level1 corresponds to mipp and level2 corresponds to mpop. when reaodin data from mipp level 1 is used when reading data from
                # mpop level 2 is used. unde the hood mpop uses mpip so this
                # all ends in mipp
                level = [e for e in config.sections if 'level1' in e][0]
                cfg_level1 = config(level)
                data_dir = cfg_level1['dir']
                filename = cfg_level1['filename']
                files = []
                d={}
                if channels:
                    for channel in channels:
                        chn = config.channels.get(channel, None)
                        if chn:
                            d['channel'] = channel
                            patt = os.path.join(data_dir, timeslot.strftime(filename) % d)
                            files+= glob.glob(patt)
                else:
                    d['channel'] = '*'
                    patt = os.path.join(data_dir, timeslot.strftime(filename) % d)
                    files+= glob.glob(patt)

                # 2 filter the files for this specific date
                # set the files attribute
                self.image_files = files

            else:
                raise IOError("Either files or timeslot needs to be provided!")
        self.mda = self._get_metadata()

    def __getitem__(self, item):
        """
            slicing
            @args:
                @item, a tuple fof 2 slices, one slice
        """
        # full disc and square
        allrows = slice(0, self.mda.number_of_lines)  # !!!
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

        return self._read(rows, columns)

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
    tslot = datetime(2007, 06, 01, hour=02, minute=30 )
    #this = GenericLoader(platform_name='Meteosat-9', timeslot=tslot)
    this = GenericLoader(platform_name='Himawari-7', timeslot=tslot, )
