import struct
import os
import io
import zstandard as zstd
import gzip
import lz4.block

def page_align(val, page_size=4096):
    return (val + page_size - 1) & ~(page_size - 1)

def repack(stock_path, built_path, output_path):
    print(f"Reading stock vendor_boot: {stock_path}")
    if stock_path.endswith('.gz'):
        with gzip.open(stock_path, 'rb') as gz_f:
            stock_bytes = gz_f.read()
        stock_file = io.BytesIO(stock_bytes)
    else:
        stock_file = open(stock_path, 'rb')
        
    try:
        stock_hdr = stock_file.read(4096)
        magic, v, page_size, k_addr, r_addr, stock_r_size = struct.unpack_from('<8sIIIII', stock_hdr, 0)
        cmdline = stock_hdr[28:28+2048].split(b'\x00')[0]
        tags_addr, name, hdr_size, dtb_size, dtb_addr = struct.unpack_from('<I16sIIQ', stock_hdr, 28+2048)
        table_size, table_entry_num, table_entry_size, bootconfig_size = struct.unpack_from('<IIII', stock_hdr, 2112)
        
        offset_ramdisk = page_size
        offset_dtb = offset_ramdisk + page_align(stock_r_size, page_size)
        offset_table = offset_dtb + page_align(dtb_size, page_size)
        offset_bootconfig = offset_table + page_align(table_size, page_size)
        
        # Read DTB
        stock_file.seek(offset_dtb)
        dtb_data = stock_file.read(dtb_size)
        
        # Read table to find fragment 0
        stock_file.seek(offset_table)
        table_data = stock_file.read(table_size)
        frag0_size, frag0_offset, frag0_type = struct.unpack_from('<III', table_data, 0)
        
        stock_file.seek(offset_ramdisk + frag0_offset)
        raw_frag0_data = stock_file.read(frag0_size)
        
        # Read stock bootconfig
        stock_file.seek(offset_bootconfig)
        raw_bc = stock_file.read(bootconfig_size)
        bc_str = raw_bc.decode('utf-8', errors='ignore')
        if "androidboot.selinux=permissive" not in bc_str:
            bc_str = "androidboot.selinux=permissive\n" + bc_str.strip() + "\n"
        bootconfig_data = bc_str.encode('utf-8')
    finally:
        stock_file.close()
        
    print(f"Stock header: version={v}, dtb_size={dtb_size}, bootconfig_size={bootconfig_size}")
    print(f"Stock Fragment 0 size: {frag0_size} bytes")
    
    # Decompress Fragment 0 (it is LZ4 legacy in stock) to uncompressed cpio
    # Then compress with ZSTD level 12 so it fits cleanly
    pos = 4
    blocks = []
    while pos < len(raw_frag0_data):
        if pos + 4 > len(raw_frag0_data): break
        b_size = struct.unpack_from('<I', raw_frag0_data, pos)[0]
        pos += 4
        if b_size == 0: break
        b_data = raw_frag0_data[pos:pos+b_size]
        pos += b_size
        try:
            decomp_b = lz4.block.decompress(b_data, uncompressed_size=8*1024*1024)
            blocks.append(decomp_b)
        except Exception as e:
            print("Fragment 0 decompress block error:", e)
            break
            
    uncompressed_frag0 = b''.join(blocks)
    print(f"Fragment 0 uncompressed size: {len(uncompressed_frag0)} bytes")

    # In Android 16, bootctl and health manifests are typed as 'device' but placed in 'system/etc/vintf/manifest/'.
    # Recovery servicemanager parses /system as framework, failing with:
    # "Cannot add a device manifest to a framework manifest" and "Unrecognized manifest.version 9.0 (libvintf@8.0)".
    # Rewrite paths to vendor/etc/vintf/manifest/ and version to 8.0 in-place (100% byte length identical).
    p1 = b'system/etc/vintf/manifest/android.hardware.boot-service.mtk.xml'
    t1 = b'vendor/etc/vintf/manifest/android.hardware.boot-service.mtk.xml'
    p2 = b'system/etc/vintf/manifest/android.hardware.health-service.example.xml'
    t2 = b'vendor/etc/vintf/manifest/android.hardware.health-service.example.xml'

    if p1 in uncompressed_frag0 or p2 in uncompressed_frag0:
        print("Redirecting device manifest fragments from /system to /vendor in Fragment 0 CPIO...")
        uncompressed_frag0 = uncompressed_frag0.replace(p1, t1).replace(p2, t2)
    if b'version="9.0"' in uncompressed_frag0:
        print("Sanitizing VINTF manifest version 9.0 -> 8.0 in Fragment 0 CPIO...")
        uncompressed_frag0 = uncompressed_frag0.replace(b'version="9.0"', b'version="8.0"')

    # Patch Trustonic TEE kernel module (mcDrvModule.ko) version check:
    # Kernel 6.12 reports API version 10, but user-space daemons expect version 9.
    name_idx = uncompressed_frag0.find(b'mcDrvModule.ko')
    if name_idx != -1:
        elf_idx = uncompressed_frag0.find(b'\x7fELF', name_idx)
        if elf_idx != -1:
            ko_len = 311296
            ko_data = uncompressed_frag0[elf_idx:elf_idx+ko_len]
            patches = [
                (b'\x40\x01\x80\x52', b'\x20\x01\x80\x52'),
                (b'\x4d\x01\x80\x52', b'\x2d\x01\x80\x52'),
                (b'\x48\x01\x80\x52', b'\x28\x01\x80\x52'),
                (b'\x43\x01\x80\x52', b'\x23\x01\x80\x52'),
            ]
            for old_bytes, new_bytes in patches:
                count = ko_data.count(old_bytes)
                if count > 0:
                    print(f"Patching mcDrvModule.ko inside Frag0 ({old_bytes.hex()} -> {new_bytes.hex()}, {count} matches)...")
                    ko_data = ko_data.replace(old_bytes, new_bytes)
            uncompressed_frag0 = uncompressed_frag0[:elf_idx] + ko_data + uncompressed_frag0[elf_idx+ko_len:]
    else:
        print("Warning: mcDrvModule.ko not found in Fragment 0 CPIO!")
    
    cctx = zstd.ZstdCompressor(level=19)
    frag0_zstd = cctx.compress(uncompressed_frag0)
    print(f"Fragment 0 ZSTD size: {len(frag0_zstd)} bytes ({len(frag0_zstd)/1024/1024:.2f} MB)")
    
    # Read built recovery ramdisk from built_path
    print(f"Reading built vendor_boot: {built_path}")
    if built_path.endswith('.gz'):
        with gzip.open(built_path, 'rb') as gz_f:
            built_bytes = gz_f.read()
        built_file = io.BytesIO(built_bytes)
    else:
        built_file = open(built_path, 'rb')
        
    try:
        built_hdr = built_file.read(4096)
        b_table_size, b_table_entry_num, b_table_entry_size = struct.unpack_from('<III', built_hdr, 2112)
        b_r_size = struct.unpack_from('<I', built_hdr, 24)[0]
        b_dtb_size = struct.unpack_from('<I', built_hdr, 2100)[0]
        b_offset_table = page_size + page_align(b_r_size, page_size) + page_align(b_dtb_size, page_size)
        
        built_file.seek(b_offset_table)
        b_table_data = built_file.read(b_table_size)
        # If there are 2 entries, entry 1 is recovery ramdisk
        if b_table_entry_num >= 2:
            rec_entry = b_table_data[b_table_entry_size : 2 * b_table_entry_size]
            rec_size, rec_offset, rec_type = struct.unpack_from('<III', rec_entry, 0)
            built_file.seek(page_size + rec_offset)
            raw_rec_data = built_file.read(rec_size)
        else:
            rec_entry = b_table_data[:b_table_entry_size]
            rec_size, rec_offset, rec_type = struct.unpack_from('<III', rec_entry, 0)
            built_file.seek(page_size + rec_offset)
            raw_rec_data = built_file.read(rec_size)
    finally:
        built_file.close()
        
    print(f"Built recovery raw size: {rec_size} bytes (magic: {raw_rec_data[:4].hex()})")
    
    # Decompress recovery ramdisk to sanitize VINTF manifests if needed
    dctx = zstd.ZstdDecompressor()
    if raw_rec_data[:4] == b'\x28\xb5\x2f\xfd':
        reader = dctx.stream_reader(io.BytesIO(raw_rec_data))
        uncompressed_rec = reader.read()
        print(f"Decompressed ZSTD recovery ramdisk size: {len(uncompressed_rec)} bytes")
    elif raw_rec_data[:2] == b'\x1f\x8b':
        uncompressed_rec = gzip.decompress(raw_rec_data)
        print(f"Uncompressed gzip recovery ramdisk size: {len(uncompressed_rec)} bytes")
    else:
        uncompressed_rec = raw_rec_data
        print(f"Raw uncompressed recovery ramdisk size: {len(uncompressed_rec)} bytes")

    # In AOSP Android 16, health and bootctl AIDL manifests carry version="9.0" and type="device".
    # Recovery servicemanager parses /system as framework, causing parse aborts.
    # Rewrite paths to vendor and version to 8.0 in-place.
    if p1 in uncompressed_rec or p2 in uncompressed_rec:
        print("Redirecting device manifest fragments from /system to /vendor in Fragment 1 CPIO...")
        uncompressed_rec = uncompressed_rec.replace(p1, t1).replace(p2, t2)
    if b'version="9.0"' in uncompressed_rec:
        print("Sanitizing VINTF manifest version 9.0 -> 8.0 in Fragment 1 CPIO...")
        uncompressed_rec = uncompressed_rec.replace(b'version="9.0"', b'version="8.0"')

    frag1_zstd = cctx.compress(uncompressed_rec)
    print(f"Fragment 1 ZSTD size: {len(frag1_zstd)} bytes ({len(frag1_zstd)/1024/1024:.2f} MB)")
    
    total_ramdisk = frag0_zstd + frag1_zstd
    vendor_ramdisk_size = len(total_ramdisk)
    print(f"Combined Vendor Ramdisk size: {vendor_ramdisk_size} bytes ({vendor_ramdisk_size/1024/1024:.2f} MB)")
    
    # Construct Ramdisk Table
    # Entry 0: PLATFORM
    entry0 = bytearray(108)
    struct.pack_into('<III', entry0, 0, len(frag0_zstd), 0, 1) # size, offset, type=1
    # Entry 1: RECOVERY
    entry1 = bytearray(108)
    struct.pack_into('<III', entry1, 0, len(frag1_zstd), len(frag0_zstd), 2) # size, offset, type=2
    rec_name_bytes = b'recovery' + b'\x00' * (32 - len(b'recovery'))
    entry1[12:12+32] = rec_name_bytes
    
    new_table_data = bytes(entry0 + entry1)
    new_table_size = len(new_table_data)
    
    # Build Header v4
    cmdline_str = cmdline.decode('utf-8', errors='ignore')
    if "bootconfig" not in cmdline_str:
        cmdline_str = (cmdline_str + " bootconfig").strip()
    cmdline_bytes = cmdline_str.encode('utf-8')[:2047]
    
    hdr = bytearray(stock_hdr)
    # Update vendor_ramdisk_size at offset 24
    struct.pack_into('<I', hdr, 24, vendor_ramdisk_size)
    # Update cmdline at offset 28
    hdr[28:28+2048] = b'\x00' * 2048
    hdr[28:28+len(cmdline_bytes)] = cmdline_bytes
    # Update table size at 2112
    struct.pack_into('<IIII', hdr, 2112, new_table_size, 2, 108, len(bootconfig_data))
    
    # Assemble full image
    out_parts = []
    out_parts.append(bytes(hdr)) # page 0 (offset 0 .. 4095)
    
    # Vendor ramdisk
    out_parts.append(total_ramdisk)
    pad1 = page_align(len(total_ramdisk), page_size) - len(total_ramdisk)
    if pad1 > 0:
        out_parts.append(b'\x00' * pad1)
        
    # DTB
    out_parts.append(dtb_data)
    pad2 = page_align(len(dtb_data), page_size) - len(dtb_data)
    if pad2 > 0:
        out_parts.append(b'\x00' * pad2)
        
    # Table
    out_parts.append(new_table_data)
    pad3 = page_align(len(new_table_data), page_size) - len(new_table_data)
    if pad3 > 0:
        out_parts.append(b'\x00' * pad3)
        
    # Bootconfig
    out_parts.append(bootconfig_data)
    pad4 = page_align(len(bootconfig_data), page_size) - len(bootconfig_data)
    if pad4 > 0:
        out_parts.append(b'\x00' * pad4)
        
    final_data = b''.join(out_parts)
    # Target partition size: 67108864 (64 MB)
    target_part_size = 67108864
    if len(final_data) > target_part_size:
        raise ValueError(f"Final image size {len(final_data)} exceeds partition size {target_part_size}!")
        
    final_padded = final_data + b'\x00' * (target_part_size - len(final_data))
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'wb') as out_f:
        out_f.write(final_padded)
        
    print(f"Successfully repacked vendor_boot to: {output_path}")
    print(f"Final file size: {len(final_padded)} bytes ({len(final_padded)/1024/1024:.2f} MB)")

if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 4:
        repack(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        stock = r'staging-repo/reference/stock_vendor_boot.img.gz'
        built = r'staging-repo/reference/stock_vendor_boot.img.gz'
        output = r'temp/tested_ofox_a16_vendor_boot.img'
        repack(stock, built, output)
