#!/usr/bin/env python3
"""
簡單的 emoji 替換腳本，修正 Windows cp950 編碼問題
"""

import re
import os

# 需要修復的文件列表
files_to_fix = [
    'f1_analysis_modular_main.py',
    'modules/rain_intensity_analyzer_json.py',
    'modules/annual_dnf_statistics_new.py',
    'modules/corner_detailed_analysis.py',
    'modules/rain_intensity_analyzer_json_fixed.py',
    'modules/compatible_data_loader.py',
    'f1t_gui_main.py',
    'modules/gui/rain_analysis_module.py',
    'test_rain_json.py',
    'test_json_save.py',
    'test_universal_chart.py',
    'f1t_gui_main_clean.py',
    'tests/test_f1t_gui_main.py',
    'modules/function_mapper.py',
    'modules/track_position_analysis.py',
    'modules/track_analysis/track_data_loader.py',
    'modules/track_analysis/track_module.py',
    'modules/track_analysis/track_module_adapter.py'
]

# 定義替換規則
replacements = {
    '✅': '[OK]',
    '❌': '[ERROR]',
    '⚠️': '[WARNING]', 
    '🌧️': '[RAIN]',
    '🚀': '[START]',
    '📊': '[DATA]',
    '💾': '[SAVE]',
    '🔄': '[PROCESS]',
    '📋': '[INFO]',
    '🔍': '[CHECK]',
    '🏎️': '[F1]',
    '🛣️': '[TRACK]',
    '⛽': '[PIT]',
    '🚨': '[ALERT]',
    '🔧': '[TOOL]',
    '📈': '[CHART]',
    '📉': '[TREND]',
    '🔑': '[KEY]',
    '🏷️': '[LABEL]',
    '📂': '[FOLDER]',
    '📁': '[FILES]',
    '🐍': '[PYTHON]',
    '📍': '[PIN]',
    '⏩': '[FORWARD]',
    '⏮️': '[BACKWARD]',
    '🎯': '[TARGET]',
    '💪': '[STRONG]',
    '🔥': '[HOT]',
    '⭐': '[STAR]',
    '🎪': '[EVENT]',
    '🏁': '[FINISH]',
    '🎮': '[CONTROL]',
    '📱': '[MOBILE]',
    '💻': '[COMPUTER]',
    '⚡': '[FAST]',
    '🌟': '[STAR]',
    '🔐': '[SECURE]',
    '🎨': '[DESIGN]',
    '🔬': '[ANALYSIS]',
    '📝': '[NOTE]',
    '⏰': '[TIME]',
    '🎛️': '[CONTROL]',
    '📺': '[DISPLAY]',
    '🌐': '[NETWORK]',
    '🔌': '[PLUGIN]',
    '⚙️': '[SETTINGS]',
    '📦': '[PACKAGE]',
    '🧩': '[COMPONENT]',
    '🛑': '[STOP]',
    '🔒': '[LOCK]',
    '🔗': '[LINK]',
    '🔚': '[END]',
    '🟢': '[GREEN]',
    '📤': '[UPLOAD]',
    '📢': '[ANNOUNCE]',
    '�': '[TEST]',
    '☀️': '[SUN]',
    '⛅': '[CLOUD]',
    '☁️': '[CLOUDY]',
    '🌤️': '[PARTLY_CLOUDY]',
    '⛈️': '[STORM]',
    '🌩️': '[LIGHTNING]',
    '🌨️': '[SNOW]',
    '❄️': '[SNOWFLAKE]',
    '🌦️': '[RAIN_SUN]',
    '🌈': '[RAINBOW]',
    '💨': '[WIND]',
    '💧': '[DROPLET]',
    '🌊': '[WAVE]',
    '➡️': '[ARROW]',
    '📅': '[CALENDAR]',
    '🗂️': '[ARCHIVE]',
    '🌡️': '[TEMP]',
    '⚖️': '[BALANCE]',
    '�️': '[MAP]',
    '⛳': '[FLAG]'
}

# 處理每個文件
for file_path in files_to_fix:
    if os.path.exists(file_path):
        print(f"[PROCESS] 修復文件: {file_path}")
        
        # 讀取檔案
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 執行替換
        emoji_count = 0
        for emoji, replacement in replacements.items():
            old_content = content
            content = content.replace(emoji, replacement)
            if content != old_content:
                emoji_count += content.count(replacement) - old_content.count(replacement)
        
        # 寫回檔案
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[OK] 完成 {file_path}: 修復了 {emoji_count} 個emoji")
    else:
        print(f"[WARNING] 文件不存在: {file_path}")

print("[OK] 所有emoji修復完成！")
