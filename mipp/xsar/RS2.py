#
# WORK IN PROGRESS for Radarsat-2
#
import numpy
from datetime import datetime
from lxml import etree

from mipp.xsar import Metadata

class TiePoints(object):
    def __init__(self, image, geodedic):
        self.image = image
        self.geodedic = geodedic

def read_metadata(xml_file):
    metadata = Metadata()    

    # XML Namespace
    ns_rs2 = {'xsi': 'http://www.rsi.ca/rs2/prod/xml/schemas'}

    # Speciel decoders
    def dec_isoformat(rts):
        return datetime.strptime(rts, "%Y-%m-%dT%H:%M:%S.%fZ")
    def dec_orbit_number(rts):
        return int(rts[:5])

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

    # Get some attributes
    for key, (att, dec) in attributes.items():
        if att.startswith('xsi'):
            rec = tree.xpath(att, namespaces=ns_rs2)
            if len(rec) > 1:
                val = tuple([dec(i.text) for i in rec])
            else:
                val = dec(rec[0].text)
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
    for elm in tiepoints_tree:
        if elm.tag.endswith('imageTiePoint'):
            pixel, line, lat, lon = None, None, None, None
            for i in elm.iter():
                if i.getparent().tag.endswith('imageCoordinate'):
                    if i.tag.endswith('pixel'):
                        pixel = float(i.text)
                    elif i.tag.endswith('line'):
                        line = float(i.text)
                elif i.getparent().tag.endswith('geodeticCoordinate'):
                    if i.tag.endswith('latitude'):
                        lat = float(i.text)
                    elif i.tag.endswith('longitude'):
                        lon = float(i.text)
            if None not in (pixel, line, lat, lon):
                pix_coordinates[counter] = [line, pixel]
                geo_coordinates[counter] = [lat, lon]
        counter += 1
        
    if counter > 0:
        setattr(metadata, 'tiepoints', TiePoints(pix_coordinates, geo_coordinates))

    return metadata

if __name__ == '__main__':
    import sys
    mda = read_metadata(sys.argv[1])
    print mda
    print mda.tiepoints.image
    print mda.tiepoints.geodedic
