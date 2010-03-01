=====================
 mpop/mipp interface
=====================

First, I thought that the interface should/would be a common level1.5 (level2)
file format (e.g a hdf5 format).

Second, I undestood, that ``mpop`` was directly reading the (uncompressed) `xrit` files.

Current interface
-----------------
From Martin, **satin/mipp.py** using **meteosat07.cfg**::

  [mviri]
  format=mipp
  dir=/local_disk/data/satellite/met7
  filename=L-000-MTP___-MET7________-%(channel)s_057E-%(segment)s-%Y%m%d%H%M-__

What about
----------
Common level1.5 configuration files::

  #
  # Level 1.5 configuration file for Meteosat-7
  #
  [satellite]
  satname = 'meteosat'
  number = '07'

  [instruments]
  name = 'mviri'

  [level1]
  format = 'mipp'
  dir = '/usr/local/safnwc/import/SEVIRI_data'
  filename = 'L-000-MTP___-MET7________-%(channel)s_057E-%(segment)s-%Y%m%d%H%M-__'
  area = 'FULL_DISK'

  [channel-1]
  name = '00_7'
  frequency = (0.5, 0.7, 0.9)
  resolution = 2500

  [channel-2]
  name = '06_4'
  frequency = (5.7, 6.4, 7.1)
  resolution = 5000

  [channel-3]
  name = '11_5'
  frequency = (10.5, 11.5, 12.5)
  resolution = 5000
