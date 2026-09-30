# Infinix GT 20 Pro (X6871) Recovery Project

Unified recovery tree and build pipeline for the Infinix GT 20 Pro (`X6871` / `mt6895`).

## Verified Stock Device Identity
* **Device**: `Infinix-X6871`
* **Manufacturer**: `INFINIX`
* **Brand**: `Infinix`
* **Model**: `Infinix X6871`
* **Product Name**: `X6871-OP`
* **Commercial Name**: `Infinix GT 20 Pro`
* **SoC / Platform**: MediaTek Dimensity 8200 Ultimate (`mt6895` / `mt6896`)
* **Baseband / Bootloader**: `Infinix-X6871`
* **Fingerprint**: `Infinix/X6871-OP/Infinix-X6871:15/AP3A.240905.015.A2/180003:user/release-keys`
* **Security Patch Level**: `2026-07-01`
* **First API Level**: 31 (Android 12)
* **Active OS**: Transsion TOS 15 (Android 15)

## Boot & Partition Architecture
* **Partition Scheme**: Dynamic Partitions with Virtual A/B (VAB)
* **Boot Image Header Version**: 4 (GKI architecture)
* **Recovery Architecture**: `vendor_boot` ramdisk (`BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := true`)
* **Vendor Boot Partition Size**: 67,108,864 bytes (64 MB)
* **Page Size**: 4096 bytes
* **Kernel Commandline**: `bootopt=64S3,32N2,64N2`
* **Kernel Base**: `0x3fff8000`
* **Ramdisk Offset**: `0x26f08000`
* **Tags Offset**: `0x07c88000`
* **DTB Size**: 318,821 bytes
* **DTB Offset**: `0x07c88000`

## Repository Structure
```
├── configs/                  # Stock device configs from physical dump (getprop, cmdline, fstabs)
├── device/
│   ├── infinix/
│   │   └── Infinix-X6871/    # Device tree (AndroidProducts.mk, BoardConfig.mk, twrp_X6871.mk, fox.mk)
│   └── transsion/
│       └── mt6895-common/    # MT6895 common tree (BoardConfigCommon.mk, crypto, bootctrl, vintf)
├── prebuilt-images/          # Verified prebuilt recovery images (Stock DTB + 64M Padded) with checksums
├── scripts/                  # Build scripts and Go test bypass patches
├── tools/                    # Image unpacking, ramdisk inspection, and repacking scripts
└── .github/workflows/        # Automated CI/CD compilation pipeline
```

## Compilation
```bash
# In OrangeFox 12.1 root
source build/envsetup.sh
lunch twrp_X6871-eng
mka adbd vendorbootimage -j$(nproc)
```

## Deployment
```bash
fastboot flash vendor_boot vendor_boot.img
```
*Note: Do not execute `fastboot reboot recovery` directly. Power down the device and hold Power + Volume Up to trigger recovery boot.*
