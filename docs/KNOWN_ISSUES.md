# Known Issues

This section documents some known issues that exist, but are unlikely to be fixed:

* Printer resource limitations and consequences of system overload:  
The 5M (PRO) has very limited system resources, especially limited ram and slow flash. In general the mod is stable for everyday use
with all features for printing and control of the printer functions, including KlipperScreen and Webcam. However, if heavy background task are attemped while printing, 
i.e. rendering a timelapse or copying huge amounts of data to the system it will very likely make the print fail (so don't do it).

* Sporadic MCU timeouts during SHAPER_CALIBRATE:  
Timeout errors during input shaper calibration can happen in some cases, since it's a quite resource intenstive task. If it happens, just restart Klipper and restart
the calibration. It's not a limitation for everyday use. It's recommened to run the calibration via Mainsail or Fluidd, not via printer UI (especially Guppy Screen).

* MCU timeouts after the printer was idle for a long time:  
If the printer was idle for multiple hours and a new print is started, timeouts during homing or print start can happen. 
This can be avoided by restarting KLipper or the printer, it was not used for a long time since the last print.

* Guppy Screen:  
Guppy Screen upstream development has currently stopped and fixing relates issues is not a priortiy for this mod. 
Also see [Guppy Screen](GUPPY_SCREEN.md) for known issues with it. Use it as-is or provide a pull request to improve it's integration. 

* USB device failures:  
USB devices connected to the screen can ocassionaly fail to be detected due to poor shielding of the USB connection in the printer. 
In most cases a reboot will fix the issue. For external connected webcams it's recommended to use a short USB cable.
