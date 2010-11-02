#
# $Id$
#
import numpy

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
                if k != 'satnumber': # eval handles octal numbers (09 != 9)
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
            if k[0] != '_' and k != 'image_data' and k != 'calibrate':
                if type(v) == numpy.ndarray:
                    v = v.tolist()
                s += k + self.token + ' ' + str(v) + '\n'
        return s[:-1]

if __name__ == '__main__':
    import sys
    print Metadata().read(sys.argv[1])
