#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復 Brake 模組的 API-ONLY 違規問題
"""

def fix_brake_module():
    file_path = 'modules/gui/lap_analysis/brake_analysis/brake_analysis_mdi.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修復第 917-925 行（Python 索引從 0 開始，所以是 916-924）
    lines[916] = '                    # API-ONLY 模式：不自動創建視窗\n'
    lines[917] = '                    print(f"[brake_MDI] 💡 [API-ONLY] 未找到現有遙測分析視窗")\n'
    lines[918] = '                    print(f"[brake_MDI] 💡 提示：請手動開啟遙測分析模組或通過 API 獲取數據")\n'
    lines[919] = '                    return False\n'
    lines[920] = '            \n'
    lines[921] = '            # 方法2: 透過 API 檢查本地數據（不自動創建）\n'
    lines[922] = '            print(f"[brake_MDI] 🔍 檢查本地遙測分析數據...")\n'
    lines[923] = '            return self._check_and_load_telemetry_if_needed()\n'
    lines[924] = '            \n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print('✅ Brake 模組已修復 (brake_analysis_mdi.py)')
    print('📍 修復位置：第 917-925 行')
    print('🔧 移除：自動創建遙測分析視窗的程式碼')
    print('✨ 改為：僅檢查本地數據，符合 API-ONLY 政策')

if __name__ == '__main__':
    fix_brake_module()
