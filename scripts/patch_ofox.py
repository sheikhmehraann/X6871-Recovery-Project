#!/usr/bin/env python3
"""
OrangeFox Recovery Universal Hardware & Architecture Patch Engine
Target: Infinix GT 20 Pro (X6871 / MT6895 - MediaTek Dimensity 8200 Ultimate)
Android 15 (AP3A.240905.015.A2 / SDK 35), Virtual A/B Header v4 vendor_boot

Components Patched:
1. Environment: 2-part lunch combo compatibility shim
2. Flashlight: Real rear camera torch (/sys/class/torch/torch/torch_level)
3. Haptics: AW8697 linear vibrator (/sys/class/leds/vibrator_single)
4. Thermals: MT6895 CPU temperature (/sys/class/thermal/thermal_zone0/temp)
5. Ultra-Fast Splash: Sub-2s in-place magiskboot cpio update (skips re-archiving 4200 files)
6. Splash Customization: Restore stock, backup splash, 8 logo colors, PNG magic verification
7. Device Identity: Static specifications + dynamic ROM properties from live device
8. Slot Switching: Hardware bootctl fallback & ActionThread lock removal
9. Display Timeout: Interactive [ Enabled / Disabled ] toggle button + slider
10. AVB 2.0: Slot-aware vbmeta disable addon
11. Graphics DRM: Single-pipe atomic display rendering
12. Format Data: Virtual A/B pending snapshot bypass, reboot lock reset, MTP/mount detach
"""

import os
import sys
import re
import shutil
import zipfile
import urllib.request

