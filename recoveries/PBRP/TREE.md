# PitchBlack Recovery Project (PBRP 14.0 / Forward-Port A16) — Infinix GT 20 Pro (`Infinix-X6871`)

## Manifest & Environment Requirements

* **Manifest:** PitchBlack Recovery Manifest
* **Branch:** `android-14.0` (Latest Official Upstream) / Community A16
* **Target Architecture:** `arm64-v8a`
* **SoC:** MediaTek Dimensity 8200 Ultimate (`MT6895`)
* **Partition Target:** `vendor_boot` (Header v4, 64 MB)

```bash
mkdir -p ~/pbrp && cd ~/pbrp
repo init --depth=1 -u https://github.com/PitchBlackRecoveryProject/manifest_pb.git -b android-14.0
# Note: Official upstream PBRP stops at android-14.0. Android 16 builds use community forward-port patches atop TWRP 16.0 manifest.
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

## Makefiles Required by PBRP

* `device/infinix/Infinix-X6871/AndroidProducts.mk`
* `device/infinix/Infinix-X6871/BoardConfig.mk`
* `device/infinix/Infinix-X6871/pb_X6871.mk`

---

## PitchBlack Environment Configuration

```bash
export PB_DEVICE_SPECIFICATION="Infinix GT 20 Pro (X6871)"
export PB_TORCH_PATH="/sys/class/torch/torch/torch_level"
export PB_BATTERY_PATH="/sys/class/power_supply/battery"
export PB_VIBRATOR_PATH="/sys/class/leds/vibrator_single/activate"
export PB_BUILD_TYPE="OFFICIAL"
export PBRP_MAINTAINER="sheikhmehraann"
export PBRP_BRANCH="16.0"
export PBRP_STATUS="STABLE"
```

---

## Build Execution

```bash
source build/envsetup.sh
source device/infinix/Infinix-X6871/vendorsetup.sh
lunch pb_X6871-eng
mka adbd vendorbootimage -j$(nproc)
```

Output: `out/target/product/Infinix-X6871/vendor_boot.img`
