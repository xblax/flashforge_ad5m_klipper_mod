# Moonraker timelapse plugin

By default the moonraker timelapse plugin is disabled. You can enable it by adding `enabled: True` in the the `/root/printer_data/config/moonraker.conf` file under `[timelapse]`. 

Please leave the `extraoutputparams`, `constant_rate_factor` and `pixelformat` as is unless you know what you are doing. These have been set to speed up the timelapse rendering as much as possible.

## Output

Files are stored in `/root/printer_data/timelapse` and the images in `/root/printer_data/timelapse/images`. By default the images will be deleted after rendering.

## Knowin issues

* Larger prints with many screenshots take a considerable amount of time to render. Think 10+ minutes.
