# Generated support makefile for backend 'c'
CC := /usr/bin/cc
LD := /usr/bin/cc
SUPPORT_ROOT := /home/matthias/Code/phoenix/phoenix/fgen/backends/c/support
INCLUDE_DIR := /home/matthias/Code/phoenix/phoenix/fgen/backends/c/support/include
SRC_DIR := /home/matthias/Code/phoenix/phoenix/fgen/backends/c/support/src
LIB_DIR := /home/matthias/Code/phoenix/phoenix/fgen/backends/c/support/lib
SOURCE := /home/matthias/Code/phoenix/phoenix/fgen/backends/c/support/src/phoenix_c_support.c
OBJECT := $(LIB_DIR)/phoenix_c_support.o
TARGET := /home/matthias/Code/phoenix/phoenix/fgen/backends/c/support/lib/libphoenix_c_support.so
CFLAGS := -std=c99 -I$(INCLUDE_DIR) -fPIC -march=native
LDFLAGS := -shared -Wl,-rpath,'$$ORIGIN:$$ORIGIN/..'

.PHONY: help show support clean

help:
	@echo "Available targets: show, support, clean"

show:
	@echo "backend: c"
	@echo "support root: $(SUPPORT_ROOT)"
	@echo "header: $(INCLUDE_DIR)/phoenix_c_support.h"
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
