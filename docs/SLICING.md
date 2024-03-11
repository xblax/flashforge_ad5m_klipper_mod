# Slicing

> [!WARNING]
> Slicer profiles intended for the ADM5 with stock Flashforge software do not work out of the box with this mod. Make sure to update the printer profile as described below.

## Printer profile

Existing ADM5 profiles can be used a baseline. But make sure to configure at least the following settings in the printer profile:

* GCODE output style should be _klipper_
* Do _*not*_ use the default FlashForge OrcaSlicer settings, they do not contain proper start/end sequences. 
* Edit the printer profile to use the [START_PRINT](../printer_configs/macros.cfg#L10) and [END_PRINT](../printer_configs/macros.cfg#L46) as described in macros.cfg as start/end macros.

> **Example:**  
> `START_PRINT BED_TEMP={first_layer_bed_temperature[0]} EXTRUDER_TEMP={first_layer_temperature[0]}`  
> Variables may differ depending on the slicer used.

## Automatic Bed Leveling and Nozzle Priming

The `START_PRINT` macro will do automatically bed leveling if no bed mesh profile is loaded. If you want to level the bed before each print you can set the `FORCE_LEVEL=true` parameter.

Alternatively, save a `default` profile that is loaded on Klipper Start or manually trigger bed leveling via the provided `AUTOMATIC_BED_LEVEL` macro.

The `START_PRINT` macro will automatically print a purge line before print. This can be disabled by setting the `DISABLE_PRIMING=true` parameter.

## Configuring Moonraker / Klipper connection

To connect to the printer, use the following physical printer settings:
* Host type: `moonraker`, `klipper` or `klipper (via moonraker)`
* Hostname, IP or URL: `x.y.z.a:7125` (replace with your ip)

## Known Issues

* Some slicers output G17 codes, which are not yet supported in the klipper version used and can cause warnings.  
  For example, in OrcaSlicer this is caused by the default z-hop method selected.  
  Please change it from `spiral` to `slope` in the printer configuration of your profile.
