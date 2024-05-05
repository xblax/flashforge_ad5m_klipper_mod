
# Install

Klipper Mod for the AD5M is designed to be fully removable and not break any functions of the stock software. 

> [!CAUTION]
> *If you want to install this Klipper Mod to your AD5M (Pro) then be aware, that you risk to loose your warranty or damage the printer. Proceed at your own risk if you want to try this mod!*

## Installation

The mod uses the same installation mechanism as the stock software:
1) Download the latest `Adventurer5M-KlipperMod*.tgz` update file from the [Release](https://github.com/xblax/flashforge_ad5m_klipper_mod/releases) page onto a USB flash drive.
2) Plug in the drive before starting the printer. 
3) Successful installation will be indicated on the display when finished.

The mod installer currently requires that printers were updated to at least version 2.4.5 of the stock Flashforge firmware. Please check the release page for versions that are known to work.

After installation the printer will by default start the Klipper Mod system instead of the stock Flashforge software. It is still possible to start the stock software without uninstalling the mod, if needed. See section [Dual Boot](#dual-boot) below.

### Install on 5M Pro

The installation archives must be renamed to `Adventurer5MPro-*.tgz`. Otherwise the install files are not detected by the 5M Pro printers.

### Install Custom Files

The Klipper Mod installer has a mechanism to install custom files from USB flash drive during the installation. All files that are put inside the `klipper_mod` folder will be copied to the same path in the mod system as inside the `klipper_mod` folder. 

> **Example**  
> A file `klipper_mod/var/lib/iwd/MyWifi.psk` on the USB drive will be copied to `/var/lib/iwd/MyWifi.psk` during installation.

This mechanism can also be used to overwrite default config files. Check the [Linux](LINUX.md) documentation page for more info about the file system layout.

### Initial Network Setup

If no custom configuration is provided the mod is pre-configured for DHCP only. Connect the printer via Ethernet and use your home router web interface to find the IP that was auto-assigned to the printer.

It is also possible to install a custom network configuration via the custom file installation mechanism described above. Create a custom [`/etc/network/interfaces`](https://manpages.debian.org/bullseye/ifupdown/interfaces.5.en.html) file or install a [custom WiFi config](WIFI.md) to `/var/lib/iwd`.

### Install Log File

During the installation process a log file `klipper_mod_install.log` is written to the USB drive. This log file is helpful to understand the reason for installation failures. Please provide this file if you ask for help in the [GitHub Discussion](https://github.com/xblax/flashforge_ad5m_klipper_mod/discussions) forums.

## Updating

Updating the mod works similar to the installation. Be aware that that most local changes are lost during the update. Only a limited set of files is preserved while updating:

- Moonraker database
- G-Code files
- Network configuration and hostname
- Dropbear SSH Keys

To remove all persistent files, [Uninstall](UNINSTALL.md) the mod before re-installing.

> [!WARNING]
> If you have important files like custom printer configs make sure to create a backup before updating. You can use the custom file installation mechanism to re-install them from the USB drive.

## Dual Boot

There are multiple options to boot the stock Flashforge software, while the mod is installed.

- USB drive: put a file named `klipper_mod_skip` on a USB drive and plug it in before printer start
- SSH: log in via SSH and run the command `reboot-stock-system` to restart and boot the stock software
- Klipper Macro: Execute the Klipper macro `REBOOT_STOCK_SYSTEM`
