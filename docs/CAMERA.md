# Camera

Klipper Mod for the AD5M uses [ustreamer](https://github.com/pikvm/ustreamer) for camera streaming. Linux uvcvideo / MJPEG compatible cameras should be automatically detected when connected via USB.

If a camera is detected, ustreamer is available via HTTP at port 8080. The camera must be manually configured in Mainsail or Fluidd.
