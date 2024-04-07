# WiFi

WiFi in Klipper Mod for the AD5M is controlled by the [iNet wireless daemon](https://iwd.wiki.kernel.org/) (iwd). 

Wifi network settings are stored in `/var/lib/iwd` and the iwd daemon is configured in `/etc/iwd`. For the configuration file format look [here](https://iwd.wiki.kernel.org/networkconfigurationsettings).

## Setting up a basic WiFi connection

Normally all WiFi connections use DHCP, if you want to set a manual IP, look [here](https://iwd.wiki.kernel.org/ipconfiguration). <br />
If you want to encrypt the PSK storage, look [here](https://iwd.wiki.kernel.org/profile_encryption). <br />
If you want to use WPA2-Enterprise look [here](https://iwd.wiki.kernel.org/networkconfigurationsettings) for the correct settings.

### Configure via Ethernet / SSH

* Connect the printer to ethernet port
* SSH to the printer and [log in as root](../README.md)
* `iwlist scanning` or `iwctl station wlan0 get-networks`  to view the networks in range (and detected), if your network is missing, wait a bit and perform `iwctl station wlan0 scan`
* `iwctl station wlan0 connect [SSID]` and enter the preshared key, or `iwctl --passphrase [PSK] station wlan0 connect [SSID]`

Alternatively, edit the the SSID.psk file in `/var/lib/iwd`, see below for an example.

### Configure via USB

The `klipper_mod` dir on a usb drive can be used as an [overlay for custom config files](INSTALL.md) that are copied to the mod during installation. This can be used to set-up the initial WiFi connection.

To setup WiFi using this method you can add a file to the `klipper_mod` directory on the usb drive for the SSID 'EXAMPLE_SSID' with passphrase `********`:

Create the USB drive file: `klipper_mod/var/lib/iwd/EXAMPLE_SSID.psk`
```conf
[Settings]
AutoConnect=True

[Security]
Passphrase=********
```

> [!WARNING]
> Make sure you use linux line endings and do NOT use windows notepad to create or edit the file.

Install the mod as described in [Install](INSTALL.md) and after installation the printer should connect to your network.

### Configure with KlipperScreen

Once klipperscreen has started:
* Press settings
* Press wifi
* Wait for the networks to show up
  * If no networks are shown, go back and retry the wifi button. 
* Once your SSID shows up, press the arrow button next to it
* Enter the preshared key. Press save to continue. 
  * This might take a moment. If the screen does not proceed after about 10 seconds, press the save button again.


## Additional information

For more commands and advanced usage of iwd, see the [linux kernel page for iwd](https://iwd.wiki.kernel.org/gettingstarted) or the [arch linux example page](https://wiki.archlinux.org/title/iwd).
