#!/bin/bash
# vendorsetup.sh for PitchBlack Recovery — Infinix GT 20 Pro (X6871)

if command -v add_lunch_combo >/dev/null 2>&1; then
    add_lunch_combo pb_X6871-eng 2>/dev/null || true
fi

export ALLOW_MISSING_DEPENDENCIES=true
export PB_DEVICE_SPECIFICATION="Infinix GT 20 Pro (X6871)"
export PB_TORCH_PATH="/sys/class/torch/torch/torch_level"
export PB_BATTERY_PATH="/sys/class/power_supply/battery"
export PB_VIBRATOR_PATH="/sys/class/leds/vibrator_single/activate"
export PB_BUILD_TYPE="OFFICIAL"
export PBRP_MAINTAINER="sheikhmehraann"
export PBRP_BRANCH="16.0"
export PBRP_STATUS="STABLE"
