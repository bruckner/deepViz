#!/bin/sh

# Fill in these environment variables.
# I have tested this code with CUDA 4.0, 4.1, and 4.2. 
# Only use Fermi-generation cards. Older cards won't work.

# If you're not sure what these paths should be, 
# you can use the find command to try to locate them.
# For example, NUMPY_INCLUDE_PATH contains the file
# arrayobject.h. So you can search for it like this:
# 
# find /usr -name arrayobject.h
# 
# (it'll almost certainly be under /usr)

# CUDA toolkit installation directory.
export CUDA_INSTALL_PATH=/usr/local/cuda

# CUDA SDK installation directory.
export CUDA_SDK_PATH=/Developer/NVIDIA/CUDA-5.5/samples/common/inc

# Python include directory. This should contain the file Python.h, among others.
export PYTHON_INCLUDE_PATH=/usr/include/python2.7/

# Numpy include directory. This should contain the file arrayobject.h, among others.
export NUMPY_INCLUDE_PATH=/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/numpy/core/include/numpy/

# ATLAS library directory. This should contain the file libcblas.so, among others.
export ATLAS_LIB_PATH=/Applications/Xcode.app//Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.7.sdk/usr/lib/

make $* -j4

