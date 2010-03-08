=====================
 mpop/mipp interface
=====================

First, I thought that the interface should/would be a common level1.5 (level2)
file format.

Second, I undestood, that ``mpop`` was directly reading the (uncompressed) `xrit` files.


Current interface
-----------------
From Martin, ``mpop``'s configuration file **meteosat07.cfg**::

  [mviri]
  format=mipp
  dir=/local_disk/data/satellite/met7
  filename=L-000-MTP___-MET7________-%(channel)s_057E-%(segment)s-%Y%m%d%H%M-__

used by **satin/mipp.py**::

  meta_data, image_data = xrit.sat.read(prologue_filename, filelist)

The above should be replaces by, e.g::

  meta_data, image_data = xrit.sat.load_meteosat07(time_slot, channel)

Options
-------

Common SatelliteScene object ?
##############################
``mpop``, using inheritance::

  class Meteosat07MviriScene(MviriScene)(area, time_slot)
      # satellite definition

      class MviriScene(VisirScene)(area, time_slot)
          # Channel definitions
          channel_list = MVIRI
          instrument_name = "mviri"

          class VisirScene(SatelliteInstrumentScene)
              # Image (RGB) building !!!
              overview()

              class SatelliteInstrumentScene(SatelliteScene)(area, time_slot)
                  # Channel loader, channel accesser
                  get_channel() (__getitem__)
                  load(), get reader from configfile
                  project() !!!

                  class SatelliteScene(area, time_slot):
                      names
                      time_slot    

``MviriScene`` (or ``SeviriScene``) is where channels are defined ... it's a big objects, including 
image building and resampling. 

We could decouple with mixin-classes::

  class Meteosat07MviriScene(MviriScene, ImageBuilder, Resampler)

or composite::

  ImageBuilder.__init__(SatellitScene, ...)
  Resampler.__init__(SatellitScene, ...)

or::
  
  ...

**But no problem as it is now**, we could have


Common configuration files ?
############################

Common level1.5 configuration files::

  #
  # Level 1.5 configuration file for Meteosat-7
  #
  [satellite]
  satname = 'meteosat'
  number = '07'

  [instruments]
  name = 'mviri'

  [level2]
  format = 'mipp'

  [level1]
  format = 'xrit-mtp'
  dir = '/usr/local/safnwc/import/SEVIRI_data'
  filename = 'L-000-MTP___-MET7________-%(channel)s_057E-%(segment)s-%Y%m%d%H%M-__'
  area = 'FULL_DISK'

  [channel-1]
  name = '00_7'
  frequency = (0.5, 0.7, 0.9)
  resolution = 2500.0
  size = (5000, 5000) # total size
                      # NWCLIB can define sub-areas (in satellite projection)

  [channel-2]
  name = '06_4'
  frequency = (5.7, 6.4, 7.1)
  resolution = 5000.0
  size = (2500, 2500)

  [channel-3]
  name = '11_5'
  frequency = (10.5, 11.5, 12.5)
  resolution = 5000.0
  size = (2500, 2500)

and common environment variables::

  export PPP_CONFIG_DIR = '/opt/mpop/etc'
  export PPP_PYTHONPATH = '/opt/mpop/lib/python2.5/site-packages:/opt/lib/python2.5/site-packages'
  ...
  ...


``mpop`` would then::

    mda, image_data = xrit.sat.load_meteosat07(time_slot, channel)

where `meteosat07` point to our common configuration file
