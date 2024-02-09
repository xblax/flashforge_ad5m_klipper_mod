#!/bin/sh
# this script is called once after inital setup

# prepare swap
fallocate -l 128M /mnt/swap
mkswap /mnt/swap

# todo: prepare klipper + moonraker venv
