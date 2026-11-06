#!/system/bin/sh
# Real rear flashlight bridge for Infinix GT 20 Pro (X6871)
TORCH_NODE="/sys/devices/virtual/flashlight_core/flashlight/flashlight_torch"
FIFO="/flashlight/brightness"

while [ ! -e "$TORCH_NODE" ]; do
    sleep 1
done
chmod 0666 "$TORCH_NODE"

while true; do
    while read -r val; do
        if [ "$val" -gt 0 ] 2>/dev/null; then
            echo "0 0 0 1" > "$TORCH_NODE"
        else
            echo "0 0 0 0" > "$TORCH_NODE"
        fi
    done < "$FIFO"
    sleep 0.1
done
