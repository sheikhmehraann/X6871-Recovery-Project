# Infinix GT 20 Pro (X6871) Recovery Project — Android 16 / Kernel 6.12

Unified recovery development workspace, standalone device trees, and automated CI/CD configurations for the Infinix GT 20 Pro (models `Infinix-X6871`, `X6871`, `X6871-OP`, project code `x6871_h962`) powered by the MediaTek Dimensity 8200 Ultimate (`MT6895` / `MT6896`) running stock Transsion OS 16 (Android 16 / Linux 6.12 GKI).

---

## 1. Verified Stock ROM Baseline

All partition boundaries, offsets, ramdisk tables, and prebuilts in this repository are verified against official stock firmware:

* **Stock Firmware Build:** `X6871-16.3.0.155SP22(IN009PF001AZ)`
* **Android Version:** Android 16 (Stock XOS 16 · `BP2A.250605.031.A3`)
* **Kernel Version:** Linux 6.12.38 Generic Kernel Image (GKI)
* **Scatter File:** `reference/stock_firmware/MT6895_Android_scatter.txt`

### Stock Partition Cryptographic Hashes
| Partition Image | Physical Size (Bytes) | SHA-256 Checksum |
|---|---|---|
| `boot.img` | 67,108,864 (64.0 MB) | `4CBCD5B57CC69AB8D82A05AF7F43200DC5094044ACF488A00B3B104823E6A027` |
| `vendor_boot.img` | 67,108,864 (64.0 MB) | `07ACF97BFD2258CDF3B230240C71631F7FB7747BFF9064C7B5887FCDD7C0931F` |
| `dtbo.img` | 8,388,608 (8.0 MB) | `10834F2726358ADF83015945DADB6E37A7CB7F6E1C3FD5E167067854CF64FD39` |
| `vbmeta.img` | 12,288 (12.0 KB) | `91954D180EB21A00FABCC3276F5FB93B805B0DC56D8556A19DDF20868BFEC003` |
| `vbmeta_system.img` | 4,096 (4.0 KB) | `BFF1CCAD38DD7235EB2595C6EBAE893E63E341E78160E0CAD0C7E5BE80CC256C` |
| `vbmeta_vendor.img` | 4,096 (4.0 KB) | `10FEA75613C38CF26BEA73B978BABDC45559FBD22375C36C97675CAA27C542FD` |
| `super.img` | 6,021,361,312 (~6.02 GB) | Expands to physical `super` boundary: `12,426,428,416` bytes (~12.44 GB) |

---

## 2. Boot Header v4 Architecture & Ramdisk Fragmentation

Reverse-engineering the stock `vendor_boot.img` reveals Android 16's strict two-entry ramdisk table requirement:

```text
vendor_boot Header v4 (67,108,864 bytes / 64MB boundary)
├── Page 0 (0x0000 - 0x0FFF): Header v4 (Magic: 'VNDRBOOT', version: 4, page_size: 4096)
│   ├── Kernel Address:   0x40000000
│   ├── Ramdisk Address:  0x66F00000
│   ├── Tags Address:     0x47C80000
│   ├── DTB Address:      0x0000000047C80000 (Size: 337,316 bytes)
│   └── Header Size:      2128 bytes
├── Page 1: Vendor Ramdisk Payload
│   ├── Fragment 0 (Type 1 - PLATFORM): Stock vendor ramdisk (30,368,891 bytes / ~28.96 MB)
│   └── Fragment 1 (Type 2 - RECOVERY): Recovery filesystem (3,204,703 bytes / ~3.06 MB)
├── Page N: Flattened Device Tree Blob (dtb.img, 337,316 bytes)
├── Page M: Vendor Ramdisk Table (2 entries, 108 bytes per entry)
│   ├── Entry 0: type=1 (PLATFORM), offset=0, size=30,368,891, name=''
│   └── Entry 1: type=2 (RECOVERY), offset=30,368,891, size=3,204,703, name='recovery'
└── Page K: Bootconfig string:
    kernel.rcu_nocbs=all
    kernel.rcutree.enable_rcu_lazy=1
    kernel.rcupdate.rcu_cpu_stall_cputime=1
```

### Technical Issues Solved in this Workspace

#### A. VINTF Manifest Framework Crash Interception
In stock Android 16, `android.hardware.boot-service.mtk.xml` and `android.hardware.health-service.example.xml` declare `<manifest version="9.0" type="device">` but reside in `/system/etc/vintf/manifest/`. Recovery `servicemanager` parses `/system` as a framework manifest, aborting startup with:
`Cannot add a device manifest to a framework manifest` and `Unrecognized manifest.version 9.0 (libvintf@8.0)`.
* **Fix (`scripts/repack_vendor_boot_a16.py`):** In-place byte shimming inside the CPIO archive redirects `system/etc/vintf/` -> `vendor/etc/vintf/` and lowers version `9.0` -> `8.0` without altering file offsets.

#### B. Trustonic Kernel Module Verification (`mcDrvModule.ko`)
Inspection of stock `mcDrvModule.ko` (vermagic `6.12.38-android16-5-gcc51d883045d-4k SMP preempt mod_unload modversions aarch64`, SHA-256 `bca9abe09c7f5071f5bb88264782a6b21cd47d8442b680d2c32f8094d2e00f28`) confirms that stock Android 16 userspace daemons and kernel drivers are synchronized. Speculative instruction-level opcode patches (`MOV W0, #9`) were audited and removed to preserve binary module integrity and cryptographic signature validation.

