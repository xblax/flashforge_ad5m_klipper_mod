# KlipperScreen

*_Note: KlipperScreen is in alpha state._*

The klipper mod contains a Xorg installation and runs [klipperscreen](https://github.com/KlipperScreen/KlipperScreen) on top of that.

Klipperscreen should run as-is but not everything has been checked for proper operation. If you find a specific klipperscreen related bug please report an issue. For other bugs please also check if it occurs with the normal version (e.g. out of memory errors). You can also [join the discussion](https://github.com/xblax/flashforge_adm5_klipper_mod/discussions/12).

# Basic configuration

The configuration file for KlipperScreen is located in `/root/printer_data/configs` and can be edited by the user. Settings changes with the UX will be stored in this file. This file should be persistent across installations.

# Known issues

* Klipperscreen runs at a lower priority than other processes and during heavy load the screen might respond slower than expected.
* The WiFi interface might be slow. Currently the processes are synchronous which causes the UX to stall while fetching networks and connecting to a SSID.

