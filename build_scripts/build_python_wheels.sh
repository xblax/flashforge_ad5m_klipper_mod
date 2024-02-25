#!/bin/bash
cd "$(dirname "$0")"
set -e

log_info()
{
  CYAN='\033[0;36m'
  NC='\033[0m'
  echo -e "* ${CYAN}$1${NC}"
}

# paths

SCRIPT_DIR="$(pwd)"
GIT_ROOT="$SCRIPT_DIR/.."
BUILD_DIR="$GIT_ROOT/build_output/wheels/"
BUILDROOT="$GIT_ROOT/submodules/buildroot"

HOSTDIR="$BUILDROOT/output/host"
TARGET_PYTHON="$BUILDROOT/output/build/python3-3.11.7/python"

if [ -z "$HARDFLOAT" ]; then
	HF=""
	CROSS="arm-buildroot-linux-gnueabi"
else
	HF="+vfpv4+simd"
	CROSS="arm-buildroot-linux-gnueabihf"
fi

SYSROOT="$BUILDROOT/output/host/$CROSS/sysroot"

# set cross toolchain
export PATH="$HOSTDIR/bin:$PATH"
export LD_LIBRARY_PATH="$HOSTDIR/lib"

export CC=$CROSS-gcc
export CXX=$CROSS-g++
export LD=$CROSS-ld
export AR=$CROSS-ar
export RANLIB=$CROSS-ranlib

export CFLAGS="-O3 -s --sysroot $SYSROOT"
export CXXFLAGS="-O3 -s --sysroot $SYSROOT"
export LDFLAGS="-s --sysroot $SYSROOT"

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
python3 -m crossenv --machine=armv7l$HF --sysroot=$SYSROOT "$TARGET_PYTHON" cross_venv
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

log_info "Done"
pwd
