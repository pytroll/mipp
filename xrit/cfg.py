#
#
#
import os
import re
from ConfigParser import ConfigParser

import xrit

__all__ = ['read_config',]

def read_config(satname, instrument=''):
    return _ConfigReader(satname, instrument)

class _ConfigReader(object):

    def __init__(self, satname, instrument=''):
        try:
            home = os.environ['PPP_CONFIG_DIR']
        except KeyError:
            raise xrit.SatConfigReaderError("PPP_CONFIG_DIR environment variable is not set")

        self.config_file = home + '/' + satname + '.cfg'
        if not os.path.isfile(self.config_file):
            raise xrit.SatConfigReaderError("unknown satellite: '%s' (no such file: '%s')"%(satname, self.config_file))
        self._config = ConfigParser()
        self._config.read(self.config_file)
        
        instruments = self.get('satellite')['instruments']
        if not instrument:
            if len(instruments) == 1:
                instrument = instruments[0]
            else:
                raise xrit.SatConfigReaderError("please specify instrument")
        else:
            if instrument not in instruments: 
                raise xrit.SatConfigReaderError("unknown instrument: '%s'"%instrument)
        self.instrument = instrument
        
        self._channels = self._channels2dict(instrument)

    def __call__(self, section):
        return self.get(section)

    def get(self, section):
        options = {}
        section = str(section) # allow get(1)
        if section != 'satellite' and not section.startswith(self.instrument):
            section = self.instrument + '-' + section
        for k, v in self._config.items(section, raw=True):
            options[k] = _eval(v)
        return options

    def get_channel(self, name):
        try:
            return self._channels[name]
        except KeyError:
            raise xrit.SatConfigReaderError("unknown channel: '%s'"%name)

    @property
    def channels(self):
        return self._channels

    @property
    def channel_names(self):
        return sorted(self._channels.keys())

    def _channels2dict(self, instrument):
        rec = re.compile('^%s-\d+$'%instrument)
        channels = {}
        for sec in self._config.sections():
            if rec.findall(sec):
                c = _Channel(self._config.items(sec, raw=True), raw=True)
                channels[c.name] = c
        return channels
    
class _Channel:
    def __init__(self, kv, raw=False):
        for k, v in kv:
            if raw:
                v = _eval(v)
            setattr(self, k, v)
    def __str__(self):
        keys = sorted(self.__dict__.keys())
        s = ''
        for k in keys:
            if k[0] == '_':
                continue
            v = getattr(self, k)
            if k == 'resolution':
                v = "%.2f"%v
            elif k == 'frequency':
                v = "(%.2f, %.2f, %.2f)"%v
            s += k + ': ' + str(v) + ', '
        return s[:-2]    

def _eval(v):
    try:
        return eval(v)
    except:
        return str(v)

if __name__ == '__main__':
    import sys
    dname, fname = os.path.split(sys.argv[1])
    os.environ['PPP_CONFIG_DIR'] = dname
    cfg = read_config(os.path.splitext(fname)[0])
    for name in ('satellite', 'level1', 'level2'):
        h = cfg(name)
        print name
        for k in sorted(h.keys()):
            print '    ', k + ':',  h[k]
    for name in cfg.channel_names:
        print cfg.get_channel(name)
