"""
測試 F126 AI 分析功能（獨立於 F125）
"""

from batch_generator_gui import analyze_f125_with_ollama

print('[TEST] F126 AI Analysis (Independent)')
print('='*80)

# 測試參數
YEAR = 2025
RACE = "Abu Dhabi"
SESSION = "FP2"
MODEL = "qwen3:30b"  # 使用更強大的模型

# JSON 檔案路徑
json_path = f"json/vehicle_performance_analysis_{YEAR}_{RACE}_{SESSION}.json"

print(f'\n[INFO] 測試 F126 功能: AI 深度分析')
print(f'JSON Path: {json_path}')
print(f'AI Model: {MODEL}')
print(f'\nThis may take 2-5 minutes, please wait...\n')

# 調用 AI 分析（這就是 F126 的核心功能）
md_path = analyze_f125_with_ollama(
    json_path=json_path,
    year=YEAR,
    race=RACE,
    session=SESSION,
    model_name=MODEL
)

if md_path:
    print('\n' + '='*80)
    print('[SUCCESS] F126 AI Analysis Complete!')
    print(f'Markdown Report: {md_path}')
    print('='*80)

    # 檢查報告內容
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 驗證關鍵內容
    checks = {
        '車隊名稱': any(team in content for team in ['McLaren', 'Ferrari', 'Mercedes', 'Red Bull']),
        '圈速分析': '圈速與車隊表現分析' in content or 'Top 5' in content,
        'AI 模型標註': MODEL in content,
    }

    print('\n[驗證] AI 分析報告品質:')
    for check_name, passed in checks.items():
        status = '✓' if passed else '✗'
        print(f'  {status} {check_name}')

    print(f'\n[INFO] 報告總長度: {len(content)} 字元')

else:
    print('\n[FAILED] F126 AI Analysis Failed')
