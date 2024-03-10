

### Technical Overview

The mod is self-contained in a [chroot](https://en.wikipedia.org/wiki/Chroot) environment. Therefore it's relatively safe to change the printer configuration without breaking the printer's stock functionality if you want to go back. The mod system environment is based on [Buildroot](https://buildroot.org/) embedded Linux.

Be careful if you insist to break out of the jail. The host system is mounted read-only to `/mnt/orig_root`.

The printer data partition is mounted to `/mnt/data` and G-Codes can be found in `/mnt/data/gcodes`. The mod system itself lives in the `.klipper_mod` folder on the data partition. Do not attempt to delete it while running the mod.