#!/bin/bash
#
# This file is part of the OrangeFox Recovery Project
# Copyright (C) 2020-2025 The OrangeFox Recovery Project

device_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${device_dir}/../../.." && pwd)"
patch_files=(
    "${device_dir}/patches/01-patch-vibration.patch"
    "${device_dir}/patches/02-patch-health-hal.patch"
    "${device_dir}/patches/04-patch-native-vendor-ramdisk.patch"
    "${device_dir}/patches/06-patch-fbe-auth-token.patch"
    "${device_dir}/patches/07-patch-sideload-install-once.patch"
)

export ALLOW_MISSING_DEPENDENCIES=true
export FOX_BUILD_DEVICE=X6871
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

legacy_patch="${device_dir}/patches/03-patch-vendor-boot-postprocess.patch"
if (cd "${workspace_root}" && patch -p1 -R --dry-run --silent < "${legacy_patch}" >/dev/null 2>&1); then
    (cd "${workspace_root}" && patch -p1 -R --silent < "${legacy_patch}") || return 1
fi
unset legacy_patch

patches_ok=true
for patch_file in "${patch_files[@]}"; do
    if [[ ! -f "${patch_file}" ]] || ! command -v patch >/dev/null 2>&1; then
        echo "[Infinix-X6871] Missing patch or patch command: ${patch_file}"
        patches_ok=false
        break
    fi
    if (cd "${workspace_root}" && patch -p1 -N --dry-run --silent < "${patch_file}" >/dev/null 2>&1); then
        if ! (cd "${workspace_root}" && patch -p1 -N --silent < "${patch_file}"); then
            patches_ok=false
            break
        fi
        echo "[Infinix-X6871] Applied $(basename "${patch_file}")."
    elif (cd "${workspace_root}" && patch -p1 -R --dry-run --silent < "${patch_file}" >/dev/null 2>&1); then
        echo "[Infinix-X6871] Already applied $(basename "${patch_file}")."
    else
        echo "[Infinix-X6871] Patch does not apply: ${patch_file}"
        patches_ok=false
        break
    fi
done

# Ensure Unmap_Super_Devices does not abort Format Data on unmap errors
python3 "${device_dir}/patch_pm.py" "${workspace_root}" 2>/dev/null || true

if [[ "${patches_ok}" != true ]]; then
    unset device_dir workspace_root patch_files patch_file patches_ok
    return 1
fi
unset device_dir workspace_root patch_files patch_file patches_ok
