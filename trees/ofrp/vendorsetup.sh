#!/bin/bash
# vendorsetup.sh for OrangeFox 14.1 — Infinix GT 20 Pro (X6871)

if command -v add_lunch_combo >/dev/null 2>&1; then
    add_lunch_combo fox_X6871-eng 2>/dev/null || true
    add_lunch_combo fox_X6871-ap2a-eng 2>/dev/null || true
fi

export ALLOW_MISSING_DEPENDENCIES=true
export FOX_BUILD_DEVICE="X6871"
export FOX_VIRTUAL_AB_DEVICE=1
export FOX_VENDOR_BOOT_RECOVERY=1
export FOX_INSTALLER_VENDOR_BOOT_RAMDISK_INSTALL=0
export FOX_USE_ZSTD_BINARY=1
export FOX_USE_DMSETUP=1
export OF_DEFAULT_KEYMASTER_VERSION=5.0
export OF_USE_AIDL_BOOT_CONTROL=1
export OF_FLASHLIGHT_ENABLE=1
export OF_FL_PATH1="/flashlight"
export OF_ENABLE_VIBRATION=1
export OF_VIBRATION_DEFAULT_DURATION=100
export OF_USE_NEW_HAPTICS=1
export OF_SCREEN_H=2436
export OF_STATUS_H=90
export OF_STATUS_INDENT_LEFT=48
export OF_STATUS_INDENT_RIGHT=48
export FOX_DELETE_MAGISK_ADDON=1
export FOX_ENABLE_KERNELSU_SUPPORT=0
export FOX_ENABLE_KERNELSU_NEXT_SUPPORT=0
export FOX_ENABLE_SUKISU_SUPPORT=0
export OF_WIPE_METADATA_AFTER_DATAFORMAT=1
export OF_MAINTAINER="sheikhmehraann"

device_dir="$(cd "$(dirname """")" && pwd)"
workspace_root="$(cd ""/../../.."" && pwd)"
python3 ""/patch_pm.py"" """" 2>/dev/null || true
python3 ""/patch_theme.py"" """" 2>/dev/null || true
