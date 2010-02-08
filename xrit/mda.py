#
# $Id$
#
import numpy

class Metadata(object):
    def read(self, file_name):
        """Read until empty line or 'EOH'.
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
                k, v = [s.strip() for s in line.split('=', 1)]
                try:
                    v = eval(v)
                except:
                    pass
                if k:
                    setattr(self, k, v)
        finally:
            fp.close()
        return self
            
    def __str__(self):
        keys = sorted(self.__dict__.keys())
        s = ''
        for k in keys:
            v = getattr(self, k)
            if k[0] != '_' and k != 'image_data':
                if type(v) == numpy.ndarray:
                    v = v.tolist()
                s += k + ' = ' + str(v) + '\n'
        return s[:-1]

if __name__ == '__main__':
    import sys
    print Metadata().read(sys.argv[1])
