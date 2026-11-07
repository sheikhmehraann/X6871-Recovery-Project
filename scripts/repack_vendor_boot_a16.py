import struct
import os
import io
import zstandard as zstd
import gzip
import lz4.block

def page_align(val, page_size=4096):
    return (val + page_size - 1) & ~(page_size - 1)

def make_cpio_record(name, data, mode=0o100644):
    name_bytes = name.encode('utf-8') + b'\x00'
    namesize = len(name_bytes)
    filesize = len(data)
    hdr = f"07070100000000{mode:08x}00000000000000000000000100000000{filesize:08x}00000000000000000000000000000000{namesize:08x}00000000"
    out = bytearray(hdr.encode('ascii'))
    out += name_bytes
    if len(out) % 4 != 0:
        out += b'\x00' * (4 - (len(out) % 4))
    out += data
    if len(out) % 4 != 0:
        out += b'\x00' * (4 - (len(out) % 4))
    return bytes(out)

def unpack_cpio_records(data):
    records = []
    pos = 0
    data_len = len(data)
    while pos + 110 <= data_len:
        magic = data[pos:pos+6]
        if magic not in (b'070701', b'070702'):
            break
        mode = int(data[pos+14:pos+22], 16)
        filesize = int(data[pos+54:pos+62], 16)
        namesize = int(data[pos+94:pos+102], 16)
        pos += 110
        filename = data[pos:pos+namesize-1].decode('utf-8', errors='ignore')
        pos += namesize
        if pos % 4 != 0:
            pos += 4 - (pos % 4)
        file_data = data[pos:pos+filesize]
        pos += filesize
        if pos % 4 != 0:
            pos += 4 - (pos % 4)
        records.append({'mode': mode, 'name': filename, 'data': file_data})
        if filename == 'TRAILER!!!':
            break
    return records

