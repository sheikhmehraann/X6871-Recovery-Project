#!/bin/bash
#
# vendorsetup.sh for Infinix GT 20 Pro (X6871)
# Supports TWRP, OrangeFox, PitchBlack, and SkyHawk recoveries
#

# Lunch combos are defined in AndroidProducts.mk (COMMON_LUNCH_CHOICES)
# Legacy lunch fallback:
if command -v add_lunch_combo >/dev/null 2>&1; then
	add_lunch_combo twrp_X6871-eng 2>/dev/null || true
	add_lunch_combo omni_X6871-eng 2>/dev/null || true
	add_lunch_combo fox_X6871-eng 2>/dev/null || true
	add_lunch_combo pb_X6871-eng 2>/dev/null || true
	add_lunch_combo shrp_X6871-eng 2>/dev/null || true
fi

FDEVICE="X6871"

# Common base configuration
export ALLOW_MISSING_DEPENDENCIES=true
export TW_DEVICE_VERSION="X6871_sheikhmehraann"
export LC_ALL="C"

# OrangeFox environment configuration
if [ -n "$FOX_BUILD_DEVICE" ] || [ "${TARGET_PRODUCT:-}" = "fox_X6871" ]; then
	export FOX_BUILD_DEVICE="$FDEVICE"
	export FOX_VIRTUAL_AB_DEVICE=1
	export OF_ALLOW_DISABLE_NAVBAR=1
	export OF_CHECK_OVERWRITE_ATTEMPTS=1
	export OF_ENABLE_LPTOOLS=1
	export OF_ENABLE_ALL_PARTITION_TOOLS=1
	export OF_SUPPORT_ALL_BLOCK_SU_MOUNTS=1
	export OF_SUPPORT_ALL_PAYLOAD_EXTRACTOR=1
	export OF_ALLOW_DISABLE_FORCE_ENCRYPTION=1
	export OF_SETTINGS_CUSTOM_PATH="/sdcard/Fox"
	export OF_DYNAMIC_FULL_SIZE=9126805504
	export FOX_ENABLE_APP_MANAGER=1
	export FOX_RECOVERY_SYSTEM_PARTITION="/dev/block/mapper/system"
	export FOX_RECOVERY_VENDOR_PARTITION="/dev/block/mapper/vendor"
	export FOX_RECOVERY_INSTALL_PARTITION="/dev/block/by-name/vendor_boot"
	export FOX_RECOVERY_BOOT_PARTITION="/dev/block/by-name/boot"
	export FOX_USE_BASH_SHELL=1
	export FOX_ASH_IS_BASH=1
	export FOX_USE_TAR_BINARY=1
	export FOX_USE_LZ4_BINARY=1
	export FOX_USE_SED_BINARY=1
	export FOX_USE_XZ_UTILS=1
	export FOX_USE_ZSTD_BINARY=1
	export FOX_USE_NANO_EDITOR=1
	export FOX_DELETE_AROMAFM=1
	export FOX_BUILD_TYPE="Stable"
	export FOX_VARIANT="15.1.2"
	export OF_MAINTAINER="sheikhmehraann"
	export OF_ENABLE_FRP_ADDON=1
	export FOX_SUPPORT_KSU=1
	export OF_SCREEN_H=2436
fi

# PitchBlack environment configuration
if [ "${TARGET_PRODUCT:-}" = "pb_X6871" ]; then
	export PB_DEVICE_SPECIFICATION="Infinix GT 20 Pro (X6871)"
	export PB_TORCH_PATH="/sys/devices/platform/11cb0000.i2c/i2c-7/7-0050/leds/torch/brightness"
	export PB_BATTERY_PATH="/sys/class/power_supply/battery"
	export PB_VIBRATOR_PATH="/sys/class/leds/vibrator_single/activate"
	export PB_BUILD_TYPE="OFFICIAL"
	export PBRP_MAINTAINER="sheikhmehraann"
	export PBRP_BRANCH="12.1"
	export PBRP_STATUS="STABLE"
fi

# SkyHawk environment configuration
if [ "${TARGET_PRODUCT:-}" = "shrp_X6871" ]; then
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
	export SHRP_CUSTOM_FLASHLIGHT_PATH="/sys/devices/platform/11cb0000.i2c/i2c-7/7-0050/leds/torch/brightness"
fi

# Haptics activation patch
if [ -d bootable/recovery ]; then
	patch_file="device/infinix/Infinix-X6871/patches/0001-Change-haptics-activation-file-path.patch"
	if [ -f "$patch_file" ]; then
		git -C bootable/recovery apply "$PWD/$patch_file" >/dev/null 2>&1 || true
	fi
fi

return 0 2>/dev/null || true
