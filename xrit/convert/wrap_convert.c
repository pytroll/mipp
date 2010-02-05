/* -*-c-*-
 * 
 * $Id$
 * 
 * It will unpack 10 bit words into right adjusted 16 bit words.
 *
 */
#include <Python.h>
#include <stdlib.h>

#include "wrap_convert.h"

static PyObject *wrap_10216(PyObject *self, PyObject *args) {
    unsigned char *in_buffer;
    unsigned int in_length;
    unsigned int dec_length;
    unsigned short *dec_buffer;
    PyObject *array = NULL;

    if (!PyArg_ParseTuple(args, "s#", &in_buffer, &in_length)) {
        return NULL;
    }
    if (in_length > 0) {
	dec_length = (unsigned int)((4*in_length)/5);
	dec_buffer = (unsigned short *)calloc(dec_length, sizeof(unsigned short));
        dec_length = dec10216(in_buffer, in_length, dec_buffer);
        if (dec_length > 0) {	    
	    array = Py_BuildValue("s#", dec_buffer, (size_t)(dec_length)*sizeof(unsigned short));
        }
	free(dec_buffer);
    }
    if (array) {
	return array;
    }
    Py_RETURN_NONE;    
}

/* Set up the method table. */
static PyMethodDef convert_methods[] = {
    {"dec10216", wrap_10216, 1, "convert a blob of 10 bit words to a blob of 16 bit words"},
    {NULL, NULL, 0, NULL},   /* Sentinel */
};

PyMODINIT_FUNC init_convert(void) {
    (void)Py_InitModule("_convert", convert_methods);
}
