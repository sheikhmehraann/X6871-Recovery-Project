# Infinix GT 20 Pro (X6871) Recovery Project — Android 16 / Kernel 6.12

Unified recovery device tree and automated build configurations for the Infinix GT 20 Pro (models `Infinix-X6871`, `X6871`, `X6871-OP`, project code `x6871_h962`) powered by the MediaTek Dimensity 8200 Ultimate (`MT6895` / `MT6896`) running stock Transsion OS 16 (Android 16 / Linux 6.12 GKI).

---

## 1. Supported Recovery Projects

This repository hosts unified device trees and specialized configuration profiles for all five major Android custom recoveries:

| Recovery Project | Target Lunch Combo | Base Manifest | Build Makefile | Dedicated Profile |
|---|---|---|---|---|
| TeamWin Recovery Project (TWRP) | `twrp_X6871-eng` | TWRP 16.0 (AOSP tos16 / A16) | `device/infinix/Infinix-X6871/twrp_X6871.mk` | [recoveries/TWRP](recoveries/TWRP/TREE.md) |
| OrangeFox Recovery Project (OFRP) | `fox_X6871-ap2a-eng` | OrangeFox 14.1 (AOSP AP2A / SDK 34) | `device/infinix/Infinix-X6871/fox_X6871.mk` | [recoveries/OFRP](recoveries/OFRP/TREE.md) |
| PitchBlack Recovery Project (PBRP) | `pb_X6871-eng` | PBRP 12.1 / 14 | `device/infinix/Infinix-X6871/pb_X6871.mk` | [recoveries/PBRP](recoveries/PBRP/TREE.md) |
| SkyHawk Recovery Project (SHRP) | `shrp_X6871-eng` | SHRP 12.1 | `device/infinix/Infinix-X6871/shrp_X6871.mk` | [recoveries/SHRP](recoveries/SHRP/TREE.md) |
| Yet Another Recovery Project (YARP) | `yarp_X6871-eng` | YARP / TWRP 16.0 | `device/infinix/Infinix-X6871/yarp_X6871.mk` | [recoveries/YARP](recoveries/YARP/TREE.md) |

---

## 2. Hardware Specifications

| Attribute | Specification |
|---|---|
| Device Model | Infinix GT 20 Pro (`Infinix-X6871`, `X6871`, `X6871-OP`) |
| Platform / SoC | MediaTek Dimensity 8200 Ultimate (`MT6895` / `MT6896`) |
| Architecture | ARM64 (`arm64-v8a`, `generic`) |
| CPU Topology | 1x Cortex-A78 @ 3.1 GHz + 3x Cortex-A78 @ 3.0 GHz + 4x Cortex-A55 @ 2.0 GHz |
| GPU | Mali-G610 MC6 |
| Display Panel | 6.78-inch AMOLED, 1080 x 2436 resolution, 144Hz refresh rate, single-pipe DRM |
| Touch Controller | Goodix GT9916 capacitive touch IC (`gt9916_common.ko` + `adaptive-ts.ko`) |
| Storage Interface | Samsung UFS 3.1 (`KLUEG4RHGB-B0E1`) |
| Partition Scheme | Virtual A/B (VAB) with Dynamic Partitions (`super`) |
| Boot Image Version | Boot Header Version 4 (`BOARD_BOOT_HEADER_VERSION := 4`) |
| Target Partition | `vendor_boot` (strict physical boundary: `67,108,864` bytes / 64.0 MB) |
| Target Firmware | Android 16 (Stock XOS 16, build `BP2A.250605.031.A3`) |
| Kernel Version | Linux 6.12.38 Generic Kernel Image (GKI) |
| Security / TEE | Trustonic Kinibi OS (KeyMint v3.0, Gatekeeper, mcDriverDaemon) |
| Haptics | Awinic AW8697 linear vibrator (`vibrator_single`) + AAC RichTap (`richtap_haptic_hv.ko`) |
| Battery / Power | MediaTek MT6375 Battery Driver (`/sys/class/power_supply/battery`) |
| Flashlight | OCP81375 camera torch interface (`/sys/class/torch/torch/torch_level`) |

---

## 3. Storage & Partition Topology

