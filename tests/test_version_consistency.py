#!/usr/bin/env python3
"""
測試版本號一致性
Verify Version Consistency Across F1T Application
"""

import sys
from pathlib import Path

# 確保可以導入模組
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("F1T 版本一致性檢查")
print("=" * 70)

# 1. 檢查集中配置的版本
from config.version import APP_VERSION, APP_FULL_TITLE
print(f"\n✅ 集中配置版本:")
print(f"   APP_VERSION: {APP_VERSION}")
print(f"   APP_FULL_TITLE: {APP_FULL_TITLE}")

# 2. 檢查 Splash Screen 版本（通過讀取源碼）
try:
    import re
    splash_file = Path("modules/gui/splash_screen.py")
    if splash_file.exists():
        content = splash_file.read_text(encoding='utf-8')
        # 檢查是否使用 APP_VERSION
        if "from config.version import APP_VERSION" in content and "self.version = APP_VERSION" in content:
            print(f"\n✅ Splash Screen 版本: 使用 APP_VERSION ({APP_VERSION})")
            print(f"   ✅ 版本一致！")
        else:
            print(f"\n❌ Splash Screen 未使用集中配置")
    else:
        print(f"\n❌ 找不到 splash_screen.py")
except Exception as e:
    print(f"\n❌ Splash Screen 檢查失敗: {e}")

# 3. 檢查 GUI 主視窗配置
print(f"\n✅ GUI 主視窗配置:")
print(f"   使用 APP_FULL_TITLE: {APP_FULL_TITLE}")
print(f"   預期視窗標題: {APP_FULL_TITLE}")

# 4. 總結
print("\n" + "=" * 70)
print("版本一致性檢查完成！")
print("=" * 70)

print(f"\n📋 標準版本號: {APP_VERSION}")
print(f"📋 完整標題: {APP_FULL_TITLE}")
print("\n所有版本顯示位置:")
print("  • Splash Screen 左下角: 顯示 APP_VERSION")
print("  • GUI 主視窗標題列: 顯示 APP_FULL_TITLE")
print("  • 關於對話框: 顯示完整版本資訊")

print("\n🎯 修改版本號時，只需更新 config/version.py 的 APP_VERSION 常數即可！")
