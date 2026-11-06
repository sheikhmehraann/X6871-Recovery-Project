#!/bin/bash
# vendorsetup.sh for TWRP 16.0 — Infinix GT 20 Pro (X6871)

if command -v add_lunch_combo >/dev/null 2>&1; then
    add_lunch_combo twrp_X6871-eng 2>/dev/null || true
    add_lunch_combo omni_X6871-eng 2>/dev/null || true
fi

export ALLOW_MISSING_DEPENDENCIES=true
export LC_ALL="C"
export USE_CCACHE=1
export TW_DEVICE_VERSION="X6871_TWRP16"
