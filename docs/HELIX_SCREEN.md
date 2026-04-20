# Helix Screen

*_Note: HelixScreen support is in preview state on the AD5M._*

[HelixScreen](https://github.com/prestonbrown/helixscreen) is a modern LVGL-based touchscreen UI for Klipper-driven 3D printers. It renders directly to the framebuffer (no Xorg) and connects to the local Moonraker instance on port 7125.

The HelixScreen variant of Klipper Mod is a preview build for users who want to try HelixScreen on the AD5M. If you encounter any issues that could be caused by resource exhaustion (mostly system RAM), please check if the issue also occurs with the default variant.

## Configuration

HelixScreen stores its runtime state under `/data/helixscreen/`:

- `/data/helixscreen/config/` — persistent settings (created with defaults on first boot)
- `/data/helixscreen/cache/` — cache files
- `/data/helixscreen/log/helixscreen.log` — stdout/stderr of the running binary

Most settings can be changed directly from the on-screen UI. Advanced settings live in `/data/helixscreen/config/helixconfig.json`; edit that file over SSH if the UI does not expose the knob you need.

## Switching variants

If you already have the KlipperScreen or GuppyScreen variant flashed, uninstall Klipper Mod first (see [UNINSTALL.md](UNINSTALL.md)) before flashing the HelixScreen variant. Printer configuration under `/root/printer_data/config/` is preserved across re-installs.

## Known issues

* Pressing the power button will not wake up the screen.
* HelixScreen and its bundled XML assets are larger than GuppyScreen; check free space in `/mnt/UDISK` before flashing if your printer is heavily customized.
