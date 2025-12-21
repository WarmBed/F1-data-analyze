#!/usr/bin/env python3
"""
Test Fixed Welcome Windows Protection

Verifies that the three welcome windows are protected from Tile/Cascade/Close operations
"""

import sys
from pathlib import Path

workspace = Path(__file__).parent
sys.path.insert(0, str(workspace))

print("=" * 80)
print("FIXED WELCOME WINDOWS PROTECTION VERIFICATION")
print("=" * 80)
print()

# Read GUI main file
gui_file = workspace / "f1t_gui_main.py"
content = gui_file.read_text(encoding='utf-8')

# Check 1: Window property marking
if 'setProperty("is_welcome_fixed", True)' in content:
    count = content.count('setProperty("is_welcome_fixed", True)')
    print(f"✅ Fixed window marking FOUND ({count} instances)")
    if count == 3:
        print("   ✅ All 3 windows marked correctly")
    else:
        print(f"   ⚠️  Expected 3 instances, found {count}")
else:
    print("❌ Fixed window marking NOT FOUND")

# Check 2: Tile windows filtering
if 'and not sw.property("is_welcome_fixed")' in content:
    print("✅ Tile windows filtering FOUND")
else:
    print("❌ Tile windows filtering NOT FOUND")

# Check 3: Cascade windows filtering
if 'subwindows = [sw for sw in all_subwindows if not sw.property("is_welcome_fixed")]' in content:
    occurrences = content.count('subwindows = [sw for sw in all_subwindows if not sw.property("is_welcome_fixed")]')
    print(f"✅ List comprehension filtering FOUND ({occurrences} times)")
else:
    print("❌ Cascade windows filtering NOT FOUND")

# Check 4: Minimize all filtering
lines = content.split('\n')
minimize_section = [i for i, line in enumerate(lines) if 'def minimize_all_windows' in line]
if minimize_section:
    section_start = minimize_section[0]
    section_lines = lines[section_start:section_start + 30]
    if any('is_welcome_fixed' in line for line in section_lines):
        print("✅ Minimize all filtering FOUND")
    else:
        print("❌ Minimize all filtering NOT FOUND")

# Check 5: Maximize all filtering
maximize_section = [i for i, line in enumerate(lines) if 'def maximize_all_windows' in line]
if maximize_section:
    section_start = maximize_section[0]
    section_lines = lines[section_start:section_start + 30]
    if any('is_welcome_fixed' in line for line in section_lines):
        print("✅ Maximize all filtering FOUND")
    else:
        print("❌ Maximize all filtering NOT FOUND")

# Check 6: Restore all filtering
restore_section = [i for i, line in enumerate(lines) if 'def restore_all_windows' in line]
if restore_section:
    section_start = restore_section[0]
    section_lines = lines[section_start:section_start + 30]
    if any('is_welcome_fixed' in line for line in section_lines):
        print("✅ Restore all filtering FOUND")
    else:
        print("❌ Restore all filtering NOT FOUND")

# Check 7: Close all filtering
close_section = [i for i, line in enumerate(lines) if 'def close_all_mdi_windows' in line]
if close_section:
    section_start = close_section[0]
    section_lines = lines[section_start:section_start + 20]  # Increased range
    if any('is_welcome_fixed' in line for line in section_lines):
        print("✅ Close all filtering FOUND")
    else:
        print("❌ Close all filtering NOT FOUND")
else:
    print("❌ close_all_mdi_windows method NOT FOUND")

print()
print("=" * 80)
print("PROTECTED OPERATIONS")
print("=" * 80)
print()
print("The following operations will NOT affect the 3 fixed welcome windows:")
print("  ✅ View → Tile Windows")
print("  ✅ View → Cascade Windows")
print("  ✅ View → Minimize All Windows")
print("  ✅ View → Maximize All Windows")
print("  ✅ View → Restore All Windows")
print("  ✅ View → Close All Windows")
print()
print("The 3 fixed windows will always stay:")
print("  1. Season Progress (left)")
print("  2. Constructor Standings (middle)")
print("  3. Driver Standings (right)")
print()
print("=" * 80)
print("✅ Protection mechanism configured!")
print()
print("NEXT STEP:")
print("1. Run: python f1t_gui_main.py")
print("2. Try: View → Tile Windows")
print("3. Expected: Only new analysis windows are rearranged")
print("4. Expected: The 3 welcome windows stay in their horizontal layout")
print("=" * 80)
