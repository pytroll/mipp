#
# WORK IN PROGRESS for CosmoSkyMed
#
import os
import copy
import numpy as np
from datetime import datetime, timedelta
from lxml import etree

import logging
logger = logging.getLogger('mipp')

import mipp
from mipp.read_geotiff import read_geotiff, tiff2areadef
from mipp.xsar import Metadata

__all__ = ['read_metadata', 'read_image']

class _Calibrator(object):
    def __init__(self, mda):
        self.error = "Unknown calibration"

    def __call__(self, image, calibrate=1):
        if calibrate == 0:
            return (image,
                    'counts')
        raise mipp.CalibrationError, self.error

def read_metadata(xmlbuffer):
    mda = Metadata()    

    # Speciel decoders
    def dec_timeformat(strn):
        strn = strn.split('.')        
        return (datetime.strptime(strn[0], "%Y-%m-%d %H:%M:%S") + 
                timedelta(seconds=float('.' + strn[1])))
    def dec_orbit_number(strn):
        return int(strn[:5])

    attributes = (
        ('_ROOT_/Attribute', {
                'Satellite ID': ('satellite_name', str),
                'Product Filename': ('image_filename', str),
                'Product Type': ('product_type', str),
                'Acquisition Station ID': ('facility_id', str),
                'Scene Sensing Start UTC': ('time_start', dec_timeformat),
                'Scene Sensing Stop UTC': ('time_stop', dec_timeformat),
                'Orbit Number': ('orbit_number', dec_orbit_number),
                'Sample Format': ('product_format', str),
                'Image Scale': ('image_scale', str),
                'Image Layers': ('layers', int),
                'Bits per Sample': ('bits_per_sample', int),
                'Samples per Pixel': ('samples_per_pixel', int),
                }),
        
        ('MBI/Attribute', {
                'Column Spacing': ('sample_spacing', float),
                'Line Spacing': ('line_spacing', float)
                }),

        ('S01/Attribute', {            
                'Polarisation': ('polarisation', str),
                }),
        )

    tree = etree.fromstring(xmlbuffer)

    #
    # Get Atrributes
    #
    for path, attr in attributes:
        names = attr.keys()
        path = tree.xpath(path)
        for i in path:
            name = i.attrib['Name']
            if name in names:
                names.remove(name)
                val = i.text
                setattr(mda, attr[name][0], attr[name][1](val))

    

    satid = 'CSK'
    if not mda.satellite_name.upper().startswith(satid):
        raise mipp.ReaderError(
            "This does not look like a CosmoSkymed product, " + 
            "satellite ID does now start with '%s'"%satid)

    mda.image_filename = os.path.splitext(mda.image_filename)[0] + '.MBI.tif'

    mda.no_data_value = 0
    mda.calibrated = 'NOTCALIBRATED'

    return mda

def read_image(mda, filename=None, mask=True, calibrate=1):
    mda = copy.copy(mda)
    mda.calibrate = _Calibrator(mda)
    mda.calibration_unit = 'counts'
    mda.is_calibrated = False
    del mda.calibrated
    mda.product_name = (mda.time_start.strftime("%Y%m%d_%H%M%S") + '_' + 
                        mda.satellite_name + '_' +  
                        mda.product_type + '_' +
                        mda.polarisation)
    logger.info('Product name: %s'% mda.product_name)
    
    if not filename:
        filename = mda.image_filename

    params, data = read_geotiff(filename)
    area_def = tiff2areadef(params['projection'],
                            params['geotransform'],
                            data.shape)

    mda.proj4_params = area_def.proj4_string.replace('+', '')
    mda.area_extent = area_def.area_extent
    mda.tiff_params = params

    if calibrate:
        data, mda.calibration_unit = mda.calibrate(data, calibrate)
        mda.is_calibrated = True
        logger.info('calibrated: %s %s [%.2f -> %.2f -> %.2f] %s'%
                    (str(data.shape), data.dtype, data.min(),
                     data.mean(), data.max(), mda.calibration_unit))

    if mask:
        mask = (data == mda.no_data_value)
        data = np.ma.array(data, mask=mask, copy=False)

    return mda, data

if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as fp:
        _mda = read_metadata(fp.read())
    _mda.image_filename = os.path.dirname(sys.argv[1]) + '/' + \
        _mda.image_filename        
    print _mda
    _mda, _data = read_image(_mda, calibrate=False)
    print _data.min(), _data.mean(), _data.max()
