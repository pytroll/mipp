#
# $Id$ 
#
import sys
import numpy
import types
import glob
import types
import imp
import types

import xrit
from xrit import logger
import geosnav
from slicer import ImageSlicer

__all__ = ['load_meteosat07',
           'load_goes11',
           'load_goes12',
           'load_mtsat1r',
           'load_files',
           'SatDecodeError',
           'SatNoFiles']

class SatDecodeError(Exception):
    pass

class SatNoFiles(SatDecodeError):
    pass

class SatelliteLoader(object):
    # Currently this one only works for geos satellites
    #
    # We will return an ImageSlicer object where access to data is like:
    # image[:], image[] or image() will return full disk
    # image[2:56, 1020:1070]
    # image(center, size)
    #
    def __init__(self, config_reader):
        #
        # Read configuration file based on satellite name
        #
        sat = config_reader('satellite')
        projname = sat['projection'].lower()
        if not projname.startswith('geos'):
            raise SatDecodeError("Currently we only support projections of type: 'GEOS'")        
        sublon = float(projname.split('(')[1].split(')')[0])

        #
        # Load format decoder based on level1 format
        #
        format = config_reader('level1')['format']
        try:
            args = imp.find_module(format)
        except ImportError:
            raise SatDecodeError("Unknown level-1 format: '%s'"%format)
        self._metadata_reader = imp.load_module(format, *args).read_metadata

        #
        # Attributing
        #
        self.__dict__.update(sat)    
        self.sublon = sublon
        self.proj4_params = "proj=geos lon_0=%.2f lat_0=0.00 a=6378169.00 b=6356583.80 h=35785831.00"%sublon
        self._config_reader = config_reader
        self.satname = self.satname + self.number
        self.no_data_value = 0
        delattr(self, 'number')

    def load(self, time_stamp, channel, **kwarg):
        if channel not in self._config_reader.channel_names:
            raise SatDecodeError("Unknown channel name '%s'"%channel)
        opt = self._config_reader('level1')
        val = {}
        val["channel"] = channel
        val["segment"] = "PRO".ljust(9, '_')
        prologue = glob.glob(opt['dir'] + '/' + \
                             (time_stamp.strftime(opt['filename'])%val))
        if not prologue:
            raise SatNoFiles("No prologue file: '%s'"%(time_stamp.strftime(opt['filename'])%val))
        prologue = prologue[0]
            
        val["segment"] = "0????????"
        image_files = glob.glob(opt['dir'] + '/' + \
                                time_stamp.strftime(opt['filename'])%val)
        if not image_files:
            raise SatNoFiles("No data files: '%s'"%(time_stamp.strftime(opt['filename'])%val))
        image_files.sort()
        str = 'Files:\n'
        str += '    ' + prologue + '\n'
        for f in image_files:
            str += '    ' + f + '\n'
        str = str[:-1]
        logger.info(str)

        prologue = xrit.read_prologue(prologue)
        return self.load_files(prologue, image_files, **kwarg)

    def load_files(self, prologue, image_files, only_metadata=False, **kwargs):
        image_files.sort()
        if only_metadata:
            return self._read_metadata(prologue, image_files, **kwargs)
        else:
            return self._read(prologue, image_files, **kwargs)
        

    def _read_metadata(self, prologue, image_files):
        mda = self._metadata_reader(prologue, image_files)
        
        if "%.2f"%mda.sublon != "%.2f"%self.sublon:
            raise SatDecodeError("Sub satellite point is %.2f, for %s is should be %.2f"%
                                 (mda.sublon, self.satname, self.sublon))
        
        chn = self._config_reader.get_channel(mda.channel)
        if mda.image_size[0] != chn.size[0]:
            raise SatDecodeError("Unknown image width for %s, %s: %d"%(self.satname, mda.channel, mda.image_size[0]))
                                
        mda.pixel_size = numpy.array([chn.resolution, chn.resolution], dtype=numpy.float32)
        for k, v in self.__dict__.items():
            if k[0] != '_' and type(v) != types.FunctionType:
                setattr(mda, k, v)
                
        img = xrit.read_imagedata(image_files[0])
        # !!! fishy
        mda.navigation = geosnav.GeosNavigation(mda.sublon, img.navigation.cfac, img.navigation.lfac,
                                                mda.image_size[0]//2,mda.image_size[0]//2)
        mda.center = (mda.sublon, 0.0)
        
        return mda

    def _read(self, prologue, image_files, **kwargs):
        mda = self._read_metadata(prologue, image_files)
	len_img = (((mda.image_size[0] + mda.line_offset)*mda.image_size[1])*mda.data_type)//8
        logger.info("Data size: %dx%d pixels, %d bytes, %d bits per pixel",
                    mda.image_size[0], mda.image_size[1], len_img, mda.data_type)

        #
        # Return a proxy slicer
        #
        return ImageSlicer(mda, image_files, **kwargs)
            
#-----------------------------------------------------------------------------
#
# Interface
#
#-----------------------------------------------------------------------------
def load_files(prologue, image_files, **kwarg):
    if type(prologue) == type('string'):
        prologue = xrit.read_prologue(prologue)
    satname = prologue.platform.lower()
    return SatelliteLoader(xrit.cfg.read_config(satname)).load_files(prologue, image_files, **kwarg)
 
def load(satname, time_stamp, channel, **kwarg):
    return SatelliteLoader(xrit.cfg.read_config(satname)).load(time_stamp, channel, **kwarg)
 
def load_meteosat07(time_stamp, channel, **kwarg):
    return load('meteosat07', time_stamp, channel, **kwarg)
 
def load_goes11(time_stamp, channel, **kwarg):
    return load('goes11', time_stamp, channel, **kwarg)
 
def load_goes12(time_stamp, channel, **kwarg):
    return load('goes12', time_stamp, channel, **kwarg)
 
def load_mtsat1r(time_stamp, channel, **kwarg):
    return load('mtsat1r', time_stamp, channel, **kwarg)

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    from datetime import datetime
    import Image as pil

    #mda, img = load_mtsat1r(datetime(2010, 2, 1, 9, 0), '10_8', mask=True)(center=(130, -30), size=(500,500))
    #mda, img = load('met7', datetime(2010, 2, 1, 10, 0), '00_7', mask=True)
    #mda, img = load('met7', datetime(2010, 2, 1, 10, 0), '00_7', mask=True)(center=(7.036, 55.137), size=(560, 560))
    #mda, img = load('met7', datetime(2010, 2, 1, 10, 0), '11_5', mask=True)(center=(50., 10.), size=(600, 500))
    
    #image = load('met7', datetime(2010, 2, 1, 10, 0), '11_5', mask=True, calibrate=False)
    #mda, img = image(center=(50., 10.), size=(600, 500))
    #mda, img = image[500:600, 500:600]
    
    #mda, img = load('met7', datetime(2010, 2, 1, 10, 0), '11_5', mask=True)
    #mda, img = load('goes12', datetime(2010, 1, 31, 12, 0), '10_7', mask=True)
    mda, img = load('goes12', datetime(2010, 1, 31, 12, 0), '10_7', mask=True, calibrate=True)(center=(-110, 23.5), size=(500,600))
    #mda, img = load('goes11', datetime(2010, 2, 1, 3, 0), '00_7', mask=True)
    #mda, img = load('goes11', datetime(2010, 2, 1, 3, 0), '10_7', mask=True)( center=(-110, 23.5), size=(500,500))
    print mda
    print 'min/max =', "%.3f/%.3f %s"%(img.min(), img.max(), mda.calibration_unit)
    fname = './' + mda.product_name + '.png'
    print >>sys.stderr, 'Writing', fname
    img = ((img - img.min()) * 255.0 /
           (img.max() - img.min()))
    if type(img) == numpy.ma.MaskedArray:
        img = img.filled(mda.no_data_value)
    img = pil.fromarray(numpy.array(img, numpy.uint8))
    img.save(fname)
    print mda.navigation
    #print (51.35, 10.36), '->', mda.navigation.pixel((51.35, 10.36))
    #print (43.58, 12.66), '->', mda.navigation.pixel((43.58, 12.66))
    #print (50, 10), '->', mda.navigation.pixel((50, 10))
    #print (-110, 23.5), '->', mda.navigation.pixel((-110, 23.5))
    #print (-120, 35), '->', mda.navigation.pixel((-120, 35))
