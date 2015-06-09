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
        self.mda = self._get_metadata()
        self.image = None

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

    
    def __init__(self, config_reader):
        #
        # Read configuration file based on satellite name
        #
        sat = config_reader('satellite')
        projname = sat['projection'].lower()
        if not projname.startswith('geos'):
            raise mipp.ReaderError("currently we only support projections of type: 'GEOS'")

        #
        # Load format decoder based on level1 format
        #
        format = config_reader('level1')['format']
        try:
            pth = None
            for mod in format.split("/")[:-1]:
                pth = [imp.find_module(mod, pth)[1]]
            args = imp.find_module(format.split("/")[-1], pth)

        except ImportError, err:
            raise mipp.ReaderError(("unknown level-1 format: '%s'" % format)
                                   + "in " + str(pth) + "\n" + str(err))
        try:
            m = imp.load_module(format, *args)
        finally:
            if args[0]:
                args[0].close()

        self._metadata_reader = m.read_metadata

        #
        # Attributing
        #
        self.__dict__.update(sat)

        self._config_reader = config_reader
        self.satname = self.satname + self.number
        self.satnumber = self.number
        delattr(self, 'number')

        # backwards compatible
        if not hasattr(self, 'proj4_params'):
            try:
                sublon = float(projname.split('(')[1].split(')')[0])
            except (IndexError, ValueError):
                raise mipp.ReaderError("Could not determine sub satellite " +
                                       "point from projection name '%s'" %
                                       projname)
            self.proj4_params = "proj=geos lon_0=%.2f lat_0=0.00 a=6378169.00 b=6356583.80 h=35785831.00" % sublon

    def load(self, time_stamp, channel, **kwarg):
        if channel not in self._config_reader.channel_names:
            raise mipp.ReaderError("unknown channel name '%s'" % channel)
        opt = self._config_reader('level1')
        val = {}
        val["channel"] = channel + '*'

        # Prologue

        val["segment"] = "PRO".ljust(9, '_')

        filename_pro = opt.get('filename_pro', opt['filename'])
        prologue = glob.glob(
            time_stamp.strftime(os.path.join(opt['dir'], filename_pro)) % val)

        if not prologue:
            raise mipp.NoFiles("missing prologue file: '%s'" % (time_stamp.strftime(filename_pro) % val))
        prologue = prologue[0]

        # Regular channels

        val["segment"] = "0????????"
        image_files = glob.glob(
            time_stamp.strftime(os.path.join(opt['dir'], opt['filename'])) % val)
        if not image_files:
            raise mipp.NoFiles("no data files: '%s'" % (time_stamp.strftime(opt['filename']) % val))
        image_files.sort()

        # Check if the files are xrit-compressed, and decompress them
        # accordingly:
        decomp_files = decompress(image_files)

        logger.info("Read %s" % prologue)
        prologue = _xrit.read_prologue(prologue)

        # Epilogue

        val["segment"] = "EPI".ljust(9, '_')

        filename_epi = opt.get('filename_epi', opt['filename'])
        epilogue = glob.glob(
            time_stamp.strftime(os.path.join(opt['dir'], filename_epi)) % val)

        if not epilogue:
            logger.info("No epilogue file to read.")
        else:
            epilogue = epilogue[0]
            logger.info("Read %s" % epilogue)
            epilogue = _xrit.read_epilogue(epilogue)
            return self.load_files(prologue, decomp_files,
                                   epilogue=epilogue, **kwarg)

        return self.load_files(prologue, decomp_files, **kwarg)

    def load_files(self, prologue, image_files, only_metadata=False, **kwargs):
        image_files.sort()
        if only_metadata:
            return self._read_metadata(prologue, image_files, **kwargs)
        else:
            return self._read(prologue, image_files, **kwargs)

    def _read_metadata(self, prologue, image_files, epilogue=None):
        if epilogue:
            mda = self._metadata_reader(prologue, image_files, epilogue=epilogue)
        else:
            mda = self._metadata_reader(prologue, image_files)
        if "%.2f" % mda.sublon != "%.2f" % self.sublon:
            if CHECK_CONFIG_SUBLON:
                raise mipp.ReaderError("Sub satellite point in config file (%.2f) don't match data (%.2f)" %
                                       (self.sublon, mda.sublon))
            else:
                logger.warning("Modifying sub satellite point from %.2f to %.2f" %
                               (self.sublon, mda.sublon))
                self.sublon = mda.sublon

        try:
            self.satnumber = mda.satnumber
        except AttributeError:
            pass

        chn = self._config_reader.get_channel(mda.channel)
        if mda.image_size[0] != chn.size[0]:
            raise mipp.ReaderError("unknown image width for %s, %s: %d" %
                                   (self.satname, mda.channel, mda.image_size[0]))

        mda.pixel_size = numpy.array([chn.resolution, chn.resolution], dtype=numpy.float64)
        for k, v in self.__dict__.items():
            if k[0] != '_' and type(v) != types.FunctionType:
                setattr(mda, k, v)

        img = _xrit.read_imagedata(image_files[0])

        return mda

    def _read(self, prologue, image_files, epilogue=None, **kwargs):
        if epilogue:
            mda = self._read_metadata(prologue, image_files, epilogue=epilogue)
        else:
            mda = self._read_metadata(prologue, image_files)
        len_img = (((mda.image_size[0] + mda.line_offset) * mda.image_size[1]) * mda.data_type) // 8
        logger.info("Data size: %dx%d pixels, %d bytes, %d bits per pixel",
                    mda.image_size[0], mda.image_size[1], len_img, mda.data_type)

        #
        # Return a proxy slicer
        #
        return ImageLoader(mda, image_files, **kwargs)

    #
    # Manipulate proj4's lon_0 parameter
    #
    _sublon_re = re.compile('(lon_0)=(\S+)')

    def _get_sublon(self):
        m = self._sublon_re.search(self.proj4_params)
        if m:
            return float(m.group(2))
        raise TypeError, "'SatelliteLoader' object (attribute proj4_params) has no 'sublon' attribute"

    def _set_sublon(self, slon):
        slon = "lon_0=%.2f" % float(slon)
        p = self.proj4_params
        m = self._sublon_re.search(p)
        if m:
            self.proj4_params = p.replace(m.group(0), slon)
        else:
            self.proj4_params += " %s" % slon
    sublon = property(_get_sublon, _set_sublon)

