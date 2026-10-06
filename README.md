# OrangeFox Recovery for Infinix GT 20 Pro (X6871)

Unofficial **OrangeFox Recovery R12.1 (Stable)** device tree and automated build system for the **Infinix GT 20 Pro** (`X6871` / `X6871-OP`), powered by the MediaTek Dimensity 8200 Ultimate (`MT6895` / `MT6896`).

Maintained by [@withmehraan](https://github.com/sheikhmehraann) with active community testing.

---

## Device Specifications

| Attribute | Specification |
|---|---|
| **Device Model** | Infinix GT 20 Pro (`Infinix X6871` |
| **SoC** | MediaTek Dimensity 8200 Ultimate  |
| **Platform** | `mt6895` / `mt6896` |
| **Display** | 1080 x 2436 AMOLED (144Hz, Single-Pipe DRM) |
| **Kernel Version** | 5.10.237-android12-9 (Header v4) |
| **Architecture** | ARM64 (aarch64-linux-android) |
| **Partition Scheme** | Virtual A/B (VAB) + Dynamic Partitions |
| **Recovery Location** | `vendor_boot` (Header v4, 64 MB budget) |
| **Target OS** | Android 15 / XOS 15 |

---

## Current Status & Verified Features

Tested and verified on live Infinix GT 20 Pro hardware running stock XOS 15:

* **Storage Decryption:** Full File-Based Encryption (FBEv2) support with hardware metadata decryption Decrypts PIN, password, and pattern lock screens cleanly.
* **Dynamic Super Partitions:** All 14 logical partitions inside are fully mapped and available across Flash Image, Partition Backup, and Mount menus.
* **Ultra-Fast Splash Engine:** Proprietary in-place Header v4 `vendor_boot` repacker accelerated by multi-core `pigz` parallel gzip compression across all 8 CPU cores. Splash changes execute in **~2.4 seconds** (down from 38 seconds). Dual-slot sync updates both `vendor_boot_a` and `vendor_boot_b` simultaneously.
* **Boot Slot Management:** Native A/B slot display (`Slot A` / `Slot B`) with direct active slot switching and hardware `bootctl` fallback.
* **Display & Graphics:** Tailored single-pipe Direct Rendering Manager (`minuitwrp/graphics_drm.cpp`) eliminating MTK panel flicker and atomic commit drops.
* **Peripherals & Drivers:**
  * Haptic Feedback: Dedicated AW8697 linear vibrator driver via sysfs `vibrator_single`.
  * Flashlight: Real rear camera torch control using the OCP81375 LED driver.
  * Thermals: Real-time CPU temperature readout (`thermal_zone0` / `soc_max`).
  * Connectivity: MTP file transfer over USB, ADB sideload, and USB-OTG external drives.
* **AOSP & Custom ROM Flashing:** Full `update_engine_sideload` and dynamic partition resizing support for PixelOS, LineageOS, and GSI packages.
* **Built-in Root Suite:** Direct integration with Magisk v28.1 

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

* **sheikhmehraann** for maintainership and device-specific bringup.

