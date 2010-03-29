#
# $Id$ 
#
import sys
import numpy
import types
import glob
import types
import imp

import xrit

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

class _SatelliteLoader(object):
    # Currently this one only works for geos satellites
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
        self._sublon = sublon
        self.proj4_params = "proj=geos lon_0=%.2f lat_0=0.00 a=6378169.00 b=6356583.80 h=35785831.00"%sublon
        self._config_reader = config_reader
        self.satname = self.satname + self.number
        self.no_data_value = 0
        delattr(self, 'number')

    def load(self, time_stamp, channel, mask=False, calibrate=True, only_metadata=False):
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
        print >>sys.stderr, 'Files:'
        print >>sys.stderr, '    ', prologue
        for f in image_files:
            print >>sys.stderr, '    ', f

        prologue = xrit.read_prologue(prologue)
        return self.load_files(prologue, image_files, mask, calibrate, only_metadata)

    def load_files(self, prologue, image_files, mask=False, calibrate=True, only_metadata=False):
        if only_metadata:
            return self._read_metadata(prologue, image_files)
        else:
            return self._read(prologue, image_files, mask, calibrate)
        

    def _read_metadata(self, prologue, image_files):
        mda = self._metadata_reader(prologue, image_files)
        
        if mda._sublon != self._sublon:
            raise SatDecodeError("Sub satellite point is %.2f, for %s is should be %.2f"%
                                 (mda._sublon, self.satname, self._sublon))
        
        chn = self._config_reader.get_channel(mda.channel)
        if mda.image_size[0] != chn.size[0]:
            raise SatDecodeError("Unknown image width for %s, %s: %d"%(self.satname, mda.channel, mda.image_size[0]))
                                
        mda.pixel_size = numpy.array([chn.resolution, chn.resolution], dtype=numpy.float32)
        for k, v in self.__dict__.items():
            if k[0] != '_' and type(v) != types.FunctionType:
                setattr(mda, k, v)
                
        return mda

    def _read(self, prologue, image_files, mask=False, calibrate=True):
        mda = self._read_metadata(prologue, image_files)
	len_img = (((mda.image_size[0] + mda.line_offset)*mda.image_size[1])*mda.data_type)//8
        print >>sys.stdout, "Data size: %dx%d pixels, %d bytes, %d bits per pixel"%\
              (mda.image_size[0], mda.image_size[1], len_img, mda.data_type)
        
        raw_img = _make_image(image_files)
        
        if mda.data_type == 10:
            tmp = xrit.convert.dec10216(raw_img)
            del raw_img
            raw_img = tmp
            mda.data_type = 16
            dtype = numpy.uint16
        elif mda.data_type == 8:
            dtype = numpy.uint8
        elif mda.data_type == 16:
            dtype = numpy.uint16
        else:
            raise SatDecodeError("Unknown data type: %d"%prologue.structure.nb)
    
        img = numpy.frombuffer(raw_img, dtype=dtype)
        img.shape = (mda.image_size[1], mda.image_size[0]+mda.line_offset)
        if mda.line_offset != 0:
            img = img[:,mda.line_offset:]
            mda.line_offset = 0
        l = min(mda.image_size[1], mda.image_size[0])
        img = img[:l,:l]
        mda.image_size = (l,l)
        if mda.first_pixel == 'south east':
            print >>sys.stderr, "Rotating image 180 degrees"
            img = numpy.rot90(numpy.rot90(img))
            tmp = img.copy() # Make it ownen data
            del img
            img = tmp
            mda.first_pixel = 'north west'
        if mda.first_pixel != 'north west':
            print >>sys.stderr, "Weird image orientation, first pixel: '%s'"%mda.first_pixel        
        delattr(mda, 'line_offset')
        delattr(mda, 'first_pixel')

        mda.calibrated = calibrate
        if calibrate:
            # do this before masking.
            img = _calibrate(mda, img)
        
        if mask:
            img = numpy.ma.array(img, mask=(img == mda.no_data_value), copy=False)
        return mda, img

