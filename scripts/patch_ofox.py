#!/usr/bin/env python3
"""
OrangeFox Recovery Hardware & Architecture Patch Engine for Infinix GT 20 Pro (X6871 / MT6895)
Patches:
1. Flashlight: Direct hardware support for MediaTek OCP81375 (/sys/class/torch/torch/torch_level) - ignores aw22xxx_led mecha loop
2. Haptics: Full recursive source patch for AW8697 Linear Vibrator (/sys/class/leds/vibrator_single)
3. Thermals: Unlocked CPU temp display for MT6895 soc_max (/sys/class/thermal/thermal_zone0/temp)
4. Splash: Native 1080x2436 AMOLED resolution scaling across all splash XML resources
5. DRM: Single-pipe atomic display rendering for MediaTek MT6895
6. Build: Android 14 2-part and 3-part lunch combo compatibility shim for envsetup.sh
"""

import os
import sys
import re

def patch_envsetup(fox_root):
    envsetup_paths = [
        os.path.join(fox_root, "build/make/envsetup.sh"),
        os.path.join(fox_root, "build/envsetup.sh")
    ]
    # Dynamically detect available release config
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
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"[+] Successfully patched {path} with 2-part lunch compatibility shim ({avail_release})")
                    patched = True
                elif "TARGET_RELEASE:-" in content:
                    content = re.sub(r'release="\$\{TARGET_RELEASE:-[^}]+\}"', f'release="${{TARGET_RELEASE:-{avail_release}}}"', content)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
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

    # 1. Block aw22xxx_led (Mecha Loop RGB) from being detected as flashlight LED during directory walk
    if "aw22xxx" not in content:
        content = content.replace(
            "while ((dentry = readdir(dd))) {",
            "while ((dentry = readdir(dd))) {\n\t\t\tif (strstr(dentry->d_name, \"aw22xxx\") || strstr(dentry->d_name, \"loop\")) continue;"
        )

    # 2. Unconditionally prioritize the real camera flash next to the rear camera
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
        print("[+] Patched action.cpp with rear camera flashlight priority")

    # 3. Ensure writing "1\n" for ON and "0\n" for OFF when controlling torch_level
    content = content.replace(
        'TWFunc::write_to_file(bright_one, max_brt_one);',
        'if (bright_one.find("torch") != std::string::npos) { TWFunc::write_to_file(bright_one, "1\\n"); } else { TWFunc::write_to_file(bright_one, max_brt_one); }'
    )
    content = content.replace(
        'TWFunc::write_to_file(bright_one, "0");',
        'TWFunc::write_to_file(bright_one, "0\\n");'
    )

    with open(action_cpp, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] Successfully hardened action.cpp with real camera flashlight controls")
    return True

def patch_haptics(fox_root):
    # Walk all files under bootable/recovery and vendor/recovery
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
                            with open(fpath, "w", encoding="utf-8") as f:
                                f.write(content)
                            patched_count += 1
                    except Exception as e:
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

    # 1. Unconditionally unlock tw_no_cpu_temp so the GUI always displays CPU temperature
    content = re.sub(r'mConst\.SetValue\s*\(\s*"tw_no_cpu_temp"\s*,\s*"1"\s*\);', 'mConst.SetValue("tw_no_cpu_temp", "0");', content)
    content = re.sub(r'mConst\.SetValue\s*\(\s*"tw_no_cpu_temp"\s*,\s*"\w+"\s*\);', 'mConst.SetValue("tw_no_cpu_temp", "0");', content)

    # 2. Force default user settings to show CPU temperature on status bar
    content = re.sub(r'mPersist\.SetValue\s*\(\s*"tw_show_cpu_temp"\s*,\s*"0"\s*\);', 'mPersist.SetValue("tw_show_cpu_temp", "1");', content)
    content = re.sub(r'mPersist\.SetValue\s*\(\s*"of_status_cpu_temp"\s*,\s*"0"\s*\);', 'mPersist.SetValue("of_status_cpu_temp", "1");', content)

    # 3. Ensure fallback in read function
    content = re.sub(r'if\s*\(\s*TWFunc::read_file\s*\(\s*cpu_temp_file\s*,\s*results\s*\)\s*!=\s*0\s*\)',
                     'if (TWFunc::read_file(cpu_temp_file, results) != 0 && TWFunc::read_file("/sys/class/thermal/thermal_zone0/temp", results) != 0 && TWFunc::read_file("/sys/devices/virtual/thermal/thermal_zone0/temp", results) != 0)', content)

    with open(data_cpp, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] Successfully patched data.cpp with thermal zone 0 unlocked and status bar enabled")
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

    # Also patch customization.xml to ensure /tmp/orangefox directories exist before copy
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
                            with open(fpath, "w", encoding="utf-8") as f:
                                f.write(content)
                            print(f"[+] Hardened {fpath} with ramdisk splash directory creation")
                    except Exception as e:
                        pass
    print(f"[+] Successfully patched {patched_count} splash XML files to 1080x2436")
    return True

