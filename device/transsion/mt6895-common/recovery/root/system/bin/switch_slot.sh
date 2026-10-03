#!/sbin/sh
# Active Boot Slot Switcher for Infinix GT 20 Pro (X6871)
# 29exop craft

BOOTCTL="/system/bin/bootctl"
if [ ! -x "$BOOTCTL" ]; then
    echo "[-] bootctl binary not found or not executable!"
    exit 1
fi

CURRENT=$($BOOTCTL get-current-slot)
CUR_SUFFIX=$($BOOTCTL get-suffix $CURRENT)

echo "[*] Current active slot: $CURRENT ($CUR_SUFFIX)"

if [ "$CURRENT" = "0" ]; then
    TARGET=1
    TGT_SUFFIX="_b"
else
    TARGET=0
    TGT_SUFFIX="_a"
fi

echo "[*] Switching active slot to: $TARGET ($TGT_SUFFIX)..."
$BOOTCTL set-active-boot-slot $TARGET
RET=$?

if [ $RET -eq 0 ]; then
    echo "[+] SUCCESS: Active boot slot set to $TARGET ($TGT_SUFFIX)!"
    echo "[*] Reboot recovery or system to boot into slot $TARGET."
else
    echo "[-] FAILED: bootctl returned exit code $RET"
    exit 1
fi
