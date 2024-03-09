#!/bin/busybox ash
#
remove_action () {
#
# Unmount the device.  The user should really unmount it before
# disconnecting
   umount ${2}
#
# Delete the directory in ${mountdir}
   rm -rf ${2}
}
# At bootup, "mdev -s" is called.  It does not pass any environmental
# variables other than MDEV.  If no ACTION variable is passed, exit
# the script.
#
# Execute only if the device already exists; otherwise exit

#1>  /dev/fd1
#0<  /dev/fd0
#2>> /dev/shm/mdev_err.txt

mountdir="/media"
if [ ! -b ${MDEV} ] ; 
then 
    if [ ! -d "${mountdir}/${MDEV}"];
    then
        echo EXIT?
        exit 0 ; 
    fi
fi
#
# Make mountdir a var in case the pmount default directory ever changes
#
# Flag for whether or not we have a partition.  0=no, 1=yes, default no
partition=0
#
# File descriptors 0, 1, and 2 are closed before launching this script.
# Many linux utilities are hard-coded to work with these file descriptors.
# So we need to manually open them.
#
# Note that the redirect of stderr to a temporary logfile in /dev/shm in
# append mode is commented out.  Uncomment if you want to debug problems.
#
# Uncomment next line for debug data dump to /dev/shm/mdevlog.txt.
# env >> /dev/shm/mdevlog.txt

#
# Check for various conditions during an "add" operation
if [ "X${ACTION}" == "Xadd" ] ; then
#
# Flag for mounting if it's a regular partition
   if [ "X${DEVTYPE}" == "Xpartition" ] ; then
      partition=1 ;
#
# Further checks if DEVTYPE is disk; looking for weird setup where the
# entire USB key is formatted as one partition, without the standard
# partition table.
   elif [ "X${DEVTYPE}" == "Xdisk" ] ; then
#
# If it's "disk", check for string "FAT" in first 512 bytes of device.
# Flag as a partition if the string is found.
      if dd if=${MDEV} bs=512 count=1 2>/dev/null | grep "FAT" 1>/dev/null ; then
         partition=1
      fi
   fi
fi
#
# check for various conditions during a "remove" operation
if [ "X${ACTION}" == "Xremove" ] ; then
#
# Check for a disk or regular partition
   if [ "X${DEVTYPE}" == "Xpartition" ] || [ "X${DEVTYPE}" == "Xdisk" ] ; then
#
# Flag for unmounting if device exists in /proc/mounts mounted somewhere
# under the ${mountdir} directory (currently hardcoded as "/media").  It
# really should be unmounted manually by the user before removal, but
# people don't always remember.
      if grep "^/dev/${MDEV} ${mountdir}/" /proc/mounts 1>/dev/null ; then
         partition=1
      fi
   fi
#
# If the user has manually unmounted a device before disconnecting it, the
# directory is no longer listed in /proc/mounts.  This makes things more
# difficult.  The script has to walk through ${mountdir} and remove all
# directories that don't show up in /proc/mounts
   for dir in $( ls ${mountdir} )
   do
      if [ -d ${mountdir}/${dir} ]; then
         if ! grep " ${mountdir}/${dir} " /proc/mounts ; then
            rm -rf ${mountdir}/${dir}
         fi
      fi
   done
fi

#
# If not flagged as a partition, bail out.
if [ ${partition} -ne 1 ] ; then exit 0 ; fi
#
# The "add" action.
if [ "X${ACTION}" == "Xadd" ] ; then
#
# Create the directory in ${mountdir}
   mkdir -p ${mountdir}/${MDEV}
#
# Mount the directory in ${mountdir}
   mount -t vfat -o ro,codepage=437,iocharset=utf8,noatime /dev/${MDEV} ${mountdir}/${MDEV}
   rm -f /root/printer_data/gcodes/usb
   ln -s /media/${MDEV} /root/printer_data/gcodes/usb
#
# The "remove" action.
elif [ "X${ACTION}" == "Xremove" ] ; then
#
# Get info from /proc/mounts, and call remove_action to unmount the
# device and remove the associated directory
   rm -f /root/printer_data/gcodes/usb
   procmounts=$(grep "^/dev/${MDEV} ${mountdir}/" /proc/mounts)
   remove_action ${procmounts}
fi
