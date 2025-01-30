# Guppy Screen

*_Note: Guppy Screen is in alpha state._*

[GuppyScreen](https://github.com/ballaswag/guppyscreen/) is an alternative gui created by @ballaswag originally for the K1 but wit a bit of editing also runs on the AD5M(Pro). It uses far less resources than KlipperScreen and is more responsive but has less features (at the moment).

Some options can be edited in the 'systems' menu, for others edit `/root/printer_data/config/guppyscreen.json`, [see the documentation](https://ballaswag.github.io/docs/guppyscreen/configuration/) for the settings.

It is **_not_** recommended to set the logs to debug due to excessive writing.

## Known issues

* Input shaper will stop the first time due to excessive memory consumption triggering an eboard timeout
* FIRMWARE_RESET message might not show up after input shaper error, you must use fluidd or mainsail in that case.
* RESET message might not show up after input shaper error, you must use fluidd or mainsail in that case.
* "Printer initializing" message might be stuck on screen for a while. (infinity is also a while, if you have this, please let it be known)
* Pressing the power button will not wake up the screen (but the message will show)
