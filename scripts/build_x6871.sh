#!/usr/bin/env bash

cd /root/X6871-Recovery-Project/fox_12.1

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
unset FOX_VERSION
export FOX_BUILD_TYPE="Stable"
export FOX_VARIANT="15.1.2"
export OF_MAINTAINER="withmehraan"
export LC_ALL="C"
export GOGC=50
export GOMAXPROCS=4
export USE_CCACHE=1
export CCACHE_EXEC=/usr/bin/ccache
export CCACHE_DIR=/var/cache/ccache

echo "[*] Sourcing build/envsetup.sh and lunching..."
set +e
set +u
source build/envsetup.sh
lunch twrp_X6871-eng
LUNCH_RC=$?
if [ ${LUNCH_RC} -ne 0 ]; then
    echo "[!] Lunch failed with code ${LUNCH_RC}"
    exit 1
fi
set -e

echo "[*] Starting mka adbd vendorbootimage -j4..."
START_TIME=$(date +%s)
mka adbd vendorbootimage -j4 2>&1 | tee /tmp/build.log
BUILD_STATUS=${PIPESTATUS[0]}
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo "[*] Compilation completed in ${ELAPSED} seconds with status ${BUILD_STATUS}."

OUTPUT_DIR="/mnt/c/Users/Admin/Videos/Github/X6871-Recovery-Project/Output"
mkdir -p "${OUTPUT_DIR}"

PRODUCT_DIR="out/target/product/Infinix-X6871"

if [ -f "${PRODUCT_DIR}/vendor_boot.img" ]; then
    echo "[✓] vendor_boot.img successfully created!"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    cp -v "${PRODUCT_DIR}/vendor_boot.img" "${OUTPUT_DIR}/OrangeFox-R12.0-X6871-NewBuild-${TIMESTAMP}.img"
    cp -v "${PRODUCT_DIR}/vendor_boot.img" "${OUTPUT_DIR}/vendor_boot.img"
    
    find "${PRODUCT_DIR}" -maxdepth 2 -name "OrangeFox*.zip" -exec cp -v {} "${OUTPUT_DIR}/" \; 2>/dev/null || true
    
    cd "${OUTPUT_DIR}"
    md5sum "OrangeFox-R12.0-X6871-NewBuild-${TIMESTAMP}.img" > "OrangeFox-R12.0-X6871-NewBuild-${TIMESTAMP}.img.md5"
    sha256sum "OrangeFox-R12.0-X6871-NewBuild-${TIMESTAMP}.img" > "OrangeFox-R12.0-X6871-NewBuild-${TIMESTAMP}.img.sha256"
    
    echo "=========================================================="
    echo "[✓] SUCCESS: Build artifacts deployed to ${OUTPUT_DIR}"
    ls -la "${OUTPUT_DIR}/OrangeFox-R12.0-X6871-NewBuild-${TIMESTAMP}.img"
    echo "=========================================================="
    
    echo "[*] Triggering host shutdown in 120 seconds..."
    /mnt/c/Windows/System32/shutdown.exe /s /t 120 /c "OrangeFox Recovery build complete! Shutting down in 2 minutes. Run shutdown /a to abort." || true
else
    echo "=========================================================="
    echo "[✗] ERROR: vendor_boot.img was NOT found in ${PRODUCT_DIR}"
    echo "=========================================================="
    tail -n 100 /tmp/build.log
    exit 1
fi
