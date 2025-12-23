#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量修復所有 GUI 模組的雙層嵌套問題

問題：API 返回 {success, data: {success, data: {metadata, analysis}}}
解決：在 _on_api_success 中檢測並提取內層 data
"""

import os
import re
from pathlib import Path

# 需要修復的檔案列表
FILES_TO_FIX = [
    "modules/gui/telemetry_analysis_mdi.py",
    "modules/gui/rain_analysis/rain_analysis_mdi.py",
    "modules/gui/tire_analysis/tire_analysis_mdi.py",
    "modules/gui/pitstop_analysis/pitstop_analysis_mdi.py",
    "modules/gui/track_analysis/track_analysis_mdi.py",
    "modules/gui/weather_timeline/weather_timeline_mdi.py",
    "modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py",
    "modules/gui/lap_analysis/telemetry_data_loader_base.py",
    "modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py",
    "modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py",
    "modules/gui/accident_analysis/accident_data_manager.py",
]

# 修復邏輯（插入到 raw_data 提取之後）
FIX_CODE = """
            # 🔧 處理雙層嵌套格式：API 返回 {success, data: {success, data: {metadata, analysis}}}
            # 如果 raw_data 是雙層嵌套格式，提取內層 data
            if isinstance(raw_data, dict) and "data" in raw_data and "success" in raw_data:
                raw_data = raw_data["data"]
"""

def fix_file(file_path: str) -> bool:
    """修復單個檔案"""
    if not os.path.exists(file_path):
        print(f"❌ 檔案不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經修復
    if "處理雙層嵌套格式" in content:
        print(f"✅ 已修復（跳過）: {file_path}")
        return True
    
    # 搜索模式：raw_data = payload.get("data") 後面緊接著其他代碼
    pattern = r'(raw_data = payload\.get\("data"\)\n)'
    
    if not re.search(pattern, content):
        print(f"⚠️ 找不到匹配模式: {file_path}")
        return False
    
    # 插入修復代碼
    new_content = re.sub(pattern, r'\1' + FIX_CODE, content, count=1)
    
    if new_content == content:
        print(f"⚠️ 修復失敗（內容未改變）: {file_path}")
        return False
    
    # 寫回檔案
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 修復成功: {file_path}")
    return True

def main():
    print("=" * 60)
    print("開始批量修復 GUI 模組的雙層嵌套問題")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for file_path in FILES_TO_FIX:
        print(f"\n處理: {file_path}")
        if fix_file(file_path):
            success_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 60)
    print(f"修復完成：成功 {success_count} 個，失敗 {fail_count} 個")
    print("=" * 60)

if __name__ == "__main__":
    main()
