from StringIO import StringIO

from mipp.xrit import _convert

BLOB_SIZE = 5120 # has to be a multiplum of 5
HRPT_RECLEN = 11090

def dec10216(in_buffer):
    fp = StringIO(in_buffer)    
    data = ''
    blob = fp.read(BLOB_SIZE)
    while blob:
        blob = _convert.dec10216(blob)
        if blob:
            data += blob
        blob = fp.read(BLOB_SIZE)
    return data

def hrpt_dec10216(in_buffer):
    #
    # It will handle the input data as raw HRPT data (level 0), which
    # originally is saved as packed 10 bit words width a record length
    # of (11090 - 2) (the last two words are ignored).
    # The AAPP software expect 10 bit right adjusted in 16 bit words
    # and a complete record length of 11090 words.
    #
    # !!! THIS ONE COULD BE FASTER !!!
    #
    fp = StringIO(dec10216(in_buffer))
    data = ''
    blob_size = (HRPT_RECLEN - 2)*2
    blob = fp.read(blob_size)
    while blob:
        if len(blob) == blob_size:
            blob += '\0\0\0\0'
        data += blob
        blob = fp.read(blob_size)
    return data

if __name__ == '__main__':
    import sys    
    try:
        if sys.argv[1] == 'hrpt':
            decoder = hrpt_dec10216
    except IndexError:
        decoder = dec10216
    sys.stdout.write(decoder(sys.stdin.read()))
