# -*- coding: utf-8 -*-

# Copyright (c) 2015 Lars Orum Rasmussen

# Author(s):

#   Lars Orum Rasmussen

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

""" A dataset is the "contract" between MIPP and MPOP. It's what MIPP will
return from `load`.

"""
class InfoObject(object):
    def __init__(self, **attributes):
        self.info = attributes

class Dataset(InfoObject):
    def __init__(self, data, **attributes):
        InfoObject.__init__(self, **attributes)
        self.data = data

    def __str__(self):
        return str(self.data) + "\n" + str(self.info)

    def __repr__(self):
        return repr(self.data) + "\n" + repr(self.info)

    def copy(self, copy_data=True):
        if copy_data:
            data = self.data.copy()
        else:
            data = self.data
        return Dataset(data, **self.info)
