#!/usr/bin/env python3
"""
主程式模組替換腳本
將原有的速度/RPM分析圖表組件替換為統一的通用版本
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(file_path):
    """備份原始檔案"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ 備份檔案: {backup_path}")
    return backup_path

def replace_speed_chart_imports(content):
    """替換速度圖表導入"""
    replacements = [
        # 原導入 -> 新導入
        (r'from modules\.speed_analysis_chart_widget import SpeedAnalysisChartWidget',
         'from modules.speed_analysis_chart_widget_refactored import SpeedAnalysisChartWidget'),
    ]
    
    for old_pattern, new_text in replacements:
        content = re.sub(old_pattern, new_text, content)
    
    return content

def replace_rpm_chart_imports(content):
    """替換RPM圖表導入"""
    replacements = [
        # 原導入 -> 新導入
        (r'from modules\.rpm_analysis_chart_widget import RPMAnalysisChartWidget',
         'from modules.rpm_analysis_chart_widget_refactored import RPMAnalysisChartWidget'),
    ]
    
    for old_pattern, new_text in replacements:
        content = re.sub(old_pattern, new_text, content)
    
    return content

def migrate_main_file(main_file_path):
    """遷移主程式檔案"""
    print(f"🔄 開始遷移主程式: {main_file_path}")
    
    # 備份原始檔案
    backup_path = backup_file(main_file_path)
    
    # 讀取檔案內容
    with open(main_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 執行替換
    print("📝 替換速度圖表導入...")
    content = replace_speed_chart_imports(content)
    
    print("📝 替換RPM圖表導入...")
    content = replace_rpm_chart_imports(content)
    
    # 寫回檔案
    with open(main_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 主程式遷移完成: {main_file_path}")
    return backup_path

def verify_migration():
    """驗證遷移結果"""
    main_file = "c:\\Users\\mike2\\OneDrive\\Code\\F1-data-analyze\\f1t_gui_main.py"
    
    print("🔍 驗證遷移結果...")
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查新導入是否存在
    speed_refactored_imports = len(re.findall(r'speed_analysis_chart_widget_refactored', content))
    rpm_refactored_imports = len(re.findall(r'rpm_analysis_chart_widget_refactored', content))
    
    # 檢查舊導入是否還存在
    old_speed_imports = len(re.findall(r'from modules\.speed_analysis_chart_widget import', content))
    old_rpm_imports = len(re.findall(r'from modules\.rpm_analysis_chart_widget import', content))
    
    print(f"📊 新版速度圖表導入: {speed_refactored_imports} 處")
    print(f"📊 新版RPM圖表導入: {rpm_refactored_imports} 處")
    print(f"⚠️  舊版速度圖表導入殘留: {old_speed_imports} 處")
    print(f"⚠️  舊版RPM圖表導入殘留: {old_rpm_imports} 處")
    
    if old_speed_imports == 0 and old_rpm_imports == 0:
        print("✅ 所有導入已成功替換！")
        return True
    else:
        print("❌ 仍有舊版導入需要處理")
        return False

def create_migration_script():
    """創建完整的遷移腳本"""
    main_file = "c:\\Users\\mike2\\OneDrive\\Code\\F1-data-analyze\\f1t_gui_main.py"
    
    print("🚀 開始主程式模組遷移...")
    print("=" * 60)
    
    try:
        # 執行遷移
        backup_path = migrate_main_file(main_file)
        
        # 驗證結果
        success = verify_migration()
        
        if success:
            print("\n🎉 遷移成功完成！")
            print(f"📁 備份檔案: {backup_path}")
            print("🔧 所有圖表組件已升級為統一架構")
        else:
            print("\n⚠️  遷移部分完成，請檢查剩餘問題")
        
        return success
        
    except Exception as e:
        print(f"❌ 遷移過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_migration_script()
