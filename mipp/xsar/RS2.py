#
# WORK IN PROGRESS
#
import numpy
from datetime import datetime
from lxml import etree

from mipp.xsar.mda import Metadata

class TiePoints(object):
    def __init__(self, image, geodedic):
        self.image = image
        self.geodedic = geodedic

def read_metadata(xml_file):
    metadata = Metadata()    

    # XML Namespace
    ns_rs2 = {'xsi': 'http://www.rsi.ca/rs2/prod/xml/schemas'}

    # Speciel decoders
    def dec_isoformat(s):
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")
    def dec_orbit_number(s):
        return int(s[:5])

    attributes = {
        'product_id': ('xsi:productId', str),
        'satellite_name': ('xsi:sourceAttributes/xsi:satellite', str),
        'sensor_name': ('xsi:sourceAttributes/xsi:sensor', str),
        'beam_mode': ('xsi:sourceAttributes/xsi:beamModeMnemonic', str),
        'facility_id': ('xsi:sourceAttributes/xsi:inputDatasetFacilityId', str),
        'start_time': ('xsi:sourceAttributes/xsi:rawDataStartTime', dec_isoformat),
        'orbit_number': ('xsi:sourceAttributes/xsi:orbitAndAttitude/xsi:orbitInformation/xsi:orbitDataFile', dec_orbit_number),
        'product_format': ('xsi:imageAttributes/xsi:productFormat', str),
        'bits_per_sample': ('xsi:imageAttributes/xsi:rasterAttributes/xsi:bitsPerSample', int),
        'samples': ('xsi:imageAttributes/xsi:rasterAttributes/xsi:numberOfSamplesPerLine', int),
        'lines': ('xsi:imageAttributes/xsi:rasterAttributes/xsi:numberOfLines', int),
        'sample_spacing': ('xsi:imageAttributes/xsi:rasterAttributes/xsi:sampledPixelSpacing', float),
        'line_spacing': ('xsi:imageAttributes/xsi:rasterAttributes/xsi:sampledLineSpacing', float),
        'data_files': ('xsi:imageAttributes/xsi:fullResolutionImageData', str),
        'center_lat': ('centre_lat', str),
        'center_lon': ('centre_lon', str),
        'tie_point_lines': ('tie_point_lines', str),
        'tie_point_samples': ('tie_point_samples', str),
        'tie_point_line_jump': ('tie_point_line_jump', str),
        'tie_point_sample_jump': ('tie_point_sample_jump', str)}

    tree = etree.parse(xml_file)

    # Get some atributes
    for key, (att, dec) in attributes.items():
        if att.startswith('xsi'):
            r = tree.xpath(att, namespaces=ns_rs2)
            if len(r) > 1:
                val = tuple([dec(i.text) for i in r])
            else:
                val = dec(r[0].text)
            setattr(metadata, key, val)

    #
    # Get tiepoints
    #
    tiepoints_xpath = 'xsi:imageAttributes/xsi:geographicInformation/xsi:geolocationGrid/xsi:imageTiePoint'
    tiepoints_tree = tree.xpath(tiepoints_xpath, namespaces=ns_rs2)
    tiepoints_count = len(tiepoints_tree)

    pix_coordinates = numpy.zeros((tiepoints_count, 2))
    geo_coordinates = numpy.zeros((tiepoints_count, 2))
    counter = 0
    for e in tiepoints_tree:
        if e.tag.endswith('imageTiePoint'):
            pixel, line, lat, lon = None, None, None, None
            for c in e.iter():
                if c.getparent().tag.endswith('imageCoordinate'):
                    if c.tag.endswith('pixel'):
                        pixel = float(c.text)
                    elif c.tag.endswith('line'):
                        line = float(c.text)
                elif c.getparent().tag.endswith('geodeticCoordinate'):
                    if c.tag.endswith('latitude'):
                        lat = float(c.text)
                    elif c.tag.endswith('longitude'):
                        lon = float(c.text)
            if None not in (pixel, line, lat, lon):
                pix_coordinates[counter] = [line, pixel]
                geo_coordinates[counter] = [lat, lon]
        counter += 1
        
    if counter > 0:
        setattr(metadata, 'tiepoints', TiePoints(pix_coordinates, geo_coordinates))

    return metadata

if __name__ == '__main__':
    import sys
    md = read_metadata(sys.argv[1])
    print md
    print md.tiepoints.image
    print md.tiepoints.geodedic