def patch_identity_fingerprint(fox_root):
    stock_fp = "Infinix/X6871-OP/Infinix-X6871:15/AP3A.240905.015.A2/180003:user/release-keys"
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
                if file.endswith((".cpp", ".c", ".h", ".hpp", ".sh", ".py")):
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        orig = content
                        if "alps/hal_mgvi_64" in content:
                            content = re.sub(r'alps/hal_mgvi_64[^\s"\';\)]+', stock_fp, content)
                        if "ro.build.fingerprint" in content and "alps" in content:
                            content = content.replace("alps", "Infinix")
                        if content != orig:
                            with open(fpath, "w", encoding="utf-8") as f:
                                f.write(content)
                            patched_count += 1
                    except Exception as e:
                        pass
    print(f"[+] Successfully patched {patched_count} source files with stock device identity fingerprint")
    return True

def patch_graphics_drm(fox_root):
    drm_cpp = os.path.join(fox_root, "bootable/recovery/minuitwrp/graphics_drm.cpp")
    if not os.path.isfile(drm_cpp):
        print(f"[-] graphics_drm.cpp not found at {drm_cpp}")
        return False

    repo_script_drm = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graphics_drm.cpp")
    if os.path.isfile(repo_script_drm):
        try:
            with open(repo_script_drm, "r", encoding="utf-8") as f_src:
                src_content = f_src.read()
            with open(drm_cpp, "w", encoding="utf-8") as f_dst:
                f_dst.write(src_content)
            print(f"[+] Successfully deployed verified MediaTek single-pipe graphics_drm.cpp to {drm_cpp}")
            return True
        except Exception as e:
            print(f"[!] Direct copy of graphics_drm.cpp failed ({e}), falling back to in-place patching...")

    try:
        with open(drm_cpp, "r", encoding="utf-8") as f:
            code = f.read()

        if "#define DEFAULT_NUM_LMS 2" in code:
            code = code.replace("#define DEFAULT_NUM_LMS 2", "#define DEFAULT_NUM_LMS 1")

        old_zpos = """  /* populate z-order property required for 4 layer mixer */
  if (number_of_lms == 4)
    zpos = plane >> 1;

  atomic_add_prop_to_plane(plane_res, atomic_req,
                           plane_res[plane].plane->plane_id, "zpos", zpos);"""

        new_zpos = """  /* populate z-order property required for 4 layer mixer */
  if (number_of_lms == 4) {
    zpos = plane >> 1;
    atomic_add_prop_to_plane(plane_res, atomic_req,
                             plane_res[plane].plane->plane_id, "zpos", zpos);
  }"""
        if old_zpos in code:
            code = code.replace(old_zpos, new_zpos)

        old_add_prop = """static int atomic_add_prop_to_plane(Plane *plane_res, drmModeAtomicReq *req,
                                    uint32_t obj_id, const char *prop_name,
                                    uint64_t value) {
  uint32_t prop_id;

  prop_id = find_plane_prop_id(obj_id, prop_name, plane_res);
  if (prop_id == 0) {
    printf("Could not find obj_id = %d\\n", obj_id);
    return -EINVAL;
  }"""

        new_add_prop = """static int atomic_add_prop_to_plane(Plane *plane_res, drmModeAtomicReq *req,
                                    uint32_t obj_id, const char *prop_name,
                                    uint64_t value) {
  uint32_t prop_id;

  prop_id = find_plane_prop_id(obj_id, prop_name, plane_res);
  if (prop_id == 0) {
    if (strcmp(prop_name, "zpos") != 0) {
      printf("Could not find prop %s for obj_id = %d\\n", prop_name, obj_id);
    }
    return -EINVAL;
  }"""
        if old_add_prop in code:
            code = code.replace(old_add_prop, new_add_prop)

        old_update = """  /* Add property */
  for(i = 0; i < number_of_lms; i++)
    drmModeAtomicAddProperty(atomic_req, plane_res[i].plane->plane_id,
                             fb_prop_id, drm_surfaces[current_buffer]->fb_id);"""

        new_update = """  /* Add property */
  for(i = 0; i < number_of_lms; i++) {
    drmModeAtomicAddProperty(atomic_req, plane_res[i].plane->plane_id,
                             fb_prop_id, drm_surfaces[current_buffer]->fb_id);
    atomic_add_prop_to_plane(plane_res, atomic_req,
                             plane_res[i].plane->plane_id, "CRTC_ID",
                             main_monitor_crtc->crtc_id);
  }"""
        if old_update in code:
            code = code.replace(old_update, new_update)

        old_disable = """static void disable_non_main_crtcs(int fd,
                    drmModeRes *resources,
                    drmModeCrtc* main_crtc) {
  uint32_t prop_id;
  drmModeAtomicReqPtr atomic_req = drmModeAtomicAlloc();
  for (int i = 0; i < resources->count_connectors; i++) {
    drmModeConnector* connector = drmModeGetConnector(fd, resources->connectors[i]);
    drmModeCrtc* crtc = find_crtc_for_connector(fd, resources, connector);
    if (crtc->crtc_id != main_crtc->crtc_id) {
      // Switching to atomic commit. Given only crtc, we can only set ACTIVE = 0
      // to disable any Nonmain CRTCs
      find_prop_id(&crtc_res, crtc, Crtc, crtc->crtc_id, "ACTIVE", prop_id);
      if (prop_id == 0)
        return;

      if (drmModeAtomicAddProperty(atomic_req, main_monitor_crtc->crtc_id, prop_id, 0) < 0)
        return;

    }
    drmModeFreeCrtc(crtc);
  }
  if (drmModeAtomicCommit(drm_fd, atomic_req,DRM_MODE_ATOMIC_ALLOW_MODESET, NULL))
    printf("Atomic Commit failed in DisableNonMainCrtcs\\n");

  drmModeAtomicFree(atomic_req);
}"""

        new_disable = """static void disable_non_main_crtcs(int fd,
                    drmModeRes *resources,
                    drmModeCrtc* main_crtc) {
  for (int i = 0; i < resources->count_connectors; i++) {
    drmModeConnector* connector = drmModeGetConnector(fd, resources->connectors[i]);
    if (!connector) continue;
    drmModeCrtc* crtc = find_crtc_for_connector(fd, resources, connector);
    if (crtc) {
      if (crtc->crtc_id != main_crtc->crtc_id) {
        drmModeSetCrtc(fd, crtc->crtc_id, 0, 0, 0, NULL, 0, NULL);
      }
      drmModeFreeCrtc(crtc);
    }
    drmModeFreeConnector(connector);
  }
}"""
        if old_disable in code:
            code = code.replace(old_disable, new_disable)

        with open(drm_cpp, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"[+] Successfully patched {drm_cpp} with MediaTek single-pipe DRM fixes")
        return True
    except Exception as e:
        print(f"[-] Failed patching {drm_cpp}: {e}")
        return False

