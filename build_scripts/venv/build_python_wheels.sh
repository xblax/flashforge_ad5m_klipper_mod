#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $SCRIPT_DIR/../env.sh

BUILD_DIR="$BUILD_OUT/wheels/"
HOST_DIR="$BUILDROOT_SDK/host"
CROSS="arm-buildroot-linux-gnueabihf"
SYSROOT="$HOST_DIR/$CROSS/sysroot"
TARGET_PYTHON="$BUILDROOT_SDK/build/python3-3.11.7/python"
# using the sysroot pyhton does not work for some reason
# TARGET_PYTHON="$SYSROOT/usr/bin/python3"

# set cross toolchain
export PATH="$HOST_DIR/bin:$HOST_DIR/usr/bin:$PATH"
export LD_LIBRARY_PATH="$HOST_DIR/lib:$HOST_DIR/usr/lib:$HOST_DIR/lib64:$HOST_DIR/usr/lib64"

export CC=$CROSS-gcc
export CXX=$CROSS-g++
export LD=$CROSS-ld
export AR=$CROSS-ar
export RANLIB=$CROSS-ranlib

export CFLAGS="-O3 -s"
export CXXFLAGS="-O3 -s"
export LDFLAGS="-s"

# prepare build
rm -rf $BUILD_DIR > /dev/null
mkdir -p $BUILD_DIR
cd $BUILD_DIR
export PIP_DISABLE_PIP_VERSION_CHECK=1
log_info "Purge pip cache"
pip cache purge &> /dev/null

log_info "Start building wheels in $(pwd) ... "

# create cross venv and activate
python3 -m pip install crossenv
python3 -m crossenv --machine=armv7l --sysroot=$SYSROOT "$TARGET_PYTHON" cross_venv
source cross_venv/bin/activate

log_info "Build moonraker wheels ..."

# build moonraker wheels
mkdir moonraker_wheels
MOONRAKER_DIR="$GIT_ROOT/submodules/moonraker"
# pillow needs seperate build with special parameters for cross-compilation
pip wheel -w moonraker_wheels/ --config-settings="--build-option=build_ext --disable-platform-guessing" pillow==10.2.0
pip wheel -w moonraker_wheels/ -r "$MOONRAKER_DIR/scripts/moonraker-requirements.txt"
# fix libuv build
export LIBUV_CONFIGURE_HOST=$CROSS
pip wheel -w moonraker_wheels/ -r "$MOONRAKER_DIR/scripts/moonraker-speedups.txt"

log_info "Build klipper wheels ..."

# build klipper wheels
mkdir klipper_wheels
KLIPPER_DIR="$GIT_ROOT/submodules/klipper"
pip wheel -w klipper_wheels/ -r "$KLIPPER_DIR/scripts/klippy-requirements.txt"

log_info "Building klipperscreen wheels ..."
mkdir klipperscreen_wheels
KLIPPERSCREEN_DIR="$GIT_ROOT/submodules/KlipperScreen"
pip wheel -w klipperscreen_wheels/ -r "$KLIPPERSCREEN_DIR/scripts/KlipperScreen-requirements.txt"

log_info "Done"
pwd
