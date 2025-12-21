"""檢查賽事日期和變更類型說明的來源"""
import json

# 讀取 JSON
data = json.load(open('json/fia_parts_analysis_2025.json', 'r', encoding='utf-8'))

print('=' * 80)
print('📊 賽事日期統計')
print('=' * 80)

has_date = 0
no_date = 0

for r in data['records']:
    date = r.get('賽事日期', '')
    if date:
        has_date += 1
    else:
        no_date += 1

print(f'\n總記錄數: {len(data["records"])} 筆')
print(f'有日期: {has_date} 筆 ({has_date/len(data["records"])*100:.1f}%)')
print(f'無日期: {no_date} 筆 ({no_date/len(data["records"])*100:.1f}%)')

# 檢查變更類型說明的來源
print('\n' + '=' * 80)
print('📋 變更類型說明來源')
print('=' * 80)

print('\n前 10 筆記錄檢查:')
for i, r in enumerate(data['records'][:10], 1):
    print(f'\n{i}. 賽事: {r.get("賽事", "")}')
    print(f'   部件: {r.get("部件", "")}')
    print(f'   變更類型: {r.get("變更類型", "")}')
    print(f'   類型說明: {r.get("類型說明", "")}')
    print(f'   分類信心度: {r.get("分類信心度", 0)}')
    print(f'   主分類: {r.get("主分類", "")}')
    print(f'   子分類: {r.get("子分類", "")}')

print('\n' + '=' * 80)
print('❓ 問題分析')
print('=' * 80)
print('\n1. 賽事日期:')
print('   - PDF 中沒有明確標註日期')
print('   - 簡化版解析器沒有從檔名提取日期')
print('   - 解決方案: 從 PDF 檔名或賽曆映射中補充日期')

print('\n2. 類型說明 (類型說明):')
print('   - PDF 中沒有說明更換理由')
print('   - 這是「分類器」根據部件名稱自動生成的說明')
print('   - 來源: fia_parts_classifier.py 的 UpgradeClassifierV2')
print('   - 分類器根據關鍵字匹配，自動推斷變更類型和說明')

print('\n3. 主分類/子分類:')
print('   - 也是分類器自動生成的')
print('   - 15 個主分類 + 61 個子分類')
print('   - 根據部件名稱的關鍵字進行分類')
