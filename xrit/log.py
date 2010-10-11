#
# Our logger, default loglevel is NULL and write to stderr.
#
#    * It can be controlled by environment variables DEBUG and LOGLEVEL.
#    * If DEBUG is set it will overwrite LOGLEVEL.
#    * If LOGLEVEL=NULL it will be very quiet.
#
import os
import sys
from logging import *

__all__ = ['logger',]

loglevels = {'CRITICAL': CRITICAL,
             'ERROR': ERROR,
             'WARNING': WARNING,
             'INFO': INFO,
             'DEBUG': DEBUG,
             'NULL': None}

format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
name = "mipp"

#-----------------------------------------------------------------------------

class NullHandler(Handler):
    def emit(self, record):
        pass

#-----------------------------------------------------------------------------

loglevel = os.environ.get("LOGLEVEL", "NULL").upper()
try:
    loglevel = loglevels[loglevel]
except:
    raise KeyError, "Unknown LOGLEVEL '%s'"%loglevel
if os.environ.get("DEBUG", ''):
    loglevel = DEBUG

if loglevel:
    handler = StreamHandler(sys.stderr)
else:
    handler = NullHandler()
handler.setFormatter(Formatter(format))
    
logger = getLogger(name)
logger.setLevel(loglevel)
logger.addHandler(handler)

#-----------------------------------------------------------------------------

if __name__ == '__main__':
    logger.debug("this is a debug message")
    logger.info("this is just an info message")
    logger.warning("and here is warning no %d", 22)
    logger.error("ohoh an error")
    logger.critical("now it's getting critical")
