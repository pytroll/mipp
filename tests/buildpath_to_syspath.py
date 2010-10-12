import sys
import os
from distutils.util import get_platform

proj_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
build_base = 'build'
plat = get_platform()

python_version = '.'.join([str(i) for i in sys.version_info[:2]])
build_purelib = os.path.join(build_base, 'lib' + '-' + python_version) # is it at all used ?
build_platlib = os.path.join(build_base, 'lib.' + plat + '-' + python_version)

build_path = os.path.join(proj_path, build_platlib)
if not os.path.isdir(build_path):
    assert False, "No such build path '%s'"%build_path
sys.path.insert(0, build_path)

if __name__ == '__main__':
    print build_platlib
