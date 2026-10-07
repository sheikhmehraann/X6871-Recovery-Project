#
#This file is part of the OrangeFox Recovery Project
# Copyright (C) 2024-2025 The OrangeFox Recovery Project
#
#OrangeFox is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#any later version.
#
#OrangeFox is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
# This software is released under GPL version 3 or any later version.
#See <http://www.gnu.org/licenses/>.
#
# Please maintain this if you use this script or any part of it
#

# screen settings (Infinix GT 20 Pro 1080x2436 AMOLED)
OF_SCREEN_H := 2436
OF_STATUS_H := 90
OF_STATUS_INDENT_LEFT := 48
OF_ALLOW_DISABLE_NAVBAR := 1
OF_SETTINGS_CUSTOM_PATH := /sdcard/Fox
OF_CHECK_OVERWRITE_ATTEMPTS := 1
OF_ALLOW_DISABLE_FORCE_ENCRYPTION := 1
OF_SUPPORT_ALL_PAYLOAD_EXTRACTOR := 1
OF_SUPPORT_ALL_BLOCK_SU_MOUNTS := 1
OF_DYNAMIC_FULL_SIZE := 12426428416
OF_CLOCK_POS := 0

# Flashlight (MediaTek OCP81375 camera flash driver)
OF_FLASHLIGHT_ENABLE := 1
OF_FL_PATH1 := /sys/class/torch/torch/torch_level
OF_FL_PATH2 := /sys/devices/virtual/torch/torch/torch_level
OF_USE_GREEN_LED := 0


# Backup & Storage
OF_QUICK_BACKUP_LIST := /boot;/data;
OF_ENABLE_LPTOOLS := 1
OF_ENABLE_ALL_PARTITION_TOOLS := 1
OF_NO_TREBLE_COMPATIBILITY_CHECK := 1
OF_OPTIONS_LIST_NUM := 9
OF_UNBIND_SDCARD_F2FS := 1
OF_WIPE_METADATA_AFTER_DATAFORMAT := 1
OF_BIND_MOUNT_SDCARD_ON_FORMAT := 1
OF_LOOP_DEVICE_ERRORS_TO_LOG := 1
# OF_USE_LZ4_COMPRESSION := 0 (Standard GZIP for 64MB partition budget)
OF_MAINTAINER := withmehraan
FOX_TARGET_DEVICES := X6871,Infinix-X6871,Infinix_X6871,X6871-OP
FOX_DEVICE_MODEL := Infinix GT 20 Pro
FOX_COMPATIBILITY_DEVICE := Infinix GT 20 Pro (Infinix X6871)

# Magisk & AVB
OF_USE_MAGISKBOOT := 1
OF_USE_MAGISKBOOT_FOR_ALL_PATCHES := 1
OF_PATCH_AVB20 := 1

# Advanced Security & Decryption

OF_ADVANCED_SECURITY := 1
OF_USE_TWRP_SAR_DETECT := 1
OF_SUPPORT_OZIP_DECRYPTION := 1
OF_FBE_METADATA_MOUNT_IGNORE := 0
OF_SKIP_DECRYPTED_ADOPTED_STORAGE := 1
OF_SPLASH_MAX_SIZE := 8192
OF_USE_AIDL_BOOT_CONTROL := 1
OF_SUPPORT_VBMETA_AVB2_PATCHING := 1
OF_FORCE_PREBUILT_KERNEL := 1
