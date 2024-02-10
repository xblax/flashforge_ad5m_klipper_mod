#!/bin/bash
set -e

log_info()
{
  CYAN='\033[0;36m'
  NC='\033[0m'
  echo -e "* ${CYAN}$1${NC}"
}

create_version()
{
    pushd $1
    version="$(git describe)-ffadm5_buildroot-$(date +%Y%m%d)"
    popd
    echo $version
}

# paths
SCRIPT_DIR="$(dirname "$0")"
GIT_ROOT="$SCRIPT_DIR/.."
BUILDROOT="$GIT_ROOT/submodules/buildroot"
TARGET_ROOT="$1"

# clean up root, if containing old build artefacts
rm -rf $TARGET_ROOT/root/setup
rm -rf $TARGET_ROOT/root/printer_data
rm -rf $TARGET_ROOT/root/printer_software

# create folder for initial setup files
mkdir -p $TARGET_ROOT/root/setup

# install klipper
log_info "Install Klipper"
mkdir -p $TARGET_ROOT/root/printer_software/klipper

# copy prebuild env or wheels
if [ -d $GIT_ROOT/prebuilt/klippy-env ]
then
  cp -r $GIT_ROOT/prebuilt/klippy-env $TARGET_ROOT/root/printer_software/klipper/
else
  cp -r $GIT_ROOT/prebuilt/wheels/klipper_wheels $TARGET_ROOT/root/setup/
  cp -r $GIT_ROOT/submodules/klipper/scripts/klippy-requirements.txt $TARGET_ROOT/root/setup/klipper_wheels/requirements.txt
fi

# install klippy pyhton sources
cp -r $GIT_ROOT/submodules/klipper/klippy $TARGET_ROOT/root/printer_software/klipper/
create_version $GIT_ROOT/submodules/klipper/ > $TARGET_ROOT/root/printer_software/klipper/klippy/.version

# install moonraker
log_info "Install Moonraker"
mkdir -p $TARGET_ROOT/root/printer_software/moonraker

# copy prebuilt env or wheels
if [ -d $GIT_ROOT/prebuilt/moonraker-env ]
then
  cp -r $GIT_ROOT/prebuilt/moonraker-env $TARGET_ROOT/root/printer_software/moonraker/
else
  cp -r $GIT_ROOT/prebuilt/wheels/moonraker_wheels $TARGET_ROOT/root/setup/
  cat $GIT_ROOT/submodules/moonraker/scripts/moonraker-requirements.txt > $TARGET_ROOT/root/setup/moonraker_wheels/requirements.txt
  cat $GIT_ROOT/submodules/moonraker/scripts/moonraker-speedups.txt >> $TARGET_ROOT/root/setup/moonraker_wheels/requirements.txt
fi

# install moonraker python sources
cp -r $GIT_ROOT/submodules/moonraker/moonraker $TARGET_ROOT/root/printer_software/moonraker/
create_version $GIT_ROOT/submodules/moonraker/ > $TARGET_ROOT/root/printer_software/moonraker/moonraker/.version

# install mainsail
log_info "Install Mainsail"
if [ ! -f $GIT_ROOT/prebuilt/mainsail.zip ]
then
  wget -P $GIT_ROOT/prebuilt/ https://github.com/mainsail-crew/mainsail/releases/download/v2.9.1/mainsail.zip
fi
mkdir -p $TARGET_ROOT/root/printer_software/mainsail/mainsail
unzip $GIT_ROOT/prebuilt/mainsail.zip -d $TARGET_ROOT/root/printer_software/mainsail/mainsail

# preconfigure
log_info "Install printer configs"
mkdir -p $TARGET_ROOT/root/printer_data/config
cp -r $GIT_ROOT/printer_configs/* $TARGET_ROOT/root/printer_data/config/
#ln -s /mnt/data $TARGET_ROOT/root/printer_data/gcodes
