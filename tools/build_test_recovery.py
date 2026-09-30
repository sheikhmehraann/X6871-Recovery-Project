import os
import sys
import shutil
import subprocess
import lz4.block
import struct
from repack_vendor_boot import repack_vendor_boot

PROJECT_DIR = r"C:\Users\Admin\Videos\Github\X6871-Recovery-Project"
DEVICE_TREE = os.path.join(PROJECT_DIR, "X6871-Latest-RecoveryProject")
TOOLS_DIR = os.path.join(PROJECT_DIR, "tools")
TEMP_DIR = os.path.join(PROJECT_DIR, "scriptstempfiles")

def cpio_pack(source_dir, output_cpio):
    """Packs a directory into an SVR4 (newc) CPIO archive."""
    with open(output_cpio, "wb") as f_out:
        ino = 720
        # Walk directory
        for root, dirs, files in os.walk(source_dir):
            # Sort for reproducibility
            dirs.sort()
            files.sort()
            
            rel_dir = os.path.relpath(root, source_dir).replace("\\", "/")
            if rel_dir != ".":
                # Directory entry
                write_cpio_entry(f_out, rel_dir + "/", b"", 0o040755, ino)
                ino += 1
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, source_dir).replace("\\", "/")
                with open(file_path, "rb") as content_f:
                    content = content_f.read()
                # Determine mode (scripts/binaries executable)
                mode = 0o100755 if (file.endswith((".sh", ".rc", ".py")) or "bin" in rel_path) else 0o100644
                write_cpio_entry(f_out, rel_path, content, mode, ino)
                ino += 1
        
        # Write trailer
        write_cpio_entry(f_out, "TRAILER!!!", b"", 0, ino)

def write_cpio_entry(f, name, data, mode, ino):
    name_bytes = name.encode("utf-8") + b"\x00"
    namesize = len(name_bytes)
    filesize = len(data)
    
    header = f"070701{ino:08X}{mode:08X}{0:08X}{0:08X}{1:08X}{0:08X}{filesize:08X}{0:08X}{0:08X}{0:08X}{0:08X}{namesize:08X}{0:08X}".encode("ascii")
    
    f.write(header)
    f.write(name_bytes)
    # Pad header + name to 4 bytes
    pad_hn = (4 - ((len(header) + namesize) % 4)) % 4
    f.write(b"\x00" * pad_hn)
    
    f.write(data)
    # Pad data to 4 bytes
    pad_data = (4 - (filesize % 4)) % 4
    f.write(b"\x00" * pad_data)

def compress_lz4_legacy(raw_cpio_path, lz4_out_path):
    """Compresses data using Android's legacy LZ4 format (magic 0x184c2102 + 8MB blocks)."""
    with open(raw_cpio_path, "rb") as f:
        raw_data = f.read()
    
    BLOCK_SIZE = 8 * 1024 * 1024 # 8MB
    with open(lz4_out_path, "wb") as f_out:
        f_out.write(b"\x02!L\x18") # LZ4 legacy magic
        offset = 0
        while offset < len(raw_data):
            chunk = raw_data[offset:offset + BLOCK_SIZE]
            offset += len(chunk)
            compressed_block = lz4.block.compress(chunk, mode='fast', store_size=False)
            f_out.write(struct.pack("<I", len(compressed_block)))
            f_out.write(compressed_block)
    print(f"[+] Compressed {raw_cpio_path} ({len(raw_data)} bytes) -> {lz4_out_path} ({os.path.getsize(lz4_out_path)} bytes)")

def build_test_recovery():
    print("=" * 60)
    print("Building OrangeFox Test Boot Recovery for Infinix X6871")
    print("=" * 60)
    
    rd_extracted = os.path.join(TEMP_DIR, "unpacked_fox_rd", "extracted")
    if not os.path.exists(rd_extracted):
        print(f"[-] Extracted ramdisk directory not found: {rd_extracted}")
        return False
    
    # 1. Update files from our device tree
    print("[+] Injecting updated device tree files...")
    
    # recovery.fstab
    fstab_src = os.path.join(DEVICE_TREE, "recovery.fstab")
    fstab_dst = os.path.join(rd_extracted, "system", "etc", "recovery.fstab")
    shutil.copy2(fstab_src, fstab_dst)
    print("    - Copied updated recovery.fstab")
    
    # init scripts
    root_src = os.path.join(DEVICE_TREE, "recovery", "root")
    for item in os.listdir(root_src):
        src_path = os.path.join(root_src, item)
        dst_path = os.path.join(rd_extracted, item)
        if os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)
            print(f"    - Copied {item} to ramdisk root")
    
    # 2. Pack updated ramdisk to CPIO
    print("\n[+] Packing updated recovery ramdisk to CPIO...")
    new_cpio = os.path.join(TEMP_DIR, "updated_recovery.cpio")
    cpio_pack(rd_extracted, new_cpio)
    print(f"    [+] Created {new_cpio} ({os.path.getsize(new_cpio)} bytes)")
    
    # 3. Compress with LZ4 legacy
    print("\n[+] Compressing with LZ4 legacy format...")
    new_lz4 = os.path.join(TEMP_DIR, "updated_recovery.cpio.lz4")
    compress_lz4_legacy(new_cpio, new_lz4)
    
    # 4. Repack vendor_boot v4
    print("\n[+] Repacking vendor_boot image...")
    vendor_rd = os.path.join(TEMP_DIR, "unpacked_fox", "ramdisk_0_type1_entry.cpio")
    dtb = os.path.join(DEVICE_TREE, "prebuilt", "dtb.img")
    final_output = os.path.join(PROJECT_DIR, "OrangeFox-X6871-TestBoot.img")
    
    repack_vendor_boot(vendor_rd, new_lz4, dtb, final_output)
    
    print("\n" + "=" * 60)
    print(f"[SUCCESS] Ready for testing!")
    print(f"Output File: {final_output}")
    print(f"Flash Command: fastboot flash vendor_boot {os.path.basename(final_output)}")
    print(f"Boot Key: Hold Power + Volume Up")
    print("=" * 60)
    return True

if __name__ == "__main__":
    build_test_recovery()
