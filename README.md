# OrangeFox Recovery for Infinix GT 20 Pro (X6871)

Unofficial **OrangeFox Recovery R12.1 (Stable)** device tree and automated build system for the **Infinix GT 20 Pro** (`X6871` / `X6871-OP`), powered by the MediaTek Dimensity 8200 Ultimate (`MT6895` / `MT6896`).

Maintained by [@withmehraan](https://github.com/sheikhmehraann) with active community testing.

---

## Device Specifications

| Attribute | Specification |
|---|---|
| **Device Model** | Infinix GT 20 Pro (`Infinix-X6871` / `X6871-OP`) |
| **SoC** | MediaTek Dimensity 8200 Ultimate (4nm, Octa-core) |
| **Platform** | `mt6895` / `mt6896` |
| **Display** | 1080 x 2436 AMOLED (144Hz, Single-Pipe DRM) |
| **Kernel Version** | 5.10.237-android12-9 (Header v4) |
| **Architecture** | ARM64 (aarch64-linux-android) |
| **Partition Scheme** | Virtual A/B (VAB) + Dynamic Partitions (`super`) |
| **Recovery Location** | `vendor_boot` (Header v4, 64 MB budget) |
| **Target OS** | Android 15 / XOS 15 (`AP3A.240905.015.A2 / 180003`) |

---

## Current Status & Verified Features

Tested and verified on live Infinix GT 20 Pro hardware running stock XOS 15:

* **Storage Decryption:** Full File-Based Encryption (FBEv2) support with hardware metadata decryption (`/dev/block/mapper/userdata`). Decrypts PIN, password, and pattern lock screens cleanly.
* **Dynamic Super Partitions:** All 14 logical partitions inside `super` (`system`, `vendor`, `product`, `system_ext`, `vendor_dlkm`, `odm_dlkm`, `tr_carrier`, `tr_company`, `tr_mi`, `tr_overlayfs`, `tr_preload`, `tr_product`, `tr_region`, `tr_theme`) are fully mapped and available across Flash Image, Partition Backup, and Mount menus.
* **Ultra-Fast Splash Engine:** Proprietary in-place Header v4 `vendor_boot` repacker accelerated by multi-core `pigz` parallel gzip compression across all 8 CPU cores. Splash changes execute in **~2.4 seconds** (down from 38 seconds). Dual-slot sync updates both `vendor_boot_a` and `vendor_boot_b` simultaneously.
* **Boot Slot Management:** Native A/B slot display (`Slot A` / `Slot B`) with direct active slot switching and hardware `bootctl` fallback.
* **Display & Graphics:** Tailored single-pipe Direct Rendering Manager (`minuitwrp/graphics_drm.cpp`) eliminating MTK panel flicker and atomic commit drops.
* **Peripherals & Drivers:**
  * Haptic Feedback: Dedicated AW8697 linear vibrator driver via sysfs `vibrator_single`.
  * Flashlight: Real rear camera torch control using the OCP81375 LED driver.
  * Thermals: Real-time CPU temperature readout (`thermal_zone0` / `soc_max`).
  * Connectivity: MTP file transfer over USB, ADB sideload, and USB-OTG external drives.
* **AOSP & Custom ROM Flashing:** Full `update_engine_sideload` and dynamic partition resizing support for PixelOS, LineageOS, and GSI packages.
* **Built-in Root Suite:** Direct integration with Magisk v28.1 (`/FFiles/OF_Magisk`), KernelSU, and APatch.

---

## Installation

Because the Infinix GT 20 Pro uses Android Header v4 with Virtual A/B, the recovery ramdisk lives inside `vendor_boot`. **Do NOT flash to `boot`.**

### Fastboot Installation

1. Download the latest release from the [GitHub Releases](https://github.com/sheikhmehraann/X6871-Recovery-Project/releases) tab.
2. Put the phone into Fastboot mode:
   ```bash
   adb reboot bootloader
   ```
3. Flash the recovery image to both boot slots:
   ```bash
   fastboot flash vendor_boot_a vendor_boot.img
   fastboot flash vendor_boot_b vendor_boot.img
   ```
4. Reboot into recovery:
   ```bash
   fastboot reboot recovery
   ```
   *(Or hold `Power + Volume Up` while the phone powers on).*

---

## Building from Source

Builds are automatically compiled and published through GitHub Actions on push to `main`. To reproduce the build locally:

### 1. Environment & Dependencies
Recommended build environment: Ubuntu 22.04 LTS (x86_64) with at least 16 GB RAM and 60 GB free disk space.

```bash
sudo apt-get update && sudo apt-get install -y \
  git-core gnupg flex bison build-essential zip curl zlib1g-dev \
  libc6-dev-i386 libncurses5 x11proto-core-dev libx11-dev lib32z1-dev \
  libgl1-mesa-dev libxml2 libxml2-utils xsltproc unzip fontconfig \
  python3 python-is-python3 libssl-dev rsync bc liblz4-tool libncurses5-dev \
  squashfs-tools libtinfo5 openjdk-11-jdk-headless ccache pigz
```

### 2. Sync Minimal Manifest
```bash
mkdir -p ~/fox_14.1 && cd ~/fox_14.1
git clone --depth=1 https://gitlab.com/OrangeFox/sync.git ~/OrangeFox_sync
cd ~/OrangeFox_sync
./orangefox_sync.sh --branch 14.1 --path ~/fox_14.1
```

### 3. Clone Device Trees & Apply Patches
```bash
cd ~/fox_14.1
mkdir -p device/infinix device/transsion

# Clone or copy device trees
cp -r /path/to/X6871-Recovery-Project/device/infinix/Infinix-X6871 device/infinix/
ln -sf Infinix-X6871 device/infinix/X6871
cp -r /path/to/X6871-Recovery-Project/device/transsion/mt6895-common device/transsion/

# Run the OrangeFox patch engine
python3 /path/to/X6871-Recovery-Project/scripts/patch_ofox.py ~/fox_14.1
```

### 4. Compile
```bash
source build/envsetup.sh
lunch twrp_X6871-eng
mka adbd vendorbootimage -j$(nproc)
```

The compiled image will be located at:
`out/target/product/X6871/vendor_boot.img`

---

## Repository Structure

```text
├── .github/
│   └── workflows/
│       └── orangefox.yml        # CI build and automated release workflow
├── configs/                     # Extracted stock system dumps, fstabs, file_contexts
├── device/
│   ├── infinix/
│   │   └── Infinix-X6871/       # Device tree (BoardConfig, fstab, flags, vendorsetup)
│   └── transsion/
│       └── mt6895-common/       # Common platform tree (init, drm, HAL configs)
├── scripts/
│   ├── build_x6871.sh           # Local automated compilation script
│   ├── gotestrunner.go          # Blueprint test runner stub for minimal tree
│   ├── graphics_drm.cpp         # Verified MediaTek single-pipe DRM implementation
│   └── patch_ofox.py            # Hardware, architecture, identity, and pigz patch engine
└── tools/
    ├── repack_vendor_boot.py    # Standalone Header v4 vendor_boot repacker
    ├── unpack_ramdisk.py        # CPIO extraction utility
    └── unpack_vendor_boot.py    # Header v4 vendor_boot unpacker
```

---

## Community & Support

* **Release Channel:** [Telegram - GT 20 Pro Updates](https://t.me/Gt20ProINUpdates)
* **Discussion Group:** [Telegram - GT 20 Pro Discussion](https://t.me/Gt20ProIN)
* **Bug Reports:** Open an issue on this repository with `/tmp/recovery.log` attached.

---

## Credits

* **OrangeFox Recovery Project** for the recovery base and UI engine.
* **TeamWin (TWRP)** for core partition and decryption logic.
* **sheikhmehraann** for maintainership and device-specific bringup.
* The Infinix GT 20 Pro tester community for ongoing testing and feedback.
