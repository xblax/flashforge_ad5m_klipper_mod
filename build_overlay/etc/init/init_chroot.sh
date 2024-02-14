#!/bin/sh
# "Init" process for chroot environment

# mount swap
swapon /mnt/swap
# set hostname
hostname -F /etc/hostname
# start chroot init scripts
/etc/init.d/rcS

exit 0
