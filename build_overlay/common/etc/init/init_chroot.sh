#!/bin/sh
# "Init" process for chroot environment

mkdir -p /dev/shm
mkdir -p /run/lock/subsys

# load kernel modules for wifi
insmod /lib/modules/cbc.ko
insmod /lib/modules/md4.ko
insmod /lib/modules/sha512_generic.ko
insmod /lib/modules/uinput.ko
insmod /mnt/orig_root/lib/modules/8821cu.ko

# mount swap
swapon /mnt/swap
# set hostname
hostname -F /etc/hostname
# restore last known time
fake-hwclock load

# start chroot init scripts
/etc/init.d/rcS

exit 0
