import struct
import os
import io
import zstandard as zstd
import gzip
import lz4.block

def page_align(val, page_size=4096):
    return (val + page_size - 1) & ~(page_size - 1)

def parse_cpio(data):
    files = {}
    pos = 0
    while pos + 110 <= len(data):
        magic = data[pos:pos+6]
        if magic != b'070701' and magic != b'070702':
            break
        ino = int(data[pos+6:pos+14], 16)
        mode = int(data[pos+14:pos+22], 16)
        uid = int(data[pos+22:pos+30], 16)
        gid = int(data[pos+30:pos+38], 16)
        nlink = int(data[pos+38:pos+46], 16)
        mtime = int(data[pos+46:pos+54], 16)
        filesize = int(data[pos+54:pos+62], 16)
        devmajor = int(data[pos+62:pos+70], 16)
        devminor = int(data[pos+70:pos+78], 16)
        rdevmajor = int(data[pos+78:pos+86], 16)
        rdevminor = int(data[pos+86:pos+94], 16)
        namesize = int(data[pos+94:pos+102], 16)
        check = int(data[pos+102:pos+110], 16)
        pos += 110
        name = data[pos:pos+namesize-1].decode('utf-8', errors='ignore')
        pos = (pos + namesize + 3) & ~3
        file_data = data[pos:pos+filesize]
        pos = (pos + filesize + 3) & ~3
        if name == 'TRAILER!!!':
            break
        files[name] = {
            'ino': ino, 'mode': mode, 'uid': uid, 'gid': gid,
            'nlink': nlink, 'mtime': mtime, 'devmajor': devmajor,
            'devminor': devminor, 'rdevmajor': rdevmajor,
            'rdevminor': rdevminor, 'check': check, 'data': file_data
        }
    return files

def pad4(stream):
    rem = stream.tell() % 4
    if rem:
        stream.write(b'\x00' * (4 - rem))

def build_cpio(files):
    out = io.BytesIO()
    for name, info in files.items():
        name_bytes = name.encode('utf-8') + b'\x00'
        namesize = len(name_bytes)
        file_data = info['data']
        filesize = len(file_data)
        header = f"070701{info['ino']:08X}{info['mode']:08X}{info['uid']:08X}{info['gid']:08X}{info['nlink']:08X}{info['mtime']:08X}{filesize:08X}{info['devmajor']:08X}{info['devminor']:08X}{info['rdevmajor']:08X}{info['rdevminor']:08X}{namesize:08X}{info['check']:08X}".encode('ascii')
        out.write(header)
        out.write(name_bytes)
        pad4(out)
        out.write(file_data)
        pad4(out)
    
    trailer = b"TRAILER!!!\x00"
    t_namesize = len(trailer)
    trailer_hdr = f"070701{0:08X}{0:08X}{0:08X}{0:08X}{1:08X}{0:08X}{0:08X}{0:08X}{0:08X}{0:08X}{0:08X}{t_namesize:08X}{0:08X}".encode('ascii')
    out.write(trailer_hdr)
    out.write(trailer)
    pad4(out)
    total = out.tell()
    pad_512 = (512 - (total % 512)) % 512
    if pad_512:
        out.write(b'\x00' * pad_512)
    return out.getvalue()

