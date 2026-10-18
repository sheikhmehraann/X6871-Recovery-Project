# Multi-Recovery Project for Infinix GT 20 Pro (X6871)

Unified recovery device tree and automated build configurations for the Infinix GT 20 Pro (`X6871` / `X6871-OP`), powered by the MediaTek Dimensity 8200 Ultimate (`MT6895` / `MT6896`).

Maintained by [sheikhmehraann](https://github.com/sheikhmehraann).

---

## Supported Recoveries

This repository contains build targets and device tree configurations for:

1. **TWRP** (TeamWin Recovery Project) - Target: `twrp_X6871` / `omni_X6871`
2. **OFRP** (OrangeFox Recovery Project R12.1) - Target: `fox_X6871`
3. **PBRP** (PitchBlack Recovery Project) - Target: `pb_X6871`
4. **SHRP** (SkyHawk Recovery Project) - Target: `shrp_X6871`

---

## Device Specifications

| Attribute | Value |
|---|---|
| Device Model | Infinix GT 20 Pro (`X6871`, `X6871-OP`) |
| Platform / SoC | MediaTek Dimensity 8200 Ultimate (`MT6895` / `MT6896`) |
| Display | 1080 x 2436 AMOLED (144Hz refresh rate, single-pipe DRM) |
| Kernel Version | 5.10.x Android Common Kernel |
| Architecture | ARM64 (`arm64-v8a`) |
| Partition Layout | Virtual A/B (VAB) with Dynamic Partitions |
| Recovery Location | `vendor_boot` (Boot Header v4, 64 MB partition size) |
| Target Firmware | Android 14 / Android 15 (XOS 14 / XOS 15) |

---

## Hardware Support & Status

All four recovery variants share the common device tree and include:

- **Storage Decryption:** File-Based Encryption (FBEv2) metadata decryption via hardware KeyMint V1. Decrypts lockscreen PIN, pattern, and password.
- **Dynamic Super Partitions:** Maps all logical partitions (`system`, `vendor`, `product`, `system_ext`, `odm_dlkm`, `vendor_dlkm`, and regional Transsion carrier partitions) for flashing, backup, and mounting.
- **Display Driver:** Single-pipe direct rendering pipeline (`graphics_drm.cpp`) configured for the 1080x2436 144Hz panel.
- **A/B Slot Operations:** Slot suffix detection and active boot slot switching via `bootctl`.
- **Peripherals:**
  - Rear camera LED torch via OCP81375 sysfs interface.
  - Linear haptics via `vibrator_single`.
  - CPU thermal telemetry from `thermal_zone0`.
  - USB ConfigFS (MTP, ADB sideload, and USB-OTG storage).
- **OrangeFox Specifics:**
  - Bundled Fox Addons (Magisk, KernelSU v3.3.1 LKM, VBMeta disabler/enabler, pattern/pin remover, FRP remover).
  - Parallel pigz compression for in-place splash flashing.
  - Full-height scrollable addons interface with 144Hz kinetic inertia.

---

## Installation

The recovery ramdisk resides inside the `vendor_boot` partition. Do not flash to the `boot` partition.

1. Download the recovery image for your preferred project from GitHub Releases or actions artifacts.
2. Put the device into Fastboot mode:
   ```bash
   adb reboot bootloader
   ```
3. Flash the recovery image to both boot slots:
   ```bash
   fastboot flash vendor_boot_a vendor_boot.img
   fastboot flash vendor_boot_b vendor_boot.img
   ```
4. Reboot to recovery:
   ```bash
   fastboot reboot recovery
   ```

---

## Building Locally

### Setup
Sync the minimal recovery manifest (Android 12.1, 14.1, or recovery-specific sync tree), then clone this repository into `device/infinix/Infinix-X6871` and ensure `device/transsion/mt6895-common` is present.

### Build Commands
Use `scripts/build_x6871.sh` with the target recovery name:

```bash
# OrangeFox Recovery Project
./scripts/build_x6871.sh ofox

# TeamWin Recovery Project
./scripts/build_x6871.sh twrp

# PitchBlack Recovery Project
./scripts/build_x6871.sh pbrp

# SkyHawk Recovery Project
./scripts/build_x6871.sh shrp
```

Or manually with build envsetup:
```bash
source build/envsetup.sh

# Select target
lunch twrp_X6871-eng   # For TWRP
lunch fox_X6871-eng    # For OrangeFox
lunch pb_X6871-eng     # For PitchBlack
lunch shrp_X6871-eng   # For SkyHawk

# Build vendor_boot
mka adbd vendorbootimage -j$(nproc)
```

---

## Repository Structure

```text
├── .github/
│   └── workflows/
│       ├── orangefox.yml        # OrangeFox automated build and release
│       ├── twrp.yml             # TWRP automated build workflow
│       ├── pbrp.yml             # PitchBlack automated build workflow
│       └── shrp.yml             # SkyHawk automated build workflow
├── configs/                     # Device properties, file_contexts, and fstabs
├── device/
│   ├── infinix/
│   │   └── Infinix-X6871/       # Model specific configs (BoardConfig, makefiles)
│   └── transsion/
│       └── mt6895-common/       # Platform tree (init scripts, HALs, fstabs)
├── scripts/
│   ├── build_x6871.sh           # Local multi-recovery build script
│   ├── gotestrunner.go          # Blueprint test bypass stub
│   ├── graphics_drm.cpp         # MT6895 single-pipe DRM implementation
│   └── patch_ofox.py            # Device patching script for recovery sources
└── tools/
    ├── repack_vendor_boot.py    # Boot header v4 vendor_boot repacker
    ├── unpack_ramdisk.py        # Ramdisk extractor
    └── unpack_vendor_boot.py    # Boot header v4 vendor_boot unpacker
```

---

## Community & Support

- Updates Channel: [t.me/Gt20ProINUpdates](https://t.me/Gt20ProINUpdates)
- Discussion Group: [t.me/Gt20ProIN](https://t.me/Gt20ProIN)
- Maintainer: [@sheikhmehraann](https://github.com/sheikhmehraann)