#-----------------------------------------------------------------------------
#
# Interface
#
#-----------------------------------------------------------------------------


def decompress(infiles, **options):
    """Check if the files are xrit-compressed, and decompress them
    accordingly:
    """
    if 'outdir' in options:
        cmd = options['outdir']
    else:
        cmd = os.environ.get('XRIT_DECOMPRESS_OUTDIR', None)

    if not cmd:
        logger.info("XRIT_DECOMPRESS_OUTDIR is not defined. " +
                    "The decompressed files will be put in " +
                    "the same directory as compressed ones")

    decomp_files = []
    for filename in infiles:
        if filename.endswith('C_'):
            # Try decompress it:
            logger.debug('Try decompressing ' + filename)
            if cmd:
                outdir = cmd
            else:
                outdir = os.path.dirname(filename)
            outfile = _xrit.decompress(filename, outdir)
            decomp_files.append(outfile)
        else:
            decomp_files.append(filename)

    return decomp_files


def load_files(prologue, image_files, epilogue=None, **kwarg):
    if type(prologue) == type('string'):
        logger.info("Read %s" % prologue)
        prologue = _xrit.read_prologue(prologue)
    if epilogue and type(epilogue) == type('string'):
        logger.info("Read %s" % epilogue)
        epilogue = _xrit.read_epilogue(epilogue)
    satname = prologue.platform.lower()
    return SatelliteLoader(mipp.cfg.read_config(satname)).load_files(prologue,
                                                                     image_files,
                                                                     epilogue=epilogue,
                                                                     **kwarg)


def load(satname, time_stamp, channel, **kwarg):
    return SatelliteLoader(mipp.cfg.read_config(satname)).load(time_stamp, channel, **kwarg)


def load_meteosat07(time_stamp, channel, **kwarg):
    return load('meteosat07', time_stamp, channel, **kwarg)


def load_meteosat09(time_stamp, channel, **kwarg):
    return load('meteosat09', time_stamp, channel, **kwarg)


def load_goes11(time_stamp, channel, **kwarg):
    return load('goes11', time_stamp, channel, **kwarg)


def load_goes12(time_stamp, channel, **kwarg):
    return load('goes12', time_stamp, channel, **kwarg)


def load_goes13(time_stamp, channel, **kwarg):
    return load('goes13', time_stamp, channel, **kwarg)


def load_mtsat1r(time_stamp, channel, **kwarg):
    return load('mtsat1r', time_stamp, channel, **kwarg)


def load_mtsat2(time_stamp, channel, **kwarg):
    return load('mtsat2', time_stamp, channel, **kwarg)


def load_electrol(time_stamp, channel, **kwarg):
    return load('electrol', time_stamp, channel, **kwarg)

#-----------------------------------------------------------------------------
