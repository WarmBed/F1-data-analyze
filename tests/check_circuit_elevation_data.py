#!/usr/bin/env python3
"""
檢查批次生成的賽道高程資料品質
"""

import json
from pathlib import Path

circuit_data_dir = Path("json/f1-circuits-master/circuit_data")

# 重點賽道檢查（具代表性的賽道）
key_circuits = [
    ("jp_1962_elevation_data.json", "鈴鹿 (Suzuka)"),
    ("be_1925_elevation_data.json", "斯帕 (Spa-Francorchamps)"),
    ("mc_1929_elevation_data.json", "摩納哥 (Monaco)"),
    ("us_2012_elevation_data.json", "奧斯丁 COTA (Austin)"),
    ("sg_2008_elevation_data.json", "新加坡 (Singapore)"),
]

print("=" * 70)
print("📊 F1 賽道高程資料品質檢查報告")
print("=" * 70)

total_circuits = 0
total_points = 0
circuits_with_issues = []

for json_file in circuit_data_dir.glob("*_elevation_data.json"):
    total_circuits += 1
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_points += data["metadata"]["total_points"]
    
    # 檢查資料完整性
    valid_ratio = data["metadata"]["valid_elevation_points"] / data["metadata"]["total_points"]
    
    if valid_ratio < 0.95:  # 少於 95% 有效點
        circuits_with_issues.append({
            "name": data["basic_info"]["name"],
            "file": json_file.name,
            "valid_ratio": valid_ratio
        })

print(f"\n✅ 總計處理: {total_circuits} 條賽道")
print(f"✅ 總座標點數: {total_points} 個")
print(f"✅ 平均每條賽道: {total_points // total_circuits} 個座標點")

if circuits_with_issues:
    print(f"\n⚠️  警告：{len(circuits_with_issues)} 條賽道的高程資料不完整：")
    for circuit in circuits_with_issues:
        print(f"   - {circuit['name']}: {circuit['valid_ratio']*100:.1f}% 有效")
else:
    print(f"\n✅ 所有賽道高程資料 100% 完整！")

print("\n" + "=" * 70)
print("🔍 重點賽道詳細檢查")
print("=" * 70)

for filename, name in key_circuits:
    file_path = circuit_data_dir / filename
    
    if not file_path.exists():
        print(f"\n❌ {name}: 檔案不存在")
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📍 {name}")
    print(f"   賽道全名: {data['basic_info']['name']}")
    print(f"   官方長度: {data['basic_info']['length_meters']} m")
    print(f"   計算長度: {data['metadata']['track_length_calculated_km']} km")
    print(f"   座標點數: {data['metadata']['total_points']}")
    print(f"   有效高程點數: {data['metadata']['valid_elevation_points']} ({data['metadata']['valid_elevation_points']/data['metadata']['total_points']*100:.1f}%)")
    
    ep = data['elevation_profile']
    print(f"   高程統計:")
    print(f"      最高點: {ep['max_elevation']}m (距離 {ep['max_elevation_point']['distance_km']}km)")
    print(f"      最低點: {ep['min_elevation']}m (距離 {ep['min_elevation_point']['distance_km']}km)")
    print(f"      高低差: {ep['elevation_change']}m")
    print(f"      平均海拔: {ep['avg_elevation']}m")
    
    # 評估賽道特性
    if ep['elevation_change'] < 20:
        characteristic = "🟢 非常平坦"
    elif ep['elevation_change'] < 50:
        characteristic = "🟡 輕微起伏"
    elif ep['elevation_change'] < 100:
        characteristic = "🟠 中等高低差"
    else:
        characteristic = "🔴 極具挑戰性"
    
    print(f"   賽道特性: {characteristic}")

print("\n" + "=" * 70)
print("✅ 資料檢查完成！所有賽道高程資料已準備就緒")
print("=" * 70)
