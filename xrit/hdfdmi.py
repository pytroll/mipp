#
# $Id$
#
"""Will write a simple HDF5 file with a single image.
"""

import sys
import os
from datetime import datetime
import h5py

__all__ = ['save',]

def save(mda, img, file_name):

    h5 = h5py.File(file_name, 'w')
    gr = h5.create_group('geographic')
    gr.attrs['geo_number_columns'] = mda.image_size[0]
    gr.attrs['geo_number_rows'] = mda.image_size[1]
    gr.attrs['geo_pixel_size_x'] = mda.pixel_size[0]
    gr.attrs['geo_pixel_size_y'] = mda.pixel_size[1]
    gr.attrs['geo_dim_pixel'] = "KM,KM"
    gr.attrs['geo_product_center'] = mda.sub_satellite_point
    gr.attrs['full_disk'] = 'yes'
    gr = gr.create_group('map_projection')
    gr.attrs['projection_indication'] = 'yes'
    gr.attrs['projection_proj4_params'] = mda.proj4_params

    gr = h5.create_group('image1')
    gr.attrs['image_product_name'] = 'channel ' + mda.calibration_name
    gr.attrs['image_size'] = (mda.image_size[0]*mda.image_size[1]/8)*mda.data_type
    gr.attrs['image_bytes_per_pixel'] = mda.data_type/8
    gr.attrs['image_acquisition_time'] = mda.time_stamp.strftime('%d-%b-%Y %H:%M:%S.000')
    gr.attrs['image_production_time'] = mda.production_time.strftime('%d-%b-%Y %H:%M:%S.000')
    cg = gr.create_group('calibration')
    if mda.calibration_name:
        gr.attrs['image_geo_parameter'] = mda.calibration_name + '[' + mda.calibration_unit + ']'
        cg.attrs['calibration_flag'] = 'yes'
        cg.create_dataset('calibration_table', data=mda.calibration_table)
    else:
        cg.attrs['calibration_flag'] = 'no'
    ds = gr.create_dataset('image_data', data=img, compression=1)    
    ds.attrs['CLASS'] = 'IMAGE'
    ds.attrs['DISPLAY_ORIGIN'] = 'UL'
    gr = h5.create_group('satellite1')
    gr.attrs['satellite_name'] = mda.satname

    gr = h5.create_group('overview')
    gr.attrs['product_group_name']  = 'FSD_' + mda.satname + '_' + mda.channel + '_' + mda.sspname
    gr.attrs['product_datetime_start'] = mda.time_stamp.strftime('%d-%b-%Y %H:%M:%S.000')
    gr.attrs['product_datetime_end'] = mda.time_stamp.strftime('%d-%b-%Y %H:%M:%S.000')
    gr.attrs['number_image_groups'] = 1

    h5.close()
