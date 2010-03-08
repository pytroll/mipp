=========================
 Comments and discussion
=========================

Some points
-----------
  * It should be independent of ``nwclib`` (or nwclib should be made open)
  * It should be independent of ``acpg`` (using python-numeric)
  * We should agree on third party software
      * SMHI: ``_pyhl``, ``_satproj``, ``_proj``
      * DMI: ``h5py``, ``pyproj``
  * Someone should define our hdf5/netcdf-4 format, based on OPERA style ?
    (in that process don't forget OpenNDap, netcdf ...)
  * Is there a need for "analyze" memory usage ?.

    For MSGN (928x3712)
      ``seviri.hr_overview`` uses more that 2 GB of memory (``overview`` is using 300 MB).
      One channel is using 4x928x3712 = 14 MB (pynwclib.c x3 for each channel),
      we are handling four channels, it's 180 MB.


NWCLIB
------
I thought ``nwclib`` just was decoding HRIT files, extracting calibrations constants etc, but::

	|   2.- FOR L15 CONTAINING SPECTRAL RADIANCE RELATED COUNTS (Pre XXX-08)
	|   --------------------------------------------------------------------
	|   The following Schema is implemented:
	|   2.1.- Spectral Radiances are computes using the linear relationship
	|            Spectral Radiance = Counts * CAL_SLOPE + CAL_OFFSET
	|   2.2.- Brightness Temperature is computed just inverting the Planck
	|         function at the wavelength of the channel
	|   2.3.- A polynomial fit is needed to correct the deviation between
	|         brightness temp generated from spectral radiances
	|         (see SAF/NWC/CDOP/INM/SCI-TN/2 doc)
	|            BT = (BT_spec * BT_spec)* A + BT_spec * B + C
	|         Values for A, B, C coefficients are read from the Satellite
	|         Configuration File :
	|         (BTFIT_A_XXX, BTFIT_B_XXX and BTFIT_C_XXX keywords)
	|   2.4.- Effective Radiances are computed inverting the EUMETSAT
	|         formula relating Effective Radiances with BT
	|

From ``pynwclib``::

            if(read_rad)
              rad = (PyArrayObject *)SimpleNewFrom2DData(2,hr_dims,NPY_FLOAT,
                                                         SevBand(hr_seviri,channel,RAD));
            else
              rad = (PyArrayObject *)PyArray_EMPTY(2, hr_dims, NPY_FLOAT,0);
            if(SevBand(hr_seviri,channel,REFL)!=NULL)
              {
                cal = (PyArrayObject *)SimpleNewFrom2DData(2,hr_dims,NPY_FLOAT,
                                                           SevBand(hr_seviri,channel,REFL));
              }
            else
              {
                cal = (PyArrayObject *)SimpleNewFrom2DData(2,hr_dims,NPY_FLOAT,
                                                           SevBand(hr_seviri,channel,BT));
              }