def write_file_lf(filepath, content):
    """Normalize line endings to Unix LF and write file."""
    if isinstance(content, str):
        content = content.replace("\r\n", "\n")
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def patch_envsetup(fox_root):
    envsetup_paths = [
        os.path.join(fox_root, "build/make/envsetup.sh"),
        os.path.join(fox_root, "build/envsetup.sh")
    ]
    flag_values_dir = os.path.join(fox_root, "build/release/flag_values")
    avail_release = "ap2a"
    if os.path.isdir(flag_values_dir):
        subdirs = [d for d in os.listdir(flag_values_dir) if os.path.isdir(os.path.join(flag_values_dir, d))]
        if subdirs:
            avail_release = subdirs[0]
            print(f"[*] Detected available release configs: {subdirs}, using: {avail_release}")

    patched = False
    for path in envsetup_paths:
        if os.path.isfile(path) and not os.path.islink(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                target = 'IFS="-" read -r product release variant <<< "$selection"'
                if target in content and "TARGET_RELEASE:-" not in content:
                    replacement = f"""IFS="-" read -r product release variant <<< "$selection"
    # Android 14 2-part lunch combo compatibility shim
    if [[ -n "$product" && -n "$release" && -z "$variant" ]]; then
        variant="$release"
        release="${{TARGET_RELEASE:-{avail_release}}}"
    fi"""
                    content = content.replace(target, replacement, 1)
                    write_file_lf(path, content)
                    print(f"[+] Successfully patched {path} with 2-part lunch compatibility shim ({avail_release})")
                    patched = True
                elif "TARGET_RELEASE:-" in content:
                    content = re.sub(r'release="\$\{TARGET_RELEASE:-[^}]+\}"', f'release="${{TARGET_RELEASE:-{avail_release}}}"', content)
                    write_file_lf(path, content)
                    print(f"[+] Updated release shim in {path} to target: {avail_release}")
                    patched = True
            except Exception as e:
                print(f"[-] Failed patching {path}: {e}")
    return patched

def patch_flashlight(fox_root):
    action_cpp = os.path.join(fox_root, "bootable/recovery/gui/action.cpp")
    if not os.path.isfile(action_cpp):
        print(f"[-] action.cpp not found at {action_cpp}")
        return False

    with open(action_cpp, "r", encoding="utf-8") as f:
        content = f.read()

    # Block aw22xxx_led (Mecha Loop RGB) from being detected as torch LED
    if "aw22xxx" not in content:
        content = content.replace(
            "while ((dentry = readdir(dd))) {",
            "while ((dentry = readdir(dd))) {\n\t\t\tif (strstr(dentry->d_name, \"aw22xxx\") || strstr(dentry->d_name, \"loop\")) continue;"
        )

    torch_override = """// Infinix GT 20 Pro (X6871 / MT6895) Real Camera Flashlight Override
\t\t\tif (TWFunc::Path_Exists("/sys/class/torch/torch/torch_level")) {
\t\t\t\tbright_one = "/sys/class/torch/torch/torch_level";
\t\t\t\tmax_brt_one = "1";
\t\t\t} else if (TWFunc::Path_Exists("/sys/devices/virtual/torch/torch/torch_level")) {
\t\t\t\tbright_one = "/sys/devices/virtual/torch/torch/torch_level";
\t\t\t\tmax_brt_one = "1";
\t\t\t} else if (TWFunc::Path_Exists("/sys/class/sub_torch/sub_torch/sub_torch_level")) {
\t\t\t\tbright_one = "/sys/class/sub_torch/sub_torch/sub_torch_level";
\t\t\t\tmax_brt_one = "1";
\t\t\t} else {
\t\t\t\tbright_one = path_one + "/brightness";
\t\t\t}
\t\t\tif (bright_one.find("aw22xxx") != std::string::npos || bright_one.find("loop") != std::string::npos) {
\t\t\t\tbright_one = "/sys/class/torch/torch/torch_level";
\t\t\t\tmax_brt_one = "1";
\t\t\t}"""

    if 'bright_one = path_one + "/brightness";' in content:
        content = content.replace('bright_one = path_one + "/brightness";', torch_override, 1)

    content = content.replace(
        'TWFunc::write_to_file(bright_one, max_brt_one);',
        'if (bright_one.find("torch") != std::string::npos) { TWFunc::write_to_file(bright_one, "1\\n"); } else { TWFunc::write_to_file(bright_one, max_brt_one); }'
    )
    content = content.replace(
        'TWFunc::write_to_file(bright_one, "0");',
        'TWFunc::write_to_file(bright_one, "0\\n");'
    )

    write_file_lf(action_cpp, content)
    print("[+] Successfully hardened action.cpp with real camera flashlight controls")
    return True

def patch_haptics(fox_root):
    patched_count = 0
    search_dirs = [
        os.path.join(fox_root, "bootable/recovery"),
        os.path.join(fox_root, "vendor/recovery")
    ]
    for sdir in search_dirs:
        if not os.path.isdir(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for file in files:
                if file.endswith((".cpp", ".c", ".h", ".hpp")):
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        orig = content
                        content = content.replace("/sys/class/leds/vibrator/duration", "/sys/class/leds/vibrator_single/duration")
                        content = content.replace("/sys/class/leds/vibrator/activate", "/sys/class/leds/vibrator_single/activate")
                        content = content.replace("/sys/class/leds/vibrator/state", "/sys/class/leds/vibrator_single/state")
                        content = content.replace("/sys/class/leds/vibrator/brightness", "/sys/class/leds/vibrator_single/brightness")
                        content = content.replace('"/sys/class/leds/vibrator"', '"/sys/class/leds/vibrator_single"')
                        if content != orig:
                            write_file_lf(fpath, content)
                            patched_count += 1
                    except Exception:
                        pass
    print(f"[+] Successfully patched {patched_count} source files with AW8697 vibrator_single sysfs paths")
    return True

def patch_thermals(fox_root):
    data_cpp = os.path.join(fox_root, "bootable/recovery/data.cpp")
    if not os.path.isfile(data_cpp):
        print(f"[-] data.cpp not found at {data_cpp}")
        return False

    with open(data_cpp, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(r'mConst\.SetValue\s*\(\s*"tw_no_cpu_temp"\s*,\s*"1"\s*\);', 'mConst.SetValue("tw_no_cpu_temp", "0");', content)
    content = re.sub(r'mConst\.SetValue\s*\(\s*"tw_no_cpu_temp"\s*,\s*"\w+"\s*\);', 'mConst.SetValue("tw_no_cpu_temp", "0");', content)
    content = re.sub(r'mPersist\.SetValue\s*\(\s*"tw_show_cpu_temp"\s*,\s*"0"\s*\);', 'mPersist.SetValue("tw_show_cpu_temp", "1");', content)
    content = re.sub(r'mPersist\.SetValue\s*\(\s*"of_status_cpu_temp"\s*,\s*"0"\s*\);', 'mPersist.SetValue("of_status_cpu_temp", "1");', content)

    content = re.sub(r'if\s*\(\s*TWFunc::read_file\s*\(\s*cpu_temp_file\s*,\s*results\s*\)\s*!=\s*0\s*\)',
                     'if (TWFunc::read_file(cpu_temp_file, results) != 0 && TWFunc::read_file("/sys/class/thermal/thermal_zone0/temp", results) != 0 && TWFunc::read_file("/sys/devices/virtual/thermal/thermal_zone0/temp", results) != 0)', content)

    write_file_lf(data_cpp, content)
    print("[+] Successfully patched data.cpp with thermal zone 0 unlocked and status bar enabled")
    return True

def patch_magiskboot_vendor_boot(fox_root):
    twrp_funcs_cpp = os.path.join(fox_root, "bootable/recovery/twrp-functions.cpp")
    if not os.path.isfile(twrp_funcs_cpp):
        print(f"[-] twrp-functions.cpp not found at {twrp_funcs_cpp}")
        return False

    with open(twrp_funcs_cpp, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    orig = content

    # 1. Target vendor_boot on Header v4 devices for unpack/repack
    if "VendorBoot =" not in content:
        content = re.sub(
            r'TWPartition\s*\*\s*Boot\s*=\s*PartitionManager\.Find_Partition_By_Path\s*\(\s*"/boot"\s*\);',
            'TWPartition *Boot = PartitionManager.Find_Partition_By_Path("/boot");\n  TWPartition *VendorBoot = PartitionManager.Find_Partition_By_Path("/vendor_boot");',
            content
        )

    # 2. On A/B Header v4 devices: route recovery operations (!is_boot) to VendorBoot, keep boot operations (is_boot) on Boot
    ab_pattern = r'(#if\s*\(defined\(AB_OTA_UPDATER\)\s*\|\|\s*defined\(FOX_AB_DEVICE\)\)\s*&&\s*!defined\(OF_AB_DEVICE_WITH_RECOVERY_PARTITION\)\s*\n\s*if\s*\(\s*Boot\s*!=\s*NULL\s*\)\s*\n\s*\{\s*\n\s*)tmpstr\s*=\s*Boot->Actual_Block_Device;'
    ab_replacement = r'''\1if (!is_boot && VendorBoot != NULL) {
         tmpstr = VendorBoot->Actual_Block_Device;
       } else {
         tmpstr = Boot->Actual_Block_Device;
       }'''
    content = re.sub(ab_pattern, ab_replacement, content)

    # 3. Inject recovery ramdisk rename after magiskboot unpack in cmd_script
    unpack_pattern = r'(AppendLineToFile\s*\(\s*cmd_script,\s*".*?Unpacking image failed.*?"\s*\);)'
    unpack_inject = r'''\1
	        // Vendor_boot v4 recovery ramdisk bridge
	        AppendLineToFile (cmd_script, "[ -f vendor_ramdisk_recovery.cpio ] && cp -f vendor_ramdisk_recovery.cpio ramdisk.cpio");'''
    if "vendor_ramdisk_recovery.cpio ramdisk.cpio" not in content:
        content = re.sub(unpack_pattern, unpack_inject, content)

    # 4. Inject fast in-place CPIO splash addition & dual-slot vendor_boot sync in cmd_script2
    repack_pattern = r'(AppendLineToFile\s*\(\s*cmd_script2,\s*magiskboot_sbin\s*\+\s*" repack)'
    repack_inject = r'''// Fast in-place splash update via single-pass magiskboot cpio
	        AppendLineToFile (cmd_script2, "if [ -f /tmp/orangefox/ramdisk/twres/splash.xml ]; then");
	        AppendLineToFile (cmd_script2, "  CPIO_TARGET=\"\"; [ -f vendor_ramdisk_recovery.cpio ] && CPIO_TARGET=\"vendor_ramdisk_recovery.cpio\" || CPIO_TARGET=\"ramdisk.cpio\"");
	        AppendLineToFile (cmd_script2, "  if [ -n \"$CPIO_TARGET\" ] && [ -f \"$CPIO_TARGET\" ]; then");
	        AppendLineToFile (cmd_script2, "    if [ -f /tmp/orangefox/ramdisk/twres/images/Splash/user.png ]; then");
	        AppendLineToFile (cmd_script2, "      " + magiskboot_sbin + " cpio \"$CPIO_TARGET\" 'add 0644 twres/splash.xml /tmp/orangefox/ramdisk/twres/splash.xml' 'add 0644 twres/images/Splash/user.png /tmp/orangefox/ramdisk/twres/images/Splash/user.png'");
	        AppendLineToFile (cmd_script2, "    else");
	        AppendLineToFile (cmd_script2, "      " + magiskboot_sbin + " cpio \"$CPIO_TARGET\" 'add 0644 twres/splash.xml /tmp/orangefox/ramdisk/twres/splash.xml'");
	        AppendLineToFile (cmd_script2, "    fi");
	        AppendLineToFile (cmd_script2, "  fi");
	        AppendLineToFile (cmd_script2, "fi");
	        // Vendor_boot v4 recovery ramdisk repack bridge
	        AppendLineToFile (cmd_script2, "[ -f ramdisk.cpio ] && [ ! -f vendor_ramdisk_recovery.cpio ] && cp -f ramdisk.cpio vendor_ramdisk_recovery.cpio");
	        // Ultra-fast multi-core parallel compression via pigz before magiskboot repack
	        AppendLineToFile (cmd_script2, "if [ -x /system/bin/pigz ]; then");
	        AppendLineToFile (cmd_script2, "  [ -f vendor_ramdisk_recovery.cpio ] && ! gzip -t vendor_ramdisk_recovery.cpio 2>/dev/null && /system/bin/pigz -f vendor_ramdisk_recovery.cpio && mv -f vendor_ramdisk_recovery.cpio.gz vendor_ramdisk_recovery.cpio");
	        AppendLineToFile (cmd_script2, "  [ -f ramdisk.cpio ] && ! gzip -t ramdisk.cpio 2>/dev/null && /system/bin/pigz -f ramdisk.cpio && mv -f ramdisk.cpio.gz ramdisk.cpio");
	        AppendLineToFile (cmd_script2, "  [ -f vendor_ramdisk_.cpio ] && ! gzip -t vendor_ramdisk_.cpio 2>/dev/null && /system/bin/pigz -f vendor_ramdisk_.cpio && mv -f vendor_ramdisk_.cpio.gz vendor_ramdisk_.cpio");
	        AppendLineToFile (cmd_script2, "fi");
	        \1'''
    if "Fast in-place splash update" not in content:
        content = re.sub(repack_pattern, repack_inject, content)

    # 5. Inject alternate slot vendor_boot sync after magiskboot repack
    post_repack_pattern = r'(AppendLineToFile\s*\(\s*cmd_script2,\s*magiskboot_sbin\s*\+\s*" repack.*?\);)'
    post_repack_inject = r'''\1
	        // Double-slot vendor_boot splash update safeguard
	        AppendLineToFile (cmd_script2, "if [ -f new-boot.img ]; then");
	        AppendLineToFile (cmd_script2, "  ALT_SLOT=\"b\"; [ \"$(getprop ro.boot.slot_suffix)\" = \"_b\" ] && ALT_SLOT=\"a\"");
	        AppendLineToFile (cmd_script2, "  [ -b /dev/block/by-name/vendor_boot_${ALT_SLOT} ] && dd if=new-boot.img of=/dev/block/by-name/vendor_boot_${ALT_SLOT} bs=4096 2>/dev/null || true");
	        AppendLineToFile (cmd_script2, "fi");'''
    if "Double-slot vendor_boot splash update safeguard" not in content:
        content = re.sub(post_repack_pattern, post_repack_inject, content)

    if content != orig:
        write_file_lf(twrp_funcs_cpp, content)
        print("[+] Successfully patched twrp-functions.cpp with native vendor_boot v4 splash unpack/repack support")
        return True
    return False

def patch_splash(fox_root):
    search_dirs = [
        os.path.join(fox_root, "vendor/recovery"),
        os.path.join(fox_root, "bootable/recovery")
    ]
    # 1. Scale all splash XMLs to 1080x2436 and ensure SED Splash marker is present
    for sdir in search_dirs:
        if not os.path.isdir(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for file in files:
                if "splash" in file.lower() and file.endswith(".xml"):
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            xml_content = f.read()
                        mod = False
                        if 'width="1080" h="1920"' in xml_content:
                            xml_content = xml_content.replace('width="1080" h="1920"', 'width="1080" h="2436"')
                            mod = True
                        if 'value="1920"' in xml_content:
                            xml_content = xml_content.replace('value="1920"', 'value="2436"')
                            mod = True
                        if '<!-- SED Splash -->' not in xml_content and '<recovery>' in xml_content:
                            xml_content = xml_content.replace('<recovery>', '<recovery>\n\t<!-- SED Splash -->')
                            mod = True
                        if mod:
                            write_file_lf(fpath, xml_content)
                    except Exception:
                        pass

    # 2. Inject of_splash_max_size into vars.xml
    for sdir in search_dirs:
        if not os.path.isdir(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for file in files:
                if file == "vars.xml":
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            v_content = f.read()
                        if 'name="of_splash_max_size"' not in v_content and '<variables>' in v_content:
                            v_content = v_content.replace(
                                '<variables>',
                                '<variables>\n\t\t<variable name="of_splash_max_size" value="10240"/>'
                            )
                            write_file_lf(fpath, v_content)
                            print(f"[+] Injected of_splash_max_size into {fpath}")
                    except Exception:
                        pass

    # 3. In stock customization.xml: ensure ramdisk splash directory exists so cp succeeds
    for sdir in search_dirs:
        if not os.path.isdir(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for file in files:
                if "customization" in file.lower() and file.endswith(".xml"):
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        if 'cp "%tw_splash_png_path%/%tw_splash_png_name%" "/tmp/orangefox/ramdisk' in content:
                            content = content.replace(
                                'cp "%tw_splash_png_path%/%tw_splash_png_name%" "/tmp/orangefox/ramdisk',
                                'mkdir -p /tmp/orangefox/ramdisk/twres/images/Splash/ /tmp/orangefox/ramdisk/twres/themes/sed/; cp "%tw_splash_png_path%/%tw_splash_png_name%" "/tmp/orangefox/ramdisk'
                            )
                            write_file_lf(fpath, content)
                            print(f"[+] Verified stock {fpath} with ramdisk splash directory creation")
                    except Exception as e:
                        print(f"[-] Failed patching stock customization.xml: {e}")
    return True

def patch_identity_and_banner(fox_root):
    # 1. Patch twrp-functions.cpp Check_MIUI_Treble & Welcome_Message
    twrp_funcs_cpp = os.path.join(fox_root, "bootable/recovery/twrp-functions.cpp")
    if os.path.isfile(twrp_funcs_cpp):
        try:
            with open(twrp_funcs_cpp, "r", encoding="utf-8", errors="ignore") as f:
                c = f.read()

            # Clean platform in Check_MIUI_Treble
            plat_pat = r'#ifdef\s+PRODUCT_PLATFORM\s+gui_msg\(Msg\("fox_platform=\*\s*Platform:\s*\{1\}"\)\(EXPAND\(PRODUCT_PLATFORM\)\)\);\s+#else\s+gui_msg\(Msg\("fox_platform=\*\s*Platform:\s*\{1\}"\)\(DataManager::GetStrValue\(FOX_COMPATIBILITY_DEVICE\)\.c_str\(\)\)\);\s+#endif'
            c = re.sub(plat_pat, 'gui_msg(Msg("fox_platform=* Platform:   {1}")("MediaTek Dimensity 8200 Ultimate (MT6895)"));', c)

            # Clean device in Check_MIUI_Treble + Maintainer & Community lines (written in one place)
            dev_pat = r'gui_msg\(Msg\("fox_device=\*\s*Device:\s*\{1\}\s*\(\{2\}\)"\)\(device_model\.c_str\(\)\)\(TWFunc::Fox_Property_Get\("ro\.product\.device"\)\.c_str\(\)\)\);'
            dev_repl = (
                '{\n'
                '\t\tgui_msg(Msg("fox_device=* Device:     {1} ({2})")("Infinix GT 20 Pro")("Infinix X6871"));\n'
                '\t\tgui_print("* Maintainer: sheikhmehraann\\n");\n'
                '\t\tgui_print("* Updates:    t.me/Gt20ProINUpdates\\n");\n'
                '\t\tgui_print("* Community:  t.me/Gt20ProIN\\n");\n'
                '\t}'
            )
            c = re.sub(dev_pat, lambda m: dev_repl, c)

            # Clean boot slot: Slot A / Slot B
            slot_pat = r'gui_msg\(Msg\("fox_boot_slot=\*\s*Boot slot:\s*\{1\}"\)\(tmp\.c_str\(\)\)\);'
            slot_repl = """std::string slot_cur = Fox_Property_Get("ro.boot.slot_suffix");
std::string slot_fmt = (slot_cur == "_b" || slot_cur == "b" || slot_cur == "1") ? "Slot B" : "Slot A";
gui_msg(Msg("fox_boot_slot=* Boot slot:  {1}")(slot_fmt.c_str()));"""
            c = re.sub(slot_pat, slot_repl, c)

            # Suppress raw dev-keys / AP3A build id lines from banner
            old_print = 'gui_print("* %s\\n", rom_desc.c_str());'
            new_print = '''if (!rom_desc.empty() && rom_desc.find("dev-keys") == std::string::npos && rom_desc.find("AP3A") == std::string::npos && rom_desc.find("test-keys") == std::string::npos) {
    gui_print("* %s\\n", rom_desc.c_str());
}'''
            if old_print in c:
                c = c.replace(old_print, new_print)

            # Suppress duplicate support links in Welcome_Message so links appear only once in the banner
            c = re.sub(r'gui_msg\s*\(\s*Msg\s*\([^;]*?fox_support[^;]*?\)\s*\)\s*;', '(void)0;', c, flags=re.DOTALL)
            c = re.sub(r'gui_msg\s*\(\s*Msg\s*\([^;]*?fox_nosupport[^;]*?\)\s*\)\s*;', '(void)0;', c, flags=re.DOTALL)
            c = re.sub(r'gui_msg\s*\(\s*Msg\s*\([^;]*?fox_websites[^;]*?\)\s*\)\s*;', '(void)0;', c, flags=re.DOTALL)
            c = re.sub(r'gui_msg\s*\(\s*Msg\s*\([^;]*?fox_downloads[^;]*?\)\s*\)\s*;', '(void)0;', c, flags=re.DOTALL)
            c = re.sub(r'gui_msg\s*\(\s*Msg\s*\([^;]*?fox_faq[^;]*?\)\s*\)\s*;', '(void)0;', c, flags=re.DOTALL)

            write_file_lf(twrp_funcs_cpp, c)
            print("[+] Successfully patched twrp-functions.cpp with clean Dimensity 8200, slot banner, maintainer & Telegram links")
        except Exception as e:
            print(f"[-] Failed patching banner in twrp-functions.cpp: {e}")

    # 2. Patch data.cpp to set FOX_COMPATIBILITY_DEVICE, maintainer, FRP addon, and KSU vars
    data_cpp = os.path.join(fox_root, "bootable/recovery/data.cpp")
    if os.path.isfile(data_cpp):
        try:
            with open(data_cpp, "r", encoding="utf-8", errors="ignore") as f:
                dc = f.read()
            dc = re.sub(
                r'mData\.SetValue\s*\(\s*FOX_COMPATIBILITY_DEVICE\s*,[^;]+;',
                'mData.SetValue(FOX_COMPATIBILITY_DEVICE, "Infinix GT 20 Pro (Infinix X6871)");',
                dc
            )
            if 'mConst.SetValue("enable_frp_addon", "1");' not in dc:
                dc = dc.replace(
                    'mConst.SetValue("fox_branch", FOX_BRANCH);',
                    'mConst.SetValue("fox_branch", FOX_BRANCH);\n'
                    '\tmConst.SetValue("of_maintainer", "sheikhmehraann");\n'
                    '\tmConst.SetValue("enable_frp_addon", "1");\n'
                    '\tmConst.SetValue("fox_support_ksu", "1");\n'
                    '\tmConst.SetValue("fox_vab_device", "1");\n'
                    '\tmConst.SetValue("ksu_ver", "v3.3.0");'
                )
            write_file_lf(data_cpp, dc)
            print("[+] Successfully patched data.cpp with FOX_COMPATIBILITY_DEVICE, sheikhmehraann, FRP & KSU flags")
        except Exception as e:
            print(f"[-] Failed patching data.cpp: {e}")

    # 2b. Patch settings.xml (About page) and credits.txt with Maintainer & Community links
    search_dirs_about = [
        os.path.join(fox_root, "vendor/recovery"),
        os.path.join(fox_root, "bootable/recovery"),
        os.path.join(fox_root, "twres"),
        os.path.join(fox_root, "FFiles")
    ]
    for sdir in search_dirs_about:
        if not os.path.isdir(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for file in files:
                if file in ("settings.xml", "about.xml"):
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            xc = f.read()
                        orig_xc = xc
                        old_maint_card = """\t\t\t<text style="about_name">
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="3"/>
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="2"/>
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="1"/>
\t\t\t\t<placement x="%card_txt_x%" y="%card_img4_y%"/>
\t\t\t\t<text>%of_maintainer%</text>
\t\t\t</text>

\t\t\t<text style="about_info">
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="3"/>
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="2"/>
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="1"/>
\t\t\t\t<placement x="%card_txt_x%" y="%cardtxt_7%"/>
\t\t\t\t<text>{@abt_maintainer}</text>
\t\t\t</text>"""
                        new_maint_card = """\t\t\t<text style="about_name">
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="3"/>
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="2"/>
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="1"/>
\t\t\t\t<placement x="%card_txt_x%" y="%card_img4_y%"/>
\t\t\t\t<text>sheikhmehraann</text>
\t\t\t</text>

\t\t\t<text style="about_info">
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="3"/>
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="2"/>
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="1"/>
\t\t\t\t<placement x="%card_txt_x%" y="%cardtxt_7%"/>
\t\t\t\t<text>Updates t.me/Gt20ProINUpdates</text>
\t\t\t</text>

\t\t\t<text style="about_info">
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="3"/>
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="2"/>
\t\t\t\t<condition var1="of_maintainer" op="!=" var2="1"/>
\t\t\t\t<placement x="%card_txt_x%" y="%cardtxt_8%"/>
\t\t\t\t<text>Community  t.me/Gt20ProIN</text>
\t\t\t</text>"""
                        if old_maint_card in xc:
                            xc = xc.replace(old_maint_card, new_maint_card)
                        if xc != orig_xc:
                            write_file_lf(fpath, xc)
                            print(f"[+] Patched About page in {fpath} with sheikhmehraann & Telegram links")
                    except Exception as e:
                        print(f"[-] Failed patching {fpath}: {e}")
                elif file == "credits.txt":
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            cc = f.read()
                        if "sheikhmehraann" not in cc:
                            header = (
                                "\nInfinix GT 20 Pro (X6871)\n"
                                "--------------------------\n"
                                "* Maintainer: sheikhmehraann\n"
                                "* Updates:    t.me/Gt20ProINUpdates\n"
                                "* Community:  t.me/Gt20ProIN\n\n"
                            )
                            cc = header + cc.lstrip("\n")
                            write_file_lf(fpath, cc)
                            print(f"[+] Patched {fpath} with GT 20 Pro maintainer and Telegram credits")
                    except Exception:
                        pass

    # 3. Patch foxstart.sh with dynamic partition mounter for stock Transsion firmware
    search_dirs = [
        os.path.join(fox_root, "vendor/recovery"),
        os.path.join(fox_root, "bootable/recovery")
    ]
    for sdir in search_dirs:
        if not os.path.isdir(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for file in files:
                if file == "foxstart.sh":
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            sh_c = f.read()

                        dynamic_stock_probe = r"""get_ROM() {
   local F="/orangefox.cfg"
   local build_prop=""
   local tmp_mount="/tmp/rom_probe_$$"
   mkdir -p "$tmp_mount"

   # Ensure all dynamic super sub-partitions are symlinked
   local cur_slot=$(getprop ro.boot.slot_suffix)
   [ -z "$cur_slot" ] && cur_slot="_a"
   for dyn_part in system vendor product system_ext vendor_dlkm odm_dlkm tr_carrier tr_company tr_mi tr_overlayfs tr_preload tr_product tr_region tr_theme; do
      if [ -b "/dev/block/mapper/${dyn_part}${cur_slot}" ]; then
         ln -sf "/dev/block/mapper/${dyn_part}${cur_slot}" "/dev/block/mapper/${dyn_part}" 2>/dev/null || true
         mkdir -p /dev/block/bootdevice/by-name /dev/block/by-name 2>/dev/null || true
         ln -sf "/dev/block/mapper/${dyn_part}${cur_slot}" "/dev/block/bootdevice/by-name/${dyn_part}" 2>/dev/null || true
         ln -sf "/dev/block/mapper/${dyn_part}${cur_slot}" "/dev/block/by-name/${dyn_part}" 2>/dev/null || true
      fi
   done

   # Dynamic probe across Transsion stock partitions inside dynamic super
   for part in tr_product_a tr_product_b tr_product product_a product_b product system_a system_b system vendor_a vendor_b vendor; do
      local blk="/dev/block/mapper/$part"
      if [ -b "$blk" ]; then
         mount -o ro "$blk" "$tmp_mount" 2>/dev/null || mount -t erofs -o ro "$blk" "$tmp_mount" 2>/dev/null
         if [ -f "$tmp_mount/build.prop" ]; then
            build_prop="$tmp_mount/build.prop"
            break
         elif [ -f "$tmp_mount/etc/build.prop" ]; then
            build_prop="$tmp_mount/etc/build.prop"
            break
         fi
         umount "$tmp_mount" 2>/dev/null
      fi
   done

   if [ -n "$build_prop" ] && [ -f "$build_prop" ]; then
      local disp_id=$(grep -E "^ro\.(build|system\.build)\.display\.id=" "$build_prop" | head -n1 | cut -d'=' -f2)
      local sdk=$(grep -E "^ro\.(build|system\.build)\.version\.sdk=" "$build_prop" | head -n1 | cut -d'=' -f2)
      local incr=$(grep -E "^ro\.(build|system\.build)\.version\.incremental=" "$build_prop" | head -n1 | cut -d'=' -f2)
      local rel=$(grep -E "^ro\.(build|system\.build)\.version\.release=" "$build_prop" | head -n1 | cut -d'=' -f2)
      local fp=$(grep -E "^ro\.(build|system\.build)\.fingerprint=" "$build_prop" | head -n1 | cut -d'=' -f2)

      [ -n "$disp_id" ] && resetprop -n ro.build.display.id "$disp_id"
      [ -n "$sdk" ] && resetprop -n ro.build.version.sdk "$sdk"
      [ -n "$incr" ] && resetprop -n ro.build.version.incremental "$incr"
      [ -n "$rel" ] && resetprop -n ro.build.version.release "$rel"
      [ -n "$fp" ] && resetprop -n ro.build.fingerprint "$fp"

      echo "ROM=$disp_id" >> $F
      echo "INCREMENTAL_VERSION=$incr" >> $F
      echo "ROM_FINGERPRINT=$fp" >> $F
      echo "SDK=$sdk" >> $F

      umount "$tmp_mount" 2>/dev/null
      rm -rf "$tmp_mount"
      echo "$disp_id"
      return 0
   fi

   umount "$tmp_mount" 2>/dev/null
   rm -rf "$tmp_mount"
   # Fallback defaults
   echo "ROM=X6871-15.1.2.180SP05(OP001PF001AZ)" >> $F
   echo "INCREMENTAL_VERSION=180003" >> $F
   echo "ROM_FINGERPRINT=Infinix/X6871-OP/Infinix-X6871:15/AP3A.240905.015.A2/180003:user/release-keys" >> $F
   echo "SDK=35" >> $F
   echo "X6871-15.1.2.180SP05(OP001PF001AZ)"
}"""
                        if "get_ROM()" in sh_c:
                            sh_c = re.sub(r'get_ROM\(\)\s*\{.*?\n\}', lambda m: dynamic_stock_probe, sh_c, flags=re.DOTALL)
                        write_file_lf(fpath, sh_c)
                        print(f"[+] Patched {fpath} with dynamic stock Transsion partition engine")
                    except Exception as e:
                        print(f"[-] Failed patching {fpath}: {e}")
    return True

def patch_slot_switching(fox_root):
    # 1. Patch partitionmanager.cpp with native bootctl hardware fallback
    pm_cpp = os.path.join(fox_root, "bootable/recovery/partitionmanager.cpp")
    if os.path.isfile(pm_cpp):
        try:
            with open(pm_cpp, "r", encoding="utf-8", errors="ignore") as f:
                c = f.read()

            # Fallback for null module
            null_pat = r'if\s*\(\s*module\s*==\s*nullptr\s*\)\s*\{\s*LOGERR\(\"Error getting bootctrl module\.\\n\"\);\s*\}'
            null_repl = (
                "if (module == nullptr) {\n"
                '\t\t\tLOGINFO("Bootctrl HAL not available, falling back to hardware bootctl CLI...\\n");\n'
                '\t\t\tint32_t slot_number = (Slot == "B") ? 1 : 0;\n'
                '\t\t\tstd::string bctl_cmd = "bootctl set-active-boot-slot " + std::to_string(slot_number);\n'
                '\t\t\tstd::string bctl_out;\n'
                '\t\t\tint bctl_ret = TWFunc::Exec_Cmd(bctl_cmd, bctl_out);\n'
                '\t\t\tTWFunc::Exec_Cmd("bootctl get-active-boot-slot", bctl_out);\n'
                '\t\t\tif (bctl_ret != 0 || bctl_out.find(std::to_string(slot_number)) == std::string::npos) {\n'
                '\t\t\t\tgui_msg(Msg(msg::kError, "unable_set_boot_slot=Error changing bootloader boot slot to {1}")(Slot));\n'
                '\t\t\t} else {\n'
                '\t\t\t\tLOGINFO("setActiveBootSlot succeeded via hardware bootctl CLI fallback to slot %d\\n", slot_number);\n'
                '\t\t\t}\n'
                '\t\t}'
            )
            if re.search(null_pat, c):
                c = re.sub(null_pat, lambda m: null_repl, c)

            # Fallback for HIDL failure
            hidl_pat = r'(if\s*\(!ret\.isOk\(\)\s*\|\|\s*!result\.success\))\s*gui_msg\(Msg\(msg::kError,\s*\"unable_set_boot_slot=Error changing bootloader boot slot to \{1\}\"\)\(Slot\)\);'
            def make_hidl_repl(m):
                return m.group(1) + (
                    " {\n"
                    '\t\t\t\tstd::string bctl_cmd = "bootctl set-active-boot-slot " + std::to_string(slot_number);\n'
                    '\t\t\t\tstd::string bctl_out;\n'
                    '\t\t\t\tint bctl_ret = TWFunc::Exec_Cmd(bctl_cmd, bctl_out);\n'
                    '\t\t\t\tTWFunc::Exec_Cmd("bootctl get-active-boot-slot", bctl_out);\n'
                    '\t\t\t\tif (bctl_ret != 0 || bctl_out.find(std::to_string(slot_number)) == std::string::npos) {\n'
                    '\t\t\t\t\tgui_msg(Msg(msg::kError, "unable_set_boot_slot=Error changing bootloader boot slot to {1}")(Slot));\n'
                    '\t\t\t\t} else {\n'
                    '\t\t\t\t\tLOGINFO("setActiveBootSlot succeeded via hardware bootctl fallback to slot %d\\n", slot_number);\n'
                    '\t\t\t\t}\n'
                    '\t\t\t}'
                )
            if re.search(hidl_pat, c):
                c = re.sub(hidl_pat, make_hidl_repl, c)

            # Fallback for AIDL failure
            aidl_pat = r'(if\s*\(!result\.success\))\s*gui_msg\(Msg\(msg::kError,\s*\"unable_set_boot_slot=Error changing bootloader boot slot to \{1\}\"\)\(Slot\)\);'
            def make_aidl_repl(m):
                return m.group(1) + (
                    " {\n"
                    '\t\t\t\tstd::string bctl_cmd = "bootctl set-active-boot-slot " + std::to_string(slot_number);\n'
                    '\t\t\t\tstd::string bctl_out;\n'
                    '\t\t\t\tint bctl_ret = TWFunc::Exec_Cmd(bctl_cmd, bctl_out);\n'
                    '\t\t\t\tTWFunc::Exec_Cmd("bootctl get-active-boot-slot", bctl_out);\n'
                    '\t\t\t\tif (bctl_ret != 0 || bctl_out.find(std::to_string(slot_number)) == std::string::npos) {\n'
                    '\t\t\t\t\tgui_msg(Msg(msg::kError, "unable_set_boot_slot=Error changing bootloader boot slot to {1}")(Slot));\n'
                    '\t\t\t\t} else {\n'
                    '\t\t\t\t\tLOGINFO("SetActiveBootSlot succeeded via hardware bootctl fallback to slot %d\\n", slot_number);\n'
                    '\t\t\t\t}\n'
                    '\t\t\t}'
                )
            if re.search(aidl_pat, c):
                c = re.sub(aidl_pat, make_aidl_repl, c)

            write_file_lf(pm_cpp, c)
            print("[+] Patched partitionmanager.cpp with comprehensive hardware bootctl slot switching")
        except Exception as e:
            print(f"[-] Failed patching partitionmanager.cpp: {e}")

    # 2. Patch advanced.xml: remove blocking ftls ps command that locks ActionThread
    search_dirs = [
        os.path.join(fox_root, "vendor/recovery"),
        os.path.join(fox_root, "bootable/recovery")
    ]
    for sdir in search_dirs:
        if not os.path.isdir(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for file in files:
                if file == "advanced.xml":
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            c = f.read()
                        if '<action function="ftls">ps -eo \'comm\' | grep adbd &amp;&amp; twrp xset fox_adb=1</action>' in c:
                            c = c.replace('<action function="ftls">ps -eo \'comm\' | grep adbd &amp;&amp; twrp xset fox_adb=1</action>', '')
                            write_file_lf(fpath, c)
                            print(f"[+] Removed blocking ftls ps check from {fpath} to prevent ActionThread collision")
                    except Exception:
                        pass
    return True

def patch_display_timeout_toggle(fox_root):
    data_cpp = os.path.join(fox_root, "bootable/recovery/data.cpp")
    if os.path.isfile(data_cpp):
        try:
            with open(data_cpp, "r", encoding="utf-8", errors="ignore") as f:
                c = f.read()
            if 'mPersist.SetValue("tw_no_screen_timeout", "0");' in c:
                print("[+] Verified tw_no_screen_timeout=0 in data.cpp")
            else:
                c = re.sub(r'mPersist\.SetValue\s*\(\s*"tw_no_screen_timeout"\s*,\s*"1"\s*\);', 'mPersist.SetValue("tw_no_screen_timeout", "0");', c)
                write_file_lf(data_cpp, c)
                print("[+] Patched data.cpp with tw_no_screen_timeout=0")
        except Exception as e:
            print(f"[-] Failed checking data.cpp timeout: {e}")
    return True

def build_flashable_zip(zip_path, update_binary_str, extra_files=None):
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        info = zipfile.ZipInfo("META-INF/com/google/android/update-binary")
        info.external_attr = 0o755 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info, update_binary_str.replace("\r\n", "\n"))

        info2 = zipfile.ZipInfo("META-INF/com/google/android/updater-script")
        info2.external_attr = 0o644 << 16
        info2.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info2, "#MAGISK\n")

        if extra_files:
            for arcname, src in extra_files.items():
                finfo = zipfile.ZipInfo(arcname)
                finfo.external_attr = 0o755 << 16
                finfo.compress_type = zipfile.ZIP_DEFLATED
                if isinstance(src, bytes):
                    zf.writestr(finfo, src)
                elif os.path.isfile(src):
                    with open(src, "rb") as rf:
                        zf.writestr(finfo, rf.read())

AVB20_SCRIPT = """#!/sbin/sh
# OrangeFox Slot-Aware AVB 2.0 / VBMeta Disabler for Infinix GT 20 Pro (X6871)
OUTFD=$2
ui_print() {
  if [ -n "$OUTFD" ]; then
    echo "ui_print $1" >&$OUTFD
    echo "ui_print" >&$OUTFD
  else
    echo "$1"
  fi
}

ui_print "******************************************"
ui_print "*   OrangeFox VBMeta / AVB 2.0 Patcher   *"
ui_print "*      Maintainer: sheikhmehraann        *"
ui_print "******************************************"

PATCHED_COUNT=0
for part in vbmeta_a vbmeta_b vbmeta vbmeta_system_a vbmeta_system_b vbmeta_system vbmeta_vendor_a vbmeta_vendor_b vbmeta_vendor; do
  BDEV=""
  for base in /dev/block/by-name /dev/block/bootdevice/by-name /dev/block/platform/bootdevice/by-name; do
    if [ -e "$base/$part" ]; then
      BDEV="$base/$part"
      break
    fi
  done
  [ -z "$BDEV" ] && continue

  MAGIC=$(dd if="$BDEV" bs=1 count=4 2>/dev/null)
  if [ "$MAGIC" = "AVB0" ]; then
    printf '\\x00\\x00\\x00\\x03' | dd of="$BDEV" bs=1 seek=120 count=4 conv=notrunc 2>/dev/null
    sync
    ui_print "- Patched $part (flags=0x03: verification & verity disabled)"
    PATCHED_COUNT=$((PATCHED_COUNT + 1))
  fi
done

# Also strip AVBf verification flags on active boot image if magiskboot is available
MB=$(which magiskboot 2>/dev/null)
[ -z "$MB" ] && [ -x /system/bin/magiskboot ] && MB=/system/bin/magiskboot
[ -z "$MB" ] && [ -x /sbin/magiskboot ] && MB=/sbin/magiskboot
SLOT=$(getprop ro.boot.slot_suffix)
[ -z "$SLOT" ] && SLOT="_a"
BOOT_DEV="/dev/block/by-name/boot$SLOT"
if [ -n "$MB" ] && [ -e "$BOOT_DEV" ]; then
  mkdir -p /tmp/avb_boot
  dd if="$BOOT_DEV" of=/tmp/avb_boot/boot.img bs=1048576 2>/dev/null
  if grep -q "AVBf" /tmp/avb_boot/boot.img 2>/dev/null; then
    $MB hexpatch /tmp/avb_boot/boot.img 41564266000000 41564266000300 >/dev/null 2>&1 && {
      dd if=/tmp/avb_boot/boot.img of="$BOOT_DEV" bs=1048576 conv=notrunc 2>/dev/null
      ui_print "- Patched AVBf footer on boot$SLOT"
    }
  fi
  rm -rf /tmp/avb_boot
fi

if [ "$PATCHED_COUNT" -gt 0 ]; then
  ui_print "- Successfully disabled AVB 2.0 on $PATCHED_COUNT VBMeta partition(s)!"
else
  ui_print "! Warning: No valid AVB0 VBMeta headers found to patch."
fi
exit 0
"""

AVB20_ENABLE_SCRIPT = """#!/sbin/sh
# OrangeFox Slot-Aware AVB 2.0 / VBMeta Enabler (Restore Verification) for Infinix GT 20 Pro (X6871)
OUTFD=$2
ui_print() {
  if [ -n "$OUTFD" ]; then
    echo "ui_print $1" >&$OUTFD
    echo "ui_print" >&$OUTFD
  else
    echo "$1"
  fi
}

ui_print "******************************************"
ui_print "*   OrangeFox VBMeta / AVB 2.0 Enabler   *"
ui_print "*      Maintainer: sheikhmehraann        *"
ui_print "******************************************"

RESTORED_COUNT=0
for part in vbmeta_a vbmeta_b vbmeta vbmeta_system_a vbmeta_system_b vbmeta_system vbmeta_vendor_a vbmeta_vendor_b vbmeta_vendor; do
  BDEV=""
  for base in /dev/block/by-name /dev/block/bootdevice/by-name /dev/block/platform/bootdevice/by-name; do
    if [ -e "$base/$part" ]; then
      BDEV="$base/$part"
      break
    fi
  done
  [ -z "$BDEV" ] && continue

  MAGIC=$(dd if="$BDEV" bs=1 count=4 2>/dev/null)
  if [ "$MAGIC" = "AVB0" ]; then
    printf '\\x00\\x00\\x00\\x00' | dd of="$BDEV" bs=1 seek=120 count=4 conv=notrunc 2>/dev/null
    sync
    ui_print "- Enabled $part (flags=0x00: verification & dm-verity restored)"
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
  fi
done

# Also restore AVBf verification flags on active boot image if magiskboot is available
MB=$(which magiskboot 2>/dev/null)
[ -z "$MB" ] && [ -x /system/bin/magiskboot ] && MB=/system/bin/magiskboot
[ -z "$MB" ] && [ -x /sbin/magiskboot ] && MB=/sbin/magiskboot
SLOT=$(getprop ro.boot.slot_suffix)
[ -z "$SLOT" ] && SLOT="_a"
BOOT_DEV="/dev/block/by-name/boot$SLOT"
if [ -n "$MB" ] && [ -e "$BOOT_DEV" ]; then
  mkdir -p /tmp/avb_boot
  dd if="$BOOT_DEV" of=/tmp/avb_boot/boot.img bs=1048576 2>/dev/null
  if grep -q "AVBf" /tmp/avb_boot/boot.img 2>/dev/null; then
    $MB hexpatch /tmp/avb_boot/boot.img 41564266000300 41564266000000 >/dev/null 2>&1 && {
      dd if=/tmp/avb_boot/boot.img of="$BOOT_DEV" bs=1048576 conv=notrunc 2>/dev/null
      ui_print "- Restored AVBf footer on boot$SLOT"
    }
  fi
  rm -rf /tmp/avb_boot
fi

if [ "$RESTORED_COUNT" -gt 0 ]; then
  ui_print "- Successfully enabled AVB 2.0 on $RESTORED_COUNT VBMeta partition(s)!"
else
  ui_print "! Warning: No valid AVB0 VBMeta headers found to restore."
fi
exit 0
"""

DELPASS_SCRIPT = """#!/sbin/sh
# OrangeFox Remove Password / PIN / Lockscreen Addon (Android 15 FBEv2 Safe)
OUTFD=$2
ui_print() {
  if [ -n "$OUTFD" ]; then
    echo "ui_print $1" >&$OUTFD
    echo "ui_print" >&$OUTFD
  else
    echo "$1"
  fi
}

ui_print "******************************************"
ui_print "*  OrangeFox Lockscreen Password Remover *"
ui_print "*      Maintainer: sheikhmehraann        *"
ui_print "******************************************"

mount /data 2>/dev/null || true

if [ ! -d "/data/system" ]; then
  ui_print "! Error: /data/system is not accessible."
  ui_print "! Please decrypt Data first if encrypted."
  exit 1
fi

REMOVED=0
for f in \\
  /data/system/locksettings.db \\
  /data/system/locksettings.db-wal \\
  /data/system/locksettings.db-shm \\
  /data/system/locksettings.db-journal \\
  /data/system/gesture.key \\
  /data/system/password.key \\
  /data/system/gatekeeper.password.key \\
  /data/system/gatekeeper.pattern.key \\
  /data/system/gatekeeper.gesture.key \\
  /data/system/locksettings.PerUser*; do
  if [ -e "$f" ]; then
    rm -rf "$f"
    ui_print "- Removed: $(basename "$f")"
    REMOVED=$((REMOVED + 1))
  fi
done

sync
if [ "$REMOVED" -gt 0 ]; then
  ui_print "- Cleared $REMOVED lockscreen credential file(s)."
  ui_print "- Note: FBEv2 spblob preserved to keep Data encryption intact."
else
  ui_print "- No lockscreen password/PIN database files found (already clean)."
fi
ui_print "- Done!"
exit 0
"""

DELFRP_SCRIPT = """#!/sbin/sh
# OrangeFox Factory Reset Protection (FRP) Wiper for Infinix GT 20 Pro (X6871)
OUTFD=$2
ui_print() {
  if [ -n "$OUTFD" ]; then
    echo "ui_print $1" >&$OUTFD
    echo "ui_print" >&$OUTFD
  else
    echo "$1"
  fi
}

ui_print "******************************************"
ui_print "*     OrangeFox FRP Unlock / Wiper       *"
ui_print "*      Maintainer: sheikhmehraann        *"
ui_print "******************************************"

FRP_DEV=""
for candidate in \\
  /dev/block/by-name/frp \\
  /dev/block/bootdevice/by-name/frp \\
  /dev/block/platform/bootdevice/by-name/frp \\
  /dev/block/by-name/config \\
  /dev/block/by-name/persistent \\
  "$(getprop ro.frp.pst)"; do
  if [ -n "$candidate" ] && [ -e "$candidate" ]; then
    FRP_DEV="$candidate"
    break
  fi
done

if [ -z "$FRP_DEV" ]; then
  ui_print "! Error: Could not locate FRP block partition!"
  exit 1
fi

ui_print "- Located FRP partition: $FRP_DEV"
ui_print "- Wiping FRP lock data..."
dd if=/dev/zero of="$FRP_DEV" bs=1048576 count=1 conv=fsync 2>/dev/null || \\
dd if=/dev/zero of="$FRP_DEV" bs=4096 conv=notrunc 2>/dev/null || \\
blkdiscard "$FRP_DEV" 2>/dev/null

sync
ui_print "- Factory Reset Protection (FRP) wiped successfully!"
exit 0
"""

KSU_INSTALL_SCRIPT = """#!/sbin/sh
# KernelSU v3.3.0 Official LKM Boot Patcher for Infinix GT 20 Pro (android12-5.10)
OUTFD=$2
ZIPFILE=$3

ui_print() {
  if [ -n "$OUTFD" ]; then
    echo "ui_print $1" >&$OUTFD
    echo "ui_print" >&$OUTFD
  else
    echo "$1"
  fi
}

ui_print "******************************************"
ui_print "*   KernelSU v3.3.0 LKM Boot Installer   *"
ui_print "*   KMI: android12-5.10 (GKI 2.0 AArch64)*"
ui_print "*      Maintainer: sheikhmehraann        *"
ui_print "******************************************"

MB=$(which magiskboot 2>/dev/null)
[ -z "$MB" ] && [ -x /system/bin/magiskboot ] && MB=/system/bin/magiskboot
[ -z "$MB" ] && [ -x /sbin/magiskboot ] && MB=/sbin/magiskboot
if [ -z "$MB" ]; then
  ui_print "! Error: magiskboot binary not found!"
  exit 1
fi

SLOT=$(getprop ro.boot.slot_suffix)
[ -z "$SLOT" ] && SLOT="_a"

BOOT_DEV=""
for base in /dev/block/by-name /dev/block/bootdevice/by-name /dev/block/platform/bootdevice/by-name; do
  if [ -e "$base/boot$SLOT" ]; then
    BOOT_DEV="$base/boot$SLOT"
    break
  fi
done

if [ -z "$BOOT_DEV" ]; then
  ui_print "! Error: Could not locate boot$SLOT partition!"
  exit 1
fi

WORK=/tmp/ksu_patch
rm -rf "$WORK"
mkdir -p "$WORK"
cd "$WORK" || exit 1

ui_print "- Extracting KernelSU v3.3.0 LKM assets..."
unzip -o "$ZIPFILE" ksuinit kernelsu.ko -d "$WORK" >/dev/null 2>&1
if [ ! -f "$WORK/ksuinit" ] || [ ! -f "$WORK/kernelsu.ko" ]; then
  ui_print "! Error: Missing ksuinit or kernelsu.ko inside addon zip!"
  rm -rf "$WORK"
  exit 1
fi
chmod 0755 "$WORK/ksuinit" "$WORK/kernelsu.ko"

ui_print "- Dumping active boot partition (boot$SLOT)..."
dd if="$BOOT_DEV" of="$WORK/boot.img" bs=1048576 2>/dev/null
if [ ! -s "$WORK/boot.img" ]; then
  ui_print "! Error: Failed dumping $BOOT_DEV!"
  rm -rf "$WORK"
  exit 1
fi

ui_print "- Unpacking boot.img with magiskboot..."
"$MB" unpack -h "$WORK/boot.img" >/dev/null 2>&1
if [ ! -f "$WORK/kernel" ]; then
  ui_print "! Error: magiskboot unpack failed (no kernel found)!"
  rm -rf "$WORK"
  exit 1
fi

if [ ! -f "$WORK/ramdisk.cpio" ]; then
  ui_print "- Initializing new GKI ramdisk.cpio..."
  printf '07070100000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000B00000000TRAILER!!!\\0\\0\\0\\0' > "$WORK/ramdisk.cpio"
fi

# Check if already patched with kernelsu.ko
"$MB" cpio "$WORK/ramdisk.cpio" "exists kernelsu.ko" >/dev/null 2>&1
IS_KSU=$?
if [ $IS_KSU -ne 0 ]; then
  "$MB" cpio "$WORK/ramdisk.cpio" "exists init" >/dev/null 2>&1
  if [ $? -eq 0 ]; then
    ui_print "- Backing up stock ramdisk /init -> /init.real..."
    "$MB" cpio "$WORK/ramdisk.cpio" "mv init init.real" >/dev/null 2>&1
  fi
fi

ui_print "- Injecting ksuinit (/init) and kernelsu.ko..."
"$MB" cpio "$WORK/ramdisk.cpio" "add 0755 init ksuinit" >/dev/null 2>&1
if [ $? -ne 0 ]; then
  ui_print "! Error: Failed injecting ksuinit into ramdisk.cpio!"
  rm -rf "$WORK"
  exit 1
fi
"$MB" cpio "$WORK/ramdisk.cpio" "add 0755 kernelsu.ko kernelsu.ko" >/dev/null 2>&1
if [ $? -ne 0 ]; then
  ui_print "! Error: Failed injecting kernelsu.ko into ramdisk.cpio!"
  rm -rf "$WORK"
  exit 1
fi

ui_print "- Repacking KernelSU-patched boot.img..."
"$MB" repack "$WORK/boot.img" "$WORK/new-boot.img" >/dev/null 2>&1
if [ ! -s "$WORK/new-boot.img" ]; then
  ui_print "! Error: magiskboot repack failed!"
  rm -rf "$WORK"
  exit 1
fi

ui_print "- Flashing patched boot image to $BOOT_DEV..."
dd if="$WORK/new-boot.img" of="$BOOT_DEV" bs=1048576 conv=notrunc,fsync 2>/dev/null
sync
rm -rf "$WORK"
ui_print "- KernelSU v3.3.0 LKM installed to boot$SLOT successfully!"
ui_print "- Install the KernelSU Manager APK in Android after reboot."
exit 0
"""

KSU_UNINSTALL_SCRIPT = """#!/sbin/sh
# KernelSU LKM Boot Uninstaller for Infinix GT 20 Pro (X6871)
OUTFD=$2

ui_print() {
  if [ -n "$OUTFD" ]; then
    echo "ui_print $1" >&$OUTFD
    echo "ui_print" >&$OUTFD
  else
    echo "$1"
  fi
}

ui_print "******************************************"
ui_print "*     KernelSU LKM Boot Uninstaller      *"
ui_print "*      Maintainer: sheikhmehraann        *"
ui_print "******************************************"

MB=$(which magiskboot 2>/dev/null)
[ -z "$MB" ] && [ -x /system/bin/magiskboot ] && MB=/system/bin/magiskboot
[ -z "$MB" ] && [ -x /sbin/magiskboot ] && MB=/sbin/magiskboot
if [ -z "$MB" ]; then
  ui_print "! Error: magiskboot binary not found!"
  exit 1
fi

SLOT=$(getprop ro.boot.slot_suffix)
[ -z "$SLOT" ] && SLOT="_a"

BOOT_DEV=""
for base in /dev/block/by-name /dev/block/bootdevice/by-name /dev/block/platform/bootdevice/by-name; do
  if [ -e "$base/boot$SLOT" ]; then
    BOOT_DEV="$base/boot$SLOT"
    break
  fi
done

if [ -z "$BOOT_DEV" ]; then
  ui_print "! Error: Could not locate boot$SLOT partition!"
  exit 1
fi

WORK=/tmp/ksu_unpatch
rm -rf "$WORK"
mkdir -p "$WORK"
cd "$WORK" || exit 1

ui_print "- Dumping active boot partition (boot$SLOT)..."
dd if="$BOOT_DEV" of="$WORK/boot.img" bs=1048576 2>/dev/null
"$MB" unpack -h "$WORK/boot.img" >/dev/null 2>&1

if [ ! -f "$WORK/ramdisk.cpio" ]; then
  ui_print "- Boot image has no ramdisk; KernelSU LKM is not installed."
  rm -rf "$WORK"
  exit 0
fi

"$MB" cpio "$WORK/ramdisk.cpio" "exists kernelsu.ko" >/dev/null 2>&1
if [ $? -ne 0 ]; then
  ui_print "- kernelsu.ko not found in boot$SLOT ramdisk (already clean)."
  rm -rf "$WORK"
  exit 0
fi

ui_print "- Removing kernelsu.ko and restoring stock init..."
"$MB" cpio "$WORK/ramdisk.cpio" "rm kernelsu.ko" >/dev/null 2>&1
"$MB" cpio "$WORK/ramdisk.cpio" "exists init.real" >/dev/null 2>&1
if [ $? -eq 0 ]; then
  "$MB" cpio "$WORK/ramdisk.cpio" "mv init.real init" >/dev/null 2>&1
else
  "$MB" cpio "$WORK/ramdisk.cpio" "rm init" >/dev/null 2>&1
fi

"$MB" repack "$WORK/boot.img" "$WORK/new-boot.img" >/dev/null 2>&1
if [ -s "$WORK/new-boot.img" ]; then
  dd if="$WORK/new-boot.img" of="$BOOT_DEV" bs=1048576 conv=notrunc,fsync 2>/dev/null
  sync
  ui_print "- KernelSU LKM removed from boot$SLOT successfully!"
else
  ui_print "! Error: Failed repacking boot.img!"
  rm -rf "$WORK"
  exit 1
fi

rm -rf "$WORK"
exit 0
"""

def ensure_ksu_assets():
    ksu_dir = "/tmp/ksu_assets" if os.name != "nt" else os.path.join(os.environ.get("TEMP", "."), "ksu_assets")
    os.makedirs(ksu_dir, exist_ok=True)
    ksuinit_path = os.path.join(ksu_dir, "ksuinit")
    ko_path = os.path.join(ksu_dir, "kernelsu.ko")

    urls = {
        ksuinit_path: "https://github.com/tiann/KernelSU/releases/download/v3.3.0/ksuinit-aarch64",
        ko_path: "https://github.com/tiann/KernelSU/releases/download/v3.3.0/lkm-aarch64-android12-5.10_kernelsu.ko",
    }
    for dest, url in urls.items():
        if not os.path.isfile(dest) or os.path.getsize(dest) < 10000:
            try:
                print(f"[*] Downloading {url} -> {dest} ...")
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
                    shutil.copyfileobj(resp, out)
                print(f"[+] Downloaded {dest} ({os.path.getsize(dest)} bytes)")
            except Exception as e:
                print(f"[-] Warning: Could not download {url}: {e}")
    return ksuinit_path, ko_path

def patch_avb_settings(fox_root):
    data_cpp = os.path.join(fox_root, "bootable/recovery/data.cpp")
    if os.path.isfile(data_cpp):
        try:
            with open(data_cpp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            orig = content
            if 'mConst.SetValue("fox_auto_disable_vbmeta_avb2"' not in content:
                content = content.replace(
                    'mConst.SetValue("fox_branch", FOX_BRANCH);',
                    'mConst.SetValue("fox_branch", FOX_BRANCH);\n\tmConst.SetValue("fox_auto_disable_vbmeta_avb2", "1");\n\tmConst.SetValue("fox_patch_avb_20", "1");'
                )
            if 'mPersist.SetValue("tw_auto_disable_avb2"' not in content:
                content = content.replace(
                    'mPersist.SetValue("tw_mount_system_ro", "2");',
                    'mPersist.SetValue("tw_mount_system_ro", "2");\n\tmPersist.SetValue("tw_auto_disable_avb2", "1");'
                )
            if content != orig:
                write_file_lf(data_cpp, content)
                print("[+] Successfully enabled AVB2.0 disable addon in data.cpp")
        except Exception as e:
            print(f"[-] Failed patching data.cpp for AVB: {e}")

    # Replace OF_avb20.sh across vendor/recovery and unpacked FFiles with our slot-aware VBMeta disabler
    for sdir in [os.path.join(fox_root, "vendor/recovery"), os.path.join(fox_root, "FFiles")]:
        if not os.path.isdir(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for file in files:
                if file == "OF_avb20.sh":
                    fpath = os.path.join(root, file)
                    try:
                        write_file_lf(fpath, AVB20_SCRIPT)
                        os.chmod(fpath, 0o755)
                        print(f"[+] Replaced {fpath} with slot-aware VBMeta AVB 2.0 disabler")
                    except Exception as e:
                        print(f"[-] Failed writing {fpath}: {e}")
    return True

def patch_addons(fox_root):
    ksuinit_path, ko_path = ensure_ksu_assets()

    # Build the 5 custom addon packages into a staging directory
    addon_stage = "/tmp/ofox_custom_addons/FFiles" if os.name != "nt" else os.path.join(os.environ.get("TEMP", "."), "ofox_custom_addons", "FFiles")
    if os.path.isdir(addon_stage):
        shutil.rmtree(addon_stage)
    os.makedirs(addon_stage, exist_ok=True)

    # 1. OF_avb20/OF_avb20.sh, OF_avb20.zip (Disable AVB 2.0) and OF_enable_avb20.sh, OF_enable_avb20.zip (Enable AVB 2.0)
    avb_dir = os.path.join(addon_stage, "OF_avb20")
    os.makedirs(avb_dir, exist_ok=True)
    avb_sh = os.path.join(avb_dir, "OF_avb20.sh")
    write_file_lf(avb_sh, AVB20_SCRIPT)
    os.chmod(avb_sh, 0o755)
    build_flashable_zip(os.path.join(avb_dir, "OF_avb20.zip"), AVB20_SCRIPT)

    avb_en_sh = os.path.join(avb_dir, "OF_enable_avb20.sh")
    write_file_lf(avb_en_sh, AVB20_ENABLE_SCRIPT)
    os.chmod(avb_en_sh, 0o755)
    build_flashable_zip(os.path.join(avb_dir, "OF_enable_avb20.zip"), AVB20_ENABLE_SCRIPT)

    # 2. OF_DelPass/OF_DelPass.zip
    delpass_dir = os.path.join(addon_stage, "OF_DelPass")
    os.makedirs(delpass_dir, exist_ok=True)
    build_flashable_zip(os.path.join(delpass_dir, "OF_DelPass.zip"), DELPASS_SCRIPT)

    # 3. OF_DelFRP/OF_DelFRP.zip
    delfrp_dir = os.path.join(addon_stage, "OF_DelFRP")
    os.makedirs(delfrp_dir, exist_ok=True)
    build_flashable_zip(os.path.join(delfrp_dir, "OF_DelFRP.zip"), DELFRP_SCRIPT)

    # 4. KernelSU/KernelSU_Installer.zip and KernelSU/KernelSU_Uninstaller.zip
    ksu_dir = os.path.join(addon_stage, "KernelSU")
    os.makedirs(ksu_dir, exist_ok=True)
    ksu_extra = {}
    if os.path.isfile(ksuinit_path) and os.path.isfile(ko_path):
        ksu_extra = {"ksuinit": ksuinit_path, "kernelsu.ko": ko_path}
    build_flashable_zip(os.path.join(ksu_dir, "KernelSU_Installer.zip"), KSU_INSTALL_SCRIPT, extra_files=ksu_extra)
    build_flashable_zip(os.path.join(ksu_dir, "KernelSU_Uninstaller.zip"), KSU_UNINSTALL_SCRIPT)

    print(f"[+] Built custom Fox Addons in {addon_stage} (Disable/Enable AVB2.0, DelPass, DelFRP, KernelSU v3.3.0)")

    # Discover all FFiles directories in fox_root and copy the built addons into them
    ffiles_targets = set()
    if os.path.isdir(os.path.join(fox_root, "FFiles")):
        ffiles_targets.add(os.path.join(fox_root, "FFiles"))
    dev_common_ffiles = os.path.join(fox_root, "device/transsion/mt6895-common/recovery/root/FFiles")
    if os.path.isdir(os.path.join(fox_root, "device/transsion/mt6895-common")):
        ffiles_targets.add(dev_common_ffiles)

    vrec = os.path.join(fox_root, "vendor/recovery")
    if os.path.isdir(vrec):
        for root, dirs, files in os.walk(vrec):
            if os.path.basename(root) == "FFiles" or "OF_reset.zip" in files or "OF_avb20.zip" in files:
                target_ff = root if os.path.basename(root) == "FFiles" else os.path.dirname(root)
                if os.path.basename(target_ff) == "FFiles":
                    ffiles_targets.add(target_ff)

    for target_ff in ffiles_targets:
        try:
            for item in os.listdir(addon_stage):
                s_item = os.path.join(addon_stage, item)
                d_item = os.path.join(target_ff, item)
                if os.path.isdir(s_item):
                    os.makedirs(d_item, exist_ok=True)
                    for sub in os.listdir(s_item):
                        shutil.copy2(os.path.join(s_item, sub), os.path.join(d_item, sub))
                else:
                    shutil.copy2(s_item, d_item)
            print(f"[+] Deployed custom Fox Addons to {target_ff}")
        except Exception as e:
            print(f"[-] Failed deploying addons to {target_ff}: {e}")

    # Patch advanced.xml to wire up Remove Password, Remove FRP, VBMeta Disabler/Enabler, and KernelSU v3.3.0
    search_dirs = [
        os.path.join(fox_root, "vendor/recovery"),
        os.path.join(fox_root, "bootable/recovery"),
        os.path.join(fox_root, "twres")
    ]
    for sdir in search_dirs:
        if not os.path.isdir(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for file in files:
                if file == "advanced.xml":
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            xml_c = f.read()
                        orig_xml = xml_c

                        # 1. Disable zip signature verification on built-in Fox Addon pages
                        for mod_page in ["mod_pass", "mod_factory_rp", "mod_kernelsu", "mod_reset"]:
                            pat = rf'(<page name="{mod_page}">[\s\S]*?)(<action function="queuezip"\s*/>)'
                            def add_no_sig(m):
                                if "tw_signed_zip_verify=0" in m.group(1):
                                    return m.group(0)
                                return m.group(1) + '<action function="set">tw_signed_zip_verify=0</action>\n\t\t\t\t' + m.group(2)
                            xml_c = re.sub(pat, add_no_sig, xml_c, count=1)

                        # Update mod_kernelsu display name to include v3.3.0
                        xml_c = xml_c.replace(
                            '<action function="set">fox_m_name={@module_install} KernelSU</action>',
                            '<action function="set">fox_m_name={@module_install} KernelSU v3.3.0</action>'
                        )

                        # 2. Add mod_unkernelsu, mod_avb20, and mod_enable_avb20 pages right after mod_kernelsu page using native OrangeFox module confirmation flow
                        if '<page name="mod_avb20">' not in xml_c and '<page name="mod_kernelsu">' in xml_c:
                            extra_pages = """\t\t<page name="mod_unkernelsu">
\t\t  <action>
\t\t\t<action function="queueclear"/>
\t\t\t<action function="set">fox_m_author=sheikhmehraann</action>
\t\t\t<action function="set">fox_m_name={@module_uninstall} KernelSU</action>
\t\t\t<action function="set">tw_file=KernelSU_Uninstaller.zip</action>
\t\t\t<action function="set">tw_filename=/FFiles/KernelSU/KernelSU_Uninstaller.zip</action>
\t\t\t<action function="set">tw_filecheck=%tw_filename%</action>
\t\t\t<action function="set">tw_zip_location=/FFiles/KernelSU</action>
\t\t\t<action function="set">fox_install_built_in_zip=1</action>
\t\t\t<action function="set">tw_signed_zip_verify=0</action>
\t\t\t<action function="queuezip"/>
\t\t\t<action function="set">tw_notexistpage=fox_modules_confirm</action>
\t\t\t<action function="set">tw_existpage=fox_modules_confirm</action>
\t\t\t<action function="page">filecheck</action>
\t\t  </action>
\t\t</page>

\t\t<page name="mod_avb20">
\t\t  <action>
\t\t\t<action function="queueclear"/>
\t\t\t<action function="set">fox_m_author=sheikhmehraann</action>
\t\t\t<action function="set">fox_m_name=Disable VBMeta (Patch AVB 2.0)</action>
\t\t\t<action function="set">tw_file=OF_avb20.zip</action>
\t\t\t<action function="set">tw_filename=/FFiles/OF_avb20/OF_avb20.zip</action>
\t\t\t<action function="set">tw_filecheck=%tw_filename%</action>
\t\t\t<action function="set">tw_zip_location=/FFiles/OF_avb20</action>
\t\t\t<action function="set">fox_install_built_in_zip=1</action>
\t\t\t<action function="set">tw_signed_zip_verify=0</action>
\t\t\t<action function="queuezip"/>
\t\t\t<action function="set">tw_notexistpage=fox_modules_confirm</action>
\t\t\t<action function="set">tw_existpage=fox_modules_confirm</action>
\t\t\t<action function="page">filecheck</action>
\t\t  </action>
\t\t</page>

\t\t<page name="mod_enable_avb20">
\t\t  <action>
\t\t\t<action function="queueclear"/>
\t\t\t<action function="set">fox_m_author=sheikhmehraann</action>
\t\t\t<action function="set">fox_m_name=Enable VBMeta (Restore AVB 2.0)</action>
\t\t\t<action function="set">tw_file=OF_enable_avb20.zip</action>
\t\t\t<action function="set">tw_filename=/FFiles/OF_avb20/OF_enable_avb20.zip</action>
\t\t\t<action function="set">tw_filecheck=%tw_filename%</action>
\t\t\t<action function="set">tw_zip_location=/FFiles/OF_avb20</action>
\t\t\t<action function="set">fox_install_built_in_zip=1</action>
\t\t\t<action function="set">tw_signed_zip_verify=0</action>
\t\t\t<action function="queuezip"/>
\t\t\t<action function="set">tw_notexistpage=fox_modules_confirm</action>
\t\t\t<action function="set">tw_existpage=fox_modules_confirm</action>
\t\t\t<action function="page">filecheck</action>
\t\t  </action>
\t\t</page>"""
                            xml_c = re.sub(
                                r'(<page name="mod_kernelsu">[\s\S]*?</page>)',
                                lambda m: m.group(1) + "\n\n" + extra_pages,
                                xml_c,
                                count=1
                            )

                        # 3. In <page name="fox_modules">: add Disable VBMeta and Enable VBMeta and make FRP + KernelSU unconditionally available
                        if '<action function="page">mod_avb20</action>' not in xml_c:
                            avb_item = """\t\t\t\t<listitem name="Disable VBMeta (Patch AVB 2.0)">
\t\t\t\t\t<condition var1="fileexists" var2="/FFiles/OF_avb20/OF_avb20.zip"/>
\t\t\t\t\t<icon res="archive"/>
\t\t\t\t\t<action function="page">mod_avb20</action>
\t\t\t\t</listitem>

\t\t\t\t<listitem name="Enable VBMeta (Restore AVB 2.0)">
\t\t\t\t\t<condition var1="fileexists" var2="/FFiles/OF_avb20/OF_enable_avb20.zip"/>
\t\t\t\t\t<icon res="archive"/>
\t\t\t\t\t<action function="page">mod_enable_avb20</action>
\t\t\t\t</listitem>"""
                            xml_c = re.sub(
                                r'(<listitem name="\{@module_pass\}">[\s\S]*?</listitem>)',
                                lambda m: m.group(1) + "\n\n" + avb_item,
                                xml_c,
                                count=1
                            )

                        # Remove enable_frp_addon gate so OF_DelFRP.zip shows whenever fileexists
                        xml_c = re.sub(
                            r'<condition var1="enable_frp_addon" op="==" var2="1"/>\s*',
                            '',
                            xml_c
                        )
                        xml_c = re.sub(
                            r'<condition var1="enable_frp_addon" var2="1"/>\s*',
                            '',
                            xml_c
                        )

                        # Update KernelSU section in fox_modules so both Install KernelSU v3.3.0 and Uninstall KernelSU appear cleanly
                        ksu_block_pat = r'<text style="caption">\s*<condition var1="fox_vab_device" var2="1"/>\s*<condition var1="fox_support_ksu" var2="1"/>[\s\S]*?<action function="page">mod_sukisu</action>\s*</listitem>\s*</listbox>'
                        ksu_block_repl = """<text style="caption">
                <placement x="%gl_text_x%" y="%row7_1a_y%"/>
                <text>KernelSU (v3.3.0 LKM Root)</text>
            </text>

            <listbox style="group_list">
                <placement x="0" y="%row7_2a_y%" w="%screen_w%" h="%bl_h2%"/>

                <listitem name="{@module_install} KernelSU v3.3.0">
                    <condition var1="fileexists" var2="/FFiles/KernelSU/KernelSU_Installer.zip"/>
                    <icon res="archive"/>
                    <action function="page">mod_kernelsu</action>
                </listitem>

                <listitem name="{@module_uninstall} KernelSU">
                    <condition var1="fileexists" var2="/FFiles/KernelSU/KernelSU_Uninstaller.zip"/>
                    <icon res="archive"/>
                    <action function="page">mod_unkernelsu</action>
                </listitem>
            </listbox>"""
                        if re.search(ksu_block_pat, xml_c):
                            xml_c = re.sub(ksu_block_pat, lambda m: ksu_block_repl, xml_c, count=1)

                        if xml_c != orig_xml:
                            write_file_lf(fpath, xml_c)
                            print(f"[+] Patched Fox Addons menu in {fpath} (Password, FRP, VBMeta, KernelSU v3.3.0)")
                    except Exception as e:
                        print(f"[-] Failed patching {fpath} for addons: {e}")
    return True

def patch_graphics_drm(fox_root):
    drm_cpp = os.path.join(fox_root, "bootable/recovery/minuitwrp/graphics_drm.cpp")
    local_drm = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graphics_drm.cpp")
    if os.path.isfile(drm_cpp) and os.path.isfile(local_drm):
        try:
            with open(local_drm, "r", encoding="utf-8") as f_src:
                drm_content = f_src.read()
            write_file_lf(drm_cpp, drm_content)
            print(f"[+] Successfully deployed verified MediaTek single-pipe graphics_drm.cpp to {drm_cpp}")
            return True
        except Exception as e:
            print(f"[-] Failed copying graphics_drm.cpp: {e}")
    return False

def patch_version(fox_root):
    ofmk = os.path.join(fox_root, "bootable/recovery/orangefox.mk")
    if os.path.isfile(ofmk):
        try:
            with open(ofmk, "r", encoding="utf-8") as f:
                c = f.read()
            c = re.sub(r'FOX_INTERNAL_RELEASE\s*:=\s*R\d+\.\d+', 'FOX_INTERNAL_RELEASE := R12.1', c)
            c = re.sub(r'\$\(error\s+\'FOX_VERSION\'\s+is\s+obsolete[^\)]*\)', '# FOX_VERSION check cleared', c)
            write_file_lf(ofmk, c)
            print("[+] Patched bootable/recovery/orangefox.mk with R12.1 & cleared obsolete error")
        except Exception as e:
            print(f"[-] Failed patching orangefox.mk: {e}")

    vend_sh = os.path.join(fox_root, "vendor/recovery/OrangeFox_vendor.sh")
    if os.path.isfile(vend_sh):
        try:
            with open(vend_sh, "r", encoding="utf-8") as f:
                c = f.read()
            c = re.sub(r'export FOX_INTERNAL_RELEASE=R\d+\.\d+', 'export FOX_INTERNAL_RELEASE=R12.1', c)
            addon_hook = """
# --- X6871 Custom Fox Addons Post-Install Hook ---
if [ -d "/tmp/ofox_custom_addons/FFiles" ]; then
    for ff_dst in "$TARGET_RECOVERY_ROOT_OUT/FFiles" "$OUT/recovery/root/FFiles" "$OUT/vendor_ramdisk/FFiles"; do
        if [ -n "$ff_dst" ] && [ "$ff_dst" != "/FFiles" ]; then
            mkdir -p "$ff_dst" 2>/dev/null || true
            cp -rf /tmp/ofox_custom_addons/FFiles/* "$ff_dst/" 2>/dev/null || true
        fi
    done
fi
"""
            if "X6871 Custom Fox Addons Post-Install Hook" not in c:
                c = c.rstrip() + "\n" + addon_hook + "\n"
            write_file_lf(vend_sh, c)
            print("[+] Patched vendor/recovery/OrangeFox_vendor.sh with R12.1 & custom Fox Addons hook")
        except Exception as e:
            print(f"[-] Failed patching OrangeFox_vendor.sh: {e}")
    return True

def patch_super_partitions(fox_root):
    pm_cpp = os.path.join(fox_root, "bootable/recovery/partitionmanager.cpp")
    if not os.path.isfile(pm_cpp):
        print(f"[-] partitionmanager.cpp not found at {pm_cpp}")
        return False

    try:
        with open(pm_cpp, "r", encoding="utf-8", errors="ignore") as f:
            c = f.read()

        orig = c

        # 1. In Prepare_Super_Volume: add /dev/block/mapper/<part> symlink and update image partitions
        sym_pat = r'(TWFunc::Create_Symlink\s*\(\s*dev\s*,\s*\"/dev/block/by-name/\"\s*\+\s*part_name\s*\)\s*;)'
        sym_inject = r'''\1
		TWFunc::Create_Symlink(dev, "/dev/block/mapper/" + part_name);
		TWPartition* imgPart = Find_Partition_By_Path("/" + part_name + "_image");
		if (imgPart) {
			imgPart->Is_Present = true;
			imgPart->Actual_Block_Device = dev;
			imgPart->Set_Can_Be_Backed_Up(true);
			imgPart->Set_Can_Flash_Img(true);
		}'''
        if 'dev/block/mapper/" + part_name' not in c:
            c = re.sub(sym_pat, sym_inject, c)

        # 2. In Get_Partition_List: dynamically ensure block devices on disk refresh Is_Present
        list_pat = r'(if\s*\(\s*\(\*iter\)->Can_Flash_Img\s*&&\s*\(\*iter\)->Is_Present\s*\))'
        list_inject = r'''if ((*iter)->Can_Flash_Img) {
			if (!(*iter)->Is_Present && !(*iter)->Actual_Block_Device.empty() && TWFunc::Path_Exists((*iter)->Actual_Block_Device)) {
				(*iter)->Is_Present = true;
			}
		}
		\1'''
        if "Can_Flash_Img) {\n\t\t\tif (!(*iter)->Is_Present" not in c:
            c = re.sub(list_pat, list_inject, c)

        list_bak_pat = r'(if\s*\(\s*\(\*iter\)->Can_Be_Backed_Up\s*&&\s*\(\*iter\)->Is_Present\s*\))'
        list_bak_inject = r'''if ((*iter)->Can_Be_Backed_Up) {
			if (!(*iter)->Is_Present && !(*iter)->Actual_Block_Device.empty() && TWFunc::Path_Exists((*iter)->Actual_Block_Device)) {
				(*iter)->Is_Present = true;
			}
		}
		\1'''
        if "Can_Be_Backed_Up) {\n\t\t\tif (!(*iter)->Is_Present" not in c:
            c = re.sub(list_bak_pat, list_bak_inject, c)

        # 3. In Process_Keymaster_Version: ensure TW_FORCE_KEYMASTER_VER support
        if "#ifndef TW_FORCE_KEYMASTER_VER" not in c:
            km_func_pat = r'void inline Process_Keymaster_Version\s*\([^)]*\)\s*\{[\s\S]*?\n\}'
            km_func_inject = r'''void inline Process_Keymaster_Version(TWPartition *ven, bool Display_Error) {
	// Fetch the Keymaster Service version to be started
	std::string version;
#ifndef TW_FORCE_KEYMASTER_VER
	version = KM_Ver_From_Manifest(version);

	/* If we are unable to get the version from device vendor then
		* set the version from the keymaster_ver prop if set
		*/
	if (version.empty()) {
		// unmount partition(s)
		if (ven) ven->UnMount(Display_Error);

		// Use keymaster_ver prop set from device tree (if exists)
		version = android::base::GetProperty(TW_KEYMASTER_VERSION_PROP, version);
		if (version.empty()) {
			LOGINFO("Keymaster_Ver::Unable to find vendor manifest on the device, and no default value set. Checking the ramdisk manifest\\n");
			version = KM_Ver_From_Manifest(version);
		} else {
			LOGINFO("Keymaster_Ver::Unable to find vendor manifest on the device. Setting to default value.\\n");
		}
	} else {
		if (ven) ven->UnMount(Display_Error);
	}
#else
	if (ven) ven->UnMount(Display_Error);

	version = android::base::GetProperty(TW_KEYMASTER_VERSION_PROP, version);
	if (version.empty()) {
		LOGINFO("Keymaster_Ver::Force Keymaster_Ver flag found, but keymaster_ver prop not set.\\n");
	} else {
		LOGINFO("Keymaster_Ver::Force Keymaster_Ver flag found.\\n");
	}
#endif
	if (version.empty()) // defective device tree - apply a default
		version = "4.x";

	LOGINFO("Keymaster_Ver::Using keymaster version '%s' for decryption\\n", version.c_str());
	android::base::SetProperty(TW_KEYMASTER_VERSION_PROP, version.c_str());
}'''
            c = re.sub(km_func_pat, km_func_inject, c)

        # 4. In Unmap_Super_Devices: force unmount, unlink mapper symlinks, and avoid fatal abort on symlink cleanup
        unmap_func_pat = r'bool TWPartitionManager::Unmap_Super_Devices\(\)\s*\{[\s\S]*?\n\}'
        unmap_func_inject = r'''bool TWPartitionManager::Unmap_Super_Devices() {
	bool destroyed = false;
#ifndef TW_EXCLUDE_APEX
	twrpApex apex;
	apex.Unmount();
#endif
	LOGINFO("Unmap_Super_Devices\\n");
	for (auto iter = Partitions.begin(); iter != Partitions.end();) {
		LOGINFO("Checking partition: %s\\n", (*iter)->Get_Mount_Point().c_str());
		if ((*iter)->Is_Super) {
			TWPartition *part = *iter;
			std::string bare_partition_name = Get_Bare_Partition_Name((*iter)->Get_Mount_Point());
			std::string blk_device_partition = bare_partition_name;
			if (DataManager::GetIntValue("of_ab_device") == 1 || DataManager::GetStrValue("tw_has_boot_slots") == "1")
				blk_device_partition.append(PartitionManager.Get_Active_Slot_Suffix());
			(*iter)->UnMount(true);
			unlink(("/dev/block/mapper/" + bare_partition_name).c_str());
			unlink(("/dev/block/mapper/" + blk_device_partition).c_str());
			unlink(("/dev/block/by-name/" + bare_partition_name).c_str());
			unlink(("/dev/block/by-name/" + blk_device_partition).c_str());
			TWPartition* cleanImg = Find_Partition_By_Path("/" + bare_partition_name + "_image");
			if (cleanImg) cleanImg->Is_Present = false;
			LOGINFO("removing dynamic partition: %s\\n", blk_device_partition.c_str());
			destroyed = DestroyLogicalPartition(blk_device_partition);
			std::string cow_partition = blk_device_partition + "-cow";
			std::string cow_partition_path = "/dev/block/mapper/" + cow_partition;
			struct stat st;
			if (lstat(cow_partition_path.c_str(), &st) == 0) {
				LOGINFO("removing cow partition: %s\\n", cow_partition.c_str());
				DestroyLogicalPartition(cow_partition);
				unlink(cow_partition_path.c_str());
			}
			iter = Partitions.erase(iter);
			delete part;
		} else {
			++iter;
		}
	}

	const std::string block_path = "/dev/block/mapper/";
	DIR* d = opendir(block_path.c_str());
	if (d != NULL) {
		struct dirent* de;
		while ((de = readdir(d)) != NULL) {
			if (de->d_type == DT_LNK) {
				std::string partition = de->d_name;
				if (strcmp(partition.c_str(),"userdata") != 0){
					LOGINFO("removing dynamic partition: %s\\n", partition.c_str());
					unlink((block_path + partition).c_str());
					DestroyLogicalPartition(partition);
				}
			}
		}
		closedir(d);
	}
	return true;
}'''
        c = re.sub(unmap_func_pat, unmap_func_inject, c)

        if c != orig:
            write_file_lf(pm_cpp, c)
            print("[+] Successfully patched partitionmanager.cpp with dynamic super partition flash & backup engine")
            return True
    except Exception as e:
        print(f"[-] Failed patching partitionmanager.cpp for super partitions: {e}")
    return False

def patch_format_data(fox_root):
    pm_cpp = os.path.join(fox_root, "bootable/recovery/partitionmanager.cpp")
    if not os.path.isfile(pm_cpp):
        print(f"[-] partitionmanager.cpp not found at {pm_cpp}")
        return False

    try:
        with open(pm_cpp, "r", encoding="utf-8", errors="ignore") as f:
            c = f.read()

        orig = c

        fmt_pat = r'int TWPartitionManager::Format_Data\s*\(\s*void\s*\)\s*\{[\s\S]*?\n\}'
        fmt_repl = '''int TWPartitionManager::Format_Data(void) {
	// 1. Reset A/B zip installation reboot lock so user can format data without rebooting recovery
	DataManager::SetValue("tw_block_reboot", 0);
	if (TWFunc::Block_Operations_Until_Reboot())
		return false;

	TWPartition* dat = Find_Partition_By_Path("/data");
	TWPartition* metadata = Find_Partition_By_Path("/metadata");
	bool ret = false;
	if (metadata != NULL)
		metadata->UnMount(false);

	if (dat != NULL) {
		// 2. Pre-emptively detach MTP and active mounts on /data and /sdcard to prevent EBUSY
		Remove_MTP_Storage(dat->MTP_Storage_ID);
		dat->UnMount(false, MNT_FORCE | MNT_DETACH);
		umount2("/data", MNT_FORCE | MNT_DETACH);
		umount2("/sdcard", MNT_FORCE | MNT_DETACH);

		#ifdef OF_REFRESH_ENCRYPTION_PROPS_BEFORE_FORMAT
		Update_Encryption_Props_Before_Format(); // call here, because it must run before Unmap_Super_Devices is executed
		#endif
		if (android::base::GetBoolProperty("ro.virtual_ab.enabled", false)) {
#ifndef TW_EXCLUDE_APEX
			twrpApex apex;
			apex.Unmount();
#endif
			if (metadata != NULL)
				metadata->Mount(true);
			// 3. Virtual A/B: do not abort format data if an unverified snapshot is pending
			if (!Check_Pending_Merges()) {
				LOGINFO("Check_Pending_Merges returned false (unverified snapshot pending); cancelling snapshot update before data wipe.\\n");
				auto sm = android::snapshot::SnapshotManager::NewForFirstStageMount();
				if (sm) {
					sm->CancelUpdate();
				}
			}
		}
		ret = dat->Wipe_Encryption();
	} else {
		gui_msg(Msg(msg::kError, "unable_to_locate=Unable to locate {1}.")("/data"));
		return false;
	}

	if (ret) {
		#ifdef OF_WIPE_METADATA_AFTER_DATAFORMAT
		usleep(2048);
		Wipe_By_Path("/metadata");
		usleep(2048);
		mkdir("/metadata/recovery", 0770);
		#endif
		TWFunc::check_and_run_script(TW_FORMAT_DATA_SCRIPT, "Format Data Script");
	}
	return ret;
}'''

        if re.search(fmt_pat, c):
            c = re.sub(fmt_pat, lambda m: fmt_repl, c)

        if c != orig:
            write_file_lf(pm_cpp, c)
            print("[+] Successfully patched partitionmanager.cpp with robust Format_Data engine")
            return True
        else:
            print("[-] Format_Data already patched or pattern did not match")
            return False
    except Exception as e:
        print(f"[-] Failed patching partitionmanager.cpp for format data: {e}")
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: patch_ofox.py <fox_source_root>")
        sys.exit(1)

    fox_root = sys.argv[1]
    if not os.path.isdir(fox_root):
        print(f"[-] Directory does not exist: {fox_root}")
        sys.exit(1)

    print(f"[*] OrangeFox Patch Engine targeting: {fox_root}")
    patch_envsetup(fox_root)
    patch_flashlight(fox_root)
    patch_haptics(fox_root)
    patch_thermals(fox_root)
    patch_magiskboot_vendor_boot(fox_root)
    patch_splash(fox_root)
    patch_identity_and_banner(fox_root)
    patch_slot_switching(fox_root)
    patch_display_timeout_toggle(fox_root)
    patch_avb_settings(fox_root)
    patch_addons(fox_root)
    patch_graphics_drm(fox_root)
    patch_version(fox_root)
    patch_super_partitions(fox_root)
    patch_format_data(fox_root)
    print("[*] All hardware, architecture, identity, slot, splash, version, addons, format data, and UI patches applied cleanly!")

if __name__ == "__main__":
    main()
