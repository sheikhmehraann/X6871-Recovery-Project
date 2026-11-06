# SkyHawk Recovery Project (SHRP Legacy 12.1 / Forward-Port Stalled) — Infinix GT 20 Pro (`Infinix-X6871`)

## Manifest & Environment Requirements

* **Manifest:** SkyHawk Recovery Manifest
* **Branch:** `v3.1_12.1`
* **Target Architecture:** `arm64-v8a`
* **SoC:** MediaTek Dimensity 8200 Ultimate (`MT6895`)
* **Partition Target:** `vendor_boot` (Header v4, 64 MB)

```bash
mkdir -p ~/shrp && cd ~/shrp
repo init --depth=1 -u https://github.com/SKYHAWK-Recovery-Project/platform_manifest_twrp_omni.git -b v3.1_12.1
# Note: Upstream SHRP is abandoned at Android 12.1. Device tree provides the structural configuration for legacy or forward-ported builds.
repo sync -c -j$(nproc) --no-clone-bundle --no-tags
```

---

## Device Tree Placement

* Device Tree: `device/infinix/Infinix-X6871`
* Platform Common Tree: `device/transsion/mt6895-common`

```bash
mkdir -p device/infinix device/transsion
ln -s /path/to/Staging-Repo/device/infinix/Infinix-X6871 device/infinix/Infinix-X6871
ln -s /path/to/Staging-Repo/device/transsion/mt6895-common device/transsion/mt6895-common
```

---

## Makefiles Required by SHRP

* `device/infinix/Infinix-X6871/AndroidProducts.mk`
* `device/infinix/Infinix-X6871/BoardConfig.mk`
* `device/infinix/Infinix-X6871/shrp_X6871.mk`

---

## SkyHawk Environment Configuration

```bash
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
```

---

## Build Execution

```bash
source build/envsetup.sh
source device/infinix/Infinix-X6871/vendorsetup.sh
lunch shrp_X6871-eng
mka adbd vendorbootimage -j$(nproc)
```

Output: `out/target/product/Infinix-X6871/vendor_boot.img`
