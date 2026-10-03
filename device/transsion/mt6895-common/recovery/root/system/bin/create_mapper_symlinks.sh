#!/sbin/sh
# Direct Dynamic Partition Mapper Symlink Creator
# Maps unslotted names (/dev/block/mapper/system) to active slot (/dev/block/mapper/system_a)
# 29exop craft

SLOT=$(getprop ro.boot.slot_suffix)
[ -z "$SLOT" ] && SLOT="_a"

MAPPER_DIR="/dev/block/mapper"

if [ ! -d "$MAPPER_DIR" ]; then
    exit 0
fi

DYNAMIC_PARTS="system vendor product system_ext vendor_dlkm odm_dlkm tr_product tr_preload tr_carrier tr_company tr_mi tr_overlayfs tr_region tr_theme"

for part in $DYNAMIC_PARTS; do
    SLOTTED="${MAPPER_DIR}/${part}${SLOT}"
    UNSLOTTED="${MAPPER_DIR}/${part}"
    if [ -e "$SLOTTED" ] && [ ! -e "$UNSLOTTED" ]; then
        ln -sf "$SLOTTED" "$UNSLOTTED" 2>/dev/null
    fi
done

exit 0
