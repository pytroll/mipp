Changelog
=========


v1.1.0 (2018-04-11)
-------------------
- Update changelog. [Martin Raspaud]
- Bump version: 1.0.0 → 1.1.0. [Martin Raspaud]
- Merge pull request #12 from pytroll/fix-missing-image-segments. [Panu
  Lahtinen]

  Handle missing image segment data for MSG/XRIT
- Handle missing image segment data for MSG/XRIT data by raising
  ReaderError. [Panu Lahtinen]
- Merge pull request #10 from loreclem/pre-master. [Martin Raspaud]

  Added test to check the  1.5 km georeferencing shift
- Added test to check whether to apply the  1.5 km georeferencing
  correction or not. [lorenzo clementi]
- Delay the end of the 1.5 km correction. [Martin Raspaud]
- Fix 1.5 km shift correction for MSG. [Martin Raspaud]


v1.0.0 (2016-10-27)
-------------------
- Update changelog. [Martin Raspaud]
- Bump version: 0.10.0 → 1.0.0. [Martin Raspaud]
- Merge branch 'master' into release-1.0.0. [Martin Raspaud]

  Conflicts:
  	mipp/xrit/MSG.py

- Merge branch 'pre-master' [Martin Raspaud]

  Conflicts:
  	mipp/xrit/MSG.py
- Merge pull request #5 from sebiegli/master. [Martin Raspaud]

  fixed Issue #4
- Fixed Issue #4. [Sebastian]
- Add bump and changelog config files. [Martin Raspaud]
- Fix pep8 compliance. [Martin Raspaud]
- Accept unicode filenames. [Martin Raspaud]
- Fix the lowering of case in load_files for the platform name. [Martin
  Raspaud]
- Allow platform name to be provided to load_files. [Martin Raspaud]

  This is usefull for H8 files for exemple, since they don't have
  prologues.
- Fixed Issue #4. [Sebastian]
- Corrected tests, after last checkin. [Lars Orum Rasmussen]
- Sentinel reader independent of S1A and S1B. [Lars Orum Rasmussen]
- Define download_url. [Lars Orum Rasmussen]

  Better url (usr pytroll organization)

  pep8



v0.10.0 (2016-05-16)
--------------------
- Update changelog. [Martin Raspaud]
- Bump version: 0.9.2 → 0.10.0. [Martin Raspaud]
- Fix version handling in the documentation. [Martin Raspaud]
- Modify version string building for easier handling. [Martin Raspaud]

  Since some use scripts to update the version number, it is better to have
  the version string in a simple format.
- Fix HRV vs low-res channels collocation. [Martin Raspaud]
- Update the MSG header format with GSICS coefficients. [Martin Raspaud]
- Fix the LRIT MSG (8 bits) calibration. [Martin Raspaud]

  In the case for LRIT MSG, the calibration was erroneous since the counts
  are rounded to 8 bits instead of 10. In order for the calibration to work,
  the raw counts have to be multiplied by 4 before hand. At the same time,
  the data is converted to 16 uints for the multiplication to work.
- Define default header map and types in case satellite loader isn't
  used. [Martin Raspaud]
- Fix line offset for himawari 8. [Martin Raspaud]
- Fix dynamic header_maps loading. Closes #3. [Martin Raspaud]
- Add Himawari-8 JMA-HRIT support. [Martin Raspaud]
- Add setup.cfg to allow rpm building with bdist_rpm. [Martin Raspaud]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Martin Raspaud]
- Better and more meta-data. [Lars Orum Rasmussen]
- Less noisy. [Lars Orum Rasmussen]
- Added a metadata reader for sentinel-1. [Lars Orum Rasmussen]
- Removing debian directories, which by a mistake was added. [Lars Orum
  Rasmussen]
- Made a trusty debian directory. [Lars Orum Rasmussen]
- Merge branch 'sentinel-1' into pre-master. [Lars Orum Rasmussen]
- Cleanup before merge. [Lars Orum Rasmussen]
- Specifying interface. [Lars Orum Rasmussen]
- ... lot's of playing around. [Lars Orum Rasmussen]
- Bug fix, removed call to fill_borders. [Lars Orum Rasmussen]
- Using chunk_size failed. [Lars Orum Rasmussen]
- Start on Sentinel reader. [Lars Orum Rasmussen]
- Use a more correct name for geotiff module. [Lars Orum Rasmussen]
- Corrected doc/conf. [Lars Orum Rasmussen]
- Cleaning doc II. [Lars Orum Rasmussen]
- Cleaning up doc. [Lars Orum Rasmussen]
- Corrected sys.path. [Lars Orum Rasmussen]
- Now documentation is build better. [Lars Orum Rasmussen]
- Copied MPOP's way of handling version. [Lars Orum Rasmussen]
- For now, skip comparing meta-data for TSX (gdal version issue) [Lars
  Orum Rasmussen]
