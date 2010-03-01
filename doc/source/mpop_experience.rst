=========================
 mpop an user experience
=========================

It works !!!
------------
.. image:: _static/MSG2_20100217_1330_overview.png

Installing and running
----------------------
Made a debian package installing in ``/opt/mpop`` (later we will probaly install
the python library in ``/opt/lib/python2.5/site-packages/mpop``)

From ``acpg`` we stripped off:
  area.py, pcs.py, Proj.py, _projmodule.so, _satproj.so, pps_plugin_loader.py
  ... stopped counting.

``hlhdf``:
  _pyhlmodule.so

::

  > export SM_REGION_CONFIGURATION_FILE=/opt/etc/region_config.cfg
  > export PYTHONPATH=${PYTHONPATH}:/opt/mpop/lib/python2.5/site-packages

  > python
  >>> import pp.satellites.meteosat09 as met09
     Environment variable SM_AVHRR_DIR not set!
     Environment variable SM_CST_DIR not set!
     Environment variable SM_AUXILIARY_DIR not set!
     Environment variable SM_ICEMAPSOURCE_DIR not set!
     Environment variable SM_ICEMAPDATA_DIR not set!
     Environment variable SM_USGS_DIR not set!
     Environment variable SM_SUNSATANGLES_DIR not set!
     Environment variable SM_THRESHOLD_IMAGE_DIR not set!
     Environment variable SM_NWPSOURCE_DIR not set!
     Environment variable SM_NWPDATA_DIR not set!
     Environment variable SM_PRODUCT_DIR not set!
     Environment variable SM_AAPP_DATA_DIR not set!
     Environment variable AAPP_VERSION not set!
     Environment variable DIR_EPHE not set!
     Environment variable TMP_DIR not set!
     Environment variable PFS_LVL1_DIR not set!
     Environment variable BUFR_LVL1_DIR not set!
     Environment variables RTTOV_COEFF_DIR and/or RTTOV_COEFF_DIR not set!
     Couldn't find environment variable SM_NEWNAMES!
     Couldn't find environment variable SM_OVERWRITE!
     Environment variable DATA_DIR not set!

  >>> import datetime
  >>> time_slot = datetime.datetime(2010, 2, 27, 13, 30)
  >>> global_data = met09.Meteosat09SeviriScene(area="MSGF", time_slot=time_slot)
  >>> global_data.load([0.6, 0.8, 10.8])
  >>> img = global_data.overview()
  >>> img.save("./overview.png") # see above

* No problems reading MSG7, using Martins ``satin/mipp.py``.
* Once in a while it will not read HRV (to much non-empty data ?).

