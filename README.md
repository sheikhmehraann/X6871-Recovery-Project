# Infinix GT 20 Pro (X6871) — Android 16 (Kernel 6.12 GKI) Recovery Project

> [!IMPORTANT]
> **Branch Architecture:** This branch is dedicated to **Android 16 (Stock XOS 16 / Linux 6.12 GKI)** with OrangeFox Recovery 14.1 (AOSP AP2A / SDK 34).
>
> 👉 For **Android 15 (Stock XOS 14/15 / Kernel 5.10 / 5.15)**, switch to the [`main`](https://github.com/sheikhmehraann/X6871-Recovery-Project/tree/main) branch.

Automated build configurations and device tree for the Infinix GT 20 Pro (`X6871` / `X6871-OP`), powered by the MediaTek Dimensity 8200 Ultimate (`MT6895` / `MT6896`) running official Android 16.

Maintained by [sheikhmehraann](https://github.com/sheikhmehraann).

---

## Latest Verified Release (Android 16 / Kernel 6.12)

* **Current Stable Release:** [`ofox-133`](https://github.com/sheikhmehraann/X6871-Recovery-Project/releases/tag/ofox-133)
* **Direct Download:** [vendor_boot.img](https://github.com/sheikhmehraann/X6871-Recovery-Project/releases/download/ofox-133/vendor_boot.img)
* **Checksum (SHA-256):** `77c5ee97589884675e833696a702dca74c3d94b6ea33d175fb3ef74930fa7f67`
* **Size:** Exactly `67,108,864` bytes (64.0 MB strict physical hardware boundary)

---

## Device & Architecture Specifications

| Attribute | Value |
|---|---|
| Device Model | Infinix GT 20 Pro (`X6871`, `Infinix-X6871`) |
| Platform / SoC | MediaTek Dimensity 8200 Ultimate (`MT6895` / `MT6896`) |
| Target Firmware | Android 16 (Stock XOS 16 · Build `BP2A.250605.031.A3`) |
| Kernel Version | Linux 6.12.38 Generic Kernel Image (GKI) |
| Architecture | ARM64 (`arm64-v8a`) |
| Recovery Location | `vendor_boot` (Boot Header v4, Virtual A/B) |
| Base Manifest | OrangeFox 14.1 (AOSP AP2A / SDK 34) |
| Ramdisk Architecture | Dual ZSTD Ramdisk Fragments (Fragment 0: Vendor Platform, Fragment 1: Recovery) |

---

## Key Hardware Features & Fixes in Android 16

1. **Dual ZSTD Ramdisk Repacker:**
   - Seamlessly repacks stock Android 16 Fragment 0 (242 MTK kernel modules and firmware) alongside OrangeFox Fragment 1 into the 64 MB hardware boundary.
2. **Pure AIDL KeyMint & Gatekeeper Decryption:**
   - Upgraded to KeyMint AIDL v3.0 (`android.hardware.security.keymint@3.0-service.trustonic`) with authenticated Kinibi trustlets.
   - Decrypts FBEv2 userdata without freezing or dropping credentials.
3. **AIDL BootControl Linker Integration:**
   - Shims `android.hardware.boot-service.mtk` against the Android 16 C-library environment, resolving the splash-screen freeze.
4. **Dynamic Super Partition Table:**
   - Calibrated exclusively for the 16 real logical hardware volumes (`system`, `system_ext`, `vendor`, `product`, `odm`, `*_dlkm`, and Transsion partitions `tr_carrier`, `tr_company`, `tr_overlayfs`, `tr_preload`, `tr_product`, `tr_region`, `tr_misc`, `tr_manifest`).
   - Format Data unmaps cleanly without hanging on phantom devices.
5. **144Hz AMOLED Display Engine:**
   - Single-pipe Direct Rendering Manager (`graphics_drm.cpp`) configured for 1080x2436 resolution with zero tear.

---

## Flashing Instructions

Flash the compiled `vendor_boot.img` directly to the active boot slot via fastboot:

```bash
# 1. Download Build #133 vendor_boot.img
curl -L -o vendor_boot.img "https://github.com/sheikhmehraann/X6871-Recovery-Project/releases/download/ofox-133/vendor_boot.img"

# 2. Flash to vendor_boot partition
fastboot flash vendor_boot vendor_boot.img

# 3. Reboot into OrangeFox Recovery
fastboot reboot recovery
```

---

## Building Locally

### Setup
Sync OrangeFox 14.1 manifest:
```bash
mkdir -p ~/fox_14.1 && cd ~/fox_14.1
git clone --depth=1 https://gitlab.com/OrangeFox/sync.git ~/OrangeFox_sync
~/OrangeFox_sync/orangefox_sync.sh --branch 14.1 --path ~/fox_14.1
```

Clone this repository into `device/infinix/X6871`:
```bash
git clone -b android-16 https://github.com/sheikhmehraann/X6871-Recovery-Project.git device/infinix/X6871
```

### Build Command
```bash
source build/envsetup.sh
source device/infinix/X6871/vendorsetup.sh
lunch twrp_X6871-ap2a-eng
mka adbd vendorbootimage -j$(nproc)
```

Post-build, repack with stock Fragment 0 using:
```bash
python3 device/infinix/X6871/../../scripts/repack_vendor_boot_a16.py \
    reference/stock_vendor_boot.img.gz \
    out/target/product/X6871/vendor_boot.img \
    out/target/product/X6871/vendor_boot.img
```

---

## Repository Structure (Android 16 Branch)

```text
├── .github/
│   └── workflows/
│       └── orangefox.yml        # CI build & release pipeline for Android 16
├── configs/                     # Device properties, file_contexts, and fstabs
├── device/
│   ├── infinix/
│   │   └── Infinix-X6871/       # Model specific configs (BoardConfig, makefiles, patches)
│   └── transsion/
│       └── mt6895-common/       # Platform tree (init scripts, HALs, fstabs)
├── reference/
│   └── stock_vendor_boot.img.gz # Compressed stock Android 16 vendor_boot reference
└── scripts/
    ├── graphics_drm.cpp         # MT6895 single-pipe DRM implementation
    ├── patch_ofox.py            # Device patching script for recovery sources
    └── repack_vendor_boot_a16.py# Dual-ramdisk v4 vendor_boot repacker
```

---

## Community & Support

- Updates Channel: [t.me/Gt20ProINUpdates](https://t.me/Gt20ProINUpdates)
- Discussion Group: [t.me/Gt20ProIN](https://t.me/Gt20ProIN)
- Maintainer: [@sheikhmehraann](https://github.com/sheikhmehraann)
