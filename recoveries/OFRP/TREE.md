# OrangeFox Recovery Project (OFRP 14.1) — Infinix GT 20 Pro (`Infinix-X6871`)

## Manifest & Environment Requirements

* **Manifest:** OrangeFox Minimal Sync Manifest
* **Branch:** `14.1` (AOSP AP2A / SDK 34 Base)
* **Target Architecture:** `arm64-v8a`
* **SoC:** MediaTek Dimensity 8200 Ultimate (`MT6895`)
* **Partition Target:** `vendor_boot` (Header v4, 64 MB)

```bash
mkdir -p ~/fox_14.1 && cd ~/fox_14.1
git clone --depth=1 https://gitlab.com/OrangeFox/sync.git ~/OrangeFox_sync
~/OrangeFox_sync/orangefox_sync.sh --branch 14.1 --path ~/fox_14.1
```

---

## Device Tree Placement

OrangeFox accepts device placement at either:
* `device/infinix/Infinix-X6871` (with `device/transsion/mt6895-common`)
* `device/infinix/X6871`

```bash
mkdir -p device/infinix device/transsion
ln -s /path/to/Staging-Repo/device/infinix/Infinix-X6871 device/infinix/Infinix-X6871
ln -s /path/to/Staging-Repo/device/transsion/mt6895-common device/transsion/mt6895-common
```

---

## Makefiles Required by OrangeFox

* `device/infinix/Infinix-X6871/AndroidProducts.mk`
* `device/infinix/Infinix-X6871/BoardConfig.mk`
* `device/infinix/Infinix-X6871/fox_X6871.mk`
* `device/infinix/Infinix-X6871/fox.mk`

---

## OrangeFox Environment Configuration

```bash
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
export FOX_BUILD_TYPE="Stable"
export FOX_VARIANT="16.3.0"
export OF_MAINTAINER="sheikhmehraann"
export OF_ENABLE_FRP_ADDON=1
export FOX_SUPPORT_KSU=1
export OF_SCREEN_H=2436
export OF_STATUS_H=90
export OF_STATUS_INDENT_LEFT=48
export OF_STATUS_INDENT_RIGHT=48
export OF_DEFAULT_KEYMASTER_VERSION=5.0
export OF_USE_AIDL_BOOT_CONTROL=1
export OF_FLASHLIGHT_ENABLE=1
export OF_FL_PATH1="/flashlight"
export OF_ENABLE_VIBRATION=1
export OF_VIBRATION_DEFAULT_DURATION=100
export OF_USE_NEW_HAPTICS=1
export OF_WIPE_METADATA_AFTER_DATAFORMAT=1
```

---

## Build Execution & Post-Repacking

```bash
# 1. Apply tree patches and lunch target
source build/envsetup.sh
source device/infinix/Infinix-X6871/vendorsetup.sh
lunch fox_X6871-ap2a-eng

# 2. Build vendor_boot
mka adbd vendorbootimage -j$(nproc)

# 3. Repack with Stock Fragment 0 and in-place patches
python3 scripts/repack_vendor_boot_a16.py \
    reference/stock_vendor_boot.img.gz \
    out/target/product/Infinix-X6871/vendor_boot.img \
    out/target/product/Infinix-X6871/vendor_boot_repacked.img
```