- Relaxing comparing cross sums (trusty 32 vs 64 issue) [Lars Orum
  Rasmussen]
- Metadata parameter calibration_unit will, always, be empty for non
  calibrated data. [Lars Orum Rasmussen]
- Allow having timestamp items in the dir name, and remove hardcoded
  path delimiter. [Martin Raspaud]

  Courtesy of Ulrich Hamann.
- Satnumber is not defined for every satellite, so add try and except.
  [Martin Raspaud]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Martin Raspaud]
- Merged pre-master into master, new version is 0.9.2. [ras]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [ras]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [ras]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [ras]
- Corrected log info. [ras]
- Updating the satellite number to reflect the data. [Martin Raspaud]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Lars Orum Rasmussen]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Martin Raspaud]
- Misc typos and cleanups. [Martin Raspaud]
- Cosmetic. [Lars Orum Rasmussen]
- No need to import from build path (no more any binaries) [Lars Orum
  Rasmussen]
- 'get_' changed to 'read_' to be consistent in naming. [Lars Orum
  Rasmussen]
- Get absolute path of file before chdir. [Lars Orum Rasmussen]
- Better spelling :-) [Lars Orum Rasmussen]
- Getting info on observation time of the HRIT data. [Adam Dybbroe]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Lars Orum Rasmussen]
- Added a link to the EUMETSAT decompression SW. [Adam Dybbroe]
- Update info text on process_fsd usage. [Adam Dybbroe]
- Better check for correct platform. [Lars Orum Rasmussen]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Lars Orum Rasmussen]
- Issuing a nicer error-message if you try running the fsd script on MSG
  data. [Adam Dybbroe]
- Improved introduction documentation. [Adam Dybbroe]
- More gentle testing, so that tests doesn't fail if the environment
  XRIT_DECOMPRESS_PATH is not set. [Adam Dybbroe]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Lars Orum Rasmussen]
- Testdata for decompression included under tests/data. [Adam Dybbroe]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Lars Orum Rasmussen]
- Cleaning up after unit tests. [Adam Dybbroe]
- Adding the option to decompress xrit files on the fly. [Adam Dybbroe]
- Corrected error comment. [Lars Orum Rasmussen]
- Adding API documentation. [Adam Dybbroe]
- Sorry, conf.py was there already! The new one is removed, the old
  adited slightly! [Adam Dybbroe]
- Adding sphinx doc config file conf.py. [Adam Dybbroe]
- Fixing bug concerning finding the epilougue file. [Adam Dybbroe]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Martin Raspaud]
- Better error reporting regarding xRITDecompress (suggestion from Adam)
  [Lars Orum Rasmussen]
- Added a generic MPEF reader. [Lars Orum Rasmussen]
- Patch find_module for macosx. [Martin Raspaud]
- Fix HRV loading for RSS. [Martin Raspaud]
- Fix RSS reading. [Martin Raspaud]

   - loader: The offset was always zero, so it was removed.
   - MSG: the actual column and line do not seem to be needed.

- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Martin Raspaud]
- Fixed mail address. [Lars Orum Rasmussen]
- Add some documentation on the calibration process. [Martin Raspaud]


v0.9.1 (2013-01-22)
-------------------
- Version 0.9.1 for sublon fix. [Lars Orum Rasmussen]
- A few more files to be ignored. [Lars Orum Rasmussen]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Martin Raspaud]
- Use LongitudeOfSSP instead of NominalLongitude. [Martin Raspaud]


v0.9 (2013-01-14)
-----------------
- Version 0.9 for introducing Meteosat 10. [Lars Orum Rasmussen]
- Making Hudson Happy (MHH) [Lars Orum Rasmussen]
- Move a line two lines below. [Martin Raspaud]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Martin Raspaud]
- Adjust calibration coefficients for met9, add met10 & 11. [Martin
  Raspaud]


