#!/usr/bin/env python3
import sys
import os

def patch_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        print(f"[Infinix-X6871] Error reading {file_path}: {e}")
        return

    modified = False

    # 1. Update SukiSU version string from 3.1.8 to 4.2.1
    if "SukiSU Ultra 3.1.8" in content:
        content = content.replace("SukiSU Ultra 3.1.8", "SukiSU Ultra 4.2.1")
        modified = True
    if "{@module_install} SukiSU Ultra %ssu_ver%" in content:
        content = content.replace("{@module_install} SukiSU Ultra %ssu_ver%", "{@module_install} SukiSU Ultra 4.2.1")
        modified = True

    # 2. Add Vbmeta pages if not present
    if "mod_disable_vbmeta" not in content:
        vbmeta_pages = (
            '\n\t\t<page name="mod_disable_vbmeta">\n'
            '\t\t  <action>\n'
            '\t\t\t<action function="queueclear"/>\n'
            '\t\t\t<action function="set">fox_m_author=OrangeFox</action>\n'
            '\t\t\t<action function="set">fox_m_name=Disable Vbmeta / AVB</action>\n'
            '\t\t\t<action function="set">tw_file=Disable_Vbmeta.zip</action>\n'
            '\t\t\t<action function="set">tw_filename=/FFiles/OF_vbmeta/Disable_Vbmeta.zip</action>\n'
            '\t\t\t<action function="set">tw_filecheck=%tw_filename%</action>\n'
            '\t\t\t<action function="set">tw_zip_location=/FFiles/OF_vbmeta</action>\n'
            '\t\t\t<action function="set">fox_install_built_in_zip=1</action>\n'
            '\t\t\t<action function="queuezip"/>\n'
            '\t\t\t<action function="set">tw_notexistpage=fox_modules_confirm</action>\n'
            '\t\t\t<action function="set">tw_existpage=fox_modules_confirm</action>\n'
            '\t\t\t<action function="page">filecheck</action>\n'
            '\t\t  </action>\n'
            '\t\t</page>\n'
            '\n'
            '\t\t<page name="mod_enable_vbmeta">\n'
            '\t\t  <action>\n'
            '\t\t\t<action function="queueclear"/>\n'
            '\t\t\t<action function="set">fox_m_author=OrangeFox</action>\n'
            '\t\t\t<action function="set">fox_m_name=Enable Vbmeta / AVB</action>\n'
            '\t\t\t<action function="set">tw_file=Enable_Vbmeta.zip</action>\n'
            '\t\t\t<action function="set">tw_filename=/FFiles/OF_vbmeta/Enable_Vbmeta.zip</action>\n'
            '\t\t\t<action function="set">tw_filecheck=%tw_filename%</action>\n'
            '\t\t\t<action function="set">tw_zip_location=/FFiles/OF_vbmeta</action>\n'
            '\t\t\t<action function="set">fox_install_built_in_zip=1</action>\n'
            '\t\t\t<action function="queuezip"/>\n'
            '\t\t\t<action function="set">tw_notexistpage=fox_modules_confirm</action>\n'
            '\t\t\t<action function="set">tw_existpage=fox_modules_confirm</action>\n'
            '\t\t\t<action function="page">filecheck</action>\n'
            '\t\t  </action>\n'
            '\t\t</page>\n'
        )
        suki_pos = content.find('<page name="mod_sukisu">')
        if suki_pos != -1:
            suki_end = content.find("</page>", suki_pos)
            if suki_end != -1:
                content = content[:suki_end + 7] + vbmeta_pages + content[suki_end + 7:]
                modified = True

    # 3. Add Vbmeta listitems to fox_modules listbox if not present
    if "Disable Vbmeta (AVB Verification)" not in content:
        vbmeta_items = (
            '\n\t\t\t\t<listitem name="Disable Vbmeta (AVB Verification)">\n'
            '\t\t\t\t\t<condition var1="fileexists" var2="/FFiles/OF_vbmeta/Disable_Vbmeta.zip"/>\n'
            '\t\t\t\t\t<icon res="archive"/>\n'
            '\t\t\t\t\t<action function="page">mod_disable_vbmeta</action>\n'
            '\t\t\t\t</listitem>\n'
            '\n'
            '\t\t\t\t<listitem name="Enable Vbmeta (AVB Verification)">\n'
            '\t\t\t\t\t<condition var1="fileexists" var2="/FFiles/OF_vbmeta/Enable_Vbmeta.zip"/>\n'
            '\t\t\t\t\t<icon res="archive"/>\n'
            '\t\t\t\t\t<action function="page">mod_enable_vbmeta</action>\n'
            '\t\t\t\t</listitem>\n'
        )
        fox_mod_pos = content.find('<page name="fox_modules">')
        if fox_mod_pos != -1:
            listbox_end = content.find("</listbox>", fox_mod_pos)
            if listbox_end != -1:
                content = content[:listbox_end] + vbmeta_items + content[listbox_end:]
                modified = True

    if modified:
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"[Infinix-X6871] Successfully patched theme layout: {file_path}")
    else:
        print(f"[Infinix-X6871] Theme layout already up to date: {file_path}")

def main():
    if len(sys.argv) < 2:
        return
    workspace_root = sys.argv[1]
    
    # Scan for all pages/advanced.xml under bootable/recovery and vendor/recovery
    targets = []
    for root, dirs, files in os.walk(workspace_root):
        if "advanced.xml" in files:
            full_p = os.path.join(root, "advanced.xml")
            if "bootable" in full_p or "vendor" in full_p or "theme" in full_p:
                targets.append(full_p)

    for target in targets:
        patch_file(target)

if __name__ == "__main__":
    main()
