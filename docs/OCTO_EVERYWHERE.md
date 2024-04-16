# OctoEverywhere

On device support is currently not present (and not highly likely to be in the future) but user @skylatian wrote an explanation how to do it off the printer:

# From #63

https://github.com/xblax/flashforge_ad5m_klipper_mod/issues/63#issuecomment-2005655002

### It worked for me as well, but *without* config changes!

I also finally got time to give Octoeverywhere Companion a shot, and it works great — I didn't need to run a local Moonraker instance or change any config files (detail below). I'm totally fine running this externally, though down the line it would be great to have OctoEverywhere running on the AD5M.

I'm running this on an Ubuntu VM on a Synology NAS, but the process should be basically the same on any Ubuntu or Debian machine. This is basically the same as the steps [here](https://octoeverywhere.com/getstarted?source=blog_companion&companion=t), just documenting them here for reference.

## Adventurer 5M (Pro) OctoEverywhere Companion Install

On the companion device:

`sudo apt update`
`sudo apt install curl` (may be required, it was for my barebones Ubuntu image)
`bash <(curl -s https://octoeverywhere.com/companion.sh)`

While following the setup prompts that appeared, Companion failed to find a Moonraker instance at the port I provided. However, the installer then prompted for the full IP+UI port of the machine. I chose Fluidd, and it detected the Moonraker install and worked right away!

<img width="699" alt="image" src="https://github.com/xblax/flashforge_adm5_klipper_mod/assets/53362705/189e80d9-39da-41c4-9c0b-ff8766839fce">

