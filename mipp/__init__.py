#
#
import sys
from datetime import datetime

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
