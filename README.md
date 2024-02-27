# Klipper Mod for Flashforge Adventurer M5 (Pro)
This is an unofficial mod to run Moonraker, custom Klipper, Mainsail & Fluidd on the Flashforge ADM5 (Pro) 3D printers and unlock the full power of open source software.

This mod is still in an early stage. The base features are functional, but it's not a polished and ready-to-use replacement for all stock features. 

The mod is designed to be fully removable and not break any functions of the stock software. But if you install it, then please be aware, that you risk to loose warranty or damage the printer. Proceed at your own risk if you want to try this mod!

## What's working
- Klipper 0.11
- Moonraker on port 7125
- Mainsail on port 4000
- Fluidd on port 4001
- Ethernet LAN (DHCP only)
- SSH root access. Login: `root`, Password: `klipper`
- "Dual boot" with stock Flashforge system
- Printer control via Display with [KlipperScreen](https://github.com/KlipperScreen/KlipperScreen)

## What's not working
- Camera
- WiFi
- Buzzer

Support for WiFi and Camera will likely come in a later version. There are no plans for Buzzer support at the moment.

## Documentation

### Installation

The mod uses the installation mechanism of the stock firmware. Download the latest `Adventurer5M-*.tgz` release to a USB flash drive and plug it in before starting the printer. Note: if you are using the 5M Pro, please rename the archive to `Adventurer5MPro-*.tgz`, otherwise it's not detected by the installer.

After successful installation, the printer will by default start the mod system instead. If the mod is re-installed or updated, all local modifications are lost. Only the G-Code files are retained.

At the moment, the mod only allows installations on printers that were updated to version 2.4.5 of the stock firmware.

### Uninstallation and Dual Boot

The startup process can be controlled via "marker" files on a USB flash drive.

- `klipper_mod_skip` - the printer boots to stock system, while this file detected
- `klipper_mod_remove` - the mod uninstalls itself and boots to stock system
- `klipper_mod_debug` - please check the code, if needed

Have only one of these files on a flash drive at the same time, otherwise a random one will be detected during startup.

### Technical Overview

The mod is self-contained in a [chroot](https://en.wikipedia.org/wiki/Chroot) environment. Therefore it's relatively safe to change the printer configuration without breaking the printer's stock functionality if you want to go back. The mod system environment is based on [Buildroot](https://buildroot.org/) embedded Linux.

Be careful if you insist to break out of the jail. The host system is mounted read-only to `/mnt/orig_root`.

The printer data partition is mounted to `/mnt/data` and G-Codes can be found in `/mnt/data/gcodes`. The mod system itself lives in the `.klipper_mod` folder on the data partition. Do not attempt to delete it while running the mod.
