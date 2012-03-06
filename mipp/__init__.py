#
#
import sys
from datetime import datetime
from mipp._exceptions import *

if sys.version_info < (2, 5):
    import time
    def strptime(string, fmt=None):
        """This function is available in the datetime module only
        from Python >= 2.5.
        """
        return datetime(*time.strptime(string, fmt)[:6])
else:
    strptime = datetime.strptime
