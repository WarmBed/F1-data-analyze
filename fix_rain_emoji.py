#!/usr/bin/env python3
"""
修正 rain_intensity_analyzer_json.py 的 emoji 字符
"""

import re

# 讀取檔案
with open('modules/rain_intensity_analyzer_json.py', 'r', encoding='utf-8') as f:
    content = f.read()

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
    '📊': '[STATS]',
    '📦': '[PACKAGE]',
    '🧩': '[COMPONENT]',
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
    '🌡️': '[TEMP]',
    '🗂️': '[FILES]'
}

# 執行替換
for emoji, replacement in replacements.items():
    content = content.replace(emoji, replacement)

# 寫回檔案
with open('modules/rain_intensity_analyzer_json.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Rain analyzer emoji replacement completed!")
