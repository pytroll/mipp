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

import logging
logger = logging.getLogger('mipp')

import mipp
import mipp.cfg


class GenericLoader(object):

    """ Generic loader for geos satellites.
    """

    def __init__(self, satid, timeslot=None, files=None):
        """ Locate files and read metadata.
        """

        self.image = None
        if timeslot:
            # Get list of files from the timeslot
            #1 read config




            #2 filter the files for this specific date
            # set the files attribute

        elif files:
            self.files = files
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
