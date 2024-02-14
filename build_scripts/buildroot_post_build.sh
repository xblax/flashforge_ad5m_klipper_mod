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
    pushd $1 > /dev/null
    version="$(git describe --tags)-ADM5-$(date +%Y%m%d)"
    popd  > /dev/null
    echo $version
}

# paths
SCRIPT_DIR="$(dirname "$0")"
GIT_ROOT="$SCRIPT_DIR/.."
BUILDROOT="$GIT_ROOT/submodules/buildroot"
TARGET_ROOT="$1"

# move unwantend initscripts to init.o (optional)
mkdir -p $TARGET_ROOT/etc/init.o
mv $TARGET_ROOT/etc/init.d/S01syslogd $TARGET_ROOT/etc/init.o/ || true
mv $TARGET_ROOT/etc/init.d/S02klogd $TARGET_ROOT/etc/init.o/ || true
mv $TARGET_ROOT/etc/init.d/S02sysctl $TARGET_ROOT/etc/init.o/ || true
mv $TARGET_ROOT/etc/init.d/S30dbus $TARGET_ROOT/etc/init.o/ || true
mv $TARGET_ROOT/etc/init.d/S35iptables $TARGET_ROOT/etc/init.o/ || true
mv $TARGET_ROOT/etc/init.d/S40iwd $TARGET_ROOT/etc/init.o/ || true

# clean up root, if containing old build artefacts
rm -rf $TARGET_ROOT/root/setup
rm -rf $TARGET_ROOT/root/printer_data
rm -rf $TARGET_ROOT/root/printer_software

##############################
# install klipper
##############################

log_info "Install Klipper"
mkdir -p $TARGET_ROOT/root/printer_software/klipper/

# copy prebuild env or wheels
if [ -d $GIT_ROOT/prebuilt/klippy-env.tar.xz ]
then
  tar -xf $GIT_ROOT/prebuilt/klippy-env.tar.xz -C $TARGET_ROOT/root/printer_software/klipper/
else
  mkdir -p $TARGET_ROOT/root/setup/
  cp -r $GIT_ROOT/prebuilt/wheels/klipper_wheels $TARGET_ROOT/root/setup/
  cp -r $GIT_ROOT/submodules/klipper/scripts/klippy-requirements.txt $TARGET_ROOT/root/setup/klipper_wheels/requirements.txt
fi

# install klippy pyhton sources
pushd $GIT_ROOT/submodules/klipper/
cp -r klippy docs config README.md COPYING $TARGET_ROOT/root/printer_software/klipper/
create_version ./ > $TARGET_ROOT/root/printer_software/klipper/klippy/.version
popd

##############################
# install moonraker
##############################

log_info "Install Moonraker"
mkdir -p $TARGET_ROOT/root/printer_software/moonraker

# copy prebuilt env or wheels
if [ -d $GIT_ROOT/prebuilt/moonraker-env.tar.xz ]
then
  tar -xf $GIT_ROOT/prebuilt/moonraker-env.tar.xz -C $TARGET_ROOT/root/printer_software/moonraker/
else
  mkdir -p $TARGET_ROOT/root/setup/
  cp -r $GIT_ROOT/prebuilt/wheels/moonraker_wheels $TARGET_ROOT/root/setup/
  cat $GIT_ROOT/submodules/moonraker/scripts/moonraker-requirements.txt > $TARGET_ROOT/root/setup/moonraker_wheels/requirements.txt
  cat $GIT_ROOT/submodules/moonraker/scripts/moonraker-speedups.txt >> $TARGET_ROOT/root/setup/moonraker_wheels/requirements.txt
fi

# install moonraker python sources
pushd $GIT_ROOT/submodules/moonraker/
cp -r moonraker docs LICENSE README.md $TARGET_ROOT/root/printer_software/moonraker/
create_version ./ > $TARGET_ROOT/root/printer_software/moonraker/moonraker/.version
popd

##############################
# install mainsail
##############################

log_info "Install Mainsail"
if [ ! -f $GIT_ROOT/prebuilt/mainsail.zip ]
then
  wget -P $GIT_ROOT/prebuilt/ https://github.com/mainsail-crew/mainsail/releases/download/v2.9.1/mainsail.zip
fi
mkdir -p $TARGET_ROOT/root/printer_software/web/mainsail
unzip $GIT_ROOT/prebuilt/mainsail.zip -d $TARGET_ROOT/root/printer_software/web/mainsail
# set instances db to 'browser'
sed -i 's\moonraker\browser\g' $TARGET_ROOT/root/printer_software/web/mainsail/config.json

##############################
# install fluidd
##############################

log_info "Install Fluidd"
if [ ! -f $GIT_ROOT/prebuilt/fluidd.zip ]
then
  wget -P $GIT_ROOT/prebuilt/ https://github.com/fluidd-core/fluidd/releases/download/v1.28.0/fluidd.zip
fi
mkdir -p $TARGET_ROOT/root/printer_software/web/fluidd
unzip $GIT_ROOT/prebuilt/fluidd.zip -d $TARGET_ROOT/root/printer_software/web/fluidd

##############################
# install printer configs
##############################

log_info "Install printer configs"
mkdir -p $TARGET_ROOT/root/printer_data/config
mkdir -p $TARGET_ROOT/root/printer_data/logs
cp -r $GIT_ROOT/printer_configs/* $TARGET_ROOT/root/printer_data/config/
ln -s /mnt/data/gcodes $TARGET_ROOT/root/printer_data/gcodes
