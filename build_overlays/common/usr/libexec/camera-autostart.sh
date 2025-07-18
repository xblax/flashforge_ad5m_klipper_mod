#!/bin/sh
#
# Automatically start/stop ustreamer for camera livestream via http
#

CAMERA_DEVNAME=video0
CAMERA_SUBSYSTEM=video4linux
CAMERA_MIN_X_RES=1280
HTTP_PORT=8080

TAG="camera-autostart"
PID_FILE=/run/ustreamer.pid

start() {
    # check supported formats
    if ! v4l2-ctl -d /dev/$DEVNAME --list-formats | grep "MJPG"
    then
        logger -t $TAG "camera /dev/$DEVNAME does not support MJPG"
        exit 0
    fi

    # get resolutions, sort so that lowest resolution comes first in list
    # choose first resolution that is greater or equal CAMERA_MIN_X_RES, or the highest supported resolution else

    resolutions="$(v4l2-ctl -d /dev/$DEVNAME --list-framesizes MJPG | grep -i "discrete" |  cut -d" " -f3 | sort -n)"
    if [ $? -ne 0 ] || [ -z "$resolutions" ]
    then
        logger -t $TAG "failed to get resolutions for /dev/$DEVNAME"
        exit 0
    fi

    for res in $resolutions
    do
	resx="$(echo "$res" | cut -d'x' -f1)"
        resolution=$res
        if [ "$resx" -ge "$CAMERA_MIN_X_RES" ]
        then
	    break
        fi
    done

    start-stop-daemon -S -b -m -p $PID_FILE --exec ustreamer -- -d /dev/$DEVNAME -r $resolution -m MJPEG --device-timeout=2 -w 1 -I MMAP -c HW -s* -p 8080
    [ $? -eq 0 ] && logger -t $TAG "started ustreamer for /dev/$DEVNAME with res $resolution" || logger -t $TAG "failed to start ustreamer"
}

stop() {
    start-stop-daemon -K -q -p $PID_FILE
    [ $? -eq 0 ] && logger -t $TAG "stopped ustreamer for /dev/$DEVNAME" || logger -t $TAG "failed to stop ustreamer"
}

if [ "$CAMERA_DEVNAME" == "$DEVNAME" ]
then
    logger -t $TAG "received ACTION=$ACTION /dev/$DEVNAME"

    case "$ACTION" in
        add)
            start
            ;;
        remove)
            stop
            ;;
        *)
            logger -t $TAG "ACTION=$ACTION unsupported"
            exit 1
    esac
fi

exit $?
