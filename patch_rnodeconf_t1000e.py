#!/usr/bin/env python3
"""Patches rnodeconf.py to add Seeed SenseCAP T1000-E model entries."""
import sys, glob, re

# Find rnodeconf.py
try:
    import RNS
    rnodeconf_path = RNS.Utilities.rnodeconf.__file__
except Exception:
    matches = glob.glob(f"{sys.prefix}/lib/python*/site-packages/RNS/Utilities/rnodeconf.py")
    if not matches:
        print("Could not find rnodeconf.py")
        sys.exit(1)
    rnodeconf_path = matches[0]

print(f"Patching {rnodeconf_path}...")

with open(rnodeconf_path) as f:
    content = f.read()

changed = False

# 1. Add PRODUCT_T1000E and MODEL_B5 defines
if "PRODUCT_T1000E" not in content:
    content = content.replace(
        'PRODUCT_HELTEC_T114 = 0xC2',
        'PRODUCT_HELTEC_T114 = 0xC2\n    PRODUCT_T1000E      = 0x1E # Seeed SenseCAP T1000-E\n    MODEL_B5            = 0xB5 # T1000-E, LR1110, 863-928 MHz'
    )
    changed = True
    print("  Added PRODUCT_T1000E and MODEL_B5 defines")

# 2. Add product name mapping
if 'ROM.PRODUCT_T1000E' not in content:
    content = content.replace(
        'ROM.PRODUCT_HELTEC_T114: "Heltec Mesh Node T114",',
        'ROM.PRODUCT_HELTEC_T114: "Heltec Mesh Node T114",\n    ROM.PRODUCT_T1000E: "Seeed SenseCAP T1000-E",'
    )
    changed = True
    print("  Added product name mapping")

# 3. Add model capabilities to models dict — anchor on last 0xB5/0xBA/etc entry
# Find the last model entry and add after it
if "0xB5: [" not in content or "T1000" not in content:
    # Find a good anchor — the 0xC5 or last known model entry
    # Use 0xC4 line as anchor (heltec32v2)
    if '0xC4:' in content:
        content = content.replace(
            '0xC4: [420000000, 520000000, 17, "420 - 520 MHz", "rnode_firmware_heltec32v2.zip", "SX1278"],',
            '0xC4: [420000000, 520000000, 17, "420 - 520 MHz", "rnode_firmware_heltec32v2.zip", "SX1278"],\n    0xB5: [863000000, 928000000, 22, "863 - 928 MHz", "rnode_firmware_t1000e.zip", "LR1110"],'
        )
        changed = True
        print("  Added T1000-E to models dict (after 0xC4)")
    else:
        # Try adding after 0xBB
        if '0xBB:' in content:
            content = content.replace(
                '0xBB: [850000000, 950000000, 17, "850 - 950 MHz", "rnode_firmware_lora32v10.zip", "SX1276"],',
                '0xBB: [850000000, 950000000, 17, "850 - 950 MHz", "rnode_firmware_lora32v10.zip", "SX1276"],\n    0xB5: [863000000, 928000000, 22, "863 - 928 MHz", "rnode_firmware_t1000e.zip", "LR1110"],'
            )
            changed = True
            print("  Added T1000-E to models dict (after 0xBB)")

# 4. Add model selection for T1000-E in auto-installer
if "elif selected_product == ROM.PRODUCT_T1000E:" not in content:
    if "elif selected_product == ROM.PRODUCT_HELTEC_T114:" in content:
        content = content.replace(
            'elif selected_product == ROM.PRODUCT_HELTEC_T114:',
            '''elif selected_product == ROM.PRODUCT_T1000E:
                    selected_model = ROM.MODEL_B5
                    selected_platform = ROM.PLATFORM_NRF52
                    print("              Seeed SenseCAP T1000-E RNode Installer")
                elif selected_product == ROM.PRODUCT_HELTEC_T114:'''
        )
        changed = True
        print("  Added model selection for T1000-E")

if changed:
    with open(rnodeconf_path, 'w') as f:
        f.write(content)
    print("\nPatching complete!")
else:
    print("\nNo changes needed — T1000-E entries already present")