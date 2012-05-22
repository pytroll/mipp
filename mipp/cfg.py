#
#
#
import os
import re
from ConfigParser import ConfigParser

import mipp

__all__ = ['read_config']

def read_config(satname, instrument=''):
    return _ConfigReader(satname, instrument)

class _ConfigReader(object):

    def __init__(self, satname, instrument=''):
        try:
            home = os.environ['PPP_CONFIG_DIR']
        except KeyError:
            raise mipp.ConfigReaderError(
                "PPP_CONFIG_DIR environment variable is not set")

        self.config_file = home + '/' + satname + '.cfg'
        if not os.path.isfile(self.config_file):
            raise mipp.ConfigReaderError(
                "unknown satellite: '%s' (no such file: '%s')"%
                (satname, self.config_file))
        self._config = ConfigParser()
        self._config.read(self.config_file)
        
        instruments = self.get('satellite')['instruments']
        if not instrument:
            if len(instruments) == 1:
                instrument = instruments[0]
            else:
                raise mipp.ConfigReaderError("please specify instrument")
        else:
            if instrument not in instruments: 
                raise mipp.ConfigReaderError("unknown instrument: '%s'"%
                                             instrument)
        self.instrument = instrument
        
        self._channels = self._channels2dict(instrument)

    def __call__(self, section):
        return self.get(section)

    def get(self, section):
        options = {}
        section = str(section) # allow get(1)
        if section != 'satellite' and not section.startswith(self.instrument):
            section = self.instrument + '-' + section
        for key, val in self._config.items(section, raw=True):
            options[key] = _eval(val)
        return options

    def get_channel(self, name):
        try:
            return self._channels[name]
        except KeyError:
            raise mipp.ConfigReaderError("unknown channel: '%s'"%name)

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
                chn = _Channel(self._config.items(sec, raw=True), raw=True)
                channels[chn.name] = chn
        return channels
    
class _Channel:
    def __init__(self, kvs, raw=False):
        self.name = None
        for key, val in kvs:
            if raw:
                val = _eval(val)
            setattr(self, key, val)
    def __str__(self):
        keys = sorted(self.__dict__.keys())
        text = ''
        for key in keys:
            if key[0] == '_':
                continue
            val = getattr(self, key)
            if key == 'resolution':
                val = "%.2f" % val
            elif key == 'frequency':
                val = "(%.2f, %.2f, %.2f)" % val
            text += key + ': ' + str(val) + ', '
        return text[:-2]    

def _eval(val):
    try:
        return eval(val)
    except:
        return str(val)

if __name__ == '__main__':
    import sys
    dname, fname = os.path.split(sys.argv[1])
    os.environ['PPP_CONFIG_DIR'] = dname
    cfg = read_config(os.path.splitext(fname)[0])
    for _name in ('satellite', 'level1', 'level2'):
        _sec = cfg(_name)
        print _name
        for _key in sorted(_sec.keys()):
            print '    ', _key + ':',  _sec[_key]
    for _name in cfg.channel_names:
        print cfg.get_channel(_name)
