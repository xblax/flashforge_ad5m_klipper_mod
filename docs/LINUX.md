# Linux Environment

Klipper Mod for the AD5M is based on [Buildroot](https://buildroot.org/) for embedded Linux systems. 

Klipper Mod is not a conventional Linux distribution such as Debian/Linux that many Klipper users may know from the Rapsberry Pi. For example you won't find a package manager or systemd.

[Connect via SSH](../README.md) to the printer to explore the system. Linux users should feel familiar and many useful command-line tools come pre-installed with the mod.

> [!WARNING]
> Be aware of the limited system resources. Especially the 128MB ram limit what can be installed and run in background while printing. 

## Important Paths

- `/root/printer_software` contains the Klipper and Moonraker installation
- `/root/printer_data` contains printer config files, G-Codes, the moonraker database, log files
- `/var/lib/iwd` contains the [WiFi](WIFI.md) network profiles
- `/etc/init.d/` contains the init scripts for default services

## Technical Overview

The mod is self-contained in a [chroot](https://en.wikipedia.org/wiki/Chroot) environment. Therefore it's relatively safe to change the printer configuration or modify the Klipper Mod Linux environment without breaking the printer's stock functionality.

Be careful if you insist to break out of the jail. The host system is mounted read-only to `/mnt/orig_root`. The printer data partition is mounted to `/mnt/data`.

The mod system itself lives in the `.klipper_mod` folder on the printer data partition. Do not attempt to delete it while running the mod.
