#!/sbin/sh
# IMEI & NVRAM One-Tap Safety Net Restore for Infinix GT 20 Pro (X6871)
# 29exop craft

BACKUP_ROOT="/sdcard/Fox/IMEI_BACKUP"
if [ ! -d "$BACKUP_ROOT" ]; then
    BACKUP_ROOT="/data/media/0/Fox/IMEI_BACKUP"
fi

# Find latest backup
LATEST_BACKUP=$(ls -td ${BACKUP_ROOT}/IMEI_X6871_* 2>/dev/null | head -n 1)

if [ -z "$LATEST_BACKUP" ] || [ ! -d "$LATEST_BACKUP" ]; then
    echo "[-] No IMEI/NVRAM backup found in $BACKUP_ROOT!"
    exit 1
fi

echo "=========================================="
echo "  IMEI & NVRAM One-Tap Safety Net Restore "
echo "  Source: $LATEST_BACKUP"
echo "=========================================="

PARTITIONS="nvram nvdata nvcfg protect1 protect2 proinfo transec seccfg"

for part in $PARTITIONS; do
    IMG="${LATEST_BACKUP}/${part}.img"
    DEV="/dev/block/by-name/${part}"
    if [ -f "$IMG" ] && [ -b "$DEV" ]; then
        echo "[*] Restoring ${part}..."
        dd if="$IMG" of="$DEV" bs=1M conv=fsync 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "[+] ${part}: Restored successfully!"
        else
            echo "[-] ${part}: Restore failed!"
        fi
    fi
done

echo "=========================================="
echo "[+] IMEI & NVRAM Restore complete!"
echo "=========================================="
