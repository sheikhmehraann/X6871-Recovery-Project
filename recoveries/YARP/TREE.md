# Yet Another Recovery Project (YARP 16.0) — Infinix GT 20 Pro (`Infinix-X6871`)

## Manifest & Environment Requirements

* **Manifest:** Minimal TWRP / YARP AOSP Manifest
* **Branch:** `yarp-16.0` / `twrp-16.0`
* **Target Architecture:** `arm64-v8a`
* **SoC:** MediaTek Dimensity 8200 Ultimate (`MT6895`)
* **Partition Target:** `vendor_boot` (Header v4, 64 MB)

```bash
mkdir -p ~/yarp && cd ~/yarp
repo init --depth=1 -u https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git -b twrp-16.0
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

## Makefiles Required by YARP

* `device/infinix/Infinix-X6871/AndroidProducts.mk`
* `device/infinix/Infinix-X6871/BoardConfig.mk`
* `device/infinix/Infinix-X6871/yarp_X6871.mk`

---

## YARP Environment Configuration

```bash
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
```

---

## Build Execution

```bash
source build/envsetup.sh
source device/infinix/Infinix-X6871/vendorsetup.sh
lunch yarp_X6871-eng
mka adbd vendorbootimage -j$(nproc)
```

Output: `out/target/product/Infinix-X6871/vendor_boot.img`
