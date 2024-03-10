### Uninstallation and Dual Boot

The startup process can be controlled via "marker" files on a USB flash drive.

- `klipper_mod_skip` - the printer boots to stock system, while this file detected
- `klipper_mod_remove` - the mod uninstalls itself and boots to stock system
- `klipper_mod_debug` - please check the code, if needed

Have only one of these files on a flash drive at the same time, otherwise a random one will be detected during startup.