def _make_image(image_files, size=()):        
    image_files.sort()
    s = xrit.read_imagedata(image_files[0])
    start_seg_no = s.segment.planned_start_seg_no
    end_seg_no = s.segment.planned_end_seg_no
    seg_length = (s.structure.nc*s.structure.nl*s.structure.nb)//8
    last_seg_no = 0
        
    raw_img = ''
    for f in image_files:
        s = xrit.read_imagedata(f)
        pad_size = (s.segment.seg_no - last_seg_no - 1)*seg_length
        if pad_size:
            print >>sys.stderr, "Missing segment(s), will do padding for",\
                  (s.segment.seg_no - last_seg_no - 1), 'segments'
            raw_img += '\0'*pad_size
        raw_img += s.data
        last_seg_no = s.segment.seg_no
            
    pad_size = (end_seg_no - last_seg_no)*seg_length
    if pad_size:
        print >>sys.stderr, "Missing segment(s), will do padding for",\
              (end_seg_no - last_seg_no), 'segments'
        raw_img += '\0'*pad_size
    return raw_img

def _calibrate(mda, img):
    mda.calibrated = False
    mda.calibration_unit = 'counts'
    try:
        cal = mda.__dict__.pop('calibration_table')
    except KeyError:
        cal = None
    
    if cal == None or len(cal) == 0:
        return img
    if type(cal) != numpy.ndarray:
        cal = numpy.array(cal)

    if cal.shape == (256, 2):
        cal = cal[:,1] # nasty !!!
        cal[int(mda.no_data_value)] = mda.no_data_value
        img = cal[img] # this does not work on masked arrays !!!
    elif cal.shape ==(2, 2):
        scale = (cal[1][1] - cal[0][1])/(cal[1][0] - cal[0][0])
        offset = cal[0][1] - cal[0][0]*scale
        img = numpy.select([img == mda.no_data_value*scale], [mda.no_data_value], default=offset + img*scale)
    else:
        raise SatDecodeError("Could not recognize the shape %s of the calibration table"%str(cal.shape))
    mda.calibrated = True
    return img

#-----------------------------------------------------------------------------
#
# Interface
#
#-----------------------------------------------------------------------------
def load_files(prologue, image_files,
               mask=False, calibrate=True, only_metadata=False):
    if type(prologue) == type('string'):
        prologue = xrit.read_prologue(prologue)
    satname = prologue.platform.lower()
    return _SatelliteLoader(xrit.cfg.read_config(satname)).\
           load_files(prologue, image_files, mask, calibrate, only_metadata)
 
def load(satname, time_stamp, channel,
         mask=False, calibrate=True, only_metadata=False):
    return _SatelliteLoader(xrit.cfg.read_config(satname)).\
           load(time_stamp, channel, mask, calibrate, only_metadata)
 
def load_meteosat07(time_stamp, channel,
                    mask=False, calibrate=True, only_metadata=False):
    return load('meteosat07', time_stamp, channel, mask, calibrate, only_metadata)
 
def load_goes11(time_stamp, channel,
                mask=False, calibrate=True, only_metadata=False):
    return load ('goes11', time_stamp, channel, mask, calibrate, only_metadata)
 
def load_goes12(time_stamp, channel,
                mask=False, calibrate=True, only_metadata=False):
    return load('goes12', time_stamp, channel, mask, calibrate, only_metadata)
 
def load_mtsat1r(time_stamp, channel,
                 mask=False, calibrate=True, only_metadata=False):
    return load ('mtsat1r', time_stamp, channel, mask, calibrate, only_metadata)

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    from datetime import datetime
    import Image as pil

    #mda, img = load_mtsat1r(datetime(2010, 2, 1, 9, 0), '10_8', mask=True)
    mda, img = load('met7', datetime(2010, 2, 1, 10, 0), '00_7', mask=True)
    #mda, img = load('goes12', datetime(2010, 1, 31, 12, 0), '10_7', mask=True)
    #mda, img = load('goes11', datetime(2010, 2, 1, 3, 0), '00_7', mask=True)
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
