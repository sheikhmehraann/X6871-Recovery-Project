#!/usr/bin/env bash
#
# Local build script for OrangeFox Recovery R12.1 - Infinix GT 20 Pro (X6871)
# Maintained by withmehraan
#

set -euo pipefail

# Project root path
FOX_ROOT="${FOX_ROOT:-$HOME/fox_14.1}"

if [ ! -d "${FOX_ROOT}" ]; then
    echo "[-] Error: Fox source tree not found at ${FOX_ROOT}"
    echo "[-] Please set FOX_ROOT or sync the tree first."
    exit 1
fi

cd "${FOX_ROOT}"

# Build flags
export ALLOW_MISSING_DEPENDENCIES=true
export WITH_TIDY=0
export WITHOUT_CHECK_API=true
export ALLOW_LOCAL_TIDY_TRUE=false
export FOX_BUILD_DEVICE="X6871"
export FOX_VIRTUAL_AB_DEVICE=1
export FOX_VANILLA_BUILD=1
export FOX_ENABLE_APP_MANAGER=1
export FOX_RECOVERY_SYSTEM_PARTITION="/dev/block/mapper/system"
export FOX_RECOVERY_VENDOR_PARTITION="/dev/block/mapper/vendor"
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
export OF_MAINTAINER="withmehraan"
export LC_ALL="C"
export USE_CCACHE=1

# Output directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "${SCRIPT_DIR}")"
OUTPUT_DIR="${OUTPUT_DIR:-${REPO_ROOT}/output}"
mkdir -p "${OUTPUT_DIR}"

echo "[*] Setting up build environment..."
source build/envsetup.sh
lunch twrp_X6871-eng

echo "[*] Compiling vendorbootimage..."
START_TIME=$(date +%s)
mka adbd vendorbootimage -j$(nproc)
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

PRODUCT_DIR="out/target/product/X6871"
if [ ! -d "${PRODUCT_DIR}" ]; then
    PRODUCT_DIR="out/target/product/Infinix-X6871"
fi

if [ -f "${PRODUCT_DIR}/vendor_boot.img" ]; then
    echo "[+] Compilation successful in ${ELAPSED} seconds!"
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    RELEASE_NAME="OrangeFox-R12.1_${TIMESTAMP}_15.1.2-Stable-X6871"
    
    cp -v "${PRODUCT_DIR}/vendor_boot.img" "${OUTPUT_DIR}/${RELEASE_NAME}.img"
    cp -v "${PRODUCT_DIR}/vendor_boot.img" "${OUTPUT_DIR}/vendor_boot.img"
    
    find "${PRODUCT_DIR}" -maxdepth 2 -name "OrangeFox*.zip" -exec cp -v {} "${OUTPUT_DIR}/" \; 2>/dev/null || true
    
    cd "${OUTPUT_DIR}"
    sha256sum "${RELEASE_NAME}.img" > "${RELEASE_NAME}.img.sha256"
    md5sum "${RELEASE_NAME}.img" > "${RELEASE_NAME}.img.md5"
    
    echo "=========================================================="
    echo "[+] Build artifacts deployed to ${OUTPUT_DIR}:"
    ls -lh "${OUTPUT_DIR}/${RELEASE_NAME}.img"
    echo "=========================================================="
else
    echo "[-] Error: vendor_boot.img was not generated in ${PRODUCT_DIR}"
    exit 1
fi
