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

    update_binary_content = """#!/system/bin/sh

MOD_DATE="20261025";
TARGET="SukiSU_Ultra";
FOX_INSTALLER_DEBUG_MODE=1;

SCREEN=/proc/self/fd/$2;
ZIPFILE="$3";
KSUD=$(which ksud 2>/dev/null);

BOOTMODE=false;
ps | grep zygote | grep -v grep >/dev/null && BOOTMODE=true;
$BOOTMODE || ps -A 2>/dev/null | grep zygote | grep -v grep >/dev/null && BOOTMODE=true;

$BOOTMODE && TMP_DIR=/dev/tmp || TMP_DIR=/tmp;
mkdir -p $TMP_DIR;
EX_DIR=$TMP_DIR/ofox_ksu_installer;

ui_print() {
  if [ "$BOOTMODE" = "true" ]; then
    echo "$1";
  else
    until [ ! "$1" ]; do
      echo -e "ui_print $1\\nui_print" >> $SCREEN;
      shift;
    done
  fi
}

cleanup() {
   rm -rf $EX_DIR;
}

abort() {
   ui_print "$*";
   cleanup;
   exit 1;
}

# Unpack installer package
ui_print "*******************************************";
ui_print "*** |OrangeFox Recovery SukiSU Addon|   ***";
ui_print "***   |SukiSU Ultra v4.2.1-r2 Installer|***";
ui_print "***   |Kernel 6.12 GKI Boot Patcher|   ***";
ui_print "*******************************************";
ui_print " ";

if [ "$BOOTMODE" = "true" ]; then
    abort "Error: Running on Android system. Please flash inside OrangeFox Recovery.";
fi

mkdir -p $EX_DIR;
cd $EX_DIR || abort "Error: Failed to create temp directory";
unzip -o "$ZIPFILE" || abort "Error: Failed to extract installer zip";

# Locate ksud
if [ -z "$KSUD" ] || [ ! -x "$KSUD" ]; then
    if [ -f "$EX_DIR/ksud" ]; then
        cp -f "$EX_DIR/ksud" /sbin/ksud 2>/dev/null || cp -f "$EX_DIR/ksud" /tmp/ksud 2>/dev/null;
        chmod 0755 /sbin/ksud 2>/dev/null || chmod 0755 /tmp/ksud 2>/dev/null;
        KSUD=$(which ksud 2>/dev/null);
        [ -z "$KSUD" ] && [ -x /sbin/ksud ] && KSUD=/sbin/ksud;
        [ -z "$KSUD" ] && [ -x /tmp/ksud ] && KSUD=/tmp/ksud;
    fi
fi
[ -z "$KSUD" ] && abort "Error: 'ksud' binary could not be found or executed.";

# Resolve slot and boot block device
SLOT=$(getprop ro.boot.slot_suffix 2>/dev/null);
if [ -z "$SLOT" ]; then
    SLOT=$(getprop ro.boot.slot 2>/dev/null);
    [ -n "$SLOT" ] && SLOT="_$SLOT";
fi
[ -z "$SLOT" ] && SLOT="_a";

BOOT_DEV="";
for dev in \\
    "/dev/block/by-name/boot$SLOT" \\
    "/dev/block/bootdevice/by-name/boot$SLOT" \\
    "/dev/block/platform/*/by-name/boot$SLOT" \\
    "/dev/block/by-name/boot" \\
    "/dev/block/bootdevice/by-name/boot"; do
    if [ -e "$dev" ]; then
        # Verify valid ANDROID! header
        magic=$(toybox head -c 8 "$dev" 2>/dev/null);
        [ -z "$magic" ] && magic=$(head -c 8 "$dev" 2>/dev/null);
        if [ "$magic" = "ANDROID!" ]; then
            BOOT_DEV="$dev";
            break;
        fi
    fi
done

if [ -z "$BOOT_DEV" ]; then
    # Fallback to direct by-name node
    [ -e "/dev/block/by-name/boot$SLOT" ] && BOOT_DEV="/dev/block/by-name/boot$SLOT";
    [ -z "$BOOT_DEV" ] && [ -e "/dev/block/by-name/boot" ] && BOOT_DEV="/dev/block/by-name/boot";
fi

[ -z "$BOOT_DEV" ] && abort "Error: Boot partition device could not be resolved.";

ui_print "- Target Boot Partition: $BOOT_DEV (Slot: $SLOT)";

# Resolve SukiSU kernel module
MODULE_FILE="$EX_DIR/android16-6.12_kernelsu.ko";
if [ ! -f "$MODULE_FILE" ]; then
    MODULE_FILE=$(ls $EX_DIR/*6.12*kernelsu.ko 2>/dev/null | head -n 1);
fi
[ -z "$MODULE_FILE" ] || [ ! -f "$MODULE_FILE" ] && abort "Error: android16-6.12_kernelsu.ko not found in package.";

ui_print "- Selected SukiSU Module: $(basename "$MODULE_FILE")";

# Ensure temp directory for ksud
export TMPDIR=/tmp;
mkdir -p /tmp/ksud /data/local/tmp 2>/dev/null || true;

ui_print " ";
ui_print "Patching and flashing boot partition with SukiSU Ultra...";
"$KSUD" boot-patch "$BOOT_DEV" --module "$MODULE_FILE" --flash;
RET=$?;

if [ $RET -ne 0 ]; then
    ui_print "Warning: Direct block patch returned $RET, attempting file-based staging...";
    TMP_BOOT=/tmp/stock_boot.img;
    TMP_PATCHED=/tmp/patched_boot.img;
    rm -f $TMP_BOOT $TMP_PATCHED;
    dd if="$BOOT_DEV" of=$TMP_BOOT bs=4096 count=16384 2>/dev/null;
    "$KSUD" boot-patch $TMP_BOOT --module "$MODULE_FILE" --out $TMP_PATCHED;
    if [ $? -eq 0 ] && [ -s $TMP_PATCHED ]; then
        ui_print "- Writing patched boot image to $BOOT_DEV...";
        dd if=$TMP_PATCHED of="$BOOT_DEV" bs=4096 2>/dev/null;
        sync;
        RET=0;
    fi
    rm -f $TMP_BOOT $TMP_PATCHED;
fi

if [ $RET -ne 0 ]; then
    abort "Error: SukiSU boot-patch failed (exit code $RET). Check /tmp/recovery.log.";
fi

ui_print " ";
ui_print "==========================================";
ui_print "SukiSU Ultra v4.2.1-r2 Installed Successfully!";
ui_print "Target Partition: $BOOT_DEV";
ui_print "Kernel: 6.12 GKI / Android 16";
ui_print "==========================================";

cleanup;
exit 0;
"""
    with open(ub_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(update_binary_content)
    print("  Injected robust SukiSU boot.img patcher update-binary")

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

def find_zip(target_dir, name):
    if not os.path.exists(target_dir):
        return None
    for root, dirs, files in os.walk(target_dir):
        if name in files:
            return os.path.join(root, name)
    return None

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"=== Root Suites Updater: Target SukiSU Ultra v4.2.1-r2 (Target: {target_dir}) ===")
    work_dir = tempfile.mkdtemp()
    
    try:
        # SukiSU-Ultra v4.2.1-r2
        suki_zip = find_zip(target_dir, "KernelSU_Suki_Installer.zip")
        if suki_zip:
            print(f"\n--- Upgrading SukiSU-Ultra to v4.2.1-r2 ({suki_zip}) ---")
            suki_base = "https://github.com/SukiSU-Ultra/SukiSU-Ultra/releases/download/v4.2.1-r2/"
            suki_mods = {
                "android16-6.12_kernelsu.ko": suki_base + "lkm-aarch64-android16-6.12_kernelsu.ko",
                "android15-6.6_kernelsu.ko": suki_base + "lkm-aarch64-android15-6.6_kernelsu.ko",
                "android14-6.1_kernelsu.ko": suki_base + "lkm-aarch64-android14-6.1_kernelsu.ko",
                "ksud": suki_base + "ksud-aarch64-linux-android"
            }
            new_suki = {}
            for name, url in suki_mods.items():
                p = os.path.join(work_dir, "suki_" + name)
                download_file(url, p)
                new_suki[name] = p
                
            suki_source = "v4.2.1-r2:\nhttps://github.com/SukiSU-Ultra/SukiSU-Ultra/releases/tag/v4.2.1-r2\n"
            update_zip_contents(suki_zip, new_suki, suki_source)

    finally:
        shutil.rmtree(work_dir)
    print("\nSukiSU Ultra installer upgraded successfully to latest release!")

if __name__ == '__main__':
    main()
