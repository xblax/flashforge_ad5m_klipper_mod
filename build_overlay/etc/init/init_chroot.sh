#!/bin/sh

# mount swap
swapon /mnt/swap
# start chroot init scripts
/etc/init.d/rcS