v0.8 (2012-12-03)
-----------------

Fix
~~~
- Bugfix: If calibration coefficients are missing, raise a
  CalibrationError. [Martin Raspaud]
- Bugfix: forgot to import CalibrationError in MTP. [Martin Raspaud]
- Bugfix: putting back 0-clipping of radiances in MSG.py. [Martin
  Raspaud]
- Bugfix: corrected coff and loff again. [Martin Raspaud]

  Mirroring *is* needed for reversed data.

- Bugfix: Coff and loff correction. [Martin Raspaud]

  - coff and loff do not need to be mirrored when the image is upside down
  - a -1 is needed (coff and loff is 1-based in xRIT data)

- Bugfix: don't use numexpr in python 2.4 or lower. [Martin Raspaud]
- Bugfix: allowed radiances to be 0 or negative in MSG calibration,
  correcting "nodata" phenomenon in the shadow of visual channels.
  [Martin Raspaud]

Other
~~~~~
- Updeted tests, after area extent precision have changed to float64.
  [Lars Orum Rasmussen]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Martin Raspaud]
- More consistent version numbering. [Lars Orum Rasmussen]
- Getting ready for a new master version 0.8.0. [Lars Orum Rasmussen]
- Moved C code to equivalent Python code. [Lars Orum Rasmussen]
- Better precision for area extent (float64) [Martin Raspaud]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Lars Orum Rasmussen]
- Add licence. [Martin Raspaud]
- Better Window compatible. Modules specifyed as a module (and not a
  path). btw: setuptools recommend that paths is slash-separated. [Lars
  Orum Rasmussen]
- Feature: added support for electro-l n1 HRIT data. [Martin Raspaud]
- Re-imported low level XRIT readers. [Lars Orum Rasmussen]
- Corrected DecodeError exception. [Lars Orum Rasmussen]
- Better import, specially getting rid of 'import *' [Lars Orum
  Rasmussen]
- Will not compare 'tiff_params' [Lars Orum Rasmussen]
- Making distutils and Pypi happy. [Lars Orum Rasmussen]
- Pumping up version number. [Lars Orum Rasmussen]
- Corrected import of xsar module. [Lars Orum Rasmussen]
- Added solar irradiance factors to satellite dependent calibration
  (MSG). [Martin Raspaud]
- Added IR calibration coefficients for meteosat 8 (msg 1) [Martin
  Raspaud]
- Merge branch 'restruc' into pre-master. [Lars Orum Rasmussen]
- Revert to un-debug version. [Lars Orum Rasmussen]
- Introducing CosmoSkyMed. [Lars Orum Rasmussen]
- Extracting geotiff reading. [Lars Orum Rasmussen]
- Making pylint a less angry. [Lars Orum Rasmussen]
- Pumped up version number. [Lars Orum Rasmussen]
- Bug fix when extracting metadata. [Lars Orum Rasmussen]
- Corrected scrips for the new mipp structure. [Lars Orum Rasmussen]
- Restructure III and adding handling of TSX1. [Lars Orum Rasmussen]
- Restructure II. [Lars Orum Rasmussen]
- Restructure I. [Lars Orum Rasmussen]
- Corrected tests metadata to reflect the previous change. [Lars Orum
  Rasmussen]
- Restructure of metadata. [Lars Orum Rasmussen]
- A small restructure. [Lars Orum Rasmussen]

  No more metadata dependency in Calibrator's call.

  Calibrator now returns a tuble of calibrated data and unit name.

  Better "slicing" of metadata.

- Better handling of sub satellite point and sat.proj4_params. [Lars
  Orum Rasmussen]
- Downgraded pixel_size type to float64. [Lars Orum Rasmussen]
- Test data fixes after Martins fixes of fixes ??? [Lars Orum Rasmussen]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Martin Raspaud]

  Conflicts:
  	tests/data/MSG2_HRV_20101011_1400.mda
  	tests/data/MSG2_HRV_20101109_1200.mda
  	tests/data/MSG2_IR_108_20101011_1400.mda

- Tests updated after enhancing the geolocation. [Lars Orum Rasmussen]
- Added support for python 2.4 in MTP. [Martin Raspaud]
- Updated metadata for tests. [Martin Raspaud]
- Enhancing the precision of the pixel size. [Martin Raspaud]
- Bug in mirroring the loff and coff. [Martin Raspaud]
- Read coff and loff from the image navigation now... [Martin Raspaud]

  ...instead of just guessing (MTP and SGS)
