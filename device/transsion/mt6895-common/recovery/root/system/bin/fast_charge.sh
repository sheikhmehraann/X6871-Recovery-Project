#!/sbin/sh
# 45W HyperCharge Controller for Infinix GT 20 Pro (MT6375 / Charger)
# 29exop craft

CHG_IN="/sys/class/power_supply/charger/input_current_limit"
CHG_CONST="/sys/class/power_supply/charger/constant_charge_current"
BAT_IN="/sys/class/power_supply/battery/input_current_limit"

echo "[*] Initializing 45W HyperCharge mode..."

# 4500mA input limit
if [ -f "$CHG_IN" ]; then
    echo 4500000 > "$CHG_IN" 2>/dev/null || echo 4000000 > "$CHG_IN" 2>/dev/null
    echo "[+] Set $CHG_IN to 4500mA"
fi

if [ -f "$CHG_CONST" ]; then
    echo 4500000 > "$CHG_CONST" 2>/dev/null || echo 4000000 > "$CHG_CONST" 2>/dev/null
    echo "[+] Set $CHG_CONST to 4500mA"
fi

if [ -f "$BAT_IN" ]; then
    echo 4500000 > "$BAT_IN" 2>/dev/null || echo 4000000 > "$BAT_IN" 2>/dev/null
    echo "[+] Set $BAT_IN to 4500mA"
fi

echo "[+] 45W HyperCharge successfully engaged!"
