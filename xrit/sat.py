#
# $Id$ 
#
import sys
import numpy
import glob
import imp
import types

import xrit
import xrit.cfg
from xrit import logger
import geosnav
from slicer import ImageSlicer

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
        str = 'Files:\n'
        str += '    ' + prologue + '\n'
        for f in image_files:
            str += '    ' + f + '\n'
        str = str[:-1]
        logger.info(str)

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
        # !!! fishy
        mda.navigation = geosnav.GeosNavigation(mda.sublon, img.navigation.cfac, img.navigation.lfac,
                                                mda.image_size[0]//2,mda.image_size[0]//2)
        mda.center = (mda.sublon, 0.0)
        
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
        return ImageSlicer(mda, image_files, **kwargs)
            
#-----------------------------------------------------------------------------
#
# Interface
#
#-----------------------------------------------------------------------------
def load_files(prologue, image_files, epilogue=None, **kwarg):
    if type(prologue) == type('string'):
        prologue = xrit.read_prologue(prologue)
    if epilogue and type(epilogue) == type('string'):
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
if __name__ == '__main__':
    from datetime import datetime
    import Image as pil

    mda, img = load_mtsat1r(datetime(2010, 2, 1, 9, 0), '10_8', mask=True, calibrate=True)(center=(130, -30), size=(500,500))
    #mda, img = load('met7', datetime(2010, 2, 1, 10, 0), '00_7', mask=True)()
    #mda, img = load('met7', datetime(2010, 2, 1, 10, 0), '00_7', mask=True)(center=(7.036, 55.137), size=(560, 560))
    #mda, img = load('met7', datetime(2010, 2, 1, 10, 0), '11_5', mask=True, calibrate=True)(center=(50., 10.), size=(600, 500))

    #image = load_meteosat09(datetime(2009, 10, 8, 14, 30), 'VIS006', mask=False, calibrate=False)
    #image = load_meteosat07(datetime(2010, 6, 23, 8, 0), '00_7', mask=False, calibrate=False)
    #tic = datetime.now()
    #mda, img = image()#center=(0, 25), size=(600, 500)) # Over the met09 HRV break
    #toc = datetime.now()
    #print "Loaded channel in: ", toc - tic
    #mda, img = image(center=(0, 45.5), size=(600, 500)) # France and Spain

    #mda, img = image(center=(-80.8, 25.1), size=(600, 500)) # Miami

    #image = load('met7', datetime(2010, 2, 1, 10, 0), '00_7', mask=True) 
    #mda, img = image(center=(50., 10.), size=(600, 500))
    #mda, img = image()
    #mda, img = image[500:600, 500:600]
    #mda, img = image[2737:3237, 2539:3139]
    
    #mda, img = load('met7', datetime(2010, 2, 1, 10, 0), '11_5', mask=True)()
    #mda, img = load('goes12', datetime(2010, 1, 31, 12, 0), '10_7', mask=True)()
    #mda, img = load('goes12', datetime(2010, 1, 31, 12, 0), '10_7', mask=True, calibrate=True)(center=(-110, 23.5), size=(500,600))
    #mda, img = load('goes11', datetime(2010, 2, 1, 3, 0), '00_7', mask=True)()
    #mda, img = load('goes11', datetime(2010, 2, 1, 3, 0), '10_7', mask=True, calibrate=True)( center=(-110, 23.5), size=(500,500))
    print mda
    print 'min/max =', "%.3f/%.3f"%(img.min(), img.max())
    fname = './' + mda.product_name + '.png'
    print >>sys.stderr, 'Writing', fname
    img = ((img - img.min()) * 255.0 /
           (img.max() - img.min()))
    if type(img) == numpy.ma.MaskedArray:
        img = img.filled(mda.no_data_value)
    img = pil.fromarray(numpy.array(img, numpy.uint8))
    img.save(fname)
