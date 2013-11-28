============================
 python-mipp an introduction
============================

``mipp`` is a Meteorological Ingest-Processing Package (http://github.com/loerum/mipp).

 It's a Python library and it's main task is to convert low level satellite
 data into a format understood by ``mpop``
 (http://github.com/mraspaud/mpop). The primary purpose is to support
 Geostationary satellite data (level 1.5) but there is also support for the
 reading of some polar orbiting SAR data (see below).

 A more sophisticated interface to satellite data objects is supported by ``mpop``.

Currently it handles data from all current Meteosat Second Generation (MSG)
satellites, Meteosat 7, GOES 11-15, MTSAT's, and GOMS, all as retrieved via EUMETCast::

  L-000-MTP___-MET7________-00_7_057E-PRO______-201002261600-__
  L-000-MTP___-MET7________-00_7_057E-000001___-201002261600-C_
  L-000-MTP___-MET7________-00_7_057E-000002___-201002261600-C_
  L-000-MTP___-MET7________-00_7_057E-000003___-201002261600-C_
  ...
  ...
  L-000-MSG2__-GOES11______-00_7_135W-PRO______-201002261600-__
  L-000-MSG2__-GOES11______-00_7_135W-000001___-201002261600-C_
  L-000-MSG2__-GOES11______-00_7_135W-000002___-201002261600-C_
  L-000-MSG2__-GOES11______-00_7_135W-000003___-201002261600-C_
  ...
  ...

In addition ``mipp`` handles Synthetic Apperture Radar (SAR) data from
Terrscan-X, Cosmo-Sky Med, and Radarsat 2.

``mipp`` will:

  * Decompress XRIT files (if Eumetsat's ``xRITDecompress`` is
    available). Software to uncompress HRIT/XRIT can be obtained from EUMETSAT
    (register and download the `Public Wavelet Transform Decompression Library
    Software`_). Please be sure to set the environment variable
    ``XRIT_DECOMPRESS_PATH`` to point to the full path to the decompression
    software, e.g. ``/usr/bin/xRITDecompress``. Also you can specify where the
    decompressed files should be stored after decompression, using the
    environment variable ``XRIT_DECOMPRESS_OUTDIR``. If this variable is not
    set the decompressed files will be found in the same directory as the
    compressed ones.


  * Decode/strip-off (according to [CGMS]_, [MTP]_, [SGS]_) XRIT headers and collect meta-data.

  * Catenate image data into a numpy-array.

    * if needed, convert 10 bit data to 16 bit
    * if a region is defined (by a slice or center, size), only read what is specified.

.. note::

    * MET7: not calibrated.
    * GOES, METSAT: calibration constants to Kelvin or Radiance (not Reflectance).



Code Layout
-----------

.. describe:: xrit.py

  It knows about the genric HRIT/XRIT format

  * ``headers = read_headers(file_handle)``

.. describe:: MTP.py

  It knows about the specific format OpenMTP for MET7

  * ``mda = read_metadata(prologue, image_file)``

.. describe:: SGS.py

  It knows about the specific format Support Ground Segments for GOES and MTSAT

  * ``mda = read_metadata(prologue, image_files)``

.. describe:: sat.py

  It knows about satellites base on configurations files. 
  It returns a slice-able object (see below).

  * ``image = load('met7', time_stamp, channel, mask=False, calibrated=True)``
  * ``image = load_files(prologue, image_files, **kwarg)``

.. describe:: slicer.py

  It knows how to slice satellite images (return from ``load(...)``).
  It returns meta-data and a numpy array.

  * ``mda, image_data = image[1300:1800,220:520]``
  * ``mda, image_data = image(center, size)``

**Utilities**

.. describe:: cfg.py

  It knows how to read configuration files, describing satellites (see below).

.. describe:: convert.py

  10 to 16 byte converter (uses a C extension)

.. describe:: bin_reader.py

  It reads binary data (network byte order)

  * ``read_uint1(buf)``
  * ``read_uint2(buf)``
  * ``read_float4(buf)``
  * ...

.. describe:: mda.py

  A simple (anonymous) metadata reader and writer

.. describe:: geosnav.py

  It will convert from/to pixel coordinates to/from geographical longitude, latitude coordinates.

Example definition of a satellite
---------------------------------
.. code-block:: ini

  # An item like:
  #   name = value
  # is read in python like:
  #   try:
  #       name = eval(value)
  #   except:
  #       name = str(value)
  #

  [satellite]
  satname = 'meteosat'
  number = '07'
  instruments = ('mviri',)
  projection = 'geos(57.0)'

  [mviri-level2]
  format = 'mipp'

  [mviri-level1]
  format = 'xrit/MTP'
  dir = '/data/eumetcast/in'
  filename = 'L-000-MTP___-MET7________-%(channel)s_057E-%(segment)s-%Y%m%d%H%M-__'

  [mviri-1]
  name = '00_7' 
  frequency = (0.5, 0.7, 0.9)
  resolution = 2248.49
  size = (5000, 5000)

  [mviri-2]
  name = '06_4'
  frequency = (5.7, 6.4, 7.1)
  resolution = 4496.98
  size = (2500, 2500)

  [mviri-3]
  name = '11_5'
  frequency = (10.5, 11.5, 12.5)
  resolution = 4496.98
  size = (2500, 2500)


Usage
-----
.. code-block:: python

    import xrit

    image = xrit.sat.load('meteosat07', datetime(2010, 2, 1, 10, 0), '00_7', mask=True)
    mda, image_data = image(center=(50., 10.), size=(600, 500))
    print mda
    fname = './' + mda.product_name + '.dat'
    print >>sys.stderr, 'Writing', fname
    fp = open(fname, "wb")
    image_data.tofile(fp)
    fp.close()


Examples of the usage of some lower level tools
-----------------------------------------------
 
Here an example how to get the observation times (embedded in the 'Image
Segment Line Quality' record) of each scanline in a segment:

.. code-block:: python

    import mipp.xrit.MSG

    segfile = "/local_disk/data/MSG/HRIT/H-000-MSG3__-MSG3________-WV_062___-000002___-201311211300-__"
    lineq = mipp.xrit.MSG.get_scanline_quality(segfile)
    print lineq[0]
   
    (465, datetime.datetime(2013, 11, 21, 13, 1, 48, 924000), 1, 1, 0)
    

A script, process_fsd
---------------------

The script is intended for work on other geostationary data than the MSG
(Meteosat) data, the so-called Foreign Satellite Data (FSD). That is e.g. GOES,
MTSAT and COMS.

.. code-block:: text

    process_fsd --check-satellite <prologue-file>
        check if we handle this satellite
        
    process_fsd --check [-l] <prologue-file>
        check if number of image segments are as planned
        -l, list corresponding image segment files
        
    process_fsd --decompress [-o<output-dir>] <file> ... <file>
        decompress files to output-dir (default is working directory)
        -l, list decompressed files
        
    process_fsd --metadata <prologue-file> <image-segment> ... <image-segment>
        print meta-data
        
    process_fsd [-o<output-dir>] <prologue-file> <image-segment> ... <image-segment>
        it will binary dump image-data and ascii dump of meta-data)


==============================

 .. _Public Wavelet Transform Decompression Library Software: http://www.eumetsat.int/website/home/Data/DataDelivery/SupportSoftwareandTools/index.html
 .. [CGMS] LRIT/HRIT Global Specification; CGMS 03; Issue 2.6; 12 August 1999 
    "MSG Ground Segment LRIT/HRIT Mission Specific Implementation"
    EUM/MSG/SPE/057; Issue 6; 21 June 2006 
 .. [MTP] "The Meteosat Archive; Format Guide No. 1; Basic Imagery: OpenMTP Format"; EUM FG 1; Rev 2.1; April 2000
 .. [SGS] "MSG Ground Segment LRIT/HRIT Mission Specific Implementation"; EUM/MSG/SPE/057; Issue 6; 21 June 2006




