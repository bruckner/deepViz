Compilation notes for OS X 10.7.5
===

Follow general instructions from here:
https://code.google.com/p/cuda-convnet/wiki/Compiling

You can use CUDA 5.5 (latest release) with convnet with some tweaks, described here:
https://gist.github.com/kuantkid/4180952

Also, comment out line 332 of common-gcc-4.0.mk, as follows:
```
#LIB += -lcutil_$(LIB_ARCH)$(LIBSUFFIX) -lshrutil_$(LIB_ARCH)$(LIBSUFFIX)
```

For python dependencies, you can use pip.  The atlas dependency can be
satisfied with libraries already installed for XCode.  I used find to 
locate files that were breaking the build; they should be in subdirectories
of `/Applications/XCode`.  You probably need XCode command line utils
installed.  They seem to move things around a lot from version to version,
too, so be prepared to search more widely.

My modified `build.sh` and `Makefile` are included here as examples. The
example files mentioned in there are useful references.

