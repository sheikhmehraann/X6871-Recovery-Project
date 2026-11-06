#
# Copyright (C) 2026 The Android Open Source Project
# SkyHawk Recovery Project configuration for Infinix GT 20 Pro (X6871)
#

$(call inherit-product, device/infinix/Infinix-X6871/device.mk)

PRODUCT_NAME := shrp_X6871
PRODUCT_DEVICE := X6871
PRODUCT_BRAND := Infinix
PRODUCT_MODEL := Infinix GT 20 Pro
PRODUCT_MANUFACTURER := INFINIX

# SkyHawk recovery configuration
SHRP_PATH := device/infinix/Infinix-X6871
SHRP_MAINTAINER := sheikhmehraann
SHRP_DEVICE_CODE := X6871
SHRP_EDL_MODE := 0
SHRP_EXTERNAL := /sdcard
SHRP_INTERNAL := /data/media/0
SHRP_OTG := /usb_otg
SHRP_FLASH := 1
SHRP_FONTS := default
SHRP_OFFICIAL := true
SHRP_DARK := true
SHRP_EXPRESS := true
SHRP_DEV := "sheikhmehraann"
SHRP_REC := /dev/block/by-name/vendor_boot
SHRP_REC_TYPE := vendor_boot
SHRP_CUSTOM_FLASHLIGHT := true
SHRP_CUSTOM_FLASHLIGHT_PATH := "/sys/devices/platform/11cb0000.i2c/i2c-7/7-0050/leds/torch/brightness"

PRODUCT_BUILD_PROP_OVERRIDES += \
    PRODUCT_NAME="X6871" \
    PRODUCT_DEVICE="X6871" \
    PRODUCT_MODEL="Infinix GT 20 Pro" \
    PRODUCT_BRAND="Infinix" \
    PRODUCT_MANUFACTURER="INFINIX" \
    TARGET_DEVICE="X6871" \
    BUILD_FINGERPRINT="Infinix/X6871-OP/Infinix-X6871:15/AP3A.240905.015.A2/180003:user/release-keys" \
    BUILD_DISPLAY_ID="X6871-15.1.2.180SP05(OP001PF001AZ)" \
    PRIVATE_BUILD_DESC="X6871-user 15 AP3A.240905.015.A2 release-keys"
