#
# $Id$ 
#
import sys
import numpy
import types

import xrit
import SGS
import MTP
import convert

__all__ = ['read', 'read_metadata']

class SatDecodeError(Exception):
    pass

class SatelliteReader(object):
    def __init__(self, satname, sspname, channels, metadata_reader):
        self.satname = satname
        self.sspname = sspname
        self._metadata_reader = metadata_reader
        self._channels = channels
        
        lon0 = float(sspname[:-1])
        if sspname[-1].upper() == 'W':
            lon0 *= -1
        self.sub_satellite_point = numpy.array([lon0, 0.0], dtype=numpy.float32)
            
        p = ['proj=geos', '', 'lat_0=0.00 a=6378169.00 b=6356583.80 h=35785831.00']
        p[1] = 'lon_0=%.2f'%lon0
        self.proj4_params = ' '.join(p)

    def read_metadata(self, prologue, image_files):
        mda = self._metadata_reader(prologue, image_files)
        
        if mda.satname != self.satname:
            raise SatDecodeError("This is no '%s' satellite file"%self.satname)
        if (mda.sub_satellite_point[0] != self.sub_satellite_point[0]) or \
               (mda.sub_satellite_point[1] != self.sub_satellite_point[1]):
            raise SatDecodeError("Sub satellite point is %s, for %s is should be %s"%
                                 (str(mda.sub_satellite_point), self.satname, str(self.sub_satellite_point)))
        
        chn = self._channels.get(mda.channel, None)
        if not chn:
            raise SatDecodeError("Unknown channel for %s: '%s'"%(mda.satname, mda.channel))
        if mda.image_size[0] == chn[0]:
            self.pixel_size = numpy.array([chn[1], chn[1]], dtype=numpy.float32)
        else:
            raise SatDecodeError("Unknown image width for %s, %s: %d"%(self.satname, mda.channel, mda.image_size[0]))
            
        for k, v in self.__dict__.items():
            if k[0] != '_' and type(v) != types.FunctionType:
                setattr(mda, k, v)
                
        return mda

    def read(self, prologue, image_files):
        mda = self.read_metadata(prologue, image_files)
        
        raw_img = ''
        for f in sorted(image_files):
            raw_img += xrit.read_imagedata(f).data
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
        
        return mda, img
        
#-----------------------------------------------------------------------------
#
# Hard-coded satellite parmeters.
#
#-----------------------------------------------------------------------------
satellites = {
    'MET7': 
    SatelliteReader('MET7',
                    '057E',
                    {'00_7': (5000, 2.24849),   # channel width and pixel size
                     '06_4': (2500, 4.49698),
                     '11_5': (2500, 4.49698)},
                    MTP.read_metadata
                    ),
    'GOES11':
    SatelliteReader('GOES11',
                    '135W',
                    {'00_7': (2816, 4.0065756),
                     '03_9': (2816, 4.0065756),
                     '06_8': (1408, 8.013151),
                     '10_7': (2816, 4.0065756)},
                    SGS.read_metadata),
    'GOES12':
    SatelliteReader('GOES12',
                    '075W',
                    {'00_7': (2816, 4.0065756),
                     '03_9': (2816, 4.0065756),
                     '06_6': (2816, 4.0065756),
                     '10_7': (2816, 4.0065756)},
                    SGS.read_metadata),
    'MTSAT1R':
    SatelliteReader('MTSAT1R',
                    '140E',
                    {'00_7': (2752, 4.0),
                     '03_8': (2752, 4.0),
                     '06_8': (2752, 4.0),
                     '10_8': (2752, 4.0)},
                    SGS.read_metadata)
    }
            
satellite_names = tuple(sorted(satellites.keys()))              

#-----------------------------------------------------------------------------

def read(prologue, image_files, only_metadata=False):
    if type(prologue) == type(" "):
        # guess it's a name of a file
        prologue = xrit.read_prologue(prologue)
    sd = satellites.get(prologue.platform, None)
    if sd == None:
        raise SatDecodeError("Unknown satellite: '%s'"%prologue.platform)
    if only_metadata:
        return sd.read_metadata(prologue, image_files)
    return sd.read(prologue, image_files)

def read_metadata(prologue, image_files):
    return read(prologue, image_files, only_metadata=True)

if __name__ == '__main__':
    mda, img = read(sys.argv[1], sys.argv[2:])
    print mda
    fname = './' + mda.product_name + '.dat'
    print >>sys.stderr, 'Writing', fname
    fp = open(fname, "wb")
    img.tofile(fp)
    fp.close()