### Physical Partition Boundaries
* `super`: `12,426,428,416` bytes (~12.44 GB)
* `boot`: `67,108,864` bytes (64.0 MB, slotted `_a` / `_b`)
* `vendor_boot`: `67,108,864` bytes (64.0 MB, slotted `_a` / `_b`)
* `init_boot`: `8,388,608` bytes (8.0 MB, slotted `_a` / `_b`)
* `dtbo`: `8,388,608` bytes (8.0 MB, slotted `_a` / `_b`)
* `vbmeta`: `8,388,608` bytes (8.0 MB, slotted `_a` / `_b`)

### Dynamic Logical Volumes (Inside `super`)
The device exposes 16 logical partitions mapped across `main_a` and `main_b`:
* AOSP Standard: `system`, `system_ext`, `vendor`, `product`, `odm`
* Dynamic Kernel Modules: `system_dlkm`, `vendor_dlkm`, `odm_dlkm`
* Transsion Regional & Carrier: `tr_product`, `tr_preload`, `tr_carrier`, `tr_company`, `tr_region`, `tr_overlayfs`, `tr_misc`, `tr_manifest`

All logical partitions are declared in `device/transsion/mt6895-common/recovery/root/system/etc/recovery.fstab` and `BoardConfigCommon.mk`.

---

## 4. Boot Header v4 & Ramdisk Architecture

Android 16 firmware on MT6895 requires the bootloader to read `vendor_boot` (Header v4) using a two-entry ramdisk table:

```text
vendor_boot Header v4 (67,108,864 bytes / 64MB boundary)
├── Page 0 (0x0000 - 0x0FFF): Header v4 (Magic: 'VNDRBOOT', version: 4, page_size: 4096)
├── Page 1: Vendor Ramdisk Payload
│   ├── Fragment 0 (Type 1 - PLATFORM): Stock vendor ramdisk (242 MTK drivers, firmware, init scripts)
│   └── Fragment 1 (Type 2 - RECOVERY): Recovery filesystem (TWRP / OrangeFox / PBRP / SHRP / YARP)
├── Page N: Flattened Device Tree Blob (dtb.img, 337,316 bytes)
├── Page M: Vendor Ramdisk Table (108 bytes per entry)
│   ├── Entry 0: size=Frag0_sz, offset=0, type=1 (PLATFORM)
│   └── Entry 1: size=Frag1_sz, offset=Frag0_sz, type=2 (RECOVERY, name='recovery')
└── Page K: Bootconfig string ("androidboot.selinux=permissive ...")
```

### Technical Fixes Implemented in this Tree

#### 1. VINTF Manifest Framework Crash Interception
In Android 16, `android.hardware.boot-service.mtk.xml` and `android.hardware.health-service.example.xml` declare `<manifest version="9.0" type="device">` but are installed into `/system/etc/vintf/manifest/`. Recovery `servicemanager` treats `/system` as a framework manifest, terminating with:
`Cannot add a device manifest to a framework manifest` and `Unrecognized manifest.version 9.0 (libvintf@8.0)`.
* **Resolution:** `scripts/repack_vendor_boot_a16.py` performs in-place byte shimming inside the CPIO archive:
  `system/etc/vintf/` -> `vendor/etc/vintf/` and `version="9.0"` -> `version="8.0"`.

#### 2. Trustonic Kernel Module Opcode Patch (`mcDrvModule.ko`)
Under Linux Kernel 6.12, `mcDrvModule.ko` returns driver API version 10, whereas the user-mode daemon expects API version 9.
* **Resolution:** `scripts/repack_vendor_boot_a16.py` modifies the ARM64 immediate instructions in-place inside `mcDrvModule.ko`:
  `\x40\x01\x80\x52` -> `\x20\x01\x80\x52` (`MOV W0, #9`).

#### 3. Dual-Zstandard Adaptive Compression
Stock Fragment 0 is LZ4-compressed (~110 MB uncompressed). Merging it with Fragment 1 exceeds the 64.0 MB boundary.
* **Resolution:** Both Fragment 0 and Fragment 1 are compressed using Zstandard (levels 22/21/19) to ensure the total image fits within 67,108,864 bytes with 4096-byte padding.

