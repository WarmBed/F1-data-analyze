#!/usr/bin/env python3
"""
測試腳本：模擬 GUI 中高頻調用 color_palette_provider.ensure_loaded()
"""

import sys
import time
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.gui.themes import color_palette_provider

def test_high_frequency_calls():
    """模擬 paintEvent 中的高頻調用"""
    
    print("=" * 80)
    print("🧪 測試場景：模擬 GUI 渲染中的高頻 ensure_loaded() 調用")
    print("=" * 80)
    print()
    
    # 測試 1: 首次調用（會發起 API 請求）
    print("📌 測試 1: 首次調用 ensure_loaded()")
    start = time.time()
    color_palette_provider.ensure_loaded(year=2025)
    elapsed = time.time() - start
    print(f"   ⏱️  耗時: {elapsed:.3f} 秒")
    print()
    
    # 測試 2: 連續調用 1000 次（模擬 paintEvent 中的調用）
    print("📌 測試 2: 連續調用 1000 次（模擬渲染路徑）")
    start = time.time()
    for i in range(1000):
        color_palette_provider.ensure_loaded(year=2025)
    elapsed = time.time() - start
    print(f"   ⏱️  總耗時: {elapsed:.3f} 秒")
    print(f"   ⏱️  平均每次: {elapsed/1000*1000:.3f} 毫秒")
    print()
    
    # 測試 3: 獲取車手顏色
    print("📌 測試 3: 獲取車手顏色")
    test_drivers = ["VER", "LEC", "HAM", "NOR", "PIA"]
    for driver_code in test_drivers:
        color = color_palette_provider.get_driver_color(driver_code, format="hex")
        print(f"   🎨 {driver_code}: {color}")
    print()
    
    # 顯示統計資訊
    print("=" * 80)
    print("📊 統計資訊")
    print("=" * 80)
    print(f"總調用次數: {color_palette_provider._ensure_loaded_call_count}")
    print(f"緩存命中: {color_palette_provider._cache_hit_count}")
    if color_palette_provider._ensure_loaded_call_count > 0:
        hit_rate = (color_palette_provider._cache_hit_count / 
                   color_palette_provider._ensure_loaded_call_count * 100)
        print(f"緩存命中率: {hit_rate:.1f}%")
    print()
    
    # 結論
    if elapsed < 0.1:
        print("✅ 性能測試通過：1000 次調用耗時 < 100ms")
    else:
        print(f"⚠️  性能警告：1000 次調用耗時 {elapsed*1000:.0f}ms（應 < 100ms）")
    print()

if __name__ == "__main__":
    test_high_frequency_calls()
