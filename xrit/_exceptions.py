#
# $Id$
#

#-----------------------------------------------------------------------------
#
# All exception from the mipp module
#
#-----------------------------------------------------------------------------
class MippError(Exception):
    pass

#-----------------------------------------------------------------------------
#
# Decode errors
#
#-----------------------------------------------------------------------------
class XRITDecodeError(MippError):
    pass

class SGSDecodeError(XRITDecodeError):
    pass


class MTPDecodeError(XRITDecodeError):
    pass

#-----------------------------------------------------------------------------
#
# Image readings error
#
#-----------------------------------------------------------------------------
class SatReaderError(MippError):
    pass

class SatNoFiles(SatReaderError):
    pass

#-----------------------------------------------------------------------------
#
# Config file reader error
#
#-----------------------------------------------------------------------------
class SatConfigReaderError(MippError):
    pass

#-----------------------------------------------------------------------------
#
# Navigations error
#
#-----------------------------------------------------------------------------
class NavigationError(MippError):
    pass
