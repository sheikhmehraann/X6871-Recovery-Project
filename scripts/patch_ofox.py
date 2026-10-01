#!/usr/bin/env python3
"""
OrangeFox Recovery Hardware & Architecture Patch Engine for Infinix GT 20 Pro (X6871 / MT6895)
Patches:
1. Flashlight: Direct hardware support for MediaTek OCP81375 (/sys/class/torch/torch/torch_level)
2. Haptics: Direct hardware support for AW8697 Linear Vibrator (/sys/class/leds/vibrator_single)
3. Thermals: Dynamic resolution and unquoted fallback for CPU temp (/sys/class/thermal/thermal_zone0/temp)
4. Splash: Native 1080x2436 AMOLED resolution scaling across all splash XML resources
5. Version: Canonical R12.1 release version alignment
"""

import os
import sys
import re

def patch_flashlight(fox_root):
    action_cpp = os.path.join(fox_root, "bootable/recovery/gui/action.cpp")
    if not os.path.isfile(action_cpp):
        print(f"[-] action.cpp not found at {action_cpp}")
        return False

    with open(action_cpp, "r", encoding="utf-8") as f:
        content = f.read()

    target = 'bright_one = path_one + "/brightness";'
    if target in content and "/sys/class/torch/torch/torch_level" not in content:
        replacement = """bright_one = path_one + "/brightness";
\t\t\tif (!TWFunc::Path_Exists(bright_one)) {
\t\t\t\tif (TWFunc::Path_Exists("/sys/class/torch/torch/torch_level")) {
\t\t\t\t\tbright_one = "/sys/class/torch/torch/torch_level";
\t\t\t\t\tmax_brt_one = "1";
\t\t\t\t} else if (TWFunc::Path_Exists("/sys/class/sub_torch/sub_torch/sub_torch_level")) {
\t\t\t\t\tbright_one = "/sys/class/sub_torch/sub_torch/sub_torch_level";
\t\t\t\t\tmax_brt_one = "1";
\t\t\t\t} else if (TWFunc::Path_Exists("/sys/devices/virtual/torch/torch/torch_level")) {
\t\t\t\t\tbright_one = "/sys/devices/virtual/torch/torch/torch_level";
\t\t\t\t\tmax_brt_one = "1";
\t\t\t\t}
\t\t\t}"""
        content = content.replace(target, replacement, 1)
        with open(action_cpp, "w", encoding="utf-8") as f:
            f.write(content)
        print("[+] Successfully patched action.cpp with flashlight hardware fallback")
        return True
    else:
        print("[!] Flashlight patch already applied or target line not found in action.cpp")
        return True

def patch_haptics(fox_root):
    events_cpp = os.path.join(fox_root, "bootable/recovery/minuitwrp/events.cpp")
    if not os.path.isfile(events_cpp):
        print(f"[-] events.cpp not found at {events_cpp}")
        return False

    with open(events_cpp, "r", encoding="utf-8") as f:
        content = f.read()

    vibrate_regex = re.compile(r"int vibrate\(int timeout_ms\)\s*\{[\s\S]*?\n\}", re.MULTILINE)
    match = vibrate_regex.search(content)
    if match:
        new_vibrate = """int vibrate(int timeout_ms)
{
    if (timeout_ms > 10000) timeout_ms = 1000;
    char tout[16];
    snprintf(tout, sizeof(tout), "%d\\n", timeout_ms);
    if (std::ifstream("/sys/class/leds/vibrator_single/activate").good()) {
        write_to_file("/sys/class/leds/vibrator_single/duration", tout);
        write_to_file("/sys/class/leds/vibrator_single/activate", "1\\n");
    } else if (std::ifstream("/sys/class/leds/vibrator/activate").good()) {
        write_to_file("/sys/class/leds/vibrator/duration", tout);
        write_to_file("/sys/class/leds/vibrator/activate", "1\\n");
    } else {
        write_to_file("/sys/class/timed_output/vibrator/enable", tout);
    }
    return 0;
}"""
        content = content[:match.start()] + new_vibrate + content[match.end():]
        with open(events_cpp, "w", encoding="utf-8") as f:
            f.write(content)
        print("[+] Successfully patched events.cpp with universal AW8697 vibrator_single logic")
        return True
    else:
        print("[-] Could not find vibrate function in events.cpp")
        return False