#### C. Dual-Zstandard Adaptive Compression
Stock Fragment 0 is LZ4-compressed (~110 MB uncompressed). Merging it with Fragment 1 exceeds the 64.0 MB boundary.
* **Fix:** Fragment 0 and Fragment 1 are compressed using Zstandard (levels 22/21/19) to ensure the composite image fits within 67,108,864 bytes with 4096-byte alignment.

---

## 3. Supported Recovery Projects & Standalone Trees

This repository provides **both** dedicated standalone device trees (`trees/`) for individual upstream checkouts and a unified all-in-one build tree (`device/infinix/Infinix-X6871`):

| Recovery Project | Dedicated Upstream Tree | Target Lunch Combo | Upstream Support Status | Manifest Source & Branch | Build Makefile |
|---|---|---|---|---|---|
| TeamWin Recovery Project (TWRP) | [trees/twrp/](trees/twrp/) | `twrp_X6871-eng` | Community A16 Active | `TWRP-Test/platform_manifest_twrp_aosp.git -b twrp-16.0` | `twrp_X6871.mk` |
| OrangeFox Recovery Project (OFRP) | [trees/ofrp/](trees/ofrp/) | `fox_X6871-eng` | Official A16 Branch | `gitlab.com/orangefox/manifest.git -b fox_16.0` | `fox_X6871.mk` |
| PitchBlack Recovery Project (PBRP) | [trees/pbrp/](trees/pbrp/) | `pb_X6871-eng` | Community Forward-Port | `PitchBlackRecoveryProject/manifest_pb.git -b android-14.0` | `pb_X6871.mk` |
| SkyHawk Recovery Project (SHRP) | [trees/shrp/](trees/shrp/) | `shrp_X6871-eng` | Stalled at A12.1 | `SKYHAWK-Recovery-Project/platform_manifest_twrp_omni.git -b v3.1_12.1` | `shrp_X6871.mk` |
| YuKongA Recovery Project (YARP) | [trees/yarp/](trees/yarp/) | `yarp_X6871-eng` | Active MTK A16 Fork | `TWRP-Test/platform_manifest_twrp_aosp.git -b twrp-16.0` | `yarp_X6871.mk` |

All five standalone recovery trees share the common platform tree:
* **Common Platform Tree:** [trees/common/](trees/common/) (`device/transsion/mt6895-common`)

For individual upstream conventions and symlink instructions, see [trees/README.md](trees/README.md) and [recoveries/](recoveries/).

---

## 4. Hardware Specifications

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

## 5. Storage & Partition Topology

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

All logical partitions are declared in `trees/common/recovery/root/system/etc/recovery.fstab` and `BoardConfigCommon.mk`.

---

## 6. Repository File Layout

```text
.
├── .github/
│   └── workflows/
│       ├── twrp.yml                    # Automated TWRP 16.0 CI build
│       ├── orangefox.yml               # Automated OrangeFox A16 CI build
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
├── trees/                              # Dedicated upstream device trees
│   ├── twrp/                           # Standalone TWRP 16.0 tree
│   ├── ofrp/                           # Standalone OrangeFox 14.1 tree
│   ├── pbrp/                           # Standalone PitchBlack Recovery tree
│   ├── shrp/                           # Standalone SkyHawk Recovery tree
│   ├── yarp/                           # Standalone YARP tree
│   └── common/                         # Shared Transsion MT6895 common tree
├── device/
│   ├── infinix/
│   │   └── Infinix-X6871/              # Unified all-in-one device model tree
│   └── transsion/
│       └── mt6895-common/              # Unified platform common tree
├── recoveries/                         # Upstream specifications & developer guides
│   ├── TWRP/                           # TWRP 16.0 specifications
│   ├── OFRP/                           # OrangeFox 14.1 specifications
│   ├── PBRP/                           # PitchBlack specifications
│   ├── SHRP/                           # SkyHawk specifications
│   └── YARP/                           # YARP specifications
├── reference/
│   ├── stock_firmware/
│   │   ├── MT6895_Android_scatter.txt # Official MediaTek partition scatter
│   │   └── partition_info.json        # Parsed dynamic partition map
│   └── stock_vendor_boot.img.gz       # Golden stock Android 16 vendor_boot
├── scripts/
│   ├── build_x6871.sh                  # Local compilation dispatcher (all 5 targets)
│   ├── repack_vendor_boot_a16.py       # Dual-ZSTD repacker with opcode patches
│   ├── patch_ofox.py                   # Automated OrangeFox AST patch engine
│   └── graphics_drm.cpp                # MT6895 atomic DRM display engine
├── tools/
│   ├── unpack_vendor_boot.py           # Header v4 extraction tool
│   ├── repack_vendor_boot.py           # Header v4 packaging tool
│   └── unpack_ramdisk.py               # CPIO extraction utility
├── .gitignore                          # Unix build artifact exclusion list
└── README.md                           # Master recovery developer documentation
```

---

## 7. Building from Source

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

### Local Compilation via Unified Dispatcher
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

---

## 8. Installation & Flashing

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

## 9. Hardware Status Matrix

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

## 10. Authors & Credits

* **Device Trees & Integration:** sheikhmehraann, ramabondanp, Shivelight
* **TeamWin Recovery Project:** TeamWin
* **OrangeFox Recovery Project:** OFRP Team
* **PitchBlack Recovery Project:** PBRP Team
* **SkyHawk Recovery Project:** SHRP Team
* **YuKongA Recovery Project:** YuKongA
* **MediaTek Platform Bringup:** LineageOS & Transsion Open Source