#### 4. Direct DRM Modesetting Display Engine (`scripts/graphics_drm.cpp`)
Resolves black screens on the 1080x2436 144Hz AMOLED panel by bypassing legacy fbdev and directly interfacing with `/dev/dri/card0` via single-pipe atomic DRM modesetting.

---

## 5. Repository Structure

```text
.
├── .github/
│   └── workflows/
│       ├── orangefox.yml               # Automated OrangeFox A16 CI build
│       ├── twrp.yml                    # Automated TWRP 16.0 CI build
│       ├── pbrp.yml                    # Automated PitchBlack CI build
│       ├── shrp.yml                    # Automated SkyHawk CI build
│       └── yarp.yml                    # Automated YARP CI build
├── configs/
│   ├── by-name-mapping.txt             # Hardware UFS partition mappings
│   ├── getprop.txt                     # Stock build properties
│   ├── proc_cmdline.txt                # Bootloader kernel command line
│   ├── proc_version.txt                # Stock kernel version baseline
│   ├── file_contexts/                  # SELinux file contexts
│   └── fstabs/                         # Stock partition mount tables
├── device/
│   ├── infinix/
│   │   └── Infinix-X6871/              # Unified device model tree
│   │       ├── Android.mk
│   │       ├── AndroidProducts.mk      # Multi-product definitions
│   │       ├── BoardConfig.mk          # Board architecture flags
│   │       ├── device.mk
│   │       ├── twrp_X6871.mk           # TWRP target makefile
│   │       ├── fox_X6871.mk / fox.mk   # OrangeFox target makefiles
│   │       ├── pb_X6871.mk             # PBRP target makefile
│   │       ├── shrp_X6871.mk           # SHRP target makefile
│   │       ├── yarp_X6871.mk           # YARP target makefile
│   │       ├── omni_X6871.mk           # Omni fallback target makefile
│   │       ├── vendorsetup.sh          # Environment exports & patch dispatcher
│   │       ├── patches/                # Hardware haptic patches
│   │       ├── prebuilt/
│   │       │   └── dtb.img             # Android 16 Device Tree Blob
│   │       └── recovery/root/lib/modules/ # 242 compiled .ko kernel drivers
│   └── transsion/
│       └── mt6895-common/              # Platform common configuration
│           ├── Android.mk
│           ├── BoardConfigCommon.mk    # Common boot header & partition sizes
│           ├── common.mk               # Shared packages and services
│           ├── system.prop             # Platform properties
│           ├── mtk_plpath_utils/       # MTK preloader path utility
│           ├── patches/                # Build system ZSTD patches
│           ├── prebuilt/
│           │   └── empty_recovery.cpio.zst # Standalone empty recovery fragment
│           └── recovery/root/          # Init scripts, HALs, VINTF, mcRegistry
├── recoveries/                         # Dedicated recovery profile directories
│   ├── TWRP/                           # TWRP 16.0 tree requirements & guide
│   ├── OFRP/                           # OrangeFox 14.1 tree requirements & guide
│   ├── PBRP/                           # PitchBlack 12.1 tree requirements & guide
│   ├── SHRP/                           # SkyHawk 12.1 tree requirements & guide
│   └── YARP/                           # YARP 16.0 tree requirements & guide
├── reference/
│   ├── stock_firmware/
│   │   ├── MT6895_Android_scatter.txt # Official MediaTek partition scatter
│   │   └── partition_info.json        # Parsed dynamic partition map
│   └── stock_vendor_boot.img.gz       # Golden stock Android 16 vendor_boot
├── scripts/
│   ├── build_x6871.sh                  # Local compilation dispatcher (all 5 targets)
│   ├── repack_vendor_boot_a16.py       # Dual-ZSTD repacker with opcode patches
│   ├── patch_ofox.py                   # Automated OrangeFox AST patch engine
│   ├── graphics_drm.cpp                # MT6895 atomic DRM display engine
│   └── gotestrunner.go                 # Blueprint test bypass stub
└── tools/
    ├── unpack_vendor_boot.py           # Header v4 extraction tool
    ├── repack_vendor_boot.py           # Header v4 packaging tool
    └── unpack_ramdisk.py               # CPIO extraction utility
```

---

## 6. Building from Source

