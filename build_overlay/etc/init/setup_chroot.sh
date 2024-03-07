#!/bin/sh
# This script is called once after inital setup

# prepare swap
fallocate -l 128M /mnt/swap
mkswap /mnt/swap

# static data setup
static_dir="/mnt/data/.klipper_mod/static"
mkdir -p $static_dir

setup_static_data()
{
  # initial static data is initialized from the chroot
  if [ ! -e "$static_dir/$1" ]; then
    mkdir -p "$static_dir/"$(dirname "$1")
    mv "$1" "$static_dir/$1"
  fi

  # symlink the target to the static data
  rm -rf "$1"
  ln -s "$static_dir/$1" "$1"
}

# keep essential network settings
setup_static_data /etc/hostname
setup_static_data /var/lib/iwd
setup_static_data /etc/network/interfaces
setup_static_data /etc/dropbear

# keep moonraker database
mkdir -p /root/printer_data/database/
setup_static_data /root/printer_data/database/
