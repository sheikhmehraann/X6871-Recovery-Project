#
# Copyright (C) 2026 The Android Open Source Project
# Omni / TWRP configuration for Infinix GT 20 Pro (X6871)
#

$(call inherit-product, device/infinix/Infinix-X6871/device.mk)

PRODUCT_NAME := omni_X6871
PRODUCT_DEVICE := X6871
PRODUCT_BRAND := Infinix
PRODUCT_MODEL := Infinix GT 20 Pro
PRODUCT_MANUFACTURER := INFINIX

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
