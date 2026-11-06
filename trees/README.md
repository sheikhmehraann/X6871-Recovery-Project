# Android 16 Recovery Trees — Infinix GT 20 Pro (Infinix-X6871)

Independent recovery device trees for the Infinix GT 20 Pro (MediaTek Dimensity 8200 Ultimate / MT6895) running stock Transsion OS 16 (Android 16 / Linux 6.12 GKI).

---

## 1. Upstream Support & Manifest Matrix

| Recovery Project | Upstream Authority | Highest Official Branch | Android 16 Status | Real Manifest URL |
|---|---|---|---|---|
| TWRP | TeamWin / TWRP-Test | twrp-14.1 (Official) / twrp-16.0 (Community Test) | Supported via TWRP-Test | `https://github.com/TWRP-Test/platform_manifest_twrp_aosp.git -b twrp-16.0` |
| OrangeFox (OFRP) | OrangeFox Recovery | fox_16.0 | Supported Official | `https://gitlab.com/orangefox/manifest.git -b fox_16.0` |
| PBRP | PitchBlack Recovery | android-14.0 | Unsupported Upstream (Downstream Forward-Port) | `https://github.com/PitchBlackRecoveryProject/manifest_pb.git -b android-14.0` |
| SHRP | SkyHawk Recovery | shrp-12.1 | Unsupported Upstream (Stalled at Android 12) | `https://github.com/SKYHAWK-Recovery-Project/platform_manifest_twrp_omni.git` |
| YARP | YuKongA Recovery Project | yarp-16.0 (TWRP-16 Base) | Supported via YuKongA Base | `https://github.com/TWRP-Test/platform_manifest_twrp_aosp.git -b twrp-16.0` |

---

## 2. Directory Layout

```text
trees/
├── common/             # MT6895 platform common tree (HALs, bootctrl, vendor_ramdisk bootstrap)
├── twrp/               # TWRP 16.0 device tree (twrp_X6871.mk, omni_X6871.mk, prebuilt DTB)
├── ofrp/               # OrangeFox 14.1/16.0 device tree (fox_X6871.mk, fox.mk, post-make scripts)
├── pbrp/               # PitchBlack Recovery forward-port tree (pb_X6871.mk)
├── shrp/               # SkyHawk Recovery forward-port tree (shrp_X6871.mk)
└── yarp/               # YuKongA Recovery Project tree (yarp_X6871.mk, LVGL UI configs)
```

---

## 3. Upstream Conventions & Build Targets

### TWRP 16.0 (`trees/twrp/`)
* Upstream Manifest: `https://github.com/TWRP-Test/platform_manifest_twrp_aosp.git -b twrp-16.0`
* Device Path: `device/infinix/X6871`
* Common Path: `device/transsion/mt6895-common`
* Symlink Commands:
  ```bash
  mkdir -p device/infinix device/transsion
  ln -s $(pwd)/trees/twrp device/infinix/X6871
  ln -s $(pwd)/trees/common device/transsion/mt6895-common
  ```
* Lunch Target: `twrp_X6871-eng`
* Build Command: `mka adbd vendorbootimage -j$(nproc)`

### OrangeFox (`trees/ofrp/`)
* Upstream Manifest: `https://gitlab.com/orangefox/manifest.git -b fox_16.0`
* Device Path: `device/infinix/X6871`
* Common Path: `device/transsion/mt6895-common`
* Symlink Commands:
  ```bash
  mkdir -p device/infinix device/transsion
  ln -s $(pwd)/trees/ofrp device/infinix/X6871
  ln -s $(pwd)/trees/common device/transsion/mt6895-common
  ```
* Lunch Target: `fox_X6871-eng`
* Build Command: `mka adbd vendorbootimage -j$(nproc)`
* Post-Build Repack: `python3 scripts/repack_vendor_boot_a16.py`

### PitchBlack Recovery (`trees/pbrp/`)
* Upstream Note: PBRP upstream does not maintain an Android 16 manifest branch. This tree provides forward-ported PBRP makefiles targeting TWRP 16 / AOSP 16 build trees with PBRP vendor overlays.
* Upstream Manifest: `https://github.com/PitchBlackRecoveryProject/manifest_pb.git -b android-14.0`
* Device Path: `device/infinix/X6871`
* Common Path: `device/transsion/mt6895-common`
* Symlink Commands:
  ```bash
  mkdir -p device/infinix device/transsion
  ln -s $(pwd)/trees/pbrp device/infinix/X6871
  ln -s $(pwd)/trees/common device/transsion/mt6895-common
  ```
* Lunch Target: `pb_X6871-eng`
* Build Command: `mka adbd vendorbootimage -j$(nproc)`

### SkyHawk Recovery (`trees/shrp/`)
* Upstream Note: SHRP upstream has stalled at Android 12.1. True Android 16 support is nonexistent upstream; this tree is a forward-ported configuration for community backporting/testing.
* Upstream Manifest: `https://github.com/SKYHAWK-Recovery-Project/platform_manifest_twrp_omni.git`
* Device Path: `device/infinix/X6871`
* Common Path: `device/transsion/mt6895-common`
* Symlink Commands:
  ```bash
  mkdir -p device/infinix device/transsion
  ln -s $(pwd)/trees/shrp device/infinix/X6871
  ln -s $(pwd)/trees/common device/transsion/mt6895-common
  ```
* Lunch Target: `shrp_X6871-eng`
* Build Command: `mka adbd vendorbootimage -j$(nproc)`

### YuKongA Recovery Project (YARP) (`trees/yarp/`)
* Upstream Note: YARP is the YuKongA Recovery Project, a touch-based custom recovery fork maintaining updated UI and decryption support for newer MTK/Qualcomm Android 16 platforms.
* Upstream Base: `https://github.com/TWRP-Test/platform_manifest_twrp_aosp.git -b twrp-16.0`
* Device Path: `device/infinix/X6871`
* Common Path: `device/transsion/mt6895-common`
* Symlink Commands:
  ```bash
  mkdir -p device/infinix device/transsion
  ln -s $(pwd)/trees/yarp device/infinix/X6871
  ln -s $(pwd)/trees/common device/transsion/mt6895-common
  ```
* Lunch Target: `yarp_X6871-eng`
* Build Command: `mka adbd vendorbootimage -j$(nproc)`

---

## 4. Hardware Verification & Shims

1. Two-Fragment Boot Header v4:
   - MediaTek bootloader validates Fragment 1 (type 2 / RECOVERY) for recovery mode while loading Fragment 0 (type 1 / PLATFORM) for boot drivers.
   - Physical vendor_boot boundary is strictly 64 MB (67,108,864 bytes).
2. VINTF Manifest Shim:
   - In stock Android 16 Fragment 0, boot and health services are declared as `<manifest version="9.0" type="device">` under `system/etc/vintf/manifest/`.
   - Recovery servicemanager rejects device manifests in `/system` (treating `/system` as framework).
   - In-place repacker rewrites `system/etc/vintf/` to `vendor/etc/vintf/` and `version="9.0"` to `version="8.0"`.
3. Trustonic TEE:
   - Stock `mcDrvModule.ko` (vermagic `6.12.38-android16-5-gcc51d883045d-4k`) is preserved intact without speculative opcode patches.
   - User-space matching daemons from stock vendor provide native decryption compatibility without binary corruption.
