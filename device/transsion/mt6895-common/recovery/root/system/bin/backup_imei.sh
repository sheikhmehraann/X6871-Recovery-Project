#!/sbin/sh
# IMEI & NVRAM One-Tap Safety Net Backup for Infinix GT 20 Pro (X6871)
# 29exop craft

BACKUP_ROOT="/sdcard/Fox/IMEI_BACKUP"
if [ ! -d "/sdcard" ]; then
    BACKUP_ROOT="/data/media/0/Fox/IMEI_BACKUP"
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TARGET_DIR="${BACKUP_ROOT}/IMEI_X6871_${TIMESTAMP}"
mkdir -p "$TARGET_DIR" 2>/dev/null

if [ ! -d "$TARGET_DIR" ]; then
    echo "[-] Cannot create backup directory: $TARGET_DIR"
    echo "[-] Ensure Internal Storage is decrypted!"
    exit 1
fi

echo "=========================================="
echo "  IMEI & NVRAM One-Tap Safety Net Backup  "
echo "  Target: $TARGET_DIR"
echo "=========================================="

PARTITIONS="nvram nvdata nvcfg protect1 protect2 proinfo transec seccfg"

for part in $PARTITIONS; do
    DEV="/dev/block/by-name/${part}"
    if [ -b "$DEV" ]; then
        echo "[*] Backing up ${part}..."
        dd if="$DEV" of="${TARGET_DIR}/${part}.img" bs=1M 2>/dev/null
        if [ $? -eq 0 ]; then
            sha256sum "${TARGET_DIR}/${part}.img" > "${TARGET_DIR}/${part}.img.sha256"
            echo "[+] ${part}: OK ($(du -h "${TARGET_DIR}/${part}.img" | cut -f1))"
        else
            echo "[-] ${part}: FAILED!"
        fi
    else
        echo "[!] Partition $DEV not found, skipping."
    fi
done

echo "=========================================="
echo "[+] IMEI & NVRAM Safety Net Backup complete!"
echo "[+] Saved to: $TARGET_DIR"
echo "=========================================="
