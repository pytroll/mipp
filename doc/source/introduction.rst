======================
 mipp an introduction
======================

``mipp`` is a Meteorological Ingest-Processing Package (http://github.com/loerum/mipp).

 It's a Python libray and it's main task is to convert satellite level-1.5 data into a 
 format understood by ``mpop`` (http://github.com/mraspaud/mpop).

In the beginning, it will handle **MET7**, **GEOS11**, **GOES12** and **MTSAT1R**,
"eumetcasted" FSD data::

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


``mipp`` will:
  * decompress XRIT files.
  * decode/strip-off (according to [CGMS]_, [MTP]_, [SGS]_) XRIT headers and collect meta-data.
  * catenate image data into a numpy-array (if needed convert 10 bit data to 16 bit).

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

  It knows about satellites 
    * ``mda, image_date = read(prologue, image_files, only_metadata=False)``
    * ``mda = read_metadata(prologue, image_files)``

**Utilities**

.. describe:: convert.py

  10 to 16 byte converter (uses a little C extension)

.. describe:: bin_reader.py

  It reads binary data (network byte order)
   * ``read_uint1(buf)``
   * ``read_uint2(buf)``
   * ``read_float4(buf)``
   * ...

.. describe:: mda.py

  A simple (anonymous) metadata reader and writer

.. describe::  hdfdmi.py

  DMI's hdf5 format (writer)

Definition of a satellites
--------------------------
::

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
            

    def read(prologue, image_files):
        prologue = xrit.read_prologue(prologue)
        sd = satellites.get(prologue.platform, None)
        if sd == None:
            raise SatDecodeError("Unknown satellite: '%s'"%prologue.platform)
        return sd.read(prologue, image_files)


Usage
-----
.. code-block:: python

    import xrit

    mda, image_data = xrit.sat.read(sys.argv[1], sys.argv[2:])
    print mda
    fname = './' + mda.product_name + '.dat'
    print >>sys.stderr, 'Writing', fname
    fp = open(fname, "wb")
    image_data.tofile(fp)
    fp.close()

    # In the spirit of mpop, we should also have:
    mda, image_data = xrit.sat.read(sat_name, time_slot)


Script
------

.. describe:: process_fsd

::

    process_fsd --check [-l] <prologue-file>
        check if number of image segments are as planned
        -l, list corresponding image segment files
        
    process_fsd --decompress [-o<output-dir>] <file> ... <file>
        decompress files to output-dir (default is working directory)
        -l, list decompressed files
        
    process_fsd --metadata <prologue-file> <image-segment> ... <image-segment>
        print meta-data
        
    process_fsd [h] [-o<output-dir>] <prologue-file> <image-segment> ... <image-segment>
        -h, save image data to a HDF5 file
            (default is binary dump of image-data and ascii dump of meta-data)\


==============================

 .. rubric:: References:

 .. [CGMS] LRIT/HRIT Global Specification; CGMS 03; Issue 2.6; 12 August 1999 
    "MSG Ground Segment LRIT/HRIT Mission Specific Implementation"
    EUM/MSG/SPE/057; Issue 6; 21 June 2006 
 .. [MTP] "The Meteosat Archive; Format Guide No. 1; Basic Imagery: OpenMTP Format"; EUM FG 1; Rev 2.1; April 2000
 .. [SGS] "MSG Ground Segment LRIT/HRIT Mission Specific Implementation"; EUM/MSG/SPE/057; Issue 6; 21 June 2006
