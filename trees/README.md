# Android 16 Recovery Trees — Infinix GT 20 Pro (`Infinix-X6871`)

Independent, upstream-compliant recovery device trees for the Infinix GT 20 Pro (MediaTek Dimensity 8200 Ultimate / `MT6895`) running stock Transsion OS 16 (Android 16 / Linux 6.12 GKI).

---

## 1. Directory Structure

```text
trees/
├── common/             # Transsion MT6895 platform common tree (BoardConfigCommon, HALs, Trustonic)
├── twrp/               # Standalone TWRP 16.0 device tree (twrp_X6871.mk, omni_X6871.mk)
├── ofrp/               # Standalone OrangeFox 14.1 device tree (fox_X6871.mk, fox.mk)
├── pbrp/               # Standalone PitchBlack Recovery device tree (pb_X6871.mk)
├── shrp/               # Standalone SkyHawk Recovery device tree (shrp_X6871.mk)
└── yarp/               # Standalone Yet Another Recovery Project device tree (yarp_X6871.mk)
```

---

## 2. Upstream Conventions & Integration

Each standalone tree conforms directly to its upstream build system. To integrate into a specific recovery source checkout:

### TWRP 16.0 (`trees/twrp/`)
* **Manifest:** `https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git -b twrp-16.0`
* **Target Path:** `device/infinix/Infinix-X6871`
* **Platform Path:** `device/transsion/mt6895-common`
* **Symlink Setup:**
  ```bash
  mkdir -p device/infinix device/transsion
  ln -s /path/to/trees/twrp device/infinix/Infinix-X6871
  ln -s /path/to/trees/common device/transsion/mt6895-common
  ```
* **Lunch Combo:** `twrp_X6871-eng`
* **Build Command:** `mka adbd vendorbootimage -j$(nproc)`

---

### OrangeFox Recovery Project 14.1 (`trees/ofrp/`)
* **Manifest:** `https://gitlab.com/OrangeFox/sync.git` via `orangefox_sync.sh --branch 14.1`
* **Target Path:** `device/infinix/Infinix-X6871` or `device/infinix/X6871`
* **Platform Path:** `device/transsion/mt6895-common`
* **Symlink Setup:**
  ```bash
  mkdir -p device/infinix device/transsion
  ln -s /path/to/trees/ofrp device/infinix/Infinix-X6871
  ln -s /path/to/trees/common device/transsion/mt6895-common
  ```
* **Lunch Combo:** `fox_X6871-ap2a-eng`
* **Build Command:** `mka adbd vendorbootimage -j$(nproc)`
* **Post-Repack:** Execute `scripts/repack_vendor_boot_a16.py` to compress with Stock Fragment 0 and in-place patches.

---

### PitchBlack Recovery Project (`trees/pbrp/`)
* **Manifest:** `https://github.com/PitchBlackRecoveryProject/manifest_pb.git -b android-12.1`
* **Target Path:** `device/infinix/Infinix-X6871`
* **Platform Path:** `device/transsion/mt6895-common`
* **Symlink Setup:**
  ```bash
  mkdir -p device/infinix device/transsion
  ln -s /path/to/trees/pbrp device/infinix/Infinix-X6871
  ln -s /path/to/trees/common device/transsion/mt6895-common
  ```
* **Lunch Combo:** `pb_X6871-eng`
* **Build Command:** `mka adbd vendorbootimage -j$(nproc)`

---

### SkyHawk Recovery Project (`trees/shrp/`)
* **Manifest:** `https://github.com/SKYHAWK-Recovery-Project/platform_manifest_twrp_omni.git -b v3.1_12.1`
* **Target Path:** `device/infinix/Infinix-X6871`
* **Platform Path:** `device/transsion/mt6895-common`
* **Symlink Setup:**
  ```bash
  mkdir -p device/infinix device/transsion
  ln -s /path/to/trees/shrp device/infinix/Infinix-X6871
  ln -s /path/to/trees/common device/transsion/mt6895-common
  ```
* **Lunch Combo:** `shrp_X6871-eng`
* **Build Command:** `mka adbd vendorbootimage -j$(nproc)`

---

### Yet Another Recovery Project (`trees/yarp/`)
* **Manifest:** `https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git -b twrp-16.0`
* **Target Path:** `device/infinix/Infinix-X6871`
* **Platform Path:** `device/transsion/mt6895-common`
* **Symlink Setup:**
  ```bash
  mkdir -p device/infinix device/transsion
  ln -s /path/to/trees/yarp device/infinix/Infinix-X6871
  ln -s /path/to/trees/common device/transsion/mt6895-common
  ```
* **Lunch Combo:** `yarp_X6871-eng`
* **Build Command:** `mka adbd vendorbootimage -j$(nproc)`

---

## 3. Shared Platform Requirements (`trees/common/`)

All five recoveries rely on `trees/common/`:
* `BoardConfigCommon.mk`: Header v4 definitions, 64MB partition boundary, dynamic partitions (`super`), ZSTD compression flags.
* `common.mk`: Shared recovery packages and AIDL boot/health service inclusions.
* `system.prop`: Verified stock hardware properties and Trustonic crypto configuration.
* `recovery/root/`:
  * AIDL boot HAL prebuilt (`system/bin/hw/android.hardware.boot-service.mtk_recovery`) and `libmtk_bsg.so`.
  * Trustonic KeyMint v3.0, Gatekeeper, and `mcDriverDaemon` stack.
  * Verified mount tables (`recovery.fstab` and `twrp.flags`).
