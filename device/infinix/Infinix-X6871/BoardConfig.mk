#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/infinix/Infinix-X6871

# Inherit from mt6895-common
include device/transsion/mt6895-common/BoardConfigCommon.mk

# Assert
TARGET_OTA_ASSERT_DEVICE := Infinix-X6871,X6871,X6871-OP,Infinix_X6871


# Init
TARGET_INIT_VENDOR_LIB := libinit_Infinix-X6871
TARGET_RECOVERY_DEVICE_MODULES := libinit_Infinix-X6871

# TWRP Configs
TW_DEVICE_VERSION := X6871_by_withmehraan
