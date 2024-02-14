#!/bin/sh
# This script is called once after inital setup

# prepare swap
fallocate -l 128M /mnt/swap
mkswap /mnt/swap
