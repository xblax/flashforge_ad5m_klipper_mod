#!/bin/bash
cd "$(dirname "$0")"
set -e

# paths
SCRIPT_DIR="$(pwd)"
GIT_ROOT="$SCRIPT_DIR/.."
BUILD_DIR="$GIT_ROOT/build_output/wheels/"
BUILDROOT="$GIT_ROOT/submodules/buildroot"

CROSS="arm-buildroot-linux-gnueabi"
HOSTDIR="$BUILDROOT/output/host"
SYSROOT="$HOSTDIR/$CROSS/sysroot"
TARGET_PYTHON="$BUILDROOT/output/target/usr/bin/python3"

# set cross toolchain
export PATH="$HOSTDIR/bin:$PATH"
export LD_LIBRARY_PATH="$HOSTDIR/lib:$PATH"

export CC=$CROSS-gcc
export CXX=$CROSS-g++
export LD=$CROSS-ld
export AR=$CROSS-ar
export RANLIB=$CROSS-ranlib

export CFLAGS="-O3 -s --sysroot $SYSROOT -I "
export CXXFLAGS="-O3 -s --sysrot $SYSROOT"
export LDFLAGS="-s --sysroot $SYSROOT"

# create python host venv
rm -rf $BUILD_DIR > /dev/null
mkdir -p $BUILD_DIR
cd $BUILD_DIR
python3 -m venv host_venv

# create cross venv and activate
host_venv/bin/python3 -m pip install crossenv
host_venv/bin/python3 -m crossenv --machine=armv7l --sysroot="$SYSROOT" "$TARGET_PYTHON" cross_venv
source cross_venv/bin/activate

# build moonraker wheels
mkdir moonraker_wheels
MOONRAKER_DIR="$GIT_ROOT/submodules/moonraker"
# pillow needs seperate build with special parameters for cross-compilation
pip wheel -w moonraker_wheels --config-settings="--build-option=build_ext --disable-platform-guessing" pillow==10.2.0
pip wheel -w moonraker_wheel/ -r "$MOONRAKER_DIR/scripts/moonraker-requirements.txt"
# fix libuv build
export LIBUV_CONFIGURE_HOST=$CROSS
pip wheel -w moonraker_wheel/ -r "$MOONRAKER_DIR/scripts/moonraker-speedups.txt"

# build klipper wheels
mkdir klipper_wheels
KLIPPER_DIR="$GIT_ROOT/submodules/klipper"
pip wheel -w klipper_wheels/ -r "$KLIPPER_DIR/scripts/klippy-requirements.txt"
