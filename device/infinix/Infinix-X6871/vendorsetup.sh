#!/bin/bash
#
# vendorsetup.sh for Infinix GT 20 Pro (X6871 / MT6895)
# Multi-Recovery: TWRP, OrangeFox, PitchBlack, SkyHawk, and YARP
#

device_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${device_dir}/../../.." && pwd)"

# Register legacy lunch combo fallbacks if supported by build system
if command -v add_lunch_combo >/dev/null 2>&1; then
    add_lunch_combo twrp_X6871-eng 2>/dev/null || true
    add_lunch_combo fox_X6871-eng 2>/dev/null || true
    add_lunch_combo fox_X6871-ap2a-eng 2>/dev/null || true
    add_lunch_combo pb_X6871-eng 2>/dev/null || true
    add_lunch_combo shrp_X6871-eng 2>/dev/null || true
    add_lunch_combo yarp_X6871-eng 2>/dev/null || true
    add_lunch_combo omni_X6871-eng 2>/dev/null || true
fi

# Base build exports
export ALLOW_MISSING_DEPENDENCIES=true
export LC_ALL="C"
export USE_CCACHE=1
export TW_DEVICE_VERSION="X6871_A16"

# 1. OrangeFox Recovery Project Configuration
if [ -n "$FOX_BUILD_DEVICE" ] || [[ "${TARGET_PRODUCT:-}" =~ ^(fox|orangefox)_X6871 ]]; then
    export FOX_BUILD_DEVICE="X6871"
    export FOX_VIRTUAL_AB_DEVICE=1
    export FOX_VENDOR_BOOT_RECOVERY=1
    export FOX_INSTALLER_VENDOR_BOOT_RAMDISK_INSTALL=0
    unset FOX_VENDOR_BOOT_POSTPROCESS_SCRIPT FOX_REFERENCE_VENDOR_BOOT_IMAGE
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
fi

# 2. PitchBlack Recovery Project Configuration
if [[ "${TARGET_PRODUCT:-}" =~ ^pb_X6871 ]]; then
    export PB_DEVICE_SPECIFICATION="Infinix GT 20 Pro (X6871)"
    export PB_TORCH_PATH="/sys/class/torch/torch/torch_level"
    export PB_BATTERY_PATH="/sys/class/power_supply/battery"
    export PB_VIBRATOR_PATH="/sys/class/leds/vibrator_single/activate"
    export PB_BUILD_TYPE="OFFICIAL"
    export PBRP_MAINTAINER="sheikhmehraann"
    export PBRP_BRANCH="16.0"
    export PBRP_STATUS="STABLE"
fi

# 3. SkyHawk Recovery Project Configuration
if [[ "${TARGET_PRODUCT:-}" =~ ^shrp_X6871 ]]; then
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
fi

# 4. Yet Another Recovery Project Configuration
if [[ "${TARGET_PRODUCT:-}" =~ ^yarp_X6871 ]]; then
    export YARP_DEVICE_CODE="X6871"
    export YARP_MAINTAINER="sheikhmehraann"
    export YARP_BUILD_TYPE="OFFICIAL"
    export YARP_VERSION="16.0"
    export YARP_THEME="dark"
    export YARP_FLASHLIGHT_PATH="/sys/class/torch/torch/torch_level"
    export YARP_BATTERY_PATH="/sys/class/power_supply/battery"
    export YARP_VIBRATOR_PATH="/sys/class/leds/vibrator_single/activate"
    export YARP_CPU_TEMP_PATH="/sys/class/thermal/thermal_zone0/temp"
    export YARP_USE_ZSTD=true
    export YARP_ENFORCE_PERMISSIVE=true
fi

# Apply device patches cleanly
patch_files=(
    "${device_dir}/patches/01-patch-vibration.patch"
    "${device_dir}/patches/02-patch-health-hal.patch"
    "${device_dir}/patches/04-patch-native-vendor-ramdisk.patch"
    "${device_dir}/patches/06-patch-fbe-auth-token.patch"
    "${device_dir}/patches/07-patch-sideload-install-once.patch"
)

patches_ok=true
for patch_file in "${patch_files[@]}"; do
    if [[ ! -f "${patch_file}" ]] || ! command -v patch >/dev/null 2>&1; then
        continue
    fi
    if (cd "${workspace_root}" && patch -p1 -N --dry-run --silent < "${patch_file}" >/dev/null 2>&1); then
        (cd "${workspace_root}" && patch -p1 -N --silent < "${patch_file}") || patches_ok=false
    fi
done

# Run auxiliary layout patchers if present
python3 "${device_dir}/patch_pm.py" "${workspace_root}" 2>/dev/null || true
python3 "${device_dir}/patch_theme.py" "${workspace_root}" 2>/dev/null || true

return 0 2>/dev/null || true
