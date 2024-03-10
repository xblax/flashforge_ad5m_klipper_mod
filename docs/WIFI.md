# WiFi

* Connect the printer to ethernet port
* SSH to the printer and log in as root
* `iwlist` or `iwctl station wlan0 get-networks`  to view the networks in range (and detected), if your network is missing, wait a bit or perform `iwctl station wlan0 scan`
* `iwctl station wlan0 connect [SSID]` and enter the preshared key, or `iwctl --passphrase [PSK] station wlan0 connect [SSID]`

Useful iwctl commands:

* `iwctl` to connect to the iwctl prompt and perform actions directly
* `iwctl device list` to view wifi devices
* `iwctl station [wifi device] scan` to (re)start scanning
* `iwctl --passphrase [psk] station wlan0 connect [wifinetworkname]` to connect to a network

Your preshared keys keys will be stored in `/var/lib/iwd/`. For more advanced (e.g. EAP-PEAP) configurations see the [archlinux wiki](https://wiki.archlinux.org/title/iwd) 
