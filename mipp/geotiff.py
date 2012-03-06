from osgeo import gdal, osr

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
    geotransform = dst.GetGeoTransform()
    projection = dst.GetProjection()
    metadata = dst.GetMetadata()

    logger.debug('description: %s'%dst.GetDescription())
    logger.debug('driver: %s / %s'%(dst.GetDriver().ShortName,
                                    dst.GetDriver().LongName))
    logger.debug('size: %d x %d x %d'%(dst.RasterXSize, dst.RasterYSize,
                                       dst.RasterCount))
    logger.debug('geo transform: %s'%str(geotransform))
    logger.debug('origin: %.3f, %.3f'%(geotransform[0], geotransform[3]))
    logger.debug('pixel size: %.3f, %.3f'%(geotransform[1], geotransform[5]))
    logger.debug('projection: %s'%projection)
    logger.debug('metadata: %s', metadata)

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

    params = dict((('geotransform', geotransform),
                   ('projection', projection),
                   ('metadata', metadata)))

    return params, data