def patch_magiskboot_vendor_boot(fox_root):
    twrp_funcs_cpp = os.path.join(fox_root, "bootable/recovery/twrp-functions.cpp")
    if not os.path.isfile(twrp_funcs_cpp):
        print(f"[-] twrp-functions.cpp not found at {twrp_funcs_cpp}")
        return False

    with open(twrp_funcs_cpp, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    orig = content

    # 1. Target vendor_boot on Header v4 devices for unpack/repack
    old_boot_find = 'TWPartition *Boot = PartitionManager.Find_Partition_By_Path("/boot");'
    new_boot_find = """TWPartition *Boot = PartitionManager.Find_Partition_By_Path("/boot");
  TWPartition *VendorBoot = PartitionManager.Find_Partition_By_Path("/vendor_boot");"""
    if old_boot_find in content and "VendorBoot =" not in content:
        content = content.replace(old_boot_find, new_boot_find, 1)

    old_ab_check = """#if (defined(AB_OTA_UPDATER) || defined(FOX_AB_DEVICE)) && !defined(OF_AB_DEVICE_WITH_RECOVERY_PARTITION)
  if (Boot != NULL)
    {
       tmpstr = Boot->Actual_Block_Device;"""
    new_ab_check = """#if (defined(AB_OTA_UPDATER) || defined(FOX_AB_DEVICE)) && !defined(OF_AB_DEVICE_WITH_RECOVERY_PARTITION)
  if (VendorBoot != NULL)
    {
       tmpstr = VendorBoot->Actual_Block_Device;
    }
  else if (Boot != NULL)
    {
       tmpstr = Boot->Actual_Block_Device;"""
    if old_ab_check in content:
        content = content.replace(old_ab_check, new_ab_check, 1)

    # 2. Inject recovery ramdisk rename after magiskboot unpack
    unpack_needle = 'AppendLineToFile (cmd_script, "[ $? == 0 ] && LOGINFO \\"- Succeeded.\\" || abort \\"- Unpacking image failed.\\");'
    unpack_inject = """AppendLineToFile (cmd_script, "[ $? == 0 ] && LOGINFO \\"- Succeeded.\\" || abort \\"- Unpacking image failed.\\");
\t        // Vendor_boot v4 recovery ramdisk bridge
\t        AppendLineToFile (cmd_script, "[ -f vendor_ramdisk_recovery.cpio ] && mv -f vendor_ramdisk_recovery.cpio ramdisk.cpio");"""
    if unpack_needle in content and "vendor_ramdisk_recovery.cpio" not in content:
        content = content.replace(unpack_needle, unpack_inject, 1)

    # 3. Inject vendor_ramdisk_recovery.cpio copy before magiskboot repack
    repack_needle = 'AppendLineToFile (cmd_script2, magiskboot_sbin + " repack \\"" + tmpstr + "\\" > /dev/null 2>&1");'
    repack_inject = """// Vendor_boot v4 recovery ramdisk repack bridge
\t        AppendLineToFile (cmd_script2, "[ -f ramdisk.cpio ] && cp -f ramdisk.cpio vendor_ramdisk_recovery.cpio");
\t        AppendLineToFile (cmd_script2, magiskboot_sbin + " repack \\"" + tmpstr + "\\" > /dev/null 2>&1");"""
    if repack_needle in content and "vendor_ramdisk_recovery.cpio" not in content:
        content = content.replace(repack_needle, repack_inject, 1)

    if content != orig:
        with open(twrp_funcs_cpp, "w", encoding="utf-8") as f:
            f.write(content)
        print("[+] Successfully patched twrp-functions.cpp with native vendor_boot v4 splash unpack/repack support")
        return True
    else:
        print("[*] twrp-functions.cpp already patched or target blocks not found")
        return False

def patch_foxstart_identity(fox_root):
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
                if file == "foxstart.sh":
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        orig = content

                        target = 'ROM=$(get_ROM)'
                        replacement = """ROM=$(get_ROM)
   # Dynamic runtime device identity detection (Clean Native OrangeFox Standard)
   # Static Device Identity (Infinix GT 20 Pro - X6871)
   [ -x "$SETPROP" ] && {
      $SETPROP "ro.product.brand" "Infinix" > /dev/null 2>&1
      $SETPROP "ro.product.model" "Infinix X6871" > /dev/null 2>&1
      $SETPROP "ro.product.marketname" "Infinix GT 20 Pro" > /dev/null 2>&1
      $SETPROP "ro.product.device" "Infinix-X6871" > /dev/null 2>&1
      $SETPROP "ro.board.platform" "mt6895" > /dev/null 2>&1
   }

   # Dynamic Runtime Properties - Read directly from the running ROM / system
   RT_RELEASE=$(getprop ro.build.version.release)
   [ -z "$RT_RELEASE" ] && [ -f /system/build.prop ] && RT_RELEASE=$(grep -m1 '^ro.build.version.release=' /system/build.prop | cut -d= -f2)
   [ -z "$RT_RELEASE" ] && [ -f /system_root/system/build.prop ] && RT_RELEASE=$(grep -m1 '^ro.build.version.release=' /system_root/system/build.prop | cut -d= -f2)
   [ -n "$RT_RELEASE" ] && {
      RELEASE_VERSION="$RT_RELEASE"
      echo "RELEASE_VERSION=$RT_RELEASE" >> $CFG
      [ -x "$SETPROP" ] && {
         $SETPROP "ro.build.version.release" "$RT_RELEASE" > /dev/null 2>&1
         $SETPROP "orangefox.system.release" "$RT_RELEASE" > /dev/null 2>&1
      }
   }

   RT_DISP=$(getprop ro.build.display.id)
   [ -z "$RT_DISP" ] && [ -f /system/build.prop ] && RT_DISP=$(grep -m1 '^ro.build.display.id=' /system/build.prop | cut -d= -f2)
   [ -z "$RT_DISP" ] && [ -f /system_root/system/build.prop ] && RT_DISP=$(grep -m1 '^ro.build.display.id=' /system_root/system/build.prop | cut -d= -f2)
   [ -n "$RT_DISP" ] && {
      tmp2="$RT_DISP"
      [ -x "$SETPROP" ] && $SETPROP "ro.build.display.id" "$RT_DISP" > /dev/null 2>&1
   }

   RT_FP=$(getprop ro.build.fingerprint)
   [ -z "$RT_FP" ] && [ -f /system/build.prop ] && RT_FP=$(grep -m1 '^ro.build.fingerprint=' /system/build.prop | cut -d= -f2)
   [ -z "$RT_FP" ] && [ -f /system_root/system/build.prop ] && RT_FP=$(grep -m1 '^ro.build.fingerprint=' /system_root/system/build.prop | cut -d= -f2)
   [ -n "$RT_FP" ] && {
      FP="$RT_FP"
      echo "ROM_FINGERPRINT=$RT_FP" >> $CFG
      [ -x "$SETPROP" ] && {
         $SETPROP "ro.build.fingerprint" "$RT_FP" > /dev/null 2>&1
         $SETPROP "orangefox.system.fingerprint" "$RT_FP" > /dev/null 2>&1
      }
   }

   RT_SDK=$(getprop ro.build.version.sdk)
   [ -z "$RT_SDK" ] && [ -f /system/build.prop ] && RT_SDK=$(grep -m1 '^ro.build.version.sdk=' /system/build.prop | cut -d= -f2)
   [ -n "$RT_SDK" ] && {
      ANDROID_SDK="$RT_SDK"
      echo "ANDROID_SDK=$RT_SDK" >> $CFG
      [ -x "$SETPROP" ] && {
         $SETPROP "ro.build.version.sdk" "$RT_SDK" > /dev/null 2>&1
         $SETPROP "orangefox.rom.sdk" "$RT_SDK" > /dev/null 2>&1
      }
   }"""
                        if target in content and "Dynamic Runtime Properties" not in content:
                            content = content.replace(target, replacement, 1)

                        if content != orig:
                            with open(fpath, "w", encoding="utf-8") as f:
                                f.write(content)
                            patched_count += 1
                            print(f"[+] Patched {fpath} with dynamic runtime identity detection")
                    except Exception as e:
                        print(f"[-] Failed patching {fpath}: {e}")
    return patched_count > 0

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
                with open(data_cpp, "w", encoding="utf-8") as f:
                    f.write(content)
                print("[+] Successfully enabled AVB2.0 disable addon in data.cpp")
        except Exception as e:
            print(f"[-] Failed patching data.cpp for AVB: {e}")

    # Patch OF_avb20.sh to support A/B devices
    for root, _, files in os.walk(os.path.join(fox_root, "vendor/recovery")):
        for file in files:
            if file == "OF_avb20.sh":
                fpath = os.path.join(root, file)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        sh_c = f.read()
                    old_ab = """\tslot_suffix=$(getprop ro.boot.slot_suffix);
\tif [ -n "$slot_suffix" ]; then
\t\tabort "- AVB 2.0 patching is inappropriate for an A/B device.";
\tfi"""
                    new_ab = """\tslot_suffix=$(getprop ro.boot.slot_suffix);
\tbootpart=$(find /dev/block -name "boot$slot_suffix" | grep "by-name/boot$slot_suffix" -m 1 2>/dev/null);
\t[ -z "$bootpart" ] && bootpart=$(find /dev/block -name "vendor_boot$slot_suffix" | grep "by-name/vendor_boot$slot_suffix" -m 1 2>/dev/null);"""
                    if old_ab in sh_c:
                        sh_c = sh_c.replace(old_ab, new_ab, 1)
                        with open(fpath, "w", encoding="utf-8") as f:
                            f.write(sh_c)
                        print(f"[+] Patched {fpath} for A/B slot-aware AVB2.0 patching")
                except Exception as e:
                    pass
    return True

def main():
    fox_root = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"[*] OrangeFox Patch Engine targeting: {os.path.abspath(fox_root)}")
    patch_envsetup(fox_root)
    patch_flashlight(fox_root)
    patch_haptics(fox_root)
    patch_thermals(fox_root)
    patch_splash(fox_root)
    patch_magiskboot_vendor_boot(fox_root)
    patch_identity_fingerprint(fox_root)
    patch_foxstart_identity(fox_root)
    patch_avb_settings(fox_root)
    patch_graphics_drm(fox_root)
    print("[*] Hardware and architecture patches applied successfully!")

if __name__ == "__main__":
    main()
