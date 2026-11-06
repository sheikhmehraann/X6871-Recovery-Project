#!/bin/bash
# vendorsetup.sh for YARP 16.0 — Infinix GT 20 Pro (X6871)

if command -v add_lunch_combo >/dev/null 2>&1; then
    add_lunch_combo yarp_X6871-eng 2>/dev/null || true
fi

export ALLOW_MISSING_DEPENDENCIES=true
export YARP_DEVICE_CODE="X6871"
export YARP_MAINTAINER="sheikhmehraann"
export YARP_BUILD_TYPE="OFFICIAL"
export YARP_VERSION="16.0"
export YARP_THEME="dark"
export YARP_FLASHLIGHT_PATH="/sys/class/torch/torch/torch_level"
export YARP_BATTERY_PATH="/sys/class/power_supply/battery"
export YARP_VIBRATOR_PATH="/sys/class/leds/vibrator_single/activate"
export YARP_CPU_TEMP_PATH="/sys/class/thermal/thermal_zone0/temp"
export YARP_USE_ZSTD=true
export YARP_ENFORCE_PERMISSIVE=true
