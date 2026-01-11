# -*- coding: utf-8 -*-
"""測試模組幫助系統"""

import sys
sys.path.insert(0, '.')

try:
    from windows.widgets.module_help_system import ModuleHelpRegistry, ModuleHelpDialog, show_module_help
    print("[OK] Module help system imported successfully")
    
    # 註冊所有模組
    ModuleHelpRegistry.register_all()
    print(f"[OK] Registered {len(ModuleHelpRegistry._registry)} modules")
    
    # 測試標題到模組鍵的映射
    test_cases = [
        ("Driver Strategy", "driver_strategy"),
        ("車手策略", "driver_strategy"),
        ("Top Speed History", "top_speed_history"),
        ("最高速歷史", "top_speed_history"),
        ("Track Map", "track_map"),
        ("賽道地圖", "track_map"),
        ("SF% History", "sf_percentage_chart"),
        ("油門 95% 歷史", "throttle_history"),
        ("Sector Comparison S1", "sector_comparison_s1"),
        ("分段比較 S2", "sector_comparison_s1"),
        ("Unknown Module", "_default"),
    ]
    
    print("\n[TEST] Title to Module Key Mapping:")
    all_passed = True
    for title, expected_key in test_cases:
        result = ModuleHelpRegistry.get_module_key_from_title(title)
        status = "PASS" if result == expected_key else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"  {status}: '{title}' -> '{result}' (expected: '{expected_key}')")
    
    # 測試獲取幫助內容
    print("\n[TEST] Get Help Content:")
    content = ModuleHelpRegistry.get_help_content("driver_strategy")
    print(f"  driver_strategy title: {content.get('title', 'N/A')}")
    print(f"  driver_strategy has description: {bool(content.get('description'))}")
    print(f"  driver_strategy has features: {bool(content.get('features'))}")
    print(f"  driver_strategy has colors: {bool(content.get('colors'))}")
    
    if all_passed:
        print("\n[SUCCESS] All tests passed!")
    else:
        print("\n[WARNING] Some tests failed!")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
