#!/usr/bin/env python3
"""Patches rnodeconf.py to add Seeed SenseCAP T1000-E model entries.
Run on any machine that uses rnodeconf: python3 patch_rnodeconf_t1000e.py
"""
import sys

try:
    import RNS.Utilities.rnodeconf as rnc
    path = rnc.__file__
except ImportError:
    # Try finding it directly
    import subprocess
    result = subprocess.run([sys.executable, "-c", "import RNS.Utilities.rnodeconf as rnc; print(rnc.__file__)"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Cannot find rnodeconf.py — is RNS installed?")
        sys.exit(1)
    path = result.stdout.strip()

print(f"Patching {path}...")

with open(path, "r") as f:
    content = f.read()

changes = 0

# 1. Add PRODUCT_T1000E and MODEL_B5 defines
if "PRODUCT_T1000E" not in content:
    content = content.replace(
        "PRODUCT_HELTEC_T114 = 0xC2",
        'PRODUCT_HELTEC_T114 = 0xC2\n    PRODUCT_T1000E      = 0x1E # Seeed SenseCAP T1000-E\n    MODEL_B5            = 0xB5 # T1000-E, LR1110, 863-928 MHz'
    )
    changes += 1
    print("  Added PRODUCT_T1000E and MODEL_B5 defines")

# 2. Add to products dict
if 'ROM.PRODUCT_T1000E' not in content or '"Seeed SenseCAP T1000-E"' not in content:
    content = content.replace(
        'ROM.PRODUCT_HELTEC_T114: "Heltec Mesh Node T114",',
        'ROM.PRODUCT_HELTEC_T114: "Heltec Mesh Node T114",\n    ROM.PRODUCT_T1000E: "Seeed SenseCAP T1000-E",'
    )
    changes += 1
    print("  Added to products dict")

# 3. Add to models dict
if "0xB5:" not in content:
    content = content.replace(
        '0x17: [779000000, 928000000, 22, "779 - 928 Mhz", "rnode_firmware_techo.zip", "SX1262"],',
        '0x17: [779000000, 928000000, 22, "779 - 928 Mhz", "rnode_firmware_techo.zip", "SX1262"],\n    0xB5: [863000000, 928000000, 22, "863 - 928 MHz", "rnode_firmware_t1000e.zip", "LR1110"],'
    )
    changes += 1
    print("  Added to models dict")

# 4. Add installer menu entry
if "c_dev == 18" not in content:
    content = content.replace(
        '''                elif c_dev == 17:
                    selected_product = ROM.PRODUCT_STATION_G2''',
        '''                elif c_dev == 17:
                    selected_product = ROM.PRODUCT_STATION_G2'''
    )
    # Add after the Station G2 block
    old = '''                    print("---------------------------------------------------------------------------")
                    input()
                elif c_dev == 18:'''
    if old not in content:
        # Find the end of c_dev == 17 block and add c_dev == 18
        content = content.replace(
            '''                    print("who would like to experiment with it. Hit enter to continue.")
                    print("---------------------------------------------------------------------------")
                    input()

            except Exception as e:''',
            '''                    print("who would like to experiment with it. Hit enter to continue.")
                    print("---------------------------------------------------------------------------")
                    input()
                elif c_dev == 18:
                    selected_product = ROM.PRODUCT_T1000E
                    clear()
                    print("")
                    print("---------------------------------------------------------------------------")
                    print("              Seeed SenseCAP T1000-E RNode Installer")
                    print("")
                    print("Important! Using RNode firmware on T1000-E devices should currently be")
                    print("considered experimental. It is not intended for production or critical use.")
                    print("The currently supplied firmware is provided AS-IS as a courtesy to those")
                    print("who would like to experiment with it. Hit enter to continue.")
                    print("---------------------------------------------------------------------------")
                    input()

            except Exception as e:'''
        )
    changes += 1
    print("  Added installer menu entry (c_dev == 18)")

# 5. Add model selection for T1000-E
if "elif selected_product == ROM.PRODUCT_T1000E:" not in content:
    content = content.replace(
        '''                except Exception as e:
                    print("That band does not exist, exiting now.")
                    graceful_exit()

            if selected_model != ROM.MODEL_FF''',
        '''                except Exception as e:
                    print("That band does not exist, exiting now.")
                    graceful_exit()

            elif selected_product == ROM.PRODUCT_T1000E:
                selected_model = ROM.MODEL_B5
                selected_platform = ROM.PLATFORM_NRF52

            if selected_model != ROM.MODEL_FF'''
    )
    changes += 1
    print("  Added model selection for T1000-E")

if changes > 0:
    with open(path, "w") as f:
        f.write(content)
    print(f"\nDone! {changes} changes applied to {path}")
else:
    print("\nNo changes needed — T1000-E entries already present")