#
# Copyright (C) 2026 The OrangeFox Recovery Project
# OrangeFox Recovery Project configuration for Infinix GT 20 Pro (X6871)
#

$(call inherit-product, device/infinix/X6871/device.mk)
$(call inherit-product, device/infinix/X6871/fox.mk)

PRODUCT_NAME := fox_X6871
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
    BUILD_FINGERPRINT="Infinix/X6871-IN/Infinix-X6871:16/BP2A.250605.031.A3/301550059:user/release-keys" \
    BUILD_DISPLAY_ID="X6871-16.3.0.155SP22(IN009PF001AZ)" \
    PRIVATE_BUILD_DESC="X6871-user 16 BP2A.250605.031.A3 release-keys"
