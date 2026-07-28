#!/usr/bin/env python3
"""
Patches rnodeconf.py to add custom RNode model entries for:
  - B&Q Station G2 (ESP32-S3 + SX1262, 868/915 MHz, product 0x60)
  - Seeed SenseCAP T1000-E (nRF52840 + LR1110, 863-928 MHz, product 0x1E)

Usage:
  source venv/bin/activate    # activate the venv where RNS is installed
  python3 patch_rnodeconf.py  # run this script
  rnodeconf /dev/ttyACM0 -i   # verify it works

Safe to run multiple times — skips entries that already exist.
"""
import sys, glob

# Find rnodeconf.py in the active venv
try:
    import RNS
    rnodeconf_path = RNS.Utilities.rnodeconf.__file__
except Exception:
    matches = glob.glob(f"{sys.prefix}/lib/python*/site-packages/RNS/Utilities/rnodeconf.py")
    if not matches:
        # Try user site
        import site
        for sp in site.getsitepackages():
            matches += glob.glob(f"{sp}/RNS/Utilities/rnodeconf.py")
    if not matches:
        print("Could not find rnodeconf.py — is RNS installed?")
        sys.exit(1)
    rnodeconf_path = matches[0]

print(f"Patching {rnodeconf_path}...")

with open(rnodeconf_path) as f:
    content = f.read()

changed = False

# === Station G2 (product 0x60, models 0x62/0x63) ===

# 1. Add product and model defines
if "PRODUCT_STATION_G2" not in content:
    content = content.replace(
        'PRODUCT_HELTEC_T114 = 0xC2',
        'PRODUCT_STATION_G2  = 0x60 # B&Q Station G2\n    '
        'PRODUCT_HELTEC_T114 = 0xC2\n    '
        'MODEL_62            = 0x62 # Station G2 915 MHz\n    '
        'MODEL_63            = 0x63 # Station G2 868 MHz\n    '
        'PRODUCT_T1000E      = 0x1E # Seeed SenseCAP T1000-E\n    '
        'MODEL_B5            = 0xB5 # T1000-E, LR1110, 863-928 MHz'
    )
    changed = True
    print("  Added Station G2 + T1000-E product/model defines")

# 2. Add product name mappings
if 'ROM.PRODUCT_STATION_G2' not in content:
    content = content.replace(
        'ROM.PRODUCT_HELTEC_T114: "Heltec Mesh Node T114",',
        'ROM.PRODUCT_STATION_G2: "B&Q Station G2",\n    '
        'ROM.PRODUCT_HELTEC_T114: "Heltec Mesh Node T114",\n    '
        'ROM.PRODUCT_T1000E: "Seeed SenseCAP T1000-E",'
    )
    changed = True
    print("  Added product name mappings")

# 3. Add model entries to models dict
# Station G2 868 MHz (0x63)
if "0x63: [" not in content or "station_g2" not in content.lower():
    # Anchor on 0xBB (last common model entry)
    if '0xBB:' in content:
        content = content.replace(
            '0xBB: [850000000, 950000000, 17, "850 - 950 MHz", "rnode_firmware_lora32v10.zip", "SX1276"],',
            '0xBB: [850000000, 950000000, 17, "850 - 950 MHz", "rnode_firmware_lora32v10.zip", "SX1276"],\n'
            '    0x62: [902000000, 928000000, 22, "902 - 928 MHz", "rnode_firmware_station_g2_915.zip", "SX1262"],\n'
            '    0x63: [863000000, 870000000, 22, "863 - 870 MHz", "rnode_firmware_station_g2_868.zip", "SX1262"],\n'
            '    0xB5: [863000000, 928000000, 22, "863 - 928 MHz", "rnode_firmware_t1000e.zip", "LR1110"],'
        )
        changed = True
        print("  Added Station G2 + T1000-E to models dict")

# 4. Add model selection in auto-installer
if "elif selected_product == ROM.PRODUCT_STATION_G2:" not in content:
    if "elif selected_product == ROM.PRODUCT_HELTEC_T114:" in content:
        content = content.replace(
            'elif selected_product == ROM.PRODUCT_HELTEC_T114:',
            '''elif selected_product == ROM.PRODUCT_STATION_G2:
                    selected_platform = ROM.PLATFORM_ESP32
                    print("              B&Q Station G2 RNode Installer")
                    print("")
                    print("Select frequency band:")
                    print("  [1] 868 MHz (Europe/UK)")
                    print("  [2] 915 MHz (Americas)")
                    band_choice = input("Enter choice (1-2): ").strip()
                    if band_choice == "1":
                        selected_model = ROM.MODEL_63
                    else:
                        selected_model = ROM.MODEL_62
                    print("")
                elif selected_product == ROM.PRODUCT_T1000E:
                    selected_model = ROM.MODEL_B5
                    selected_platform = ROM.PLATFORM_NRF52
                    print("              Seeed SenseCAP T1000-E RNode Installer")
                elif selected_product == ROM.PRODUCT_HELTEC_T114:'''
        )
        changed = True
        print("  Added model selection for Station G2 + T1000-E")

if changed:
    with open(rnodeconf_path, 'w') as f:
        f.write(content)
    print("\nPatching complete!")
else:
    print("\nNo changes needed — all entries already present")

# Verify
try:
    import importlib
    importlib.reload(RNS.Utilities.rnodeconf)
    from RNS.Utilities import rnodeconf as rc
    print("\nVerification:")
    for k in [0x62, 0x63, 0xB5]:
        if k in rc.models:
            print(f"  {hex(k)}: {rc.models[k]}")
        else:
            print(f"  {hex(k)}: MISSING!")
except Exception as e:
    print(f"\nVerification skipped: {e}")