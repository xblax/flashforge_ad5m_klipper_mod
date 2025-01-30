# KlipperScreen

The klipper mod contains a Xorg installation and runs [klipperscreen](https://github.com/KlipperScreen/KlipperScreen) on top of that.

Klipperscreen should run as-is but not everything has been checked for proper operation. If you find a specific klipperscreen related bug please report an issue. For other bugs please also check if it occurs with the normal version (e.g. out of memory errors). You can also [join the discussion](https://github.com/xblax/flashforge_ad5m_klipper_mod/discussions/12).

# Basic configuration

The configuration file for KlipperScreen is located in `/root/printer_data/configs` and can be edited by the user. Settings changes with the UX will be stored in this file. This file should be persistent across installations.

The following options have been added which are not in standard KlipperScreen:

```
[main]
screen_brightness: int
```

`screen_brightness` can be set to an integer, cofiguration options in the menu are 10-100 in increments of 10. Zero is not selectable since it would disable the screen.

# Known issues

* Klipperscreen runs at a lower priority than other processes and during heavy load the screen might respond slower than expected.
* The WiFi interface might be slow. Currently the processes are synchronous which causes the UX to stall while fetching networks and connecting to a SSID.

