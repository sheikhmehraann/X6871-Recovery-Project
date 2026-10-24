#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from X6871 device
$(call inherit-product, device/infinix/X6871/device.mk)

# Inherit some common TWRP stuff.
$(call inherit-product, vendor/twrp/config/common.mk)

# Include TWRP props.
$(call inherit-product, device/infinix/X6871/twrp.mk)

# Include Fox props.
$(call inherit-product, device/infinix/X6871/fox.mk)

# Product Specifics (100% Matched to Stock Infinix GT 20 Pro X6871)
PRODUCT_NAME := twrp_X6871
PRODUCT_DEVICE := Infinix-X6871
PRODUCT_BRAND := Infinix
PRODUCT_MODEL := Infinix X6871
PRODUCT_MANUFACTURER := INFINIX

PRODUCT_GMS_CLIENTID_BASE := android-transsion