def repack_cpio(records):
    out = bytearray()
    for r in records:
        if r['name'] == 'TRAILER!!!':
            continue
        out += make_cpio_record(r['name'], r['data'], r.get('mode', 0o100644))
    out += make_cpio_record('TRAILER!!!', b'', 0)
    return bytes(out)

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
        
        # Bootconfig in vendor_boot MUST be empty (size 0) on MediaTek MT6895
        # because the OEM bootloader dynamically appends its own complete bootconfig (including kernel.rcu_*).
        # Defining duplicate keys in vendor_boot triggers Linux kernel bconf_parse error:
        # 'Failed to parse bootconfig: Value is redefined at 758', causing the kernel to drop all
        # bootconfig parameters (including androidboot.hardware=mt6895), which kills FirstStageMount.
        bootconfig_data = b""
    finally:
        stock_file.close()
        
    print(f"Stock header: version={v}, dtb_size={dtb_size}, bootconfig_size={bootconfig_size}")
    print(f"Stock Fragment 0 size: {frag0_size} bytes")
    
    # Decompress Fragment 0 (it is LZ4 legacy in stock) to uncompressed cpio
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
    # Rewrite paths to vendor/etc/vintf/manifest/ and version to 8.0 in-place.
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

    # Locate prebuilt modules directory and device fstabs
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.normpath(os.path.join(script_dir, '..', 'device', 'infinix', 'X6871', 'prebuilt', 'modules')),
        os.path.normpath(os.path.join(os.getcwd(), 'device', 'infinix', 'X6871', 'prebuilt', 'modules')),
        os.path.normpath(os.path.join(os.getcwd(), '..', 'device', 'infinix', 'X6871', 'prebuilt', 'modules')),
    ]
    modules_dir = None
    for cand in candidates:
        if os.path.isdir(cand):
            modules_dir = cand
            break

    fstab_candidates = [
        os.path.normpath(os.path.join(script_dir, '..', 'device', 'infinix', 'X6871', 'recovery', 'root', 'first_stage_ramdisk', 'fstab.mt6895')),
        os.path.normpath(os.path.join(os.getcwd(), 'device', 'infinix', 'X6871', 'recovery', 'root', 'first_stage_ramdisk', 'fstab.mt6895')),
    ]
    fstab_path = None
    for fc in fstab_candidates:
        if os.path.exists(fc):
            fstab_path = fc
            break

    touch_mods = [
        'tui-common.ko',
        'ts_scp_common.ko',
        'touch_boost.ko',
        'adaptive-ts.ko',
        'gt9916_common.ko',
        'focaltech_ft3683g.ko',
        'gt9896s.ko'
    ]

    # --- INJECT TOUCH HARDWARE MODULES & FSTABS INTO FRAGMENT 0 ---
    print("--- Modifying Fragment 0 CPIO (Touch Drivers & Multi-Suffix Fstabs) ---")
    frag0_recs = unpack_cpio_records(uncompressed_frag0)
    frag0_map = {r['name']: r for r in frag0_recs if r['name'] != 'TRAILER!!!'}

    # 1. Update modules.load.recovery
    if 'lib/modules/modules.load.recovery' in frag0_map:
        rec = frag0_map['lib/modules/modules.load.recovery']
        text = rec['data'].decode('utf-8', errors='ignore')
        to_add = [m for m in touch_mods if m not in text]
        if to_add:
            new_text = text.rstrip('\n') + '\n' + '\n'.join(to_add) + '\n'
            rec['data'] = new_text.encode('utf-8')
            print(f"  Appended to Fragment 0 modules.load.recovery: {to_add}")

    # 2. Update modules.dep
    dep_additions = """
/lib/modules/tui-common.ko:
/lib/modules/ts_scp_common.ko: /lib/modules/scp.ko /lib/modules/mtk_tinysys_ipi.ko
/lib/modules/touch_boost.ko:
/lib/modules/adaptive-ts.ko: /lib/modules/mtk_disp_notify.ko /lib/modules/thd.ko /lib/modules/transsion_tranlog.ko
/lib/modules/gt9916_common.ko: /lib/modules/adaptive-ts.ko
/lib/modules/focaltech_ft3683g.ko: /lib/modules/adaptive-ts.ko /lib/modules/transsion_tranlog.ko
/lib/modules/gt9896s.ko: /lib/modules/spi-mt65xx.ko /lib/modules/mtk_panel_ext.ko /lib/modules/tui-common.ko /lib/modules/mtk_disp_notify.ko
"""
    if 'lib/modules/modules.dep' in frag0_map:
        rec = frag0_map['lib/modules/modules.dep']
        dep_text = rec['data'].decode('utf-8', errors='ignore')
        if 'gt9896s.ko' not in dep_text:
            rec['data'] = (dep_text.rstrip('\n') + '\n' + dep_additions.strip() + '\n').encode('utf-8')
            print("  Updated Fragment 0 lib/modules/modules.dep with touch dependencies")

    # 3. Inject touch module binaries into lib/modules/
    if modules_dir:
        print(f"  Using modules directory: {modules_dir}")
        for m in touch_mods:
            m_path = os.path.join(modules_dir, m)
            if os.path.exists(m_path):
                with open(m_path, 'rb') as mf:
                    m_data = mf.read()
                frag0_map[f'lib/modules/{m}'] = {'name': f'lib/modules/{m}', 'data': m_data, 'mode': 0o100644}
                print(f"  Injected lib/modules/{m} ({len(m_data)} bytes) into Fragment 0")
    else:
        print("  Notice: modules directory not found; searching built recovery for touch modules...")

    # 4. Inject multi-suffix fstabs into Fragment 0 first_stage_ramdisk/
    if fstab_path:
        with open(fstab_path, 'rb') as ff:
            fstab_data = ff.read()
        frag0_map['first_stage_ramdisk/fstab.mt6895'] = {'name': 'first_stage_ramdisk/fstab.mt6895', 'data': fstab_data, 'mode': 0o100644}
        frag0_map['first_stage_ramdisk/fstab.emmc'] = {'name': 'first_stage_ramdisk/fstab.emmc', 'data': fstab_data, 'mode': 0o100644}
        frag0_map['first_stage_ramdisk/fstab.default'] = {'name': 'first_stage_ramdisk/fstab.default', 'data': fstab_data, 'mode': 0o100644}
        print("  Injected multi-suffix fstabs into Fragment 0 first_stage_ramdisk/")

    uncompressed_frag0 = repack_cpio(list(frag0_map.values()))
    print(f"Repacked Fragment 0 CPIO total size: {len(uncompressed_frag0)} bytes")

    # --- READ BUILT RECOVERY RAMDISK ---
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
    
    # Decompress recovery ramdisk
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
    if p1 in uncompressed_rec or p2 in uncompressed_rec:
        print("Redirecting device manifest fragments from /system to /vendor in Fragment 1 CPIO...")
        uncompressed_rec = uncompressed_rec.replace(p1, t1).replace(p2, t2)
    if b'version="9.0"' in uncompressed_rec:
        print("Sanitizing VINTF manifest version 9.0 -> 8.0 in Fragment 1 CPIO...")
        uncompressed_rec = uncompressed_rec.replace(b'version="9.0"', b'version="8.0"')

    # --- INJECT MULTI-FSTABS AND MODULES INTO FRAGMENT 1 ---
    rec_recs = unpack_cpio_records(uncompressed_rec)
    rec_map = {r['name']: r for r in rec_recs if r['name'] != 'TRAILER!!!'}
    
    if modules_dir:
        for m in touch_mods:
            m_path = os.path.join(modules_dir, m)
            if os.path.exists(m_path):
                with open(m_path, 'rb') as mf:
                    m_data = mf.read()
                rec_map[f'lib/modules/{m}'] = {'name': f'lib/modules/{m}', 'data': m_data, 'mode': 0o100644}
                rec_map[f'vendor/lib/modules/{m}'] = {'name': f'vendor/lib/modules/{m}', 'data': m_data, 'mode': 0o100644}
                rec_map[f'system/lib/modules/{m}'] = {'name': f'system/lib/modules/{m}', 'data': m_data, 'mode': 0o100644}

    if fstab_path:
        with open(fstab_path, 'rb') as ff:
            fstab_data = ff.read()
        rec_map['first_stage_ramdisk/fstab.mt6895'] = {'name': 'first_stage_ramdisk/fstab.mt6895', 'data': fstab_data, 'mode': 0o100644}
        rec_map['first_stage_ramdisk/fstab.emmc'] = {'name': 'first_stage_ramdisk/fstab.emmc', 'data': fstab_data, 'mode': 0o100644}
        rec_map['first_stage_ramdisk/fstab.default'] = {'name': 'first_stage_ramdisk/fstab.default', 'data': fstab_data, 'mode': 0o100644}
        print("  Injected multi-suffix fstabs and touch modules into Fragment 1")

    uncompressed_rec = repack_cpio(list(rec_map.values()))
    print(f"Repacked Fragment 1 CPIO total size: {len(uncompressed_rec)} bytes")

    # Build Header v4 parameters
    cmdline_str = cmdline.decode('utf-8', errors='ignore')
    if "bootconfig" not in cmdline_str:
        cmdline_str = (cmdline_str + " bootconfig").strip()
    if "androidboot.selinux=permissive" not in cmdline_str:
        cmdline_str = (cmdline_str + " androidboot.selinux=permissive").strip()
    cmdline_bytes = cmdline_str.encode('utf-8')[:2047]

    # Target partition size: 67108864 (64 MB)
    target_part_size = 67108864
    final_padded = None
    final_data_len = 0

    # Multi-level adaptive zstd compression (starts at max level 22 to guarantee fit)
    for zstd_level in [22, 21, 19]:
        cctx = zstd.ZstdCompressor(level=zstd_level)
        frag0_zstd = cctx.compress(uncompressed_frag0)
        frag1_zstd = cctx.compress(uncompressed_rec)
        print(f"ZSTD Level {zstd_level}: Frag0={len(frag0_zstd)} bytes ({len(frag0_zstd)/1024/1024:.2f} MB), Frag1={len(frag1_zstd)} bytes ({len(frag1_zstd)/1024/1024:.2f} MB)")

        total_ramdisk = frag0_zstd + frag1_zstd
        vendor_ramdisk_size = len(total_ramdisk)

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

        hdr = bytearray(stock_hdr)
        struct.pack_into('<I', hdr, 24, vendor_ramdisk_size)
        hdr[28:28+2048] = b'\x00' * 2048
        hdr[28:28+len(cmdline_bytes)] = cmdline_bytes
        struct.pack_into('<IIII', hdr, 2112, new_table_size, 2, 108, len(bootconfig_data))

        out_parts = []
        out_parts.append(bytes(hdr)) # page 0

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
        final_data_len = len(final_data)

        if final_data_len <= target_part_size:
            headroom = target_part_size - final_data_len
            print(f"Vendor boot image successfully fit at zstd level {zstd_level}: {final_data_len} <= {target_part_size} ({headroom} bytes / {headroom/1024:.2f} KB headroom)")
            final_padded = final_data + b'\x00' * headroom
            break
        else:
            print(f"Notice: Image size {final_data_len} > {target_part_size} at level {zstd_level}, trying higher compression...")

    if final_padded is None:
        raise ValueError(f"Final image size {final_data_len} exceeds partition size {target_part_size} even at zstd level 22!")
    
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
