# WiFi

WiFi on the mod is controlled by [iwd](https://iwd.wiki.kernel.org/). The preshared keys are stored in `/var/lib/iwd` and the configuration is stored in `/etc/iwd`. For the configuration file format look [here](https://iwd.wiki.kernel.org/networkconfigurationsettings).

Warning: WiFi settings are not persistent! The `/var/lib/iwd` directory and `/etc/iwd/main.conf` will be reset on (re)installation.

# Setting up a basic WiFi connection on the FF AD5M Klipper mod 

Normally all connections use DHCP, if you want to set a manual IP, look [here](https://iwd.wiki.kernel.org/ipconfiguration). <br />
If you want to encrypt the PSK storage, look [here](https://iwd.wiki.kernel.org/profile_encryption). <br />
If you want to use WPA2-Enterprise look [here](https://iwd.wiki.kernel.org/networkconfigurationsettings) for the correct settings.

## With Ethernet

* Connect the printer to ethernet port
* SSH to the printer and [log in as root](https://github.com/xblax/flashforge_adm5_klipper_mod/blob/master/README.md)
* `iwlist scanning` or `iwctl station wlan0 get-networks`  to view the networks in range (and detected), if your network is missing, wait a bit and perform `iwctl station wlan0 scan`
* `iwctl station wlan0 connect [SSID]` and enter the preshared key, or `iwctl --passphrase [PSK] station wlan0 connect [SSID]`

## With usb

The `klipper_mod` dir on a usb drive can be used as an overlay. Everything present on the usb while booting will be copied to the system.
This can be used to configure wifi.

Warning: not not forget to remove the installation file or the system will be reinstalled.

To setup using this method you can add a file to the `klipper_mod` directory on the usb drive for the SSID 'EXAMPLE_SSID' with passphrase `********`:

Create the USB drive File: `klipper_mod/var/lib/iwd/EXAMPLE_SSID.psk`
```conf
[Settings]
AutoConnect=True

[Security]
Passphrase=********
```

Once the system stars it should connect to your network.

## With KlipperScreen

Once klipperscreen has started:
* Press settings
* Press wifi
* Wait for the networks to show up
  * If no networks are shown, go back and retry the wifi button. 
* Once your SSID shows up, press the arrow button next to it
* Enter the preshared key. Press save to continue. 
  * This might take a moment. If the screen does not proceed after about 10 seconds, press the save button again.


# Additional information

For more commands and advanced usage of iwd, see the [linux kernel page for iwd](https://iwd.wiki.kernel.org/gettingstarted) or the [arch linux example page](https://wiki.archlinux.org/title/iwd).
