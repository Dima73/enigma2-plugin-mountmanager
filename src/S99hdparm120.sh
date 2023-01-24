#!/bin/sh
# /etc/rcS.d/S99hdparm120.sh
[ ! -e /sbin/hdparm.hdparm ] && opkg install hdparm
[ -e /sbin/hdparm.hdparm ] && hdparm -S 120 /dev/sd?
exit 0
