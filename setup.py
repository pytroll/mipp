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
import os
from setuptools import setup, Extension
import imp

version = imp.load_source('mipp.version', 'mipp/version.py')

setup(name = 'mipp',
      description='Meteorological ingest processing package',
      author='Lars Orum Rasmussen',
      author_email='loerum@gmail.com',
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License v3 " +
                   "or later (GPLv3+)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Scientific/Engineering"],
      url="https://github.com/loerum/mipp",
      version = version.__version__,
      packages = ['mipp', 'mipp.xrit', 'mipp.xsar'],
      zip_safe = False,
      )
