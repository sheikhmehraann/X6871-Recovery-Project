#!/usr/bin/env python3
import os
import sys
import zipfile
import urllib.request
import tempfile
import shutil

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

def download_file(url, dest_path):
    print(f"Downloading {url} -> {dest_path}")
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req) as resp, open(dest_path, 'wb') as out:
        shutil.copyfileobj(resp, out)

def fix_update_binary(temp_dir):
    ub_path = os.path.join(temp_dir, 'META-INF', 'com', 'google', 'android', 'update-binary')
    if not os.path.exists(ub_path):
        return
    with open(ub_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Smart partition detector: only select init_boot if it actually contains the ANDROID! header
    old_detect = '''\t# detect the init_boot partition, else resort to the boot partition
\tPART=/dev/block/bootdevice/by-name/init_boot_a;
\tif [ -e $PART ]; then
\t\tPART=init_boot;
\telse
\t\tPART=boot;
\tfi'''

    new_detect = '''\t# detect whether init_boot partition is valid (has ANDROID! header), else resort to boot
\tPART=boot;
\tfor ib in /dev/block/bootdevice/by-name/init_boot_a /dev/block/by-name/init_boot_a /dev/block/by-name/init_boot; do
\t\tif [ -e "$ib" ]; then
\t\t\tmagic=$(toybox xxd -l 8 "$ib" 2>/dev/null | grep -i "ANDROID\\!");
\t\t\t[ -z "$magic" ] && magic=$(head -c 8 "$ib" 2>/dev/null | grep "ANDROID\\!");
\t\t\tif [ -n "$magic" ]; then
\t\t\t\tPART=init_boot;
\t\t\t\tbreak;
\t\t\tfi
\t\tfi
\tdone'''

    if old_detect in content:
        content = content.replace(old_detect, new_detect)
        print("  Patched init_boot vs boot detection logic")

    # Explicitly pass --partition $PART to ksud
    old_call = 'ksud boot-patch --module $FNAME --flash;'
    new_call = 'ksud boot-patch --partition $PART --module $FNAME --flash;'
    if old_call in content:
        content = content.replace(old_call, new_call)
        print("  Patched ksud boot-patch --partition $PART flag")

    with open(ub_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content.replace('\r\n', '\n'))

def update_zip_contents(zip_path, new_files, source_text):
    print(f"Updating {zip_path}...")
    temp_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(temp_dir)
        
        # Copy new files into extracted dir
        for filename, src_path in new_files.items():
            dest = os.path.join(temp_dir, filename)
            shutil.copy2(src_path, dest)
            print(f"  Injected: {filename} ({os.path.getsize(dest)} bytes)")
            
        # Update source.txt
        if source_text:
            with open(os.path.join(temp_dir, 'source.txt'), 'w', encoding='utf-8') as sf:
                sf.write(source_text)
            print(f"  Updated source.txt")

        # Fix update-binary logic
        fix_update_binary(temp_dir)

        # Repack zip preserving Unix 0755 execute attributes
        backup_path = zip_path + ".bak"
        if os.path.exists(zip_path):
            shutil.move(zip_path, backup_path)
            
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, temp_dir).replace('\\', '/')
                    zinfo = zipfile.ZipInfo(rel_p)
                    # Unix executable permission (0o755 = rwxr-xr-x)
                    zinfo.external_attr = 0o100755 << 16
                    with open(full_p, 'rb') as fp:
                        z_out.writestr(zinfo, fp.read(), compress_type=zipfile.ZIP_DEFLATED)

        if os.path.exists(backup_path):
            os.remove(backup_path)
        print(f"Successfully repacked: {zip_path} ({os.path.getsize(zip_path)} bytes)")
    finally:
        shutil.rmtree(temp_dir)

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"=== Root Suites Latest Updater (Target: {target_dir}) ===")
    work_dir = tempfile.mkdtemp()
    
    try:
        # 1. SukiSU-Ultra v4.2.1-r2
        suki_zip = os.path.join(target_dir, "KernelSU_Suki_Installer.zip")
        if os.path.exists(suki_zip):
            print("\n--- Upgrading SukiSU-Ultra to v4.2.1-r2 ---")
            suki_base = "https://github.com/SukiSU-Ultra/SukiSU-Ultra/releases/download/v4.2.1-r2/"
            suki_mods = {
                "android16-6.12_kernelsu.ko": suki_base + "lkm-aarch64-android16-6.12_kernelsu.ko",
                "android15-6.6_kernelsu.ko": suki_base + "lkm-aarch64-android15-6.6_kernelsu.ko",
                "android14-6.1_kernelsu.ko": suki_base + "lkm-aarch64-android14-6.1_kernelsu.ko",
                "android14-5.15_kernelsu.ko": suki_base + "lkm-aarch64-android14-5.15_kernelsu.ko",
                "android13-5.15_kernelsu.ko": suki_base + "lkm-aarch64-android13-5.15_kernelsu.ko",
                "android13-5.10_kernelsu.ko": suki_base + "lkm-aarch64-android13-5.10_kernelsu.ko",
                "android12-5.10_kernelsu.ko": suki_base + "lkm-aarch64-android12-5.10_kernelsu.ko",
                "ksud": suki_base + "ksud-aarch64-linux-android"
            }
            new_suki = {}
            for name, url in suki_mods.items():
                p = os.path.join(work_dir, "suki_" + name)
                download_file(url, p)
                new_suki[name] = p
                
            suki_source = "v4.2.1-r2:\nhttps://github.com/SukiSU-Ultra/SukiSU-Ultra/releases/tag/v4.2.1-r2\n"
            update_zip_contents(suki_zip, new_suki, suki_source)

        # 2. KernelSU v3.3.1
        ksu_zip = os.path.join(target_dir, "KernelSU_Installer.zip")
        if os.path.exists(ksu_zip):
            print("\n--- Upgrading KernelSU to v3.3.1 ---")
            ksu_base = "https://github.com/tiann/KernelSU/releases/download/v3.3.1/"
            ksu_mods = {
                "android16-6.12_kernelsu.ko": ksu_base + "lkm-aarch64-android16-6.12_kernelsu.ko",
                "android15-6.6_kernelsu.ko": ksu_base + "lkm-aarch64-android15-6.6_kernelsu.ko",
                "android14-6.1_kernelsu.ko": ksu_base + "lkm-aarch64-android14-6.1_kernelsu.ko",
                "android14-5.15_kernelsu.ko": ksu_base + "lkm-aarch64-android14-5.15_kernelsu.ko",
                "android13-5.15_kernelsu.ko": ksu_base + "lkm-aarch64-android13-5.15_kernelsu.ko",
                "android13-5.10_kernelsu.ko": ksu_base + "lkm-aarch64-android13-5.10_kernelsu.ko",
                "android12-5.10_kernelsu.ko": ksu_base + "lkm-aarch64-android12-5.10_kernelsu.ko",
                "ksud": ksu_base + "ksud-aarch64-linux-android"
            }
            new_ksu = {}
            for name, url in ksu_mods.items():
                p = os.path.join(work_dir, "ksu_" + name)
                download_file(url, p)
                new_ksu[name] = p
                
            ksu_source = "v3.3.1:\nhttps://github.com/tiann/KernelSU/releases/tag/v3.3.1\n"
            update_zip_contents(ksu_zip, new_ksu, ksu_source)

        # 3. KernelSU-Next v3.4.2
        ksun_zip = os.path.join(target_dir, "KernelSU_Next_Installer.zip")
        if os.path.exists(ksun_zip):
            print("\n--- Upgrading KernelSU-Next to v3.4.2 ---")
            ksun_base = "https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v3.4.2/"
            ksun_mods = {
                "android16-6.12_kernelsu.ko": ksun_base + "aarch64_android16-6.12_kernelsu.ko",
                "android15-6.6_kernelsu.ko": ksun_base + "aarch64_android15-6.6_kernelsu.ko",
                "android14-6.1_kernelsu.ko": ksun_base + "aarch64_android14-6.1_kernelsu.ko",
                "android14-5.15_kernelsu.ko": ksun_base + "aarch64_android14-5.15_kernelsu.ko",
                "android13-5.15_kernelsu.ko": ksun_base + "aarch64_android13-5.15_kernelsu.ko",
                "android13-5.10_kernelsu.ko": ksun_base + "aarch64_android13-5.10_kernelsu.ko",
                "android12-5.10_kernelsu.ko": ksun_base + "aarch64_android12-5.10_kernelsu.ko",
                "ksud": ksun_base + "ksud-aarch64-linux-android"
            }
            new_ksun = {}
            for name, url in ksun_mods.items():
                p = os.path.join(work_dir, "ksun_" + name)
                download_file(url, p)
                new_ksun[name] = p
                
            ksun_source = "v3.4.2:\nhttps://github.com/KernelSU-Next/KernelSU-Next/releases/tag/v3.4.2\n"
            update_zip_contents(ksun_zip, new_ksun, ksun_source)

    finally:
        shutil.rmtree(work_dir)
    print("\nAll root suite installers upgraded successfully to latest releases!")

if __name__ == '__main__':
    main()
