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

    def __init__(self, satid, channels=None, timeslot=None, files=None):
        """ Locate files and read metadata.
            There
        """

        self.image = None
        if files is not None:
            try:
                files[0]
            except TypeError:
                raise TypeError('Files argument has to be an iterable containing string elements representing full path to HRIT files')
            self.files = files

        else:

            if timeslot:
                # Get list of files from the timeslot
                #1 read config
                ####
                if not PPP_CFG_VARNAME in os.environ.keys():
                    raise RuntimeError('Could not find the pytroll config directory environmet variable "%s" ' % (PPP_CFG_VARNAME))
                if satid is None:
                    raise ValueError('satid argument can not be omitted or be None')
                #get the mtsat config
                mtsat_cfg = cfg.read_config(satid)
                #some confusin exists about the levels in the config file
                #it seeme level1 corresponds to mipp and level2 corresponds to mpop. when reaodin data from mipp level 1 is used when reading data from
                #mpop level 2 is used. unde the hood mpop uses mpip so this all ends in mipp
                data_level = [e for e in mtsat_cfg.sections if 'level1' in e][0]
                cfg_level = mtsat_cfg(data_level)
                data_dir = cfg_level['dir']
                filename = cfg_level['filename']
                print filename


                #2 filter the files for this specific date
                # set the files attribute

            else:
                raise IOError("Either files or timeslot needs to be provided!")
        self.mda = self._get_metadata()
    def __getitem__(self, slice):
        pass

    def load(self, area_extent=None, channels=None, calibrate="1"):
        self._channels = channels
        self.mda.area_extent = area_extent
        return self.__getitem__(self._get_slice_obj())

    def _get_slice_obj(self):
        """ Get code from loader.py
        """
        pass

    def _get_metadata(self):
        pass
