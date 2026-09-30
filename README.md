# Infinix GT 20 Pro (X6871) — OrangeFox Recovery Project

Automated CI/CD build repository for compiling OrangeFox Recovery for the Infinix GT 20 Pro (`X6871` / MediaTek Dimensity 8200).

## Device Information
* **Device:** Infinix GT 20 Pro
* **Codename:** `X6871` / `Infinix-X6871`
* **Chipset:** MediaTek Dimensity 8200 (`mt6895` / `mt6896`)
* **Partition Scheme:** Virtual A/B (VAB) with GKI Header v4
* **Recovery Target:** `vendor_boot`

## Flash Instructions
```bash
fastboot flash vendor_boot vendor_boot.img
```
*Do not use `fastboot reboot recovery` directly. Use Power + Volume Up to enter recovery.*
