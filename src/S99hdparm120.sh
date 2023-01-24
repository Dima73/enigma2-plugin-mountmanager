#!/bin/sh

[ ! -e /sbin/hdparm.hdparm ] && opkg install hdparm
[ -e /sbin/hdparm.hdparm ] && hdparm -S 120 /dev/sd?
exit 0