def make_entry(data, mode=0o100644):
    return {
        'ino': 100000, 'mode': mode, 'uid': 0, 'gid': 0,
        'nlink': 1, 'mtime': 0, 'devmajor': 0,
        'devminor': 0, 'rdevmajor': 0, 'rdevminor': 0,
        'check': 0, 'data': data
    }

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
        
        # Read bootconfig
        stock_file.seek(offset_bootconfig)
        bootconfig_data = stock_file.read(bootconfig_size)
    finally:
        stock_file.close()
        
    print(f"Stock header: version={v}, dtb_size={dtb_size}, bootconfig_size={bootconfig_size}")
    print(f"Stock Fragment 0 size: {frag0_size} bytes")
    
    # Decompress Fragment 0 (LZ4 legacy in stock) to uncompressed cpio
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
    
    # Parse Fragment 0 CPIO and inject recovery touch modules + firmware
    frag0_files = parse_cpio(uncompressed_frag0)
    print(f"Fragment 0 parsed entries: {len(frag0_files)}")
    
    # Locate touch assets from repo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    
    def find_file(candidates):
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    adaptive_ts = find_file([
        os.path.join(repo_root, "device", "infinix", "Infinix-X6871", "recovery", "root", "lib", "modules", "adaptive-ts.ko"),
        os.path.join(repo_root, "device", "infinix", "X6871", "recovery", "root", "lib", "modules", "adaptive-ts.ko")
    ])
    gt9916 = find_file([
        os.path.join(repo_root, "device", "infinix", "Infinix-X6871", "recovery", "root", "lib", "modules", "gt9916_common.ko"),
        os.path.join(repo_root, "device", "infinix", "X6871", "recovery", "root", "lib", "modules", "gt9916_common.ko")
    ])
    ft3683g = find_file([
        os.path.join(repo_root, "device", "infinix", "Infinix-X6871", "recovery", "root", "lib", "modules", "focaltech_ft3683g.ko"),
        os.path.join(repo_root, "device", "infinix", "X6871", "recovery", "root", "lib", "modules", "focaltech_ft3683g.ko")
    ])
    fw_bin = find_file([
        os.path.join(repo_root, "device", "infinix", "Infinix-X6871", "recovery", "root", "vendor", "firmware", "goodix_firmware.bin"),
        os.path.join(repo_root, "device", "infinix", "X6871", "recovery", "root", "vendor", "firmware", "goodix_firmware.bin")
    ])
    fw_cfg = find_file([
        os.path.join(repo_root, "device", "infinix", "Infinix-X6871", "recovery", "root", "vendor", "firmware", "goodix_cfg_group.bin"),
        os.path.join(repo_root, "device", "infinix", "X6871", "recovery", "root", "vendor", "firmware", "goodix_cfg_group.bin")
    ])

    if adaptive_ts and os.path.exists(adaptive_ts):
        with open(adaptive_ts, 'rb') as f:
            frag0_files['lib/modules/adaptive-ts.ko'] = make_entry(f.read())
            print(f"Injected adaptive-ts.ko ({os.path.getsize(adaptive_ts)} bytes)")

    if gt9916 and os.path.exists(gt9916):
        with open(gt9916, 'rb') as f:
            frag0_files['lib/modules/gt9916_common.ko'] = make_entry(f.read())
            print(f"Injected gt9916_common.ko ({os.path.getsize(gt9916)} bytes)")

    if ft3683g and os.path.exists(ft3683g):
        with open(ft3683g, 'rb') as f:
            frag0_files['lib/modules/focaltech_ft3683g.ko'] = make_entry(f.read())
            print(f"Injected focaltech_ft3683g.ko ({os.path.getsize(ft3683g)} bytes)")

    if fw_bin and os.path.exists(fw_bin):
        with open(fw_bin, 'rb') as f:
            bin_data = f.read()
            frag0_files['odm/firmware/goodix_firmware.bin'] = make_entry(bin_data)
            frag0_files['vendor/firmware/goodix_firmware.bin'] = make_entry(bin_data)
            print(f"Injected goodix_firmware.bin into odm/firmware and vendor/firmware ({len(bin_data)} bytes)")

    if fw_cfg and os.path.exists(fw_cfg):
        with open(fw_cfg, 'rb') as f:
            cfg_data = f.read()
            frag0_files['odm/firmware/goodix_cfg_group.bin'] = make_entry(cfg_data)
            frag0_files['vendor/firmware/goodix_cfg_group.bin'] = make_entry(cfg_data)
            print(f"Injected goodix_cfg_group.bin into odm/firmware and vendor/firmware ({len(cfg_data)} bytes)")

    # Update Fragment 0's modules.load.recovery to append touch modules
    if 'lib/modules/modules.load.recovery' in frag0_files:
        orig_load = frag0_files['lib/modules/modules.load.recovery']['data'].decode('utf-8', errors='ignore')
        needed = ['adaptive-ts.ko', 'gt9916_common.ko', 'focaltech_ft3683g.ko']
        to_append = [m for m in needed if m not in orig_load]
        if to_append:
            new_load = orig_load.strip() + '\n' + '\n'.join(to_append) + '\n'
            frag0_files['lib/modules/modules.load.recovery']['data'] = new_load.encode('utf-8')
            print(f"Appended touch modules to modules.load.recovery: {to_append}")

    # Rebuild modified Fragment 0 CPIO
    rebuilt_frag0 = build_cpio(frag0_files)
    print(f"Modified Fragment 0 CPIO size: {len(rebuilt_frag0)} bytes")

    cctx = zstd.ZstdCompressor(level=12)
    frag0_zstd = cctx.compress(rebuilt_frag0)
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
            # If only 1 entry, use entry 0
            rec_entry = b_table_data[:b_table_entry_size]
            rec_size, rec_offset, rec_type = struct.unpack_from('<III', rec_entry, 0)
            built_file.seek(page_size + rec_offset)
            raw_rec_data = built_file.read(rec_size)
    finally:
        built_file.close()
        
    print(f"Built recovery raw size: {rec_size} bytes (magic: {raw_rec_data[:4].hex()})")
    
    # Decompress recovery ramdisk (gzip or raw or zstd)
    if raw_rec_data[:2] == b'\x1f\x8b':
        uncompressed_rec = gzip.decompress(raw_rec_data)
    elif raw_rec_data[:4] == b'\x28\xb5\x2f\xfd':
        dctx = zstd.ZstdDecompressor()
        uncompressed_rec = dctx.decompress(raw_rec_data)
    else:
        uncompressed_rec = raw_rec_data
        
    print(f"Uncompressed recovery ramdisk size: {len(uncompressed_rec)} bytes")
    
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
    # Ensure cmdline has bootconfig
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
