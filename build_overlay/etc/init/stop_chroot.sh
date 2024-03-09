#!/bin/sh
# stop chroot environment

/etc/init.d/rcK
swapoff /mnt/swap

# reset the hardware clock
# this is mainly to not confuse the host system with real time on warm reboot
date -s "1970-1-1 01:00:00"
hwclock -w

exit 0
