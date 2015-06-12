#
# $Id$
#
from datetime import datetime
import numpy

def mslice(mda):
    _mda = Metadata()
    for key, val in mda.__dict__.items():
        if (not key.startswith('_') and 
            not callable(val) and
            key not in mda.ignore_attributes):
            setattr(_mda, key, val)
    return _mda

class Metadata(object):
    token = ':'
    ignore_attributes = ()
    dont_eval = ('satnumber',)

    
    def read(self, file_name):
        """Read until empty line, 'EOH' or 'EOF'.
        """
        fpi = open(file_name)
        try:
            for line in fpi:
                line = line.strip()
                if not line or line == 'EOH':
                    # end of meta-data
                    break
                line = line.split('#')[0].strip()
                if not line:
                    # just a comment
                    continue
                key, val = [s.strip() for s in line.split(self.token, 1)]
                if key not in self.dont_eval:
                    try:
                        val = eval(val)
                    except:
                        pass
                if key:
                    setattr(self, key, val)
        finally:
            fpi.close()
        return self

    def save(self, file_name):
        fpo = open(file_name, 'w')
        fpo.write(str(self) + '\n')
        fpo.close()

    def __str__(self):
        keys = sorted(self.__dict__.keys())
        strn = ''
        for key in keys:
            val = getattr(self, key)
            if (not key.startswith('_') and 
                not callable(val) and
                key not in self.ignore_attributes):
                val = _nice2cmp(val)
                strn += key + self.token + ' ' + str(val) + '\n'
        return strn[:-1]

def _nice2cmp(val):
    # ... and nice to print
    if isinstance(val, numpy.ndarray):
        val = val.tolist()
    elif isinstance(val, datetime):
        val = str(val)
    elif isinstance(val, float):
        val = str(val)
    elif isinstance(val, dict):
        sdc = {}
        for _key, _val in val.items():
            if isinstance(_val, numpy.ndarray):
                _val = _val.tolist()
            sdc[_key] = _val
        val = sdc
    return val

if __name__ == '__main__':
    import sys
    print Metadata().read(sys.argv[1])
