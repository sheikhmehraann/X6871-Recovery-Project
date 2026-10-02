import os
import sys
import struct
import lz4.frame
import lz4.block

def decompress_lz4(input_path, output_path):
    with open(input_path, "rb") as f:
        data = f.read()

    decompressed = None
    # Check magic
    if data[:4] == b"\x02!L\x18": # LZ4 legacy
        # Format: 4 bytes magic, blocks of (4 bytes size + data)
        offset = 4
        chunks = []
        while offset < len(data):
            if offset + 4 > len(data):
                break
            block_sz, = struct.unpack("<I", data[offset:offset+4])
            offset += 4
            if block_sz == 0:
                break
            block_data = data[offset:offset+block_sz]
            offset += block_sz
            # Uncompressed size for legacy lz4 block is up to 8MB
            try:
                dec = lz4.block.decompress(block_data, uncompressed_size=8*1024*1024)
                chunks.append(dec)
            except Exception as e:
                print(f"Error decompressing legacy block: {e}")
                break
        decompressed = b"".join(chunks)
    elif data[:4] == b"\x04\"M\x18": # LZ4 frame
        decompressed = lz4.frame.decompress(data)
    elif data[:6] == b"070701": # Uncompressed CPIO
        decompressed = data
    else:
        # Try frame decompress anyway
        try:
            decompressed = lz4.frame.decompress(data)
        except Exception:
            pass

    if decompressed:
        with open(output_path, "wb") as f_out:
            f_out.write(decompressed)
        print(f"[+] Decompressed {os.path.basename(input_path)} -> {os.path.basename(output_path)} ({len(decompressed)} bytes)")
        return True
    else:
        print(f"[-] Failed to decompress {input_path}")
        return False

def unpack_cpio(cpio_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(cpio_path, "rb") as f:
        data = f.read()

    pos = 0
    file_count = 0
    while pos < len(data):
        if pos + 110 > len(data):
            break
        header = data[pos:pos+110]
        if not header.startswith(b"070701"):
            break
        
        try:
            # cpio fields are hex strings:
            # magic (6), ino(8), mode(8), uid(8), gid(8), nlink(8), mtime(8), filesize(8),
            # devmajor(8), devminor(8), rdevmajor(8), rdevminor(8), namesize(8), check(8)
            filesize = int(header[54:62], 16)
            namesize = int(header[94:102], 16)
            
            name_pos = pos + 110
            name_bytes = data[name_pos:name_pos + namesize - 1] # exclude null terminator
            name = name_bytes.decode("utf-8", errors="replace").replace("\\", "/")
            
            # Align name to 4 bytes: (110 + namesize + 3) & ~3
            header_and_name_len = ((110 + namesize + 3) // 4) * 4
            file_data_pos = pos + header_and_name_len
            file_data = data[file_data_pos:file_data_pos + filesize]
            
            # Align next pos to 4 bytes
            pos = file_data_pos + (((filesize + 3) // 4) * 4)
            
            if name == "TRAILER!!!":
                break
            
            target_path = os.path.join(out_dir, name.replace("/", os.sep))
            if filesize == 0 and (name.endswith("/") or not os.path.exists(target_path)):
                os.makedirs(target_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "wb") as out_f:
                    out_f.write(file_data)
            file_count += 1
        except Exception as e:
            # Continue extracting remaining files
            pos = file_data_pos + (((filesize + 3) // 4) * 4) if 'file_data_pos' in locals() else pos + 512
            continue

    print(f"[+] Unpacked {file_count} files into {out_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python unpack_ramdisk.py <ramdisk.cpio> <out_dir>")
        sys.exit(1)
    
    in_file = sys.argv[1]
    out_dir = sys.argv[2]
    raw_cpio = os.path.join(out_dir, "decompressed.cpio")
    os.makedirs(out_dir, exist_ok=True)
    if decompress_lz4(in_file, raw_cpio):
        unpack_cpio(raw_cpio, os.path.join(out_dir, "extracted"))
