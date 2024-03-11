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
SCRIPT_DIR=$( cd -- "$( dirname -- "$0" )" &> /dev/null && pwd )
GIT_ROOT="$SCRIPT_DIR/.."
BUILDROOT="$GIT_ROOT/submodules/buildroot"
TARGET_ROOT="$1"
PATH=$PATH:$BUILDROOT/output/host/bin:$BUILDROOT/output/host

# move unwantend initscripts to init.o (optional)
mkdir -p $TARGET_ROOT/etc/init.o
mv $TARGET_ROOT/etc/init.d/S35iptables $TARGET_ROOT/etc/init.o/ || true

# clean up root, if containing old build artefacts
rm -rf $TARGET_ROOT/root/setup
rm -rf $TARGET_ROOT/root/printer_data
rm -rf $TARGET_ROOT/root/printer_software

# save build time for fake-hwclock
date -u '+%Y-%m-%d %H:%M:%S' > $TARGET_ROOT/etc/fake-hwclock.data

# update os-release
pushd $GIT_ROOT
KLIPPER_MOD_VERSION=$(git describe --tags)
popd

cat << EOF > $TARGET_ROOT/etc/os-release
NAME=Buildroot-ADM5
VERSION=-$KLIPPER_MOD_VERSION
ID=buildroot
VERSION_ID=$KLIPPER_MOD_VERSION
PRETTY_NAME="Klipper Mod $KLIPPER_MOD_VERSION"
EOF

##############################
# install klipper
##############################

log_info "Install Klipper"
mkdir -p $TARGET_ROOT/root/printer_software/klipper/

# copy prebuild env or wheels
if [ -f $GIT_ROOT/prebuilt/klippy-env.tar.xz ]
then
  tar -xf $GIT_ROOT/prebuilt/klippy-env.tar.xz -C $TARGET_ROOT/root/printer_software/klipper/
else
  mkdir -p $TARGET_ROOT/root/setup/
  cp -r $GIT_ROOT/prebuilt/wheels/klipper_wheels $TARGET_ROOT/root/setup/
  cp -r $GIT_ROOT/submodules/klipper/scripts/klippy-requirements.txt $TARGET_ROOT/root/setup/klipper_wheels/requirements.txt
fi

# install klippy pyhton sources
pushd $GIT_ROOT/submodules/klipper/

pushd klippy/chelper
cp $SCRIPT_DIR/components/klipper/Makefile .
make
rm Makefile

popd
cp $SCRIPT_DIR/components/klipper/no-gcc-check.patch .
if patch -r - -b -N -p1 < no-gcc-check.patch;
then
    log_info "Skipping patch, already applied"
else
    log_info "Patch applied"
fi
cp -r klippy docs config README.md COPYING $TARGET_ROOT/root/printer_software/klipper/
rm no-gcc-check.patch

create_version ./ > $TARGET_ROOT/root/printer_software/klipper/klippy/.version
popd

# install g-code shell extension
cp $GIT_ROOT/build_scripts/components/klipper/gcode_shell_command.py $TARGET_ROOT/root/printer_software/klipper/klippy/extras/

##############################
# install moonraker
##############################

log_info "Install Moonraker"
mkdir -p $TARGET_ROOT/root/printer_software/moonraker

# copy prebuilt env or wheels
if [ -f $GIT_ROOT/prebuilt/moonraker-env.tar.xz ]
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
# set moonraker port
sed -i 's\"port": null\"port": 7125\g' $TARGET_ROOT/root/printer_software/web/mainsail/config.json

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

###############################
# Fix dbus user if not present
###############################
if ! grep dbus $TARGET_ROOT/etc/groups;
then
    echo "dbus:x:101:dbus" >> $TARGET_ROOT/etc/groups
fi
if ! grep dbus $TARGET_ROOT/etc/passwd;
then
    echo "dbus:x:100:101:DBus messagebus user:/run/dbus:/bin/false" >> $TARGET_ROOT/etc/passwd
fi
if ! grep dbus $TARGET_ROOT/etc/shadow;
then
    echo "dbus:*:::::::" >> $TARGET_ROOT/etc/shadow
fi


###############################
# Remove nfs server start components
###############################
rm -f $TARGET_ROOT/etc/init.d/S60nfs
