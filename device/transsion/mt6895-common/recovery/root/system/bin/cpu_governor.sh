#!/sbin/sh
# Dimensity 8200 Tri-Cluster Governor Profile Controller
# Policy 0: 4x Cortex-A55 @ 2.0 GHz
# Policy 4: 3x Cortex-A78 @ 3.0 GHz
# Policy 7: 1x Cortex-A78 @ 3.1 GHz
# 29exop craft

MODE="$1"

if [ -z "$MODE" ]; then
    echo "Usage: $0 <eco|balanced|turbo>"
    exit 1
fi

case "$MODE" in
    eco|powersave)
        GOV="powersave"
        DESC="Eco / Cool Mode (Locked to low frequency)"
        ;;
    turbo|performance)
        GOV="performance"
        DESC="Turbo Max Performance (3.1 GHz locked for fast backup/restore)"
        ;;
    balanced|schedutil|*)
        GOV="schedutil"
        DESC="Balanced Dynamic Scaling"
        ;;
esac

echo "[*] Applying Dimensity 8200 Profile: $DESC ($GOV)..."

# Apply across all cpufreq policies
for p in 0 4 7; do
    POL="/sys/devices/system/cpu/cpufreq/policy${p}/scaling_governor"
    if [ -f "$POL" ]; then
        echo "$GOV" > "$POL" 2>/dev/null
    fi
done

# Apply across individual CPU cores
for c in 0 1 2 3 4 5 6 7; do
    CORE="/sys/devices/system/cpu/cpu${c}/cpufreq/scaling_governor"
    if [ -f "$CORE" ]; then
        echo "$GOV" > "$CORE" 2>/dev/null
    fi
done

echo "[+] Profile successfully applied: $DESC"
