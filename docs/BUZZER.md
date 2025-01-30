# Buzzer

The beep on the FF AD5m is a simple piezoelectric buzzer, which is controlled by a linux pwm device. It is capable of simple frequency manipulation and we included a library and gcode to allow it to be used.

This includes:
* M300 gcode to perform a `FREQUENCY` `DURATION` call like `M300 S440 P1000` for a one second A2 note.
* `PLAY_MIDI` command to play a very basic version of a midi song. Since the speaker is monotonic (and no mixing is done) it can only play one midi track e.g. `PLAY_MIDI FILE=filename C=0` to play _filename_ from `/usr/share/midi` and use track 0.  

The gcode M300 call is not quick enough to perform music like the ender printers are. Use the midi format for this.

Source available [here](https://github.com/consp/flashforge_ad5m_audio).
