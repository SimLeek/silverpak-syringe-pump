#!/bin/bash

if [ "$(whoami)" != "root" ]; then
	echo "This script must be run as root."
	exit 1
fi

modprobe ftdi-sio
echo 0403 e0b0 > /sys/bus/usb-serial/drivers/ftdi_sio/new_id

