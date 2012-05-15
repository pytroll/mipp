from setuptools import setup, Extension

ext = Extension('mipp/xrit/_convert', ['mipp/xrit/convert/wrap_convert.c',
                                       'mipp/xrit/convert/10216.c'],
                extra_compile_args = ['-std=c99', '-O9'])


setup(name = 'mipp',
      version = '0.7',
      package_dir = {'mipp':'mipp', 
                     'mipp/xrit': 'mipp/xrit',
                     'mipp/xsar': 'mipp/xsar'},
      packages = ['mipp', 'mipp/xrit', 'mipp/xsar'],
      ext_modules = [ext,],
      zip_safe = False,
      )
