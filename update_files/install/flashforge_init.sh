#!/bin/sh
set -ex

# workdir contains our update files
cd "$(dirname "$0")"
WORK_DIR="$(pwd)"
MACHINE=$1
PID=$2

# safety check, only install on supported printer
if ([ "$MACHINE" != "Adventurer5M" ] && [ "$MACHINE" != "Adventurer5MPro" ]) || \
   ([ "$PID" != "0023" ] && [ "$PID" != "0024" ]) || \
    [ "$(uname -m)" != "armv7l" ]
 then
    echo "Update file does not match machine type."
    exit 1
fi

# saftey check, only install on supported versions
FF_VERSION="$(cat /root/version)"
if [ "$FF_VERSION" != "2.4.5" ]
then
    echo "Printer software version not supported."
    exit 1
fi

MOD_INIT_FILE="/etc/init.d/S90klipper_mod"
MOD_DIR="/data/.klipper_mod"

# update start image
cat $WORK_DIR/start.img > /dev/fb0
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
    exit 1
fi

# unpack chroot environment
CHROOT_DIR="${MOD_DIR}/chroot"
mkdir -p $CHROOT_DIR
xz -dc $WORK_DIR/chroot.tar.xz | tar -xf - -C $CHROOT_DIR
sync

# do intial setup
./S90klipper_mod setup
sync

# install initfile
cp $WORK_DIR/S90klipper_mod /etc/init.d
sync

# update end image
# --------------------------------
cat $WORK_DIR/end.img > /dev/fb0

$WORK_DIR/play
exit 0
