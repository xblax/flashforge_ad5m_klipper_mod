# Uninstall

There are multiple options to uninstall Klipper Mod from an AD5M (Pro) printer.

> [!WARNING]
> During uninstall, all you local changes to the mod are removed from the printer. That includes all your custom files such as the G-Code files or custom Klipper configuration. Make sure to create a back-up if you want to re-install at a later point.
>
> If you just want to go back to go back to the stock software occasionally, consider to use on of the Dual Boot options described in the [Install](INSTALL.md) documentation. 

### Uninstall via USB

Download the `Adventurer5M-KlipperMod-uninstall.tgz` file from the [Release](https://github.com/xblax/flashforge_ad5m_klipper_mod/releases) page onto a USB flash drive, similar to the [Install](INSTALL.md) procedure.

Alternatively a marker file `klipper_mod_remove` will also trigger automatic uninstall during printer start-up.

### Uninstall via SSH

Log in via SSH run the command `remove-klipper-mod`. Confirm removal. The printer will reboot and automatically uninstall the mod during start-up.

### Uninstall via Klipper Macro

Run the macro `REMOVE_KLIPPER_MOD` and confirm the removal. The printer will reboot and automatically uninstall the mod during start-up.
