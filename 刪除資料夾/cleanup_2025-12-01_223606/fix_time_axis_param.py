#!/usr/bin/env python3
"""
臨時腳本：修復 distancediff_analysis_mdi.py 中所有缺少 use_time_axis 參數的 data_manager.load_distancediff_data() 調用
"""

import re

# 讀取檔案
filepath = r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\modules\gui\lap_analysis\distancediff_analysis\distancediff_analysis_mdi.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 定義正則表達式模式，匹配沒有 use_time_axis 的 load_distancediff_data 調用
# 匹配模式：
# - self.data_manager.load_distancediff_data(
# - 後面有多行參數
# - 最後一行是 lap2=xxx
# - 緊接著是 )
pattern = re.compile(
    r'''(self\.data_manager\.load_distancediff_data\(
        \s+year=self\.current_year,
        \s+race=self\.current_race,
        \s+session=self\.current_session,
        \s+driver1=self\.driver1,
        \s+driver2=self\.driver2,
        \s+lap1=self\.lap1,
        \s+lap2=self\.lap2)
        (\s*\))''',
    re.VERBOSE | re.MULTILINE
)

# 替換函數
def replace_func(match):
    return match.group(1) + ',\n                        use_time_axis=use_time_axis  # ✅ 新增時間軸參數\n' + '                    )'

# 執行替換
new_content = pattern.sub(replace_func, content)

# 寫回檔案
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ 修復完成！")
print(f"檔案路徑: {filepath}")
