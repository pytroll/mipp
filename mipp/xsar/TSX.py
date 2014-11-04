#
#
#
import copy
import numpy as np
from datetime import datetime
from lxml import etree
from osgeo import osr

import mipp
from mipp.read_geotiff import read_geotiff, tiff2areadef
from mipp.xsar import Metadata

import logging
logger = logging.getLogger('mipp')

no_data_value = 0

class _Calibrator(object):
    def __init__(self, mda):
        self.factor = mda.calibration_factor
        self.unit = mda.calibration_unit.lower()
        self.error = None
        if mda.calibrated != 'CALIBRATED':
            self.error = "Data is not calibrated"
        if mda.beamid != mda.calibration_beamid:
            self.error = \
                "BeamID for image data and calibration factor don't match"
        if mda.calibration_unit.lower() != 'radar-brightness':
            self.error = "Unknown calibration unit '%s'" % (
                self.calibration_unit.lower())

    def __call__(self, image, calibrate=1):
        if calibrate == 0:
            return (image,
                    'counts')
        if self.error:
            raise mipp.CalibrationError, self.error
        return (image*image*self.factor,
                self.unit)

def read_metadata(xmlbuffer):

    # Speciel decoders
    def dec_isoformat(rts):
        return datetime.strptime(rts, "%Y-%m-%dT%H:%M:%S.%fZ")
    def dec_orbit_number(rts):
        return int(rts[:5])    
    def dec_satellite_name(rts):
        return rts.replace('-', '')
    def dec_calibration_unit(rts):
        _trans = {'radar brightness': 'nrcs'}
        rts = rts.replace(' ', '-').lower()
        return rts

    attributes = {
        'product_level':  ('generalHeader/itemName', str),
        'satellite_name': ('productInfo/missionInfo/mission', dec_satellite_name),
        'orbit_number': ('productInfo/missionInfo/absOrbit', dec_orbit_number),
        'sensor_type': ('productInfo/acquisitionInfo/sensor', str),
        'beam_mode': ('productInfo/acquisitionInfo/imagingMode', str),
        'polarisation': ('productInfo/acquisitionInfo/polarisationList/polLayer', str),
        'beamid': ('productInfo/acquisitionInfo/elevationBeamConfiguration', str),
        'calibrated': ('productInfo/productVariantInfo/radiometricCorrection', str),
        'calibration_factor': ('calibration/calibrationConstant/calFactor', float),
        'calibration_beamid': ('calibration/calibrationConstant/beamID', str),
        'calibration_unit': ('productInfo/imageDataInfo/pixelValueID', dec_calibration_unit),
        'image_data_path': ('productComponents/imageData/file/location/path', str),
        'image_data_filename': ('productComponents/imageData/file/location/filename', str),
        'time_start': ('productInfo/sceneInfo/start/timeUTC', dec_isoformat),        
        'center_coor_lat': ('productInfo/sceneInfo/sceneCenterCoord/lat', float),
        'center_coor_lon': ('productInfo/sceneInfo/sceneCenterCoord/lon', float)
        }

    check_attributes = {'product_level': 'level 1b product',
                        'satellite_name': 'tsx',
                        'sensor_type': 'sar'}

    tree = etree.fromstring(xmlbuffer)
    
    # Check satellite, sensor and product level
    for key, val in check_attributes.items():
        try:
            path = attributes[key][0]
            attr = tree.xpath(path)[0].text.lower()
            if not attr.startswith(val):
                raise mipp.ReaderError("This does not look like a TSX SAR " +
                                       "Level 1B Product, %s is '%s' expected '%s'" %
                                       (key, attr, val))
        except IndexError:
            raise mipp.ReaderError("This does not look like a TSX SAR " +
                                   "Level 1B Product, could not find attribute '%s' (%s)" %
                                   (key, path))

    mda = Metadata()
    for key, val in attributes.items():
        setattr(mda, key, val[1](tree.xpath(val[0])[0].text))
    mda.image_filename = (mda.image_data_path + '/' + mda.image_data_filename)
    delattr(mda, 'image_data_path')
    delattr(mda, 'image_data_filename')
    return mda

def read_image(mda, filename=None, mask=True, calibrate=1):
    mda = copy.copy(mda)
    mda.calibrate = _Calibrator(mda)
    mda.calibration_unit = 'counts'
    mda.is_calibrated = False
    del mda.calibrated
    mda.product_name = (mda.time_start.strftime("%Y%m%d_%H%M%S") + '_' + 
                        mda.satellite_name + '_' + mda.sensor_type + '_' + 
                        mda.beam_mode + '_' + mda.polarisation)
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

    mda.no_data_value = no_data_value

    if calibrate:
        data, mda.calibration_unit = mda.calibrate(data, calibrate)
        mda.is_calibrated = True
        logger.info('calibrated: %s %s [%.2f -> %.2f -> %.2f] %s'%
                    (str(data.shape), data.dtype, data.min(),
                     data.mean(), data.max(), mda.calibration_unit))

    if mask:
        mask = (data == no_data_value)
        data = np.ma.array(data, mask=mask, copy=False)

    return mda, data
