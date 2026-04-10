# Generated support makefile for backend 'cuda'
CC := /usr/local/cuda-12.6/bin/nvcc
LD := /usr/local/cuda-12.6/bin/nvcc
SUPPORT_ROOT := /home/matthias/Code/phoenix/phoenix/fgen/backends/cuda/support
INCLUDE_DIR := /home/matthias/Code/phoenix/phoenix/fgen/backends/cuda/support/include
SRC_DIR := /home/matthias/Code/phoenix/phoenix/fgen/backends/cuda/support/src
LIB_DIR := /home/matthias/Code/phoenix/phoenix/fgen/backends/cuda/support/lib
SOURCE := /home/matthias/Code/phoenix/phoenix/fgen/backends/cuda/support/src/phoenix_cuda_support.cu
OBJECT := $(LIB_DIR)/phoenix_cuda_support.o
TARGET := /home/matthias/Code/phoenix/phoenix/fgen/backends/cuda/support/lib/libphoenix_cuda_support.so
CFLAGS := -I$(INCLUDE_DIR) -Xcompiler -fPIC -Xcompiler -march=native
LDFLAGS := -shared -Xcompiler -fPIC -Xcompiler -march=native -Xlinker -rpath -Xlinker '$$ORIGIN:$$ORIGIN/..' -lcuda

.PHONY: help show support clean

help:
	@echo "Available targets: show, support, clean"

show:
	@echo "backend: cuda"
	@echo "support root: $(SUPPORT_ROOT)"
	@echo "header: $(INCLUDE_DIR)/phoenix_cuda_support.h"
	@echo "library: $(TARGET)"

support: $(TARGET)

$(LIB_DIR):
	mkdir -p $(LIB_DIR)

$(OBJECT): $(SOURCE) | $(LIB_DIR)
	$(CC) -c $(SOURCE) -o $(OBJECT) $(CFLAGS)

$(TARGET): $(OBJECT)
	$(LD) -o $(TARGET) $(OBJECT) $(LDFLAGS)

clean:
	rm -f $(OBJECT) $(TARGET)
