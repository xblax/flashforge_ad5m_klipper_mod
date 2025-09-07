#!/bin/sh
#
# MCU update script for Flashforge Adventurer 5M Klipper Mod.
# Keeps track of currently installed MCU firmware version.
#

# Allow script to be called from outside the chroot, detect environment
if [ -d "/mnt/orig_root" ]; then
    MOD_ROOT=""
    STOCK_ROOT="/mnt/orig_root"
    STOCK_EXEC="/mnt/orig_root/lib/ld-linux.so.3 --library-path /mnt/orig_root/lib:/mnt/orig_root/usr/lib/"
    CURRENT_MCU_VERSION_FILE="/root/printer_data/database/.klipper_mcu_version"
else
    MOD_ROOT="/data/.klipper_mod/chroot/"
    STOCK_ROOT=""
    STOCK_EXEC=""
    CURRENT_MCU_VERSION_FILE="/data/.klipper_mod/static/root/printer_data/database/.klipper_mcu_version"
fi

# firmware of klipper mod
MOD_MAINBOARD_MCU_FW="$MOD_ROOT/opt/klipper/firmware/mainboard.bin"
MOD_EBOARD_MCU_FW="$MOD_ROOT/opt/klipper/firmware/eboard.hex"

# stock flashforge firmware
STOCK_MAINBOARD_MCU_FW="$STOCK_ROOT/opt/PROGRAM/control/2.2.3/Mainboard-20230831.bin"
STOCK_EBOARD_MCU_FW="$STOCK_ROOT/opt/PROGRAM/control/2.2.3/Eboard-20231012.hex"

# note: mcu version file ist kept across klipper mod installs
CURRENT_MCU_VERSION=$(cat "$CURRENT_MCU_VERSION_FILE" 2> /dev/null | tr -d '\n')
MOD_KLIPPER_VERSION=$(tr -d '\n' < $MOD_ROOT/opt/klipper/klippy/.version)
KLIPPER_PID_FILE="/run/klipper.pid"

update_mainboard_mcu()
{
  $STOCK_EXEC $STOCK_ROOT/opt/PROGRAM/control/2.2.3/NationsCommand -c -d --pn /dev/ttyS5 --fn "$1" --v -r
}

update_eboard_mcu()
{
  # make sure mcu is in bootloader mode
  stty 230400 < /dev/ttyS1
  echo $'~ \x1c Request Serial Bootloader!! ~' >> /dev/ttyS1
  sleep 1
  # update
  $STOCK_EXEC $STOCK_ROOT/opt/PROGRAM/control/2.2.3/IAPCommand "$1" /dev/ttyS1
}

check_klipper_shutdown()
{
  if start-stop-daemon -K -t -p "$KLIPPER_PID_FILE" >/dev/null 2>&1; then
    echo "Klipper is running, cannot update MCUs!"
    exit 1
  fi
}

store_mcu_version()
{
  echo "$1" > "$CURRENT_MCU_VERSION_FILE"
  sync
}

update()
{
  check_klipper_shutdown
  update_mainboard_mcu "$MOD_MAINBOARD_MCU_FW" &
  update_eboard_mcu "$MOD_EBOARD_MCU_FW" &
  if wait; then
    store_mcu_version "$MOD_KLIPPER_VERSION"
    echo "MCU update success: new version $MOD_KLIPPER_VERSION"
  else
    store_mcu_version "unknown"
    echo "MCU update failed, try again after poweroff"
    exit 1
  fi
}

update_stock()
{
  check_klipper_shutdown
  update_mainboard_mcu "$STOCK_MAINBOARD_MCU_FW" &
  update_eboard_mcu "$STOCK_EBOARD_MCU_FW" &
  if wait; then
    store_mcu_version "stock"
    echo "MCU update success, installed stock firmware."
  else
    store_mcu_version "unknown"
    echo "MCU update failed, try again after poweroff."
    exit 1
  fi
}

check_update()
{
  if [ "$CURRENT_MCU_VERSION" = "$MOD_KLIPPER_VERSION" ]; then
    echo "MCUs are up to date: version $CURRENT_MCU_VERSION"
    return 0
  else
    echo "MCUs are outdated: version '$CURRENT_MCU_VERSION' (needs $MOD_KLIPPER_VERSION)"
    return 1
  fi
}

check_stock()
{
  if [ "$CURRENT_MCU_VERSION" == "stock" ]; then
    echo "MCUs have stock firmware."
    return 0
  else
    echo "MCUs not on stock firmware: version '$CURRENT_MCU_VERSION'"
    return 1
  fi
}

case "$1" in
  update)
        update
        ;;
  update_stock)
        update_stock
        ;;
  check_update)
        check_update
        ;;
  check_stock)
        check_stock
        ;;
  *)
        echo "Usage: $0 {update|update_stock|check_update|check_stock}"
        exit 1
esac
