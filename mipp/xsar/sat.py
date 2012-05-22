#
# $Id$ 
#
import os
import tarfile
import glob
import fnmatch
import imp

import logging
logger = logging.getLogger('mipp')

import mipp
import mipp.cfg

__all__ = ['load']

def _find_in_tarfile(tfile, fname):
    tar = tarfile.open(tfile)
    try:
        for name in tar.getnames():
            if name.endswith(fname):
                return name
    finally:
        tar.close()
    raise mipp.NoFiles("found no archive file '%s'"%fname)

class SatelliteLoader(object):
    def __init__(self, config_reader):
        #
        # Read configuration file based on satellite name
        #
        sat = config_reader('satellite')

        #
        # Load format decoder based on level1 format
        #
        lv1_format = config_reader('level1')['format']
        logger.info("Loading %s"%lv1_format)
        try:
            _args = imp.find_module(lv1_format)
        except ImportError:
            raise mipp.ReaderError("unknown level-1 format: '%s'"%lv1_format)
        try:
            mdl = imp.load_module(lv1_format, *_args)
        finally:
            if _args[0]:
                _args[0].close()

        self._metadata_reader = mdl.read_metadata
        self._image_reader = mdl.read_image
        self._tar_file = None

        #
        # Attributing
        #
        self.__dict__.update(sat)

        self._config_reader = config_reader
        self.satname = self.satname + self.number
        self.satnumber = self.number
        del self.number

    def load(self, time_stamp, channel, **kwargs):
        return self.load_file(self._find_tarfile(time_stamp),
                              channel, **kwargs)

    def load_file(self, filename, channel,
                  only_metadata=False, mask=True, calibrate=1):
        if channel not in self._config_reader.channel_names:
            raise mipp.ReaderError("unknown channel name '%s'"%channel)
        self._tar_file = filename
        mda = self._load_metadata(channel)
        if only_metadata:
            return mda
        mda, img = self._load_image(mda, mask=mask, calibrate=calibrate)        
        return mipp.mda.mslice(mda), img

        
    def _load_metadata(self, channel):
        del channel
        opt = self._config_reader('level1')
        mda_file = opt['filename_metadata']
        tar = tarfile.open(self._tar_file)
        names = []
        try:
            for name in tar.getnames():
                if fnmatch.fnmatch(os.path.basename(name), mda_file):
                    names.append(name)
            if len(names) == 0:
                raise mipp.NoFiles("found no metadata file: '%s'"%mda_file)
            elif len(names) > 1:
                raise mipp.NoFiles("found multiple metadata files: '%s'" %
                                   str(names))
            logger.info("Extracting '%s'"%names[0])
            xmldata = tar.extractfile(names[0]).read()
        finally:
            tar.close()
        return self._metadata_reader(xmldata)

    def _load_image(self, mda, mask=True, calibrate=1):
        import tempfile
        import shutil
        image_file = _find_in_tarfile(self._tar_file, mda.image_filename)
        tar = tarfile.open(self._tar_file)
        tmpdir = tempfile.mkdtemp()
        logger.info("Extracting '%s' into '%s'"%(image_file, tmpdir))
        try:
            tar.extract(image_file, tmpdir)
            image_file = tmpdir + '/' + mda.image_filename
            mda, image = self._image_reader(mda, image_file,
                                            mask=mask, calibrate=calibrate)
        finally:
            tar.close()
            shutil.rmtree(tmpdir)
        return mda, image

    def _find_tarfile(self, time_stamp):
        opt = self._config_reader('level1')
        if not os.path.isdir(opt['dir']):
            raise IOError, "No such directory: %s" % opt['dir']
        tar_file = glob.glob(opt['dir'] + '/' +
                             time_stamp.strftime(opt['filename_archive']))
        if not tar_file:
            raise mipp.NoFiles("found no archive file: '%s'"%
                               (time_stamp.strftime(opt['filename_archive'])))
        elif len(tar_file) > 1:
            raise mipp.NoFiles("found multiple archive files: '%s'" % 
                               str(tar_file))
        return tar_file[0]

#-----------------------------------------------------------------------------
#
# Interface
#
#-----------------------------------------------------------------------------
def load(satname, time_stamp, channel, **kwarg):
    return SatelliteLoader(
        mipp.cfg.read_config(satname)).load(time_stamp, channel, **kwarg)

def load_file(filename, channel, **kwarg):
    # Satellite name should be read from metadata (and not filename) !!!
    satname = os.path.basename(filename).split('_')[0].lower()
    return SatelliteLoader(
        mipp.cfg.read_config(satname)).load_file(filename, channel, **kwarg)

#-----------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    import getopt
    import loggers.simple
    logger = loggers.simple.get('mipp')

    only_mda = False
    opts, args = getopt.getopt(sys.argv[1:], "m")
    for k, v in opts:
        if k == '-m':
            only_mda = True
    try:
        _file = args[0]
    except IndexError:
        print >> sys.stderr, "usage: sat.py [-m] <tar-file>"
        sys.exit(1)
    _mda = load_file(_file, 'sarx', only_metadata=True)
    if only_mda:
        pass
    elif _mda.calibrated != 'CALIBRATED':
        logger.warning("Data is not calibrated")
        _mda, _image = load_file(_file, 'sarx', calibrate=0)
    else:
        _mda, _image = load_file(_file, 'sarx')
    print '\n', _mda