- Even more to be ignored. [Lars Orum Rasmussen]
- Cleanup of setup files. [Lars Orum Rasmussen]
- Making tests independent of local config dir. [Lars Orum Rasmussen]
- Cleanup ... removed debian and etc directories. [Lars Orum Rasmussen]
- Corrected unit for radiance ... I hope. [Lars Orum Rasmussen]
- Pushed the version number. [Lars Orum Rasmussen]
- Forgot about pre-master, merging II. [Lars Orum Rasmussen]
- Forgot about pre-master, merging. [Lars Orum Rasmussen]
- Fixed metadata for calibration unit. [Lars Orum Rasmussen]
- Calibration determined in Calibrator. [Lars Orum Rasmussen]
- Fast and ugly fix for persistent meta-data in Calibrator. [Lars Orum
  Rasmussen]
- Revert "changed local path to xrit data" [Lars Orum Rasmussen]

  This reverts commit 605fa8c9ecbddd96b332f6c702eec11caee52cce.

- Changed local path to xrit data. [Lars Orum Rasmussen]
- Merge branch 'pre-master' of github.com:loerum/mipp into pre-master.
  [Lars Orum Rasmussen]
- Put back navigation stuff in msg (Git bug ?) [Martin Raspaud]
- Added units in MSG calibrator. [Martin Raspaud]
- Added calibrator for MTP, IR and WV channels. [Martin Raspaud]
- Added area euro-north. [Lars Orum Rasmussen]
- Cosmetic. [Lars Orum Rasmussen]
- Added new areas, defining log-level in mpop.cfg. [Lars Orum Rasmussen]
- ... and here comes the changelog. [Lars Orum Rasmussen]
- Line and column offset less hardcoded. [Lars Orum Rasmussen]
- Updated changelog. [Lars Orum Rasmussen]
- A little more to be ignored. [Lars Orum Rasmussen]
- Updated test data. [Lars Orum Rasmussen]
- Better ... like mpop's. [Lars Orum Rasmussen]
- Cleanup. [Lars Orum Rasmussen]
- Hardcoded loff and coff ... space for improvements. [Lars Orum
  Rasmussen]
- Cleanup. [Lars Orum Rasmussen]
- Masked out NaN and Inf in MSG calibration. [Esben S. Nielsen]
- Add a mpop config file. [Lars Orum Rasmussen]
- Merge branch 'master' of github.com:loerum/mipp. [Martin Raspaud]
- Merge branch 'master' of github.com:loerum/mipp. [Lars Orum Rasmussen]
- Update area.def, added config files for NOAA. [Lars Orum Rasmussen]
- Update area file. [Lars Orum Rasmussen]
- Configuration files for NOAA. [Lars Orum Rasmussen]
- Changed version number in setup.py, and marked mipp an not zip safe.
  [Martin Raspaud]


v0.3 (2011-02-01)
-----------------

Fix
~~~
- Bugfix: MSG hrv channel was not placed correctly in frame when lower
  sensor was moving. [Martin Raspaud]
- Bugfix: reverted slice computation to correct state. [Martin Raspaud]
- Bugfix: made use of first_pixel before it was defined. [Martin
  Raspaud]
- Bugfix: loaded HRV channel data was not masked where it should.
  [Martin Raspaud]
- Bugfix: Better handling of masked arrays in slicer. [Martin Raspaud]

  Masked arrays where not always created when requested.


Other
~~~~~
- Pumping up the version number. [Lars Orum Rasmussen]
- Merge conflicts fixed. [Lars Orum Rasmussen]
- Less print. [Lars Orum Rasmussen]
- Better logging. [Lars Orum Rasmussen]
- New calibration uses numexpr when available. [Esben S. Nielsen]
- Added MPEF cloudmask reader. [Lars Orum Rasmussen]
- Removed test of geos navigation. [Lars Orum Rasmussen]
- Correct logging. [Lars Orum Rasmussen]
- Added a little test for area_extent. [Lars Orum Rasmussen]
- Consistent debug messages: columns x rows. [Lars Orum Rasmussen]
- Resolving a merge conflict. [Lars Orum Rasmussen]
- Only access logger through logging. [Lars Orum Rasmussen]
- Only access logger through logging. [Lars Orum Rasmussen]
- Corrected slice computation from an area_extent (esn) [Lars Orum
  Rasmussen]
