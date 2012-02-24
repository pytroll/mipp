/* -*-c-*-
 * 
 * $Id$ 
 * 
 * It will unpack 10 bit words into right adjusted 16 bit words.
 *
 */

#include <stdio.h>
#include <stdlib.h>

#define IN_JUMP 5
#define OUT_JUMP 4

unsigned int dec10216(unsigned char *in_buffer, unsigned int in_length, 
		      unsigned short *out_buffer) {

    unsigned char *ip;  /* in:  4 10-bit words in 5 bytes */
    unsigned short *op; /* out: 4 10-bit words in 4 words */
    unsigned int i, j;
    unsigned int tlen=0;
    unsigned int tail = in_length%5;

    if (tail != 0) {
        in_length -= tail;
        fprintf(stderr, "10216 warning: input buffer size is not a multiplum of 5 bytes (size is reduced by %d bytes)\n", tail);
    }

    for(i=0, j=0; i<in_length; i+=IN_JUMP, j+=OUT_JUMP) {

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
	tlen += OUT_JUMP;
    }

    return tlen;
}

#if 0
int main(void) {
    unsigned int inbuf_len = 5120;
    unsigned int outbuf_len = 4*5120/5;    
    unsigned char *inbuf;
    unsigned short *outbuf; 
    int olen=0, ilen=0;

    inbuf = (unsigned char*)calloc(inbuf_len, sizeof(unsigned char));
    outbuf = (unsigned short*)calloc(outbuf_len, sizeof(unsigned short));
    while ((ilen=fread(inbuf, sizeof(unsigned char), inbuf_len, stdin)) > 0) {
	olen = dec10216(inbuf, ilen, outbuf);
	if (olen > 0)
	    fwrite(outbuf, sizeof(unsigned short), olen, stdout);    
    }
    return 0;
}
#endif