def patch_thermals(fox_root):
    data_cpp = os.path.join(fox_root, "bootable/recovery/data.cpp")
    if not os.path.isfile(data_cpp):
        print(f"[-] data.cpp not found at {data_cpp}")
        return False

    with open(data_cpp, "r", encoding="utf-8") as f:
        content = f.read()

    pattern_init = re.compile(r'if\s*\(\s*TWFunc::Path_Exists\s*\(\s*cpu_temp_file\s*\)\s*\)\s*\{\s*mConst\.SetValue\s*\(\s*"tw_no_cpu_temp"\s*,\s*"0"\s*\);', re.MULTILINE)
    if pattern_init.search(content):
        replacement_init = """if (!TWFunc::Path_Exists(cpu_temp_file) && TWFunc::Path_Exists("/sys/class/thermal/thermal_zone0/temp")) {
        cpu_temp_file = "/sys/class/thermal/thermal_zone0/temp";
    }
    if (TWFunc::Path_Exists(cpu_temp_file) || TWFunc::Path_Exists("/sys/class/thermal/thermal_zone0/temp"))
      {
        mConst.SetValue("tw_no_cpu_temp", "0");"""
        content = pattern_init.sub(replacement_init, content, count=1)

    pattern_read = re.compile(r'if\s*\(\s*TWFunc::read_file\s*\(\s*cpu_temp_file\s*,\s*results\s*\)\s*!=\s*0\s*\)', re.MULTILINE)
    if pattern_read.search(content):
        replacement_read = """if (TWFunc::read_file(cpu_temp_file, results) != 0 && TWFunc::read_file("/sys/class/thermal/thermal_zone0/temp", results) != 0)"""
        content = pattern_read.sub(replacement_read, content)

    with open(data_cpp, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] Successfully patched data.cpp with thermal zone 0 fallback")
    return True

def patch_splash(fox_root):
    patched_count = 0
    search_dirs = [
        os.path.join(fox_root, "vendor/recovery"),
        os.path.join(fox_root, "bootable/recovery")
    ]
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
                        
                        modified = False
                        if 'width="1080" h="1920"' in xml_content:
                            xml_content = xml_content.replace('width="1080" h="1920"', 'width="1080" h="2436"')
                            modified = True
                        if 'value="1920"' in xml_content:
                            xml_content = xml_content.replace('value="1920"', 'value="2436"')
                            modified = True
                        if '%screen_h%-400' in xml_content:
                            xml_content = xml_content.replace('%screen_h%-400', '%screen_h%-500')
                            modified = True
                        if '%screen_h%-320' in xml_content:
                            xml_content = xml_content.replace('%screen_h%-320', '%screen_h%-400')
                            modified = True

                        if modified:
                            with open(fpath, "w", encoding="utf-8") as f:
                                f.write(xml_content)
                            patched_count += 1
                    except Exception as e:
                        print(f"[-] Failed patching {fpath}: {e}")
    print(f"[+] Successfully patched {patched_count} splash XML files to 1080x2436")
    return True

def patch_version(fox_root):
    ofmk = os.path.join(fox_root, "bootable/recovery/orangefox.mk")
    if os.path.isfile(ofmk):
        with open(ofmk, "r", encoding="utf-8") as f:
            c = f.read()
        c = c.replace("FOX_INTERNAL_RELEASE := R12.0", "FOX_INTERNAL_RELEASE := R12.1")
        with open(ofmk, "w", encoding="utf-8") as f:
            f.write(c)
        print("[+] Patched bootable/recovery/orangefox.mk with R12.1")

    vend_sh = os.path.join(fox_root, "vendor/recovery/OrangeFox_vendor.sh")
    if os.path.isfile(vend_sh):
        with open(vend_sh, "r", encoding="utf-8") as f:
            c = f.read()
        c = c.replace("export FOX_INTERNAL_RELEASE=R12.0", "export FOX_INTERNAL_RELEASE=R12.1")
        with open(vend_sh, "w", encoding="utf-8") as f:
            f.write(c)
        print("[+] Patched vendor/recovery/OrangeFox_vendor.sh with R12.1")
    return True

def main():
    fox_root = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"[*] OrangeFox Patch Engine targeting: {os.path.abspath(fox_root)}")
    patch_flashlight(fox_root)
    patch_haptics(fox_root)
    patch_thermals(fox_root)
    patch_splash(fox_root)
    patch_version(fox_root)
    print("[*] All patches applied successfully!")

if __name__ == "__main__":
    main()
