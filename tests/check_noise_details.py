"""檢查噪音記錄的詳細內容"""
import json

data = json.load(open('json/fia_parts_analysis_2025.json', 'r', encoding='utf-8'))
noise_records = [r for r in data['records'] if '噪音' in r.get('變更類型', '') or 'Noise' in r.get('變更類型', '').upper()]

print(f"噪音記錄: {len(noise_records)} 筆\n")
print("=" * 80)
print("噪音記錄範例（前 15 筆）:")
print("=" * 80)

for i, r in enumerate(noise_records[:15], 1):
    print(f"\n{i}. 賽事: {r.get('賽事', '')}")
    print(f"   車隊: {r.get('車隊', '')}")
    print(f"   部件: {r.get('部件', '')[:70]}")
    print(f"   類型: {r.get('變更類型', '')}")
    print(f"   信心度: {r.get('分類信心度', 0)}")

print("\n" + "=" * 80)
print("問題分析:")
print("=" * 80)
print("這些記錄通過了 _is_noise_line() 過濾（16 個正則表達式規則）")
print("但被分類器標記為 '噪音 (Noise)' 類型（信心度 0.8-0.95）")
print("\n解決方案:")
print("1. ✅ GUI 已添加過濾邏輯: 跳過 '噪音' 或 'Noise' 類型記錄")
print("2. ⚠️  API JSON 生成時應該默認過濾掉噪音記錄 (exclude_noise=True)")
print("3. 💡 可選: 加強 _is_noise_line() 規則，或改進分類器")
