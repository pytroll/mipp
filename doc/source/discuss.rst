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
  * Someone should define our hdf5 format, based on OPERA style ?
  * Memory usage (cleanup ?)
      For MSGN (928x3712)
      ``seviri.hr_overview`` uses more that 2 GB of memory (``overview`` is using 300 MB).
      One channel is using 4*928*3712 = 14 MB (pynwclib.c *3 for each channel),
      we are handling four channels, it's 180 MB ... a long way to 2000 MB


NWCLIB
------
I though it was just decofing HRIT files, extracting calibrations constants etc, but::

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
