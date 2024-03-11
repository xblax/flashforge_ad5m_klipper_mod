# Slicing

Make sure you use at least the following settings:

* GCODE output style should be _klipper_
* Do _*not*_ use the default FlashForge OrcaSlicer settings, they do not contain proper start/end sequences. You can use [START_PRINT](../printer_configs/macros.cfg#L10) and [END_PRINT](../printer_configs/macros.cfg#L46) as described in macros.cfg as start/end macros.
  * Example: `START_PRINT BED_TEMP={first_layer_bed_temperature[0]} EXTRUDER_TEMP={first_layer_temperature[0]}`, variables may differ depending on the slicer used.

# Configuring the moonraker/klipper connection

To connect to the printer, use the following physical printer settings:
* Host type: `moonraker`, `klipper` or `klipper (via moonraker)`
* Hostname, IP or URL: `x.y.z.a:7125` (replace with your ip)


# Known issues

* Some slicers output G17 codes, which are not yet supported in the klipper version used and can cause warnings.  
  For example, in OrcaSlicer this is caused by the default z-hop method selected.  
  Please change it from `spiral` to `slope` in the printer configuration of your profile.
