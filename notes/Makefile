MODELNAME := _ConvNet

INCLUDES := -DCUDA_5 -I$(PYTHON_INCLUDE_PATH) -I$(NUMPY_INCLUDE_PATH) -I$(CUDA_SDK_PATH) -I./include -I./include/common -I./include/cudaconv2 -I./include/nvmatrix -I./dummyinclude -I/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.7.sdk/System/Library/Frameworks/Accelerate.framework/Versions/A/Frameworks/vecLib.framework/Versions/A/Headers
LIB := -lpthread -L$(ATLAS_LIB_PATH) -L$(CUDA_INSTALL_PATH)/lib -lcblas

USECUBLAS   := 1

PYTHON_VERSION=$(shell python -V 2>&1 | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
LIB += -lpython$(PYTHON_VERSION)

GENCODE_ARCH := -gencode=arch=compute_20,code=\"sm_20,compute_20\"
COMMONFLAGS := -DNUMPY_INTERFACE -DMODELNAME=$(MODELNAME) -DINITNAME=init$(MODELNAME)

EXECUTABLE      := $(MODELNAME).so

CUFILES                         := $(shell echo src/*.cu src/cudaconv2/*.cu src/nvmatrix/*.cu)
CU_DEPS                         := $(shell echo include/*.cuh include/cudaconv2/*.cuh include/nvmatrix/*.cuh)
CCFILES                         := $(shell echo src/common/*.cpp)
C_DEPS                          := $(shell echo include/common/*.h)

include common-gcc-cuda-4.0.mk

makedirectories:
        $(VERBOSE)mkdir -p $(LIBDIR)
        $(VERBOSE)mkdir -p $(OBJDIR)/src/cudaconv2
        $(VERBOSE)mkdir -p $(OBJDIR)/src/nvmatrix
        $(VERBOSE)mkdir -p $(OBJDIR)/src/common
        $(VERBOSE)mkdir -p $(TARGETDIR)
