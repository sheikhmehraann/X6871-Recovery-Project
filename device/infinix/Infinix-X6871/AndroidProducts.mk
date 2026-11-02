#
# Copyright (C) 2026 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

PRODUCT_MAKEFILES := \
    $(LOCAL_DIR)/twrp_X6871.mk \
    $(LOCAL_DIR)/fox_X6871.mk \
    $(LOCAL_DIR)/pb_X6871.mk \
    $(LOCAL_DIR)/shrp_X6871.mk \
    $(LOCAL_DIR)/yarp_X6871.mk \
    $(LOCAL_DIR)/omni_X6871.mk

COMMON_LUNCH_CHOICES := \
    twrp_X6871-eng \
    fox_X6871-eng \
    fox_X6871-ap2a-eng \
    pb_X6871-eng \
    shrp_X6871-eng \
    yarp_X6871-eng \
    omni_X6871-eng
