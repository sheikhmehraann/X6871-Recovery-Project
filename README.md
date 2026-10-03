# OrangeFox Recovery for Infinix GT 20 Pro (X6871)

Custom OrangeFox R12.0 recovery built for the Infinix GT 20 Pro. Runs on the Dimensity 8200 Ultimate (mt6895), Android 15, Virtual A/B with dynamic partitions. Recovery lives in `vendor_boot` — the GKI boot image stays untouched.

Built and maintained by [@withmehraan](https://t.me/Gt20ProINUpdates).

## Device

| | |
|---|---|
| Codename | X6871 |
| SoC | MediaTek Dimensity 8200 Ultimate (mt6895/mt6896) |
| OS | Android 15, XOS 15 (Transsion TOS) |
| Partition Scheme | Virtual A/B, Dynamic Partitions (super) |
| Recovery Location | vendor_boot (Header v4, 64 MB) |
| Fingerprint | `Infinix/X6871-OP/Infinix-X6871:15/AP3A.240905.015.A2/180003:user/release-keys` |
| Security Patch | 2026-07-01 |

## What Works

- Decryption (FBEv2, wrappedkey, metadata encryption)
- MTP, ADB sideload
- Haptic feedback (AW8697 driver)
- Flashlight (OCP81375 camera torch)
- CPU temperature readout (thermal_zone0)
- USB OTG storage
- All 82 device partitions mounted and accessible
- Native splash changer (patches vendor_boot directly, Header v4 aware)
- Stock device identity (shows real Infinix fingerprint, not ALPS)
- AVB 2.0 disable addon (slot-aware, works on A/B)
- Active slot switcher
- 45W fast charge toggle (MT6375 charger IC)
- CPU governor profiles (tri-cluster: turbo / balanced / eco)
- IMEI and NVRAM backup/restore (nvram, nvdata, nvcfg, protect1, protect2, proinfo)
- Dynamic partition mapper symlinks
- Root suite: Magisk v28.1, KernelSU v3.3.0, APatch 11224

## What Doesn't Work

- SD card — this phone doesn't have a slot, so nothing to fix there

## Flashing

Both slots, from fastboot:

```
fastboot flash vendor_boot_a vendor_boot.img
fastboot flash vendor_boot_b vendor_boot.img
```

Then power off and boot to recovery with Power + Volume Up.

Do NOT flash `boot`. Recovery is in `vendor_boot` only.

## Building from Source

CI builds automatically on push to `main`. To build locally:

```
# sync OrangeFox 14.1 minimal manifest
repo init -u https://gitlab.com/nicholaschum/AnyKernel3.git -b fox_14.1
repo sync -j$(nproc) --force-sync

# drop device trees
cp -r device/ <fox_root>/device/

# run patches
python3 scripts/patch_ofox.py

# build
source build/envsetup.sh
lunch twrp_X6871-eng
mka adbd vendorbootimage -j$(nproc)
```

Output lands at `out/target/product/X6871/vendor_boot.img`.

The GitHub Actions workflow handles all of this — just push to `main` and grab the release.

## Repo Layout

```
.github/workflows/     CI pipeline (builds on push, creates GitHub release)
configs/               Stock device dumps — getprop, fstabs, file_contexts, partition maps
device/
  infinix/X6871/       Device tree — BoardConfig, fstab, twrp.flags, prebuilt kernel/dtb
  transsion/mt6895/    Common tree — init.rc, hardware scripts, maintainer page
device_dump/           Raw partition and mount info pulled from device
scripts/               Build scripts, patch_ofox.py (splash/identity/AVB patches)
tools/                 Vendor boot unpack/repack utilities
prebuilt-images/       Old intermediate images (cleanup candidate)
```

## Links

- Telegram Updates: https://t.me/Gt20ProINUpdates
- Telegram Discussion: https://t.me/Gt20ProIN
