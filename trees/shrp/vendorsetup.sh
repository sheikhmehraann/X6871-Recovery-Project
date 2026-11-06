#!/bin/bash
# vendorsetup.sh for SkyHawk Recovery Project — Infinix GT 20 Pro (X6871)

if command -v add_lunch_combo >/dev/null 2>&1; then
    add_lunch_combo shrp_X6871-eng 2>/dev/null || true
fi

export ALLOW_MISSING_DEPENDENCIES=true
export SHRP_PATH="device/infinix/Infinix-X6871"
export SHRP_MAINTAINER="sheikhmehraann"
export SHRP_DEVICE_CODE="X6871"
export SHRP_EDL_MODE=0
export SHRP_EXTERNAL="/sdcard"
export SHRP_INTERNAL="/data/media/0"
export SHRP_OTG="/usb_otg"
export SHRP_FLASH=1
export SHRP_FONTS="default"
export SHRP_OFFICIAL=true
export SHRP_DARK=true
export SHRP_EXPRESS=true
export SHRP_DEV="sheikhmehraann"
export SHRP_REC="/dev/block/by-name/vendor_boot"
export SHRP_REC_TYPE="vendor_boot"
export SHRP_CUSTOM_FLASHLIGHT=true
export SHRP_CUSTOM_FLASHLIGHT_PATH="/sys/class/torch/torch/torch_level"
