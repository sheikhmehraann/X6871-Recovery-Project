#!/usr/bin/env python3
import sys
import os
import re

if len(sys.argv) < 2:
    sys.exit(0)

workspace_root = sys.argv[1]
pm = os.path.join(workspace_root, "bootable/recovery/partitionmanager.cpp")

if os.path.isfile(pm):
    with open(pm, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    pattern = r"(bool TWPartitionManager::Unmap_Super_Devices\(\)\s*\{[\s\S]*?)(if\s*\(!\(\*iter\)->Unmap_Super_Device\(\)\)\s*\{\s*gui_err\([^)]+\);\s*return false;\s*\})([\s\S]*?\n\})"
    def repl(m):
        return m.group(1) + "(*iter)->UnMount(true);\n\t\t\t(*iter)->Unmap_Super_Device();" + m.group(3)

    new_content, count = re.subn(pattern, repl, content)
    if count > 0:
        with open(pm, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content)
        print("[Infinix-X6871] Successfully patched Unmap_Super_Devices in partitionmanager.cpp")
    else:
        print("[Infinix-X6871] Note: Unmap_Super_Devices pattern not matched or already patched")
