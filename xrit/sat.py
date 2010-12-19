#
# $Id$ 
#
import numpy
import glob
import imp
import types

import logging
logger = logging.getLogger('mipp')

import xrit
import xrit.cfg
from loader import ImageLoader

__all__ = ['load_meteosat07',
           'load_meteosat09',
           'load_goes11',
           'load_goes12',
           'load_goes13',
           'load_mtsat1r',
           'load_mtsat2',
           'load',
           'load_files']

class SatelliteLoader(object):
    # Currently this one only works for geos satellites
    #
    # We will return an ImageLoader object where access to data is like:
    # image[:], image[] or image() will return full disk
    # image[2:56, 1020:1070]
    # image.area_extent(area_extent)
    #
    def __init__(self, config_reader):
        #
        # Read configuration file based on satellite name
        #
        sat = config_reader('satellite')
        projname = sat['projection'].lower()
        if not projname.startswith('geos'):
            raise xrit.SatReaderError("currently we only support projections of type: 'GEOS'")        
        sublon = float(projname.split('(')[1].split(')')[0])

        #
        # Load format decoder based on level1 format
        #
        format = config_reader('level1')['format']
        try:
            args = imp.find_module(format)
        except ImportError:
            raise xrit.SatReaderError("unknown level-1 format: '%s'"%format)
        self._metadata_reader = imp.load_module(format, *args).read_metadata

        #
        # Attributing
        #
        self.__dict__.update(sat)    
        self.sublon = sublon
        if not hasattr(self, 'proj4_params'):
            self.proj4_params = "proj=geos lon_0=%.2f lat_0=0.00 a=6378169.00 b=6356583.80 h=35785831.00"%sublon
        self._config_reader = config_reader
        self.satname = self.satname + self.number
        self.satnumber = self.number
        delattr(self, 'number')

    def load(self, time_stamp, channel, **kwarg):
        if channel not in self._config_reader.channel_names:
            raise xrit.SatReaderError("unknown channel name '%s'"%channel)
        opt = self._config_reader('level1')
        val = {}
        val["channel"] = channel + '*'

        # Prologue
        
        val["segment"] = "PRO".ljust(9, '_')

        filename_pro = opt.get('filename_pro', opt['filename'])
        prologue = glob.glob(opt['dir'] + '/' + \
                             (time_stamp.strftime(filename_pro)%val))
        if not prologue:
            raise xrit.SatNoFiles("missing prologue file: '%s'"%(time_stamp.strftime(filename_pro)%val))
        prologue = prologue[0]

        # Regular channels
           
        val["segment"] = "0????????"
        image_files = glob.glob(opt['dir'] + '/' + \
                                time_stamp.strftime(opt['filename'])%val)
        if not image_files:
            raise xrit.SatNoFiles("no data files: '%s'"%(time_stamp.strftime(opt['filename'])%val))
        image_files.sort()

        logger.info("Read %s"%prologue)
        prologue = xrit.read_prologue(prologue)

        # Epilogue

        val["segment"] = "EPI".ljust(9, '_')

        filename_epi = opt.get('filename_pro', opt['filename'])
        epilogue = glob.glob(opt['dir'] + '/' + \
                             (time_stamp.strftime(filename_epi)%val))

        if not epilogue:
            logger.info("No epilogue file to read.")
        else:
            epilogue = epilogue[0]
            logger.info("Read %s"%epilogue)
            epilogue = xrit.read_epilogue(epilogue)
            return self.load_files(prologue, image_files,
                                   epilogue=epilogue, **kwarg)
        
        return self.load_files(prologue, image_files, **kwarg)

    def load_files(self, prologue, image_files, only_metadata=False, **kwargs):
        image_files.sort()
        if only_metadata:
            return self._read_metadata(prologue, image_files, **kwargs)
        else:
            return self._read(prologue, image_files, **kwargs)
        

    def _read_metadata(self, prologue, image_files, epilogue=None):
        if epilogue:
            mda = self._metadata_reader(prologue, image_files, epilogue)
        else:
            mda = self._metadata_reader(prologue, image_files)
        if "%.2f"%mda.sublon != "%.2f"%self.sublon:
            raise xrit.SatReaderError("sub satellite point is %.2f, for %s is should be %.2f"%
                                      (mda.sublon, self.satname, self.sublon))
        
        chn = self._config_reader.get_channel(mda.channel)
        if mda.image_size[0] != chn.size[0]:
            raise xrit.SatReaderError("unknown image width for %s, %s: %d"%(self.satname, mda.channel, mda.image_size[0]))
                                
        mda.pixel_size = numpy.array([chn.resolution, chn.resolution], dtype=numpy.float32)
        for k, v in self.__dict__.items():
            if k[0] != '_' and type(v) != types.FunctionType:
                setattr(mda, k, v)
                
        img = xrit.read_imagedata(image_files[0])
        
        return mda

    def _read(self, prologue, image_files, epilogue=None, **kwargs):
        if epilogue:
            mda = self._read_metadata(prologue, image_files, epilogue)
        else:
            mda = self._read_metadata(prologue, image_files)
	len_img = (((mda.image_size[0] + mda.line_offset)*mda.image_size[1])*mda.data_type)//8
        logger.info("Data size: %dx%d pixels, %d bytes, %d bits per pixel",
                    mda.image_size[0], mda.image_size[1], len_img, mda.data_type)

        #
        # Return a proxy slicer
        #
        return ImageLoader(mda, image_files, **kwargs)
            
#-----------------------------------------------------------------------------
#
# Interface
#
#-----------------------------------------------------------------------------
def load_files(prologue, image_files, epilogue=None, **kwarg):
    if type(prologue) == type('string'):
        logger.info("Read %s"%prologue)
        prologue = xrit.read_prologue(prologue)
    if epilogue and type(epilogue) == type('string'):
        logger.info("Read %s"%epilogue)
        epilogue = xrit.read_epilogue(epilogue)
    satname = prologue.platform.lower()
    return SatelliteLoader(xrit.cfg.read_config(satname)).load_files(prologue, 
                                                                     image_files, 
                                                                     epilogue=epilogue, 
                                                                     **kwarg)
 
def load(satname, time_stamp, channel, **kwarg):
    return SatelliteLoader(xrit.cfg.read_config(satname)).load(time_stamp, channel, **kwarg)
 
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

#-----------------------------------------------------------------------------
