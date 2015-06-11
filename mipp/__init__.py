#
#
import sys
from datetime import datetime, timedelta
import numpy as np

from mipp.version import __version__

if sys.version_info < (2, 5):
    import time

    def strptime(string, fmt=None):
        """This function is available in the datetime module only
        from Python >= 2.5.
        """
        return datetime(*time.strptime(string, fmt)[:6])
else:
    strptime = datetime.strptime

#-----------------------------------------------------------------------------
#
# All exception for the mipp module
#
#-----------------------------------------------------------------------------


class MippError(Exception):
    pass

#-----------------------------------------------------------------------------
#
# Decoding error
#
#-----------------------------------------------------------------------------


class DecodeError(MippError):
    pass


class UnknownSatellite(MippError):
    pass
#-----------------------------------------------------------------------------
#
# Image readings error
#
#-----------------------------------------------------------------------------


class ReaderError(MippError):
    pass


class NoFiles(ReaderError):
    pass

#-----------------------------------------------------------------------------
#
# Config file reader error
#
#-----------------------------------------------------------------------------


class ConfigReaderError(MippError):
    pass

#-----------------------------------------------------------------------------
#
# Navigations error
#
#-----------------------------------------------------------------------------


class NavigationError(MippError):
    pass

#-----------------------------------------------------------------------------
#
# Calibrations error
#
#-----------------------------------------------------------------------------


class CalibrationError(MippError):
    pass


def get_cds_time(days, msecs):
    """Get the datetime object of the time since epoch given in days and
    milliseconds of day
    """
    return datetime(1958, 1, 1) + timedelta(days=float(days),
                                            milliseconds=float(msecs))


def dec10to16(data):
    """Unpacking the 10 bit data to 16 bit"""

    arr10 = data.astype(np.uint16).flat
    new_shape = list(data.shape[:-1]) + [(data.shape[-1] * 8) / 10]
    arr16 = np.zeros(new_shape, dtype=np.uint16)
    arr16.flat[::4] = np.left_shift(arr10[::5], 2) + \
        np.right_shift((arr10[1::5]), 6)
    arr16.flat[1::4] = np.left_shift((arr10[1::5] & 63), 4) + \
        np.right_shift((arr10[2::5]), 4)
    arr16.flat[2::4] = np.left_shift(arr10[2::5] & 15, 6) + \
        np.right_shift((arr10[3::5]), 2)
    arr16.flat[3::4] = np.left_shift(arr10[3::5] & 3, 8) + \
        arr10[4::5]
    return arr16
