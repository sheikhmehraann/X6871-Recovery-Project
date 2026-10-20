# Device inputs: kernel-matched modules with their original load metadata,
# and stock first-stage fstabs. Recovery-only touch modules remain separate.
ifeq ($(strip $(MTK_VENDOR16_RAMDISK_MODULES_DIR)),)
$(error MTK_VENDOR16_RAMDISK_MODULES_DIR must name this device's module directory)
endif
ifeq ($(strip $(MTK_VENDOR16_RAMDISK_FSTABS)),)
$(error MTK_VENDOR16_RAMDISK_FSTABS must name this device's first-stage fstab files)
endif

PRODUCT_PACKAGES += init_first_stage

MTK_VENDOR16_RAMDISK_MODULE_FILES := \
    $(wildcard $(MTK_VENDOR16_RAMDISK_MODULES_DIR)/*.ko) \
    $(wildcard $(MTK_VENDOR16_RAMDISK_MODULES_DIR)/modules.*)
PRODUCT_COPY_FILES += $(foreach file,$(MTK_VENDOR16_RAMDISK_MODULE_FILES), \
    $(file):$(TARGET_COPY_OUT_VENDOR_RAMDISK)/lib/modules/$(notdir $(file)))
PRODUCT_COPY_FILES += $(foreach file,$(MTK_VENDOR16_RAMDISK_MODULE_FILES), \
    $(file):$(TARGET_RECOVERY_ROOT_OUT)/vendor/lib/modules/$(notdir $(file)))
PRODUCT_COPY_FILES += $(foreach file,$(MTK_VENDOR16_RAMDISK_FSTABS), \
    $(file):$(TARGET_COPY_OUT_VENDOR_RAMDISK)/first_stage_ramdisk/$(notdir $(file)))

# Goodix touch controller firmware & configuration
GOODIX_FW_DIR := $(DEVICE_PATH)/recovery/root/vendor/firmware
PRODUCT_COPY_FILES += \
    $(GOODIX_FW_DIR)/goodix_firmware.bin:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/odm/firmware/goodix_firmware.bin \
    $(GOODIX_FW_DIR)/goodix_firmware.bin:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/vendor/firmware/goodix_firmware.bin \
    $(GOODIX_FW_DIR)/goodix_cfg_group.bin:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/odm/firmware/goodix_cfg_group.bin \
    $(GOODIX_FW_DIR)/goodix_cfg_group.bin:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/vendor/firmware/goodix_cfg_group.bin \
    $(GOODIX_FW_DIR)/goodix_firmware.bin:$(TARGET_RECOVERY_ROOT_OUT)/odm/firmware/goodix_firmware.bin \
    $(GOODIX_FW_DIR)/goodix_firmware.bin:$(TARGET_RECOVERY_ROOT_OUT)/vendor/firmware/goodix_firmware.bin \
    $(GOODIX_FW_DIR)/goodix_cfg_group.bin:$(TARGET_RECOVERY_ROOT_OUT)/odm/firmware/goodix_cfg_group.bin \
    $(GOODIX_FW_DIR)/goodix_cfg_group.bin:$(TARGET_RECOVERY_ROOT_OUT)/vendor/firmware/goodix_cfg_group.bin
