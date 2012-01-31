#
# $Id$
#
from datetime import datetime
import numpy

_cleanup_attributes = ('line_offset', 'first_pixel',
                       'coff', 'loff',
                       'image_data', 'boundaries')
_dont_eval = ('satnumber',)

def mslice(mda):
    m = Metadata()
    for k, v in mda.__dict__.items():
        if (not k.startswith('_') and 
            not callable(v) and
            k not in _cleanup_attributes):
            setattr(m, k, v)
    return m

class Metadata(object):
    token = ':'
    
    def read(self, file_name):
        """Read until empty line, 'EOH' or 'EOF'.
        """
        fp = open(file_name)
        try:
            for line in fp:
                line = line.strip()
                if not line or line == 'EOH':
                    # end of meta-data
                    break
                line = line.split('#')[0].strip()
                if not line:
                    # just a comment
                    continue
                k, v = [s.strip() for s in line.split(self.token, 1)]
                if k not in _dont_eval:
                    try:
                        v = eval(v)
                    except:
                        pass
                if k:
                    setattr(self, k, v)
        finally:
            fp.close()
        return self

    def save(self, file_name):
        fp = open(file_name, 'w')
        fp.write(str(self) + '\n')
        fp.close()

    def __str__(self):
        keys = sorted(self.__dict__.keys())
        s = ''
        for k in keys:
            v = getattr(self, k)
            if (not k.startswith('_') and 
                not callable(v) and
                k not in _cleanup_attributes):
                v = _nice2cmp(v)
                s += k + self.token + ' ' + str(v) + '\n'
        return s[:-1]

def _nice2cmp(val):
    # ... and nice to print
    if isinstance(val, numpy.ndarray):
        val = val.tolist()
    elif isinstance(val, datetime):
        val = str(val)
    elif isinstance(val, dict):
        d = {}
        for k, v in val.items():
            if isinstance(v, numpy.ndarray):
                v = v.tolist()
            d[k] = v
        val = d
    return val

if __name__ == '__main__':
    import sys
    print Metadata().read(sys.argv[1])
