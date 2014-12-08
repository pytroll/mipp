from osgeo import gdal, osr
import numpy as np

import logging
logger = logging.getLogger('mipp')

def tiff2areadef(projection, geotransform, shape):
    # Rewamp projection
    import pyresample

    srs = osr.SpatialReference()
    srs.ImportFromWkt(projection)
    proj4 = srs.ExportToProj4()
    proj4_dict = {}
    for i in proj4.replace('+', '').split():
        try:
            key, val = [v.strip() for v in i.split('=')]
        except ValueError:
            continue        
        proj4_dict[key] = val

    area_extent = [geotransform[0],
                   geotransform[3] + geotransform[5]*shape[0],
                   geotransform[0] + geotransform[1]*shape[1],
                   geotransform[3]]
    aid = proj4_dict['proj']
    if aid.lower() == 'utm':
        aid += proj4_dict['zone']
    # give it some kind of ID
    aname = aid + '_' + str(int(sum(geotransform)/1000.))

    return pyresample.utils.get_area_def(aname, aname, aid,
                                         proj4_dict,
                                         shape[1], shape[0],
                                         area_extent)

def read_geotiff(filename):
    dst = gdal.Open(filename)

    #
    # Dataset information
    #
    metadata = dst.GetMetadata()
    logger.debug('description: %s'%dst.GetDescription())
    logger.debug('driver: %s / %s'%(dst.GetDriver().ShortName,
                                    dst.GetDriver().LongName))
    logger.debug('size: %d x %d x %d'%(dst.RasterXSize, dst.RasterYSize,
                                       dst.RasterCount))
    logger.debug('metadata: %s', metadata)

    if dst.GetProjectionRef():
        #
        # Affine georeferencing transform will be returned by GetGeoTransform().
        # (Terra, CosmoSkyMed)
        #
        geotransform = dst.GetGeoTransform()
        projection = dst.GetProjection()

        logger.info('GEO transform: %s'%str(geotransform))
        logger.debug('origin: %.3f, %.3f'%(geotransform[0], geotransform[3]))
        logger.debug('pixel size: %.3f, %.3f'%(geotransform[1], geotransform[5]))
        logger.debug('projection: %s'%projection)

        params = dict((('geotransform', geotransform),
                       ('projection', projection),
                       ('metadata', metadata)))

    elif dst.GetGCPProjection():
        #
        # Coordinate system is defined by GetGCPs() (tiepoints).
        # (Radarsat-2, Sentinel-1)
        #
        metadata['GCPProjection'] = dst.GetGCPProjection()
        logger.info("GCP Projection '%s'" % str(dst.GetGCPProjection()))
        tiep_count = dst.GetGCPCount()

        rows, cols, lons, lats = [], [], [], []
        n_cols, n_rows, _row = 0, 0, -1
        for gcp in dst.GetGCPs():
            if gcp.GCPLine != _row:
                rows.append(gcp.GCPLine)
                n_rows += 1
                n_cols = 0
                _row = gcp.GCPLine
            if gcp.GCPLine == 0:
                cols.append(gcp.GCPPixel)
            n_cols += 1
            lons.append(gcp.GCPX)
            lats.append(gcp.GCPY)

        #print  'Tiepoints', dst.GetGCPCount()
        logger.debug("Tiepoint shape (rows, columns): %d, %d" % (n_rows, n_cols))
        lons = np.array(lons, dtype=np.float).reshape((n_rows, n_cols))
        lats = np.array(lats, dtype=np.float).reshape((n_rows, n_cols))
        rows = np.array(rows, dtype=np.int)
        cols = np.array(cols, dtype=np.int)

        ##print "Regular grid ?"
        ##for i in (('row', rows), ('col', cols)):
        ##    name, data = i
        ##    j0 = data[0]
        ##    for j in data[1:]:
        ##        print name, j, j - j0
        ##        j0 = j

        tiepoints = dict((('rows', rows),
                          ('cols', cols),
                          ('lons', lons),
                          ('lats', lats)))
        
        params = dict((('tiepoints', tiepoints),
                       ('metadata', metadata)))

    #
    # Fetching raster data
    #
    band = dst.GetRasterBand(1)
    logger.info('Band(1) type: %s, size %d x %d'%(
            gdal.GetDataTypeName(band.DataType),
            dst.RasterXSize, dst.RasterYSize))
    shape = (dst.RasterYSize, dst.RasterXSize)
    if band.GetOverviewCount() > 0:
        logger.debug('overview count: %d'%band.GetOverviewCount())
    if not band.GetRasterColorTable() is None:
        logger.debug('colortable size: %d'%
                     band.GetRasterColorTable().GetCount())

    data = band.ReadAsArray(0, 0, shape[1], shape[0])
    logger.info('fetched array: %s %s %s [%d -> %.2f -> %d]'%
                (type(data), str(data.shape), data.dtype,
                 data.min(), data.mean(), data.max()))

    return params, data

if __name__ == '__main__':
    import sys
    import mpop.utils
    from geotiepoints import SatelliteInterpolator

    logger = mpop.utils.get_logger('mipp')
    mpop.utils.debug_on()

    params, data = read_geotiff(sys.argv[1])
    tie_lons = params['tiepoints']['lons']
    tie_lats = params['tiepoints']['lats']
    tie_cols = params['tiepoints']['cols']
    tie_rows = params['tiepoints']['rows']
    
    # From tie_cols and tie_rows, generate a gegulaer grid
    #fine_rows = np.arange(0, 3085, 257)
    #fine_cols = np.arange(0, 6313, 332)
    fine_rows = np.arange(0, 15436, 250)
    fine_cols = np.arange(0, 31561, 250)
    

    #print params
    #fine_cols = np.arange(0, data.shape[1])
    #fine_rows = np.arange(0, data.shape[0])

    interpolator = SatelliteInterpolator((tie_lons, tie_lats),
                                         (tie_rows, tie_cols),
                                         (fine_rows, fine_cols),
                                         1, 3)
    #np.save('tie_lons.npy', tie_lons)
    #np.save('tie_lats.npy', tie_lats)
    #np.save('tie_cols.npy', tie_cols)
    #np.save('tie_rows.npy', tie_rows)
    #np.save('fine_cols.npy', fine_cols)
    #np.save('fine_rows.npy', fine_rows)
    lons, lats = interpolator.interpolate()
    print 'RESULT :'
    print lons
    print lats
    np.save('result_lons.npy', lons)
    np.save('result_lats.npy', lats)
    #print 'DATA'
    #print data.shape
    #print data
    #print 'LON'
    #print lons.shape
    #print lons
    #print 'LAT'
    #print lats.shape
    #print lats


