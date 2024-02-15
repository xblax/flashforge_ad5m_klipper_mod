#!/bin/sh
set -ex

# workdir contains our update files
cd "$(dirname "$0")"
WORK_DIR="$(pwd)"
MACHINE=$1
PID=$2

# error handling
error_handler() {
  xzcat $WORK_DIR/img/install_fail_error.img.xz > /dev/fb0
  # always exit without error, to prevent immediate boot of flashforge software
  exit 0
}
trap '[ $? -eq 0 ] && exit 0 || error_handler' EXIT

# safety check, only install on supported printer
if ([ "$MACHINE" != "Adventurer5M" ] && [ "$MACHINE" != "Adventurer5MPro" ]) || \
   ([ "$PID" != "0023" ] && [ "$PID" != "0024" ]) || \
    [ "$(uname -m)" != "armv7l" ]
 then
    echo "Update file does not match machine type."
    xzcat $WORK_DIR/img/install_fail_vers.img.xz > /dev/fb0
    exit 0
fi

# saftey check, only install on supported versions
FF_VERSION="$(cat /root/version)"
if [ "$FF_VERSION" != "2.4.5" ]
then
    echo "Printer software version not supported."
    xzcat $WORK_DIR/img/install_fail_vers.img.xz > /dev/fb0
    exit 0
fi

MOD_INIT_FILE="/etc/init.d/S90klipper_mod"
MOD_DIR="/data/.klipper_mod"

# update start image
xzcat $WORK_DIR/img/install_start.img.xz > /dev/fb0
# --------------------------------

# uninstall previous mod version if present
rm -f $MOD_INIT_FILE
rm -rf $MOD_DIR

# check free space, we require 512MB before installation for saftey reason
FREE_SPACE=$(df /data | tail -1 | tr -s ' ' | cut -d' ' -f4)
MIN_SPACE="524228"
if [ "$FREE_SPACE" -lt "$MIN_SPACE" ]
then
    echo "Not enough free space on data partition. 512MB required!";
    xzcat $WORK_DIR/img/install_fail_mem.img.xz > /dev/fb0
    exit 0
fi

# unpack chroot environment
CHROOT_DIR="${MOD_DIR}/chroot"
mkdir -p $CHROOT_DIR
xz -dc $WORK_DIR/chroot.tar.xz | tar -xf - -C $CHROOT_DIR
sync

# do intial setup
$CHROOT_DIR/etc/init/S90klipper_mod setup
sync

# install initfile
cp $CHROOT_DIR/etc/init/S90klipper_mod /etc/init.d/
sync

# update end image
# --------------------------------
xzcat $WORK_DIR/img/install_ok.img.xz > /dev/fb0

exit 0
