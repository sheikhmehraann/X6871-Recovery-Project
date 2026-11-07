#
# Copyright (C) 2026 The Yet Another Recovery Project (YARP)
# YARP configuration for Infinix GT 20 Pro (X6871)
#

$(call inherit-product, device/infinix/X6871/device.mk)

PRODUCT_NAME := yarp_X6871
PRODUCT_DEVICE := X6871
PRODUCT_BRAND := Infinix
PRODUCT_MODEL := Infinix GT 20 Pro
PRODUCT_MANUFACTURER := INFINIX

# YARP Environment Configuration
YARP_DEVICE_CODE := X6871
YARP_MAINTAINER := sheikhmehraann
YARP_BUILD_TYPE := OFFICIAL
YARP_VERSION := 16.0
YARP_THEME := dark
YARP_FLASHLIGHT_PATH := /sys/class/torch/torch/torch_level
YARP_BATTERY_PATH := /sys/class/power_supply/battery
YARP_VIBRATOR_PATH := /sys/class/leds/vibrator_single/activate
YARP_CPU_TEMP_PATH := /sys/class/thermal/thermal_zone0/temp
YARP_USE_ZSTD := true
YARP_ENFORCE_PERMISSIVE := true

PRODUCT_BUILD_PROP_OVERRIDES += \
    PRODUCT_NAME="X6871" \
    PRODUCT_DEVICE="X6871" \
    PRODUCT_MODEL="Infinix GT 20 Pro" \
    PRODUCT_BRAND="Infinix" \
    PRODUCT_MANUFACTURER="INFINIX" \
    TARGET_DEVICE="X6871" \
    BUILD_FINGERPRINT="Infinix/X6871-IN/Infinix-X6871:16/BP2A.250605.031.A3/301550059:user/release-keys" \
    BUILD_DISPLAY_ID="X6871-16.3.0.155SP22(IN009PF001AZ)" \
    PRIVATE_BUILD_DESC="X6871-user 16 BP2A.250605.031.A3 release-keys"
