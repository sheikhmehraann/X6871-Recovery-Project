#
# Copyright (C) 2026 The Android Open Source Project
# AndroidProducts.mk for Infinix GT 20 Pro (X6871)
# Supports TWRP, OrangeFox, PitchBlack, and SkyHawk recoveries
#

PRODUCT_MAKEFILES := \
    $(LOCAL_DIR)/twrp_X6871.mk \
    $(LOCAL_DIR)/omni_X6871.mk \
    $(LOCAL_DIR)/fox_X6871.mk \
    $(LOCAL_DIR)/pb_X6871.mk \
    $(LOCAL_DIR)/shrp_X6871.mk

COMMON_LUNCH_CHOICES := \
    twrp_X6871-eng \
    twrp_X6871-userdebug \
    omni_X6871-eng \
    omni_X6871-userdebug \
    fox_X6871-eng \
    fox_X6871-userdebug \
    pb_X6871-eng \
    pb_X6871-userdebug \
    shrp_X6871-eng \
    shrp_X6871-userdebug
