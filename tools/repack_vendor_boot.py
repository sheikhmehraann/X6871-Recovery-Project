import os
import sys
import struct

def page_align(val, page_size=4096):
    return ((val + page_size - 1) // page_size) * page_size

def repack_vendor_boot(
    vendor_rd_path,
    recovery_rd_path,
    dtb_path,
    output_path,
    cmdline="bootopt=64S3,32N2,64N2",
    page_size=4096,
    kernel_addr=0x3fff8000,
    ramdisk_addr=0x26f08000,
    tags_addr=0x07c88000,
    dtb_addr=0x07000000
):
    with open(vendor_rd_path, "rb") as f:
        vendor_rd_data = f.read()

    with open(recovery_rd_path, "rb") as f:
        recovery_rd_data = f.read()

    with open(dtb_path, "rb") as f:
        dtb_data = f.read()

    # Combined vendor ramdisk: vendor_rd followed by recovery_rd
    offset_0 = 0
    size_0 = len(vendor_rd_data)
    offset_1 = size_0
    size_1 = len(recovery_rd_data)
    total_ramdisk = vendor_rd_data + recovery_rd_data

    # Table entries (v4 vendor ramdisk table):
    # struct vendor_ramdisk_table_entry_v4:
    # ramdisk_size(4), ramdisk_offset(4), ramdisk_type(4), ramdisk_name(32), board_id(64)
    # Entry 0: type 1 (PLATFORM/DEFAULT)
    entry_0 = struct.pack("<III32s64s", size_0, offset_0, 1, b"", b"")
    # Entry 1: type 2 (RECOVERY)
    entry_1 = struct.pack("<III32s64s", size_1, offset_1, 2, b"recovery", b"")
    table_data = entry_0 + entry_1

    # Header v4:
    # magic(8) = 'VNDRBOOT'
    # header_version(4) = 4
    # page_size(4) = 4096
    # kernel_addr(4)
    # ramdisk_addr(4)
    # vendor_ramdisk_size(4)
    # cmdline(2048)
    # tags_addr(4)
    # name(16)
    # header_size(4) = 2128
    # dtb_size(4)
    # dtb_addr(8)
    # vendor_ramdisk_table_size(4)
    # vendor_ramdisk_table_entry_num(4)
    # vendor_ramdisk_table_entry_size(4)
    # bootconfig_size(4) = 0
    hdr_sz = 2128
    hdr_ver = 4
    cmdline_bytes = cmdline.encode("ascii")[:2048].ljust(2048, b"\x00")
    board_name_bytes = b"".ljust(16, b"\x00")

    header = struct.pack(
        "<8sIIIII2048sI16sIIQIIII",
        b"VNDRBOOT",
        hdr_ver,
        page_size,
        kernel_addr,
        ramdisk_addr,
        len(total_ramdisk),
        cmdline_bytes,
        tags_addr,
        board_name_bytes,
        hdr_sz,
        len(dtb_data),
        dtb_addr,
        len(table_data),
        2,  # entry num
        108,  # entry size
        0  # bootconfig size
    )

    # Pad sections to page_size
    pad_header = b"\x00" * (page_align(len(header), page_size) - len(header))
    pad_ramdisk = b"\x00" * (page_align(len(total_ramdisk), page_size) - len(total_ramdisk))
    pad_dtb = b"\x00" * (page_align(len(dtb_data), page_size) - len(dtb_data))
    pad_table = b"\x00" * (page_align(len(table_data), page_size) - len(table_data))

    with open(output_path, "wb") as out_f:
        out_f.write(header + pad_header)
        out_f.write(total_ramdisk + pad_ramdisk)
        out_f.write(dtb_data + pad_dtb)
        out_f.write(table_data + pad_table)

    total_size = os.path.getsize(output_path)
    print(f"[+] Successfully repacked vendor_boot v4 image:")
    print(f"    Output: {output_path}")
    print(f"    Size: {total_size} bytes ({total_size / (1024*1024):.2f} MB)")
    print(f"    Vendor Ramdisk: {size_0} bytes")
    print(f"    Recovery Ramdisk: {size_1} bytes")
    print(f"    DTB: {len(dtb_data)} bytes")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python repack_vendor_boot.py <vendor_rd> <recovery_rd> <dtb> <out_img>")
        sys.exit(1)
    repack_vendor_boot(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
