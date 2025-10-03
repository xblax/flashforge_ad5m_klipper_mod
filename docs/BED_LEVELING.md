# Initial Calibration Before Printing
Proper calibration is essential for achieving high-quality prints.

If you’re experienced with other printers, you might assume that calibration involves adjusting the z-endstop using `Z_ENDSTOP_CALIBRATE`, calibrating the probe-to-nozzle offset with `PROBE_CALIBRATE`, and creating a bed mesh. Once done, you’d consider the printer ready to go. However, that’s not the recommended approach here.

The Z-Endstop in this setup is deliberately positioned to prevent the nozzle from crashing into the bed, even if you switch to a thicker build plate and forget to create a mesh. For this reason, the Z-Endstop should not be adjusted. In fact, attempting to save changes to it will result in an error.

In this system, the "z-offset" refers not just to the offset between the nozzle and the probe (as typically intended by Klipper) but also compensates for the lower z-endstop.

Follow the steps below to ensure perfect first layers:

## Step 1: Create a Heightmap
1. Use the "Heightmap" option in the menu to create a heightmap, or the Bed Leveling option if you are using guppyscreen.
2. Ensure the nozzle is clean and not leaking filament, as this can result in an inaccurate heightmap.
3. Perform this step with the bed and nozzle at room temperature.

**Important**: After creating the mesh, your printer still isn’t ready for printing. The nozzle-to-bed distance will be too large due to the Z-Endstop being intentionally offset.

## Step 2: Adjust the Z-Offset
While the default z-offset in the configuration works initially, it doesn’t account for the intentionally lower z-endstop. To address this, you’ll need to adjust the Z-offset using the well-known [paper test](https://www.klipper3d.org/Bed_Level.html?h=paper#the-paper-test).

1. Move the toolhead to the center of the build plate (X=0, Y=0) with Z=2.
2. Gradually lower the Z-axis to Z=0, ensuring the nozzle doesn’t come down too far and crash into the bed.
3. Once at Z=0, continue lowering the nozzle in small increments by using "babysteps" to adjust the z-offset until the paper test indicates the correct distance. The nozzle should lightly grip a sheet of paper, allowing it to slide with slight resistance.

Once the Z-offset is properly calibrated, save the new value with the `Z_ENDSTOP_CALIBRATE` command. Klipper will calculate the new Z-offset based on the adjustment.

**Note**: This process invalidates the previously created heightmap. To avoid errors, delete the heightmap and save your configuration with `SAVE_CONFIG`.

## Step 3: Recreate the Heightmap
Now, recreate the heightmap by repeating Step 1. This time, the heightmap will account for the adjusted Z-offset and produce a more accurate representation of your bed surface. The new heightmap will reflect the corrected nozzle-to-bed relationship, ensuring optimal print quality.

At Z=0, the nozzle will now be positioned precisely as determined during the paper test.

With these steps, your printer is fully calibrated and ready to deliver high-quality first layers.
