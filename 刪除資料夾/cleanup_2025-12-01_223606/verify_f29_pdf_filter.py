"""驗證 Function 29 是否只處理 Parts and parameters been replaced PDF"""
import json
from collections import Counter

data = json.load(open('json/fia_parts_analysis_2025.json', 'r', encoding='utf-8'))

print('=' * 80)
print('✅ Function 29 - PDF 篩選驗證')
print('=' * 80)

# 統計所有來源文件
source_files = [r.get('來源文件', '') for r in data['records']]
file_counter = Counter(source_files)

print(f'\n📊 總記錄數: {len(data["records"])} 筆')
print(f'📄 來源文件數: {len(file_counter)} 個不同的 PDF')

print(f'\n🔍 檢查是否所有文件都包含 "Parts and parameters been replaced":')
non_matching_files = []
for filename in file_counter.keys():
    if 'parts and parameters been replaced' not in filename.lower():
        non_matching_files.append(filename)

if non_matching_files:
    print(f'\n❌ 發現 {len(non_matching_files)} 個不符合的文件:')
    for f in non_matching_files:
        print(f'  - {f}')
else:
    print(f'\n✅ 所有 {len(file_counter)} 個文件都包含 "Parts and parameters been replaced"')

print(f'\n📋 來源文件列表 (完整):')
for i, (filename, count) in enumerate(sorted(file_counter.items()), 1):
    status = '✅' if 'parts and parameters been replaced' in filename.lower() else '❌'
    # 縮短檔名顯示
    short_name = filename.replace(' - Parts and Parameters been replaced and or changed during Parc Fermé.pdf', '')
    short_name = short_name.replace(' - Parts and parameters been replaced and or changed during Parc Fermé.pdf', '')
    short_name = short_name.replace(' - Parts and Parameters been replaced and or changed during Sprint Parc Fermé.pdf', ' (Sprint)')
    short_name = short_name.replace(' - Parts and parameters been replaced and or changed during the Sprint Parc Fermé.pdf', ' (Sprint)')
    print(f'{status} {i:2d}. {short_name:40s} ({count:3d} 筆)')

print('\n' + '=' * 80)
print('📝 結論:')
if not non_matching_files:
    print('✅ Function 29 現在只處理包含 "Parts and parameters been replaced" 的 PDF')
    print('✅ 簡化版解析器正確過濾了其他類型的 FIA 文件')
else:
    print('⚠️  發現部分文件不符合篩選條件，需要檢查')
