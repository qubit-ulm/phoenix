#!/bin/bash
set -e

# ===== Configuration =====
MODULE_NAME=$2
F90_SOURCE=$1
BUILD_DIR=f2py_build
BUILD_SUBDIR=bbdir
VENV_PYTHON="$VIRTUAL_ENV/bin/python3"

if [ ! -f "$F90_SOURCE" ]; then
    echo "Error: Fortran source '$F90_SOURCE' not found"
    exit 1
fi

echo "🔧 Cleaning old build directories..."
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

echo "🔧 Generating pyf and wrapper by triggering minimal f2py compile..."

# This generates the .pyf and wrapper, but may fail linking (that’s okay)
echo "🔧 Generating pyf and wrapper by triggering minimal f2py compile..."
f2py -m $MODULE_NAME -h $BUILD_DIR/$MODULE_NAME.pyf $F90_SOURCE --overwrite-signature 
f2py -m $MODULE_NAME -c $F90_SOURCE --build-dir $BUILD_DIR 1>/dev/null 2>&1 || true

echo "📝 Writing meson.build..."
cat > $BUILD_DIR/meson.build <<EOF
project('$MODULE_NAME',
        ['c', 'fortran'],
        version : '0.1',
        meson_version: '>=1.1.0',
        default_options : ['warning_level=1', 'buildtype=release'])

py = import('python').find_installation('$VENV_PYTHON', pure: false)
py_dep = py.dependency()

incdir_numpy = run_command(py, ['-c', 'import numpy; print(numpy.get_include())'], check: true).stdout().strip()
incdir_f2py = run_command(py, ['-c', 'import numpy.f2py; print(numpy.f2py.get_include())'], check: true).stdout().strip()
inc_np = include_directories(incdir_numpy, incdir_f2py)
np_dep = declare_dependency(include_directories: inc_np)

fortranobject_c = incdir_f2py / 'fortranobject.c'
quadmath_dep = meson.get_compiler('fortran').find_library('quadmath', required: false)

libtemp = static_library('tempmod', '$F90_SOURCE',
    fortran_args: ['-ffree-line-length-none', '-O3'],
    include_directories: include_directories('.'))

py.extension_module('$MODULE_NAME',
    ['${MODULE_NAME}module.c',
     '${MODULE_NAME}-f2pywrappers2.f90',
     fortranobject_c],
    include_directories: [inc_np, include_directories('.')],
    fortran_args: ['-ffree-line-length-none'],
    dependencies: [py_dep, np_dep, quadmath_dep],
    link_with: libtemp,
    install: false)
EOF

echo "🚀 Compiling with Meson..."
meson compile -C $BUILD_DIR/$BUILD_SUBDIR

echo "📦 Copying final .so to current directory..."
cp $BUILD_DIR/$BUILD_SUBDIR/$MODULE_NAME*.so .

echo "✅ Build complete. You can now import the module via:"
echo "   >>> import $MODULE_NAME"

