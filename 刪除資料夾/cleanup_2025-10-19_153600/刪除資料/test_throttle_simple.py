#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
簡化測試油門折線圖模組導入和創建
"""

import sys

def main():
    print("🧪 測試油門折線圖模組")
    print("=" * 60)
    
    # 測試 1: 導入
    print("\n[1/3] 測試導入...")
    try:
        from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import ThrottleLineChartModule
        print("✅ 導入成功")
    except Exception as e:
        print(f"❌ 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 測試 2: 創建實例
    print("\n[2/3] 測試創建實例...")
    try:
        module = ThrottleLineChartModule(
            year=2025,
            race="Japan",
            session="R"
        )
        print(f"✅ 創建成功")
        print(f"   模組名稱: {module.module_name}")
        print(f"   顯示名稱: {module.display_name}")
        print(f"   視窗標題: {module.get_window_title()}")
        print(f"   預設大小: {module.get_default_size()}")
    except Exception as e:
        print(f"❌ 創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 測試 3: 獲取 Widget
    print("\n[3/3] 測試獲取 Widget...")
    try:
        widget = module.get_widget()
        if widget:
            print(f"✅ Widget 獲取成功: {type(widget).__name__}")
        else:
            print(f"❌ Widget 為 None")
            return 1
    except Exception as e:
        print(f"❌ Widget 獲取失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 60)
    print("🎉 所有測試通過！模組可以正常使用")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
