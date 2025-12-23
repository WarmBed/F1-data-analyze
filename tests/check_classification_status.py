import json

# 檢查完整數據是否已分類
with open('2025_f1_parts_changes_complete.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"📊 總記錄數: {len(data)}")

if data:
    sample = data[0]
    print(f"\n🔍 第一筆記錄鍵值:")
    for key in sample.keys():
        print(f"   - {key}")
    
    has_classification = '變更類型資訊' in sample or '變更類型' in sample
    print(f"\n❓ 是否已執行分類: {'是 ✅' if has_classification else '否 ❌'}")
    
    if has_classification:
        # 統計分類結果
        type_stats = {}
        for item in data:
            if '變更類型資訊' in item:
                change_type = item['變更類型資訊'].get('變更類型', '未知')
            elif '變更類型' in item:
                change_type = item['變更類型']
            else:
                change_type = '未分類'
            
            type_stats[change_type] = type_stats.get(change_type, 0) + 1
        
        print(f"\n📊 分類統計:")
        for change_type, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = count / len(data) * 100
            print(f"   {change_type}: {count} 筆 ({percentage:.1f}%)")
    else:
        print(f"\n⚠️  數據尚未執行分類")
        print(f"💡 建議: 需要運行分類器為所有 {len(data)} 筆記錄添加分類資訊")
