#!/usr/bin/env bash
#
# Build script for Infinix GT 20 Pro (X6871)
# Supported targets: ofox (default), twrp, pbrp, shrp
# Maintainer: sheikhmehraann
#

set -euo pipefail

TARGET_RECOVERY="${1:-ofox}"
FOX_ROOT="${FOX_ROOT:-$HOME/fox_14.1}"

if [ ! -d "${FOX_ROOT}" ]; then
    echo "[-] Error: source tree not found at ${FOX_ROOT}"
    echo "[-] Set FOX_ROOT or sync the source tree first."
    exit 1
fi

cd "${FOX_ROOT}"

# Common build exports
export ALLOW_MISSING_DEPENDENCIES=true
export WITH_TIDY=0
export WITHOUT_CHECK_API=true
export ALLOW_LOCAL_TIDY_TRUE=false
export LC_ALL="C"
export USE_CCACHE=1

case "${TARGET_RECOVERY}" in
    ofox|orangefox)
        echo "[*] Configuring for OrangeFox Recovery R12.1..."
        export FOX_BUILD_DEVICE="X6871"
        export FOX_VIRTUAL_AB_DEVICE=1
        export FOX_VANILLA_BUILD=1
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
        export FOX_MAINTAINER_PATCH_VERSION=$(date +"%Y%m%d")
        unset FOX_VERSION || true
        export FOX_BUILD_TYPE="Stable"
        export FOX_VARIANT="15.1.2"
        export OF_MAINTAINER="sheikhmehraann"
        export OF_ENABLE_FRP_ADDON=1
        export FOX_SUPPORT_KSU=1
        export OF_SCREEN_H=2436
        LUNCH_TARGET="twrp_X6871-eng"
        PREFIX="OrangeFox-R12.1"
        ;;
    twrp)
        echo "[*] Configuring for TWRP..."
        LUNCH_TARGET="twrp_X6871-eng"
        PREFIX="TWRP"
        ;;
    pbrp|pitchblack)
        echo "[*] Configuring for PitchBlack Recovery..."
        export PB_DEVICE_SPECIFICATION="Infinix GT 20 Pro (X6871)"
        export PB_TORCH_PATH="/sys/devices/platform/11cb0000.i2c/i2c-7/7-0050/leds/torch/brightness"
        export PB_BATTERY_PATH="/sys/class/power_supply/battery"
        export PB_VIBRATOR_PATH="/sys/class/leds/vibrator_single/activate"
        export PB_BUILD_TYPE="OFFICIAL"
        export PBRP_MAINTAINER="sheikhmehraann"
        export PBRP_BRANCH="12.1"
        export PBRP_STATUS="STABLE"
        LUNCH_TARGET="pb_X6871-eng"
        PREFIX="PBRP"
        ;;
    shrp|skyhawk)
        echo "[*] Configuring for SkyHawk Recovery..."
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
        LUNCH_TARGET="shrp_X6871-eng"
        PREFIX="SHRP"
        ;;
    *)
        echo "[-] Unknown recovery target: ${TARGET_RECOVERY}"
        echo "[-] Supported: ofox, twrp, pbrp, shrp"
        exit 1
        ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "${SCRIPT_DIR}")"
OUTPUT_DIR="${OUTPUT_DIR:-${REPO_ROOT}/output}"
mkdir -p "${OUTPUT_DIR}"

echo "[*] Setting up build environment..."
source build/envsetup.sh
lunch "${LUNCH_TARGET}" || lunch twrp_X6871-eng

echo "[*] Compiling vendorbootimage..."
START_TIME=$(date +%s)
mka adbd vendorbootimage -j"$(nproc)"
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

PRODUCT_DIR="out/target/product/X6871"
if [ ! -d "${PRODUCT_DIR}" ]; then
    PRODUCT_DIR="out/target/product/Infinix-X6871"
fi

if [ -f "${PRODUCT_DIR}/vendor_boot.img" ]; then
    echo "[+] Build completed in ${ELAPSED} seconds."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    RELEASE_NAME="${PREFIX}_${TIMESTAMP}_X6871"
    
    cp -v "${PRODUCT_DIR}/vendor_boot.img" "${OUTPUT_DIR}/${RELEASE_NAME}.img"
    cp -v "${PRODUCT_DIR}/vendor_boot.img" "${OUTPUT_DIR}/vendor_boot.img"
    
    find "${PRODUCT_DIR}" -maxdepth 2 -name "*.zip" -exec cp -v {} "${OUTPUT_DIR}/" \; 2>/dev/null || true
    
    cd "${OUTPUT_DIR}"
    sha256sum "${RELEASE_NAME}.img" > "${RELEASE_NAME}.img.sha256"
    md5sum "${RELEASE_NAME}.img" > "${RELEASE_NAME}.img.md5"
    
    echo "=========================================================="
    echo "[+] Output saved to ${OUTPUT_DIR}:"
    ls -lh "${OUTPUT_DIR}/${RELEASE_NAME}.img"
    echo "=========================================================="
else
    echo "[-] Error: vendor_boot.img not found in ${PRODUCT_DIR}"
    exit 1
fi