### Prerequisites
Ubuntu 20.04 LTS or 22.04 LTS with standard AOSP build packages:
```bash
sudo apt-get update
sudo apt-get install -y \
    git-core gnupg flex bison build-essential zip curl zlib1g-dev \
    libc6-dev-i386 libncurses5 x11proto-core-dev libx11-dev lib32z1-dev \
    libgl1-mesa-dev libxml2 libxml2-utils xsltproc unzip fontconfig \
    python3 python-is-python3 libssl-dev rsync bc liblz4-tool libncurses5-dev \
    squashfs-tools libtinfo5 openjdk-11-jdk-headless ccache zstd
```

### Local Dispatcher Script
Use `scripts/build_x6871.sh` with the target recovery parameter:
```bash
chmod +x scripts/build_x6871.sh

# TeamWin Recovery Project
./scripts/build_x6871.sh twrp

# OrangeFox Recovery Project
./scripts/build_x6871.sh ofox

# PitchBlack Recovery Project
./scripts/build_x6871.sh pbrp

# SkyHawk Recovery Project
./scripts/build_x6871.sh shrp

# Yet Another Recovery Project
./scripts/build_x6871.sh yarp
```

For individual recovery sync instructions, refer to their dedicated documentation:
* [TWRP Build Guide](recoveries/TWRP/TREE.md)
* [OrangeFox Build Guide](recoveries/OFRP/TREE.md)
* [PitchBlack Build Guide](recoveries/PBRP/TREE.md)
* [SkyHawk Build Guide](recoveries/SHRP/TREE.md)
* [YARP Build Guide](recoveries/YARP/TREE.md)

---

## 7. Installation & Flashing

The recovery ramdisk resides inside the physical `vendor_boot` partition. Do not flash this image to `boot`.

1. Boot the device into Fastboot mode:
   ```bash
   adb reboot bootloader
   ```
2. Verify connection:
   ```bash
   fastboot devices
   ```
3. Flash the repacked `vendor_boot` image to both boot slots:
   ```bash
   fastboot flash vendor_boot_a vendor_boot.img
   fastboot flash vendor_boot_b vendor_boot.img
   ```
4. Reboot into recovery mode:
   ```bash
   fastboot reboot recovery
   ```

---

## 8. Hardware Status Matrix

| Subsystem | Driver / Interface | Status | Notes |
|---|---|---|---|
| Recovery Boot | Header v4 Dual Fragment (ZSTD) | Operational | Verified on stock XOS 16 bootloader |
| Normal OS Boot | Shared `vendor_boot` | Operational | Normal boot unaffected |
| Display | DRM atomic mode `/dev/dri/card0` | Operational | 1080x2436 @ 144Hz, zero tear |
| Touchscreen | Goodix GT9916 (`gt9916_common.ko`) | Operational | Loaded via `adaptive-ts.ko` |
| FBE Decryption | Trustonic KeyMint v3.0 / Gatekeeper | Operational | Decrypts FBEv2 userdata (PIN/pattern/password) |
| Dynamic Partitions | Linux Device Mapper (`super`) | Operational | All 16 logical volumes mapped |
| Fastbootd | USB ConfigFS gadget | Operational | Logical partition flashing functional |
| A/B Slot Switch | Stock MTK AIDL boot HAL | Operational | Slot switching functional via `bootctl` |
| USB Mass Storage | ConfigFS / MTP | Operational | Internal storage and SD card visible |
| USB-OTG | Kernel SCSI storage (`/dev/block/sdd1`) | Operational | Dual-block fallback supported |
| Battery Telemetry | MT6375 Battery Driver | Operational | Real charge percentage and voltage reported |
| Haptics | AW8697 (`vibrator_single`) | Operational | Patched in `minuitwrp/events.cpp` |
| Flashlight | OCP81375 camera torch | Operational | Level control via sysfs |
| CPU Temperature | MT6895 `thermal_zone0` | Operational | Telemetry active |

---

## 9. Authors & Credits

* **Device Trees & Integration:** sheikhmehraann, ramabondanp, Shivelight
* **TeamWin Recovery Project:** TeamWin
* **OrangeFox Recovery Project:** OFRP Team
* **PitchBlack Recovery Project:** PBRP Team
* **SkyHawk Recovery Project:** SHRP Team
* **Yet Another Recovery Project:** YARP Team
* **MediaTek Platform Bringup:** LineageOS & Transsion Open Source