- Removed meaningless comment. [Lars Orum Rasmussen]
- Cosmetic. [Lars Orum Rasmussen]
- Cosmetic, a little more consistent in using row vs line. [Lars Orum
  Rasmussen]
- Oops bug fix. [Lars Orum Rasmussen]
- Simplify, loader.area_extent -> loader._area_extent. [Lars Orum
  Rasmussen]
- Simplify, no more use of local _Region. [Lars Orum Rasmussen]
- Modified test data to reflect changes. [Lars Orum Rasmussen]
- Removed geosnav. [Lars Orum Rasmussen]
- Removed geo_navigation, moved area_extent calcuation so it's
  calculated for all. [Lars Orum Rasmussen]
- Added fishy loff and coff. [Lars Orum Rasmussen]
- Style: wrapped a few lines, and added two docstrings. [Martin Raspaud]
- Feature: fixed the area_extent loader method. Needs mda.loff and
  mda.coff to be defined, has been done here only from MSG. [Martin
  Raspaud]
- Added slicing according to an area_extent. [Lars Orum Rasmussen]
- Merge branch 'master' of github.com:loerum/mipp. [Lars Orum Rasmussen]
- Masking calibrated data was erraneous. The mask should be computed
  first. [Martin Raspaud]
- Adding support for python 2.4... [Martin Raspaud]
- Cosmetic. [Lars Orum Rasmussen]
- Merge branch 'master' of github.com:loerum/mipp. [Lars Orum Rasmussen]
- Cleaner test. [ras]
- Cosmetic renaming. [ras]
- Corrected test for new slicing. [ras]
- Handling slicing better (correct) [ras]
- Cosmetic. [ras]
- Less print. [Lars Orum Rasmussen]
- Check for a resulting image. [Lars Orum Rasmussen]
- Added test for HRV regions. [Lars Orum Rasmussen]
- Better handling of meta-data. [Lars Orum Rasmussen]
- Corrected product name. [Lars Orum Rasmussen]
- Merge branch 'master' of github.com:loerum/mipp. [Lars Orum Rasmussen]
- Handles different calibration types in MSG. [Martin Raspaud]
- Corrected test for modified meta data. [Lars Orum Rasmussen]
- Some info. [Lars Orum Rasmussen]
- Fixed bug, where mda.data_type was overwritten. [Lars Orum Rasmussen]
- Merge branch 'local-svn' [Lars Orum Rasmussen]
- Pulled Esbens mods for 'don't do any fancy operations on masked
  arrays' [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6542 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Fixed memory and performance problem in calibration. Removed prefix
  from setup.cfg. [esn]

  git-svn-id: svn+ssh://websat/sat/mipp@6541 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Merge branch 'local-svn' [Lars Orum Rasmussen]
- Now method to overwrite deafult logger. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6513 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Cosmetic. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6512 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Fixed bug in sat.py, now test for metadata. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6511 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Now method to overwrite deafult logger. [Lars Orum Rasmussen]
- Merge branch 'local-svn' [Lars Orum Rasmussen]
- Now logger can be overwritten. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6507 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Cosmetic. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6506 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Cosmetic. [Lars Orum Rasmussen]
- Merge branch 'local-svn' [Lars Orum Rasmussen]
- Fixed bug in sat.py, now test for metadata. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6482 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Fixed bug in sat.py, now test for metadata. [Lars Orum Rasmussen]
- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6325 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Specifying binary files. [Lars Orum Rasmussen]
- Added test of shape. [Lars Orum Rasmussen]
- Cleaned up 'main' block. [Lars Orum Rasmussen]
- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6324 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Not using cross sum to test. [Lars Orum Rasmussen]
- Slicer.py upgaded to loader.py. [Lars Orum Rasmussen]
- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6322 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Better for Hudson. [Lars Orum Rasmussen]
- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6321 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Now with unittests. [Lars Orum Rasmussen]
- Separate setuptools and nosetests. [Lars Orum Rasmussen]
- Introducing msg2. [Lars Orum Rasmussen]
- Introducing msg2. [Lars Orum Rasmussen]
- Make a copy of metadata ... so it's reusable. [Lars Orum Rasmussen]
- Allow epilogue to be passed as a filename. [Lars Orum Rasmussen]
- Cosmetic. [Lars Orum Rasmussen]
- Merge commit 'origin' [Lars Orum Rasmussen]
- Feature: Add calibration unit in MSG reader. [Martin Raspaud]
- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@6320 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Many changes. [Lars Orum Rasmussen]
- Many changes. [Lars Orum Rasmussen]
- Added support for epilogue file. [Martin Raspaud]

  Now epilogue file is (partially) read if it there, and the information inside
  is used for image slicing (instead of the prologue info).

