# TeamWin Recovery Project (TWRP 16.0) — Infinix GT 20 Pro (`Infinix-X6871`)

## Manifest & Environment Requirements

* **Manifest:** Minimal TWRP AOSP Manifest
* **Branch:** `twrp-16.0` (Android 16)
* **Target Architecture:** `arm64-v8a`
* **SoC:** MediaTek Dimensity 8200 Ultimate (`MT6895`)
* **Partition Target:** `vendor_boot` (Header v4, 64 MB)

```bash
mkdir -p ~/twrp_16 && cd ~/twrp_16
repo init --depth=1 -u https://github.com/TWRP-Test/platform_manifest_twrp_aosp.git -b twrp-16.0
# Note: Official TeamWin minimal-manifest-twrp has branches up to twrp-14.1. Android 16 is tracked via community TWRP-Test.
repo sync -c -j$(nproc) --no-clone-bundle --no-tags
```

---

## Device Tree Placement

TWRP requires the device and common platform trees positioned at:
* Device Tree: `device/infinix/Infinix-X6871`
* Platform Common Tree: `device/transsion/mt6895-common`

```bash
mkdir -p device/infinix device/transsion
ln -s /path/to/Staging-Repo/device/infinix/Infinix-X6871 device/infinix/Infinix-X6871
ln -s /path/to/Staging-Repo/device/transsion/mt6895-common device/transsion/mt6895-common
```

---

## Makefiles Required by TWRP

* `device/infinix/Infinix-X6871/AndroidProducts.mk`
* `device/infinix/Infinix-X6871/BoardConfig.mk`
* `device/infinix/Infinix-X6871/twrp_X6871.mk`
* `device/transsion/mt6895-common/BoardConfigCommon.mk`

---

## TWRP Build Flags

```make
# Architecture & Display
TARGET_ARCH := arm64
TARGET_CPU_ABI := arm64-v8a
DEVICE_RESOLUTION := 1080x2436
TARGET_SCREEN_WIDTH := 1080
TARGET_SCREEN_HEIGHT := 2436
TW_THEME := portrait_hdpi
TW_FRAMERATE := 144
TW_DEFAULT_BRIGHTNESS := 2047
TW_MAX_BRIGHTNESS := 5119

# Crypto & Storage
TW_INCLUDE_CRYPTO := true
TW_INCLUDE_CRYPTO_FBE := true
TW_FORCE_KEYMASTER_VER := true
TW_USE_FSCRYPT_POLICY := 2
BOARD_USES_METADATA_PARTITION := true
RECOVERY_CACHE_MOUNT_POINT := /metadata/recovery

# Boot Header v4
BOARD_BOOT_HEADER_VERSION := 4
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 67108864
BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT := true
BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := true
TARGET_NO_RECOVERY := true

# Drivers & Peripherals
TW_CUSTOM_CPU_TEMP_PATH := /sys/class/thermal/thermal_zone0/temp
TW_CUSTOM_BATTERY_PATH := /sys/class/power_supply/battery
TW_USE_LEDS_HAPTICS := true
TW_INCLUDE_FASTBOOTD := true
TW_INCLUDE_RESETPROP := true
TW_INCLUDE_LPTOOLS := true
```

---

## Build Execution

```bash
source build/envsetup.sh
source device/infinix/Infinix-X6871/vendorsetup.sh
lunch twrp_X6871-eng
mka adbd vendorbootimage -j$(nproc)
```

Output: `out/target/product/Infinix-X6871/vendor_boot.img`
