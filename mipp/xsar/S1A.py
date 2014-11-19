# -*- coding: utf-8 -*-
"""
sentinel_manifest.py

Created on Tue Nov  4 13:23:22 2014

@author: ras
"""
import os
from lxml import etree
from datetime import datetime

from mipp.xsar import Metadata

SATELLITE = 's1a'
PIXEL_SPACING = {
    'sm-f': (4, 4),
    'sm-h': (10, 10),
    'sm-m': (40, 40),
    'iw-h': (10, 10),
    'iw-m': (40, 40),
    'ew-h': (25, 25),
    'ew-m': (40, 40),
    'wv-m': (25, 25),
    }

def read_metadata(dirname):
    """Main intrance to extract metadata for a Sentinel-1 product.
    
    :Parameters:
        dirname : str
            Path to top directory.

    :Returns:
        manifest : Metadata object
            Selected paramters
    """
    dirname_mda = decode_dirname(dirname)
    return read_manifest(os.path.join(dirname, 'manifest.safe'), **dirname_mda)

def decode_dirname(dirname):
    """Decode a top Sentinel-1 directory name (or zip file), like
    S1A_EW_GRDH_1SDH_20140426T100912_20140426T101016_000329_000232_C5DF.SAFE[.zip]

    Ref: S1-RS-MDA-52-7440

    :Parameters:
        dirname : str
            Path to top directory.

    :Returns:
        metadata : dictionary
            Paramters
    """
    _POLARISATIONS = {'sh': ['hh'],
                      'sv': ['vv'],
                      'dh': ['hh', 'hv'],
                      'dv': ['vv', 'vh'],
                      'hh': ['hh'],
                      'hv': ['hv'],
                      'vv': ['vv'],
                      'vh': ['vh']}

    # Also handle zip files
    names = os.path.basename(dirname).split('.')
    dname, ext = names[:2]
    items = dname.split('_')
    mda = {'mission_id': items[0].lower(),
           'instrument_mode': items[1].lower(),
           'product_type': items[2][:3].lower(),
           'resolution_class': items[2][3].lower(),
           'processing_level': items[3][0].lower(),
           'product_class': items[3][1].lower(),
           'polarisations': _POLARISATIONS[items[3][2:4].lower()],
           'start_time': datetime.strptime(items[4], "%Y%m%dT%H%M%S"),
           'stop_time': datetime.strptime(items[5], "%Y%m%dT%H%M%S"),
           'orbit_number': items[6].lower(),
           'mission_data_id': items[7],
           'product_id': items[8],
           'product_format': ext[1:]}
    mda['channels'] = []
    for p__ in mda['polarisations']:
        mda['channels'].append('-'.join((mda['instrument_mode'], mda['resolution_class'], p__)))
    return mda
    
def read_manifest(filename, **mdax):
    """Read a Sentinel-1 manifest file, and extract selected parameters.

    :Parameters:
        filename : str
            Path to manifest file.

    :Returns:
        manifest : Metadata object
            Selected paramters
    """
    def parse_orbit(elm):
        if elm.get('type').lower() == 'start':
            return int(elm.text)

    def parse_text(elm):
        return elm.text

    def parse_tolower(elm):
        return elm.text.lower()

    def parse_satellite(elm):
        if elm.text.lower().startswith('sen'):
            return elm.text.lower()

    def parse_time(elm):
        return datetime.strptime(elm.text, "%Y-%m-%dT%H:%M:%S.%f")

    def parse_coordinates(elm):
        cor = elm.text.split()
        arr = []
        for c in cor:
            y, x =  [float(i) for i in c.split(',')]
            arr.append((x, y))
        return arr

    def parse_files(elm):
        fname = elm.get('href')        
        if fname and fname.startswith('./measurement/'):
            return os.path.join(basedir, fname[2:])
    
    named_decoder = {
        '{http://www.esa.int/safe/sentinel-1.0}startTime': (
            'start_time', 1, parse_time),
        '{http://www.esa.int/safe/sentinel-1.0}stopTime': (
            'stop_time', 1, parse_time),
        '{http://www.opengis.net/gml}coordinates': (
            'coordinates', 1, parse_coordinates),
        '{http://www.esa.int/safe/sentinel-1.0}orbitNumber': (
            'orbit_number', 1, parse_orbit),
        '{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}mode': (
            'instrument_mode', 1, parse_tolower),
        '{http://www.esa.int/safe/sentinel-1.0}familyName': (
            'satellite', 1, parse_satellite), # dublicated !
        '{http://www.esa.int/safe/sentinel-1.0/sentinel-1}pass': (
            'pass', 1, parse_tolower),
        '{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}transmitterReceiverPolarisation': (
            'polarisations', 2, parse_tolower),
        '{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}productClassDescription': (
            'description', 1, parse_text),
        '{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}productType': (
            'product_type', 1, parse_tolower),
        'fileLocation': (
            'files', 2, parse_files),
        }

    tags = named_decoder.keys()

    manifest = Metadata()
    basedir = os.path.dirname(filename)

    with open(filename) as fp:
        xml = etree.parse(fp)
        for e in xml.getroot().iter():
            if e.tag in tags:
                name, count, decoder =  named_decoder[e.tag]
                value = decoder(e)
                if value:
                    if count > 1:
                        try: 
                            getattr(manifest, name).append(value)
                        except AttributeError:
                            setattr(manifest, name, [value])
                    else:
                        setattr(manifest, name, value)

    # Add extra metadata 
    for key, val in mdax.items():
        if not hasattr(manifest, key):
            setattr(manifest, key, val)

    try:
        resolution = manifest.resolution_class
        channels = {}
        for pol in manifest.polarisations:
            _text = '-'.join([SATELLITE, manifest.instrument_mode, manifest.product_type, pol])
            _name = '-'.join([manifest.instrument_mode, resolution, pol])
            for fn in manifest.files:
                if os.path.basename(fn).startswith(_text):
                    channels[_name] = fn
        manifest.channels = channels
        manifest.pixel_spacing = PIXEL_SPACING[manifest.instrument_mode + '-' + resolution]
    except AttributeError:
        pass
                
    return manifest

if __name__ == '__main__':
    import sys
    print read_metadata(sys.argv[1])
