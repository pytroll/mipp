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
import convert
import cfg

__all__ = ['load_meteosat07',
           'load_goes11',
           'load_goes12',
           'load_mtsat1r',
           'SatDecodeError',
           'SatNoFiles']

class SatDecodeError(Exception):
    pass

class SatNoFiles(SatDecodeError):
    pass

class SatelliteLoader(object):
    # Currently this one only works for geos satellites
    
    def __init__(self, config_reader):
        sat = config_reader('satellite')
        projname = sat['projection'].lower()
        if not projname.startswith('geos'):
            raise SatDecodeError("Currently we only support projections of type: 'GEOS'")        
        sublon = float(projname.split('(')[1].split(')')[0])

        format = config_reader('level1')['format']
        try:
            args = (format,) + imp.find_module(format)
        except ImportError:
            raise SatDecodeError("Unknown level-1 format: '%s'"%format)            
        self._metadata_reader = imp.load_module(*args).read_metadata

        self.__dict__.update(sat)    
        self._sublon = sublon
        p = ['proj=geos', '', 'lat_0=0.00 a=6378169.00 b=6356583.80 h=35785831.00']
        p[1] = 'lon_0=%.2f'%sublon
        self.proj4_params = ' '.join(p)
        self._config_reader = config_reader
        self.satname = self.satname + self.number
        delattr(self, 'number')

    def load(self, time_stamp, channel, only_metadata=False):
        if channel not in self._config_reader.get_channel_names():
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
        if only_metadata:
            return self._read_metadata(prologue, image_files)
        else:
            return self._read(prologue, image_files)
        
    def _read_metadata(self, prologue, image_files):
        mda = self._metadata_reader(prologue, image_files)
        
        if mda.sublon != self._sublon:
            raise SatDecodeError("Sub satellite point is %.2f, for %s is should be %.2f"%
                                 (mda.sublon, self.satname, self._sublon))
        
        chn = self._config_reader.get_channel(mda.channel)
        if mda.image_size[0] == chn.size[0]:
            self.pixel_size = numpy.array([chn.resolution, chn.resolution], dtype=numpy.float32)
        else:
            raise SatDecodeError("Unknown image width for %s, %s: %d"%(self.satname, mda.channel, mda.image_size[0]))
            
        for k, v in self.__dict__.items():
            if k[0] != '_' and type(v) != types.FunctionType:
                setattr(mda, k, v)
                
        return mda

    def _read(self, prologue, image_files):        
        mda = self._read_metadata(prologue, image_files)
        raw_img = _make_image(image_files)
        print >>sys.stderr, "Data size:", mda.image_size
        len_img = ((mda.image_size[0] + mda.line_offset)*mda.image_size[1]/8)*mda.data_type
        if len(raw_img) != len_img:
            raise SatDecodeError("No match in image size: %d, we expected %d"%(len(raw_img),len_img))

        if mda.data_type == 10:
            tmp = convert.dec10216(raw_img)
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
            img = numpy.rot90(numpy.rot90(img))
            tmp = img.copy() # Make it ownen data
            del img
            img = tmp
            mda.first_pixel = 'north west'
        if mda.first_pixel != 'north west':
            print >>sys.stderr, "Weird image orientation, first pixel: '%s'"%mda.first_pixel        
        delattr(mda, 'line_offset')
        delattr(mda, 'first_pixel')
        delattr(mda, 'sublon')
        
        return mda, img
    
def _make_image(image_files, size=()):
    def seg_info(s):
        return  s.segment.seg_no,\
               (s.structure.nc, s.structure.nl), \
               (s.navigation.coff, s.navigation.loff), \
               (s.structure.nc*s.structure.nl*s.structure.nb)/8
        
    image_files.sort()
    s = xrit.read_imagedata(image_files[0])
    start_seg_no = s.segment.planned_start_seg_no
    end_seg_no = s.segment.planned_end_seg_no
    seg_no, seg_size, seg_off, seg_length  = seg_info(s)
    last_seg_no = 0
        
    raw_img = ''
    for f in image_files:
        s = xrit.read_imagedata(f)
        no, size, off, length = seg_info(s)
        pad_size = (no - last_seg_no - 1)*seg_length
        if pad_size:
            print >>sys.stderr, last_seg_no+1, "missing segment(s), will do padding for",\
                  (no - last_seg_no - 1), 'segments'
            raw_img += '\0'*pad_size
        print no, size, off, length
        raw_img += s.data
        last_seg_no = no
            
    pad_size = (end_seg_no - last_seg_no)*seg_length
    if pad_size:
        print >>sys.stderr, "Missing segment %d, will do padding"%(last_seg_no+1)
        raw_img += '\0'*pad_size
    return raw_img

#-----------------------------------------------------------------------------

def load(satname, time_stamp, channel, only_metadata=False):
    return SatelliteLoader(cfg.read_config(satname)).load(time_stamp, channel, only_metadata)

def load_meteosat07(time_stamp, channel, only_metadata=False):
    return load('meteosat07', time_stamp, channel, only_metadata)

def load_goes11(time_stamp, channel, only_metadata=False):
    return load('goes11', time_stamp, channel, only_metadata)

def load_goes12(time_stamp, channel, only_metadata=False):
    return load('goes12', time_stamp, channel, only_metadata)

def load_mtsat1r(time_stamp, channel, only_metadata=False):
    return load('mtsat1r', time_stamp, channel, only_metadata)

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    from datetime import datetime
    import Image as pil

    #mda, img = load('meteosat07', datetime(2010, 2, 1, 10, 0), '11_5')
    mda, img = load('goes12', datetime(2010, 1, 31, 12, 0), '10_7')
    print mda
    fname = './' + mda.product_name + '.png'
    print >>sys.stderr, 'Writing', fname
    img = ((img - img.min()) * 255.0 /
           (img.max() - img.min()))
    img = 255 - img
    img = pil.fromarray(numpy.array(img, numpy.uint8))
    img.save(fname)