- Added slicing support for MSG's HRV channel. [Martin Raspaud]

  * Added the metadata attribute "boundaries", which describes the regions on
    which a given channel is defined.

  * Modified the slicer to work with this boundaries attribute, which involves
    some code restructuring: now __call__ calls __getitem__, and metadata update
    is done __getitem__ instead of _read.

- Added calibration computation to MSG. [Martin Raspaud]
- Introducing Calibrator for each XRIT data type. [Lars Orum Rasmussen]
- Header of the MSG HRIT prologue is now read entirely. [Martin Raspaud]
- Merge branch 'master' of git@github.com:loerum/mipp. [Lars Orum
  Rasmussen]
- Introducing MSG. [Lars Orum Rasmussen]
- Nicer handling of 24 hour clock. [Lars Orum Rasmussen]
- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5924 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Nicer handling of 24 hour clock. [Lars Orum Rasmussen]
- Handle MTP.py conflict. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5923 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Correted handling of 24 hour clock. [Lars Orum Rasmussen]
- Fix merge conflict. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5921 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Correted handling of 24 hour clock. [Lars Orum Rasmussen]
- Do not use product time for age check. [Lars Orum Rasmussen]
- Introcuding goes13 VI. [Lars Orum Rasmussen]
- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5878 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Cosmetic. [Lars Orum Rasmussen]
- Introcuding goes13 VI. [Lars Orum Rasmussen]
- Cosmetic. [Lars Orum Rasmussen]
- Introducding region_name. [Lars Orum Rasmussen]
- Default is not to calibrate. [Lars Orum Rasmussen]
- Cleanup documetation. [Lars Orum Rasmussen]
- Updated documentation. [Lars Orum Rasmussen]
- Updated documentation. [Lars Orum Rasmussen]
- Added GPL license. [Lars Orum Rasmussen]
- Now check for known satellite. [Lars Orum Rasmussen]
- Now handles unknown orientation of first pixel. [Lars Orum Rasmussen]
- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5841 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- New version. [Lars Orum Rasmussen]
- Better handling of exceptions. [Lars Orum Rasmussen]
- Introducing proxy slicing. [Lars Orum Rasmussen]
- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5785 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5778 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5768 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5730 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Merge branch 'master' into local-svn. [ras]

  Conflicts:

  	debian/changelog
  	debian/control


  git-svn-id: svn+ssh://websat/sat/mipp@5716 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Debianized. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5666 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Merge branch 'master' into local-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5627 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Restart of a git-svn module. [svn]

  git-svn-id: svn+ssh://websat/sat/mipp@5626 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3



v0.1 (2010-03-30)
-----------------
- Better argument handling. [ras]
- Another new version. [ras]
- New version. [ras]
- Better config file handling. [ras]
- Cosmetic. [ras]
- Cosmetic. [ras]
- Returns calibrated data, new satellite configuration file. [ras]
- Updated changelog. [ras]
- Now with new interface. [ras]
- Now with new interface. [ras]
- New interface, using config files. [ras]
- New interface. [ras]
- Updating documentation. [ras]
- Added documentation. [ras]
- Added documentation. [ras]
- Ready for standalone decompressing. [ras]
- Ready for standalone decompressing. [ras]
- Better debian/dirs. [ras]
- Debianized. [ras]
- And now with a setup.cfg file. [ras]
- Small mods and a fix. [ras]
- Corrected README file. [ras]
- Files to be ignored. [ras]
- Files to be ignored. [ras]
- Corrected README file. [ras]
- Added a README file. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5585 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Moved satellite group to the top (for more flexibility) [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5583 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Better meta-data handler. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5582 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Some dokumentaion. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5581 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Now using hdfdmi. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5579 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3

- Mipp on the way to git-svn. [ras]

  git-svn-id: svn+ssh://websat/sat/mipp@5578 e4f3f7b9-f76c-4984-92d3-5a65a72b3fc3




