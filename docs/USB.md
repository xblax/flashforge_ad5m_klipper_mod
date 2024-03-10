# USB Auto mount

All usb drives are mounted in `/media` and are symlinked into the `/root/printer_data/gcodes/usb` directory. Only one USB drive is currently supported, as the FF AD5M only has one USB drive.

Some restrictions apply:
* Only FAT is supported and proper support is only available for FAT32 with standard extensions like long filenames. exFAT might work but is untested.
* Alternative codepage usage might result in mounting problems or malformed filenames, most users should not have any issues with this however.
