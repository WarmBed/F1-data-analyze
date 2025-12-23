"""
測試更新後的 F125 Ollama 分析（包含車隊與圈速資訊）
"""

from batch_generator_gui import analyze_f125_with_ollama

print('[TEST] Testing Updated F125 Ollama Analysis')
print('='*80)

# 測試參數
YEAR = 2025
RACE = "Abu Dhabi"
SESSION = "FP2"

# JSON 檔案路徑
json_path = f"json/vehicle_performance_analysis_{YEAR}_{RACE}_{SESSION}.json"

print(f'\n[INFO] Running Ollama AI analysis...')
print(f'JSON Path: {json_path}')
print(f'\nThis may take 1-3 minutes, please wait...\n')

md_path = analyze_f125_with_ollama(
    json_path=json_path,
    year=YEAR,
    race=RACE,
    session=SESSION
)

if md_path:
    print('\n' + '='*80)
    print('[SUCCESS] AI Analysis Complete!')
    print(f'Markdown Report: {md_path}')
    print('='*80)

    # 顯示關鍵部分
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 檢查是否包含新的分析內容
    if '圈速表現 Top 5' in content:
        print('\n[OK] Contains laptime Top 5 data')
    if '圈速表現 Bottom 5' in content:
        print('[OK] Contains laptime Bottom 5 data')
    if 'McLaren' in content or 'Ferrari' in content or 'Mercedes' in content:
        print('[OK] Contains team information')

    print(f'\n[INFO] Total length: {len(content)} characters')

else:
    print('\n[FAILED] AI Analysis Failed')
