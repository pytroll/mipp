# Copyright (c) 2009-2012.

# DMI,
# Lyngbyvej 100
# DK-2100 Copenhagen
# Denmark

# Author(s):

#   Lars Orum Rasmussen <loerum@gmail.com>  

# This file is part of mipp.

# mipp is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# mipp is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with mipp.  If not, see <http://www.gnu.org/licenses/>.

"""Setup file for mipp.
"""
from setuptools import setup, Extension

ext = Extension('mipp/xrit/_convert', ['mipp/xrit/convert/wrap_convert.c',
                                       'mipp/xrit/convert/10216.c'],
                extra_compile_args = ['-std=c99', '-O9'])


setup(name = 'mipp',
      description='Meteorological ingest processing package',
      author='Lars Orum Rasmussen',
      author_email='loerum@hmail.com',
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License v3 " +
                   "or later (GPLv3+)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Scientific/Engineering"],
      url="https://github.com/loerum/mipp",
      version = '0.7.1',
      packages = ['mipp', 'mipp/xrit', 'mipp/xsar'],
      package_dir = {'mipp':'mipp', 
                     'mipp/xrit': 'mipp/xrit',
                     'mipp/xsar': 'mipp/xsar'},
      ext_modules = [ext,],
      zip_safe = False,
      )
