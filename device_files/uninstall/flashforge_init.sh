#!/bin/sh
set -ex

# workdir contains our update files
cd "$(dirname "$0")"
WORK_DIR="$(pwd)"
MACHINE=$1
PID=$2

# error handling
error_handler() {
  xzcat $WORK_DIR/img/uninstall_fail_error.img.xz > /dev/fb0
  sync
  # always exit without error, to prevent immediate boot of flashforge software
  exit 0
}
trap '[ $? -eq 0 ] && exit 0 || error_handler' EXIT

do_setup()
{
    MOD_INIT_FILE="/etc/init.d/S00klipper_mod"
    MOD_INIT_LOG_PREFIX="/root/mod_init"
    MOD_DIR="/data/.klipper_mod"

    # remove everything
    rm -f "$MOD_INIT_FILE"
    rm -f "$MOD_INIT_LOG_PREFIX"*
    rm -rf "$MOD_DIR"

    # unconditionally restore stock MCU version
    xzcat $WORK_DIR/img/mcu_update_stock.img.xz > /dev/fb0
    /bin/sh $WORK_DIR/mcu_update.sh update_stock

    # update end image
    xzcat $WORK_DIR/img/uninstall_ok.img.xz > /dev/fb0
}

# write log (if mount point is found)
if grep "^/dev/sd[ab12]* /mnt " /proc/mounts; then
  do_setup &> /mnt/klipper_mod_uninstall.log
  sync
else
  do_setup
fi

exit 0
