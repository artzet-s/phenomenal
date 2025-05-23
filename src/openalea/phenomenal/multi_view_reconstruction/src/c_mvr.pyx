#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
import numpy as np
cimport numpy as np
np.import_array()  # Ensures NumPy C API is ready
from libc.stdlib cimport malloc, free

cdef extern from "integral_image.h":
    void c_integral_image(const unsigned char* input, 
                          const unsigned int size_x, 
                          const unsigned int size_y, 
                          unsigned int* output)


def integral_image(np.ndarray[unsigned char, ndim=2, mode="c"] input,
                   np.ndarray[unsigned int, ndim=2, mode="c"] output):

    c_integral_image(<const unsigned char*> input.data, 
                     input.shape[0], 
                     input.shape[1], 
                     <unsigned int*> output.data);
