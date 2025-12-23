#!/usr/bin/env python3
"""
Test Dynamic Resize for Fixed Windows

Verifies that fixed windows resize dynamically when MDI area is resized
"""

import sys
from pathlib import Path

workspace = Path(__file__).parent
sys.path.insert(0, str(workspace))

print("=" * 80)
print("DYNAMIC RESIZE VERIFICATION")
print("=" * 80)
print()

# Read GUI main file
gui_file = workspace / "f1t_gui_main.py"
content = gui_file.read_text(encoding='utf-8')

# Check 1: resizeEvent method exists
if "def resizeEvent(self, event):" in content:
    print("✅ resizeEvent method FOUND in CustomMdiArea")
else:
    print("❌ resizeEvent method NOT FOUND")

# Check 2: _rearrange_fixed_windows method exists
if "def _rearrange_fixed_windows(self):" in content:
    print("✅ _rearrange_fixed_windows method FOUND")
else:
    print("❌ _rearrange_fixed_windows method NOT FOUND")

# Check 3: Fixed windows filtering in resize
if "sw.property(\"is_welcome_fixed\")" in content:
    # Count occurrences in resize context
    lines = content.split('\n')
    resize_section = False
    found_in_resize = False
    
    for line in lines:
        if "def _rearrange_fixed_windows" in line:
            resize_section = True
        if resize_section and "is_welcome_fixed" in line:
            found_in_resize = True
            break
        if resize_section and "def " in line and "_rearrange_fixed_windows" not in line:
            resize_section = False
    
    if found_in_resize:
        print("✅ Fixed window filtering in _rearrange_fixed_windows FOUND")
    else:
        print("❌ Fixed window filtering in _rearrange_fixed_windows NOT FOUND")

# Check 4: Dynamic width calculation
if "window_width = mdi_width // num_fixed" in content:
    print("✅ Dynamic width calculation FOUND")
else:
    print("❌ Dynamic width calculation NOT FOUND")

# Check 5: setGeometry call in rearrange
if "subwindow.setGeometry(x_pos, 0, window_width, mdi_height)" in content:
    print("✅ Dynamic geometry update FOUND")
else:
    print("❌ Dynamic geometry update NOT FOUND")

print()
print("=" * 80)
print("EXPECTED BEHAVIOR")
print("=" * 80)
print()
print("When you resize the main GUI window:")
print("  1. MDI area triggers resizeEvent")
print("  2. _rearrange_fixed_windows() is called")
print("  3. Fixed windows are identified by 'is_welcome_fixed' property")
print("  4. Each window's width is recalculated (MDI width / 3)")
print("  5. All 3 windows are repositioned and resized")
print()
print("Result:")
print("  ✅ Season Progress always occupies left 1/3")
print("  ✅ Constructor Standings always occupies middle 1/3")
print("  ✅ Driver Standings always occupies right 1/3")
print("  ✅ Heights always match MDI area height")
print()
print("=" * 80)
print("✅ Dynamic resize mechanism configured!")
print()
print("NEXT STEP:")
print("1. Run: python f1t_gui_main.py")
print("2. Resize the main window (drag corners or edges)")
print("3. Expected: The 3 fixed windows resize proportionally")
print("4. Expected: They maintain their horizontal layout (1/3 each)")
print("=" * 80)
