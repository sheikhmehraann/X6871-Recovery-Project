import os
import sys
import struct
import re

def sanitize_filename(name):
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '', name)
    return clean if clean else "entry"

def unpack_vendor_boot(img_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(img_path, "rb") as f:
        magic = f.read(8)
        if not magic.startswith(b"VNDRBOOT"):
            print(f"[!] {img_path} is not a vendor_boot image (magic: {magic})")
            return False

        hdr_ver, page_size, k_addr, rd_addr, rd_sz = struct.unpack("<IIIII", f.read(20))
        cmdline = f.read(2048).decode("ascii", errors="ignore").strip("\x00")
        tags_addr, name, hdr_sz, dtb_sz, dtb_addr = struct.unpack("<I16sIIQ", f.read(36))
        name = name.decode("ascii", errors="ignore").strip("\x00")

        tbl_sz = tbl_num = tbl_ent_sz = bc_sz = 0
        if hdr_ver >= 4:
            tbl_sz, tbl_num, tbl_ent_sz, bc_sz = struct.unpack("<IIII", f.read(16))

        print(f"[+] Unpacking {os.path.basename(img_path)}:")
        print(f"    Header Version: {hdr_ver}")
        print(f"    Page Size: {page_size}")
        print(f"    Vendor Ramdisk Size: {rd_sz} bytes")
        print(f"    DTB Size: {dtb_sz} bytes")
        print(f"    Table Entries: {tbl_num}")
        print(f"    Cmdline: {cmdline}")

        def page_align(val):
            return ((val + page_size - 1) // page_size) * page_size

        hdr_pages = page_align(hdr_sz)
        rd_pages = page_align(rd_sz)
        dtb_pages = page_align(dtb_sz)

        # Read full vendor ramdisk
        f.seek(hdr_pages)
        ramdisk_data = f.read(rd_sz)
        rd_path = os.path.join(out_dir, "vendor_ramdisk.img")
        with open(rd_path, "wb") as rf:
            rf.write(ramdisk_data)

        # Read DTB
        f.seek(hdr_pages + rd_pages)
        dtb_data = f.read(dtb_sz)
        dtb_path = os.path.join(out_dir, "dtb.img")
        with open(dtb_path, "wb") as df:
            df.write(dtb_data)

        # Read Ramdisk Table if v4
        if tbl_sz > 0 and tbl_num > 0 and tbl_ent_sz >= 108:
            f.seek(hdr_pages + rd_pages + dtb_pages)
            tbl_data = f.read(tbl_sz)
            print(f"    [+] Parsing {tbl_num} vendor ramdisk table entries...")
            for i in range(tbl_num):
                ent_offset = i * tbl_ent_sz
                ent_data = tbl_data[ent_offset:ent_offset + tbl_ent_sz]
                if len(ent_data) >= 108:
                    rd_size_i, rd_offset_i, rd_type_i = struct.unpack("<III", ent_data[:12])
                    raw_name = ent_data[12:12+32].decode("ascii", errors="ignore").split("\x00")[0]
                    safe_name = sanitize_filename(raw_name)
                    print(f"        Entry {i}: type={rd_type_i}, name='{safe_name}', size={rd_size_i}, offset={rd_offset_i}")
                    if rd_offset_i + rd_size_i <= len(ramdisk_data):
                        sub_rd_data = ramdisk_data[rd_offset_i:rd_offset_i + rd_size_i]
                        sub_rd_path = os.path.join(out_dir, f"ramdisk_{i}_type{rd_type_i}_{safe_name}.cpio")
                        with open(sub_rd_path, "wb") as srf:
                            srf.write(sub_rd_data)
                        print(f"        [+] Saved sub-ramdisk {sub_rd_path} ({len(sub_rd_data)} bytes)")

        # Save metadata
        with open(os.path.join(out_dir, "header_info.txt"), "w") as mf:
            mf.write(f"header_version={hdr_ver}\n")
            mf.write(f"page_size={page_size}\n")
            mf.write(f"kernel_addr={hex(k_addr)}\n")
            mf.write(f"ramdisk_addr={hex(rd_addr)}\n")
            mf.write(f"cmdline={cmdline}\n")
            mf.write(f"tags_addr={hex(tags_addr)}\n")
            mf.write(f"board_name={name}\n")
            mf.write(f"dtb_size={dtb_sz}\n")
            mf.write(f"dtb_addr={hex(dtb_addr)}\n")

        return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python unpack_vendor_boot.py <image_path> <output_dir>")
        sys.exit(1)
    unpack_vendor_boot(sys.argv[1], sys.argv[2])
