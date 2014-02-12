from StringIO import StringIO
import numpy as np

def dec10216(in_buffer):
    return _dec10216(np.fromstring(in_buffer, dtype=np.uint8))

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
    HRPT_RECLEN = 11090
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

def _dec10216(inbuf):
    arr10 = inbuf.astype(np.uint16)
    arr16 = np.zeros((len(arr10) *4 / 5,), dtype=np.uint16)
    arr10_len = (len(arr16) * 5) / 4
    arr10 = arr10[:arr10_len] # adjust size
    """
    /*
     * pack 4 10-bit words in 5 bytes into 4 16-bit words
     * 
     * 0       1       2       3       4       5
     * 01234567890123456789012345678901234567890
     * 0         1         2         3         4
     */      
    ip = &in_buffer[i];
    op = &out_buffer[j];
    op[0] = ip[0]*4 + ip[1]/64;
    op[1] = (ip[1] & 0x3F)*16 + ip[2]/16;
    op[2] = (ip[2] & 0x0F)*64 + ip[3]/4;
    op[3] = (ip[3] & 0x03)*256 +ip[4];
    """
    arr16.flat[::4] = np.left_shift(arr10[::5], 2) + \
        np.right_shift((arr10[1::5]), 6)
    arr16.flat[1::4] = np.left_shift((arr10[1::5] & 63), 4) + \
        np.right_shift((arr10[2::5]), 4)
    arr16.flat[2::4] = np.left_shift(arr10[2::5] & 15, 6) + \
        np.right_shift((arr10[3::5]), 2)
    arr16.flat[3::4] = np.left_shift(arr10[3::5] & 3, 8) + \
        arr10[4::5]    
    return arr16.tostring()

if __name__ == '__main__':
    BLOB_SIZE = 10240 # has to be a multiply of 5
    import sys    
    try:
        if sys.argv[1] == 'hrpt':
            decoder = hrpt_dec10216
    except IndexError:
        decoder = dec10216
    blob = sys.stdin.read(BLOB_SIZE)
    while blob:
        sys.stdout.write(decoder(blob))
        blob = sys.stdin.read(BLOB_SIZE)
        
