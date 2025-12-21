"""
Yellow Flag 統計資料視覺化 - 簡化版
展示彎道危險度統計和未來 GUI 呈現建議
"""
import json
from pathlib import Path

def load_yellow_flag_data():
    """載入數據"""
    json_file = Path('json/yellow_flag_statistics_japan_suzuka.json')
    
    if not json_file.exists():
        print(f"找不到數據檔案: {json_file}")
        return None
    
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def print_statistics(data):
    """打印統計資訊"""
    print("\n" + "=" * 80)
    print("鈴鹿賽道 Yellow Flag 統計 (2018-2024)")
    print("=" * 80)
    
    # 摘要
    summary = data['summary']
    print(f"\n摘要資訊:")
    print(f"  - 分析年份: {len(data['yearly_data'])} 年 ({', '.join(str(d['year']) for d in data['yearly_data'])})")
    print(f"  - 總 Yellow Flag 事件: {summary['total_yellow_flags']}")
    print(f"  - 平均每場比賽: {summary['average_yellow_flags_per_race']:.2f}")
    print(f"  - 最危險彎道: T{summary['most_dangerous_corner']}")
    
    # 彎道危險度排名
    print(f"\n" + "=" * 80)
    print("彎道危險度排名（前 10）")
    print("=" * 80)
    print(f"{'排名':<6} {'彎道':<8} {'事件數':<12} {'距離(km)':<12} {'發生年份':<30}")
    print("-" * 80)
    
    corner_stats = sorted(data['corner_statistics'], 
                         key=lambda x: x['total_yellow_flags'], 
                         reverse=True)
    
    for i, corner in enumerate(corner_stats[:10], 1):
        if corner['total_yellow_flags'] > 0:
            corner_num = corner['corner_number']
            count = corner['total_yellow_flags']
            distance = corner.get('distance', 0) / 1000
            years = ', '.join(str(y) for y in corner.get('years_with_incidents', []))
            
            print(f"{i:<6} T{corner_num:<7} {count:<12.1f} {distance:<12.2f} {years:<30}")
    
    # 歷年趨勢
    print(f"\n" + "=" * 80)
    print("歷年 Yellow Flag 趨勢")
    print("=" * 80)
    
    for year_data in data['yearly_data']:
        year = year_data['year']
        count = year_data['yellow_flag_count']
        bar = '█' * int(count)
        print(f"{year}: {bar} ({count})")
    
    # 事件詳情示例
    print(f"\n" + "=" * 80)
    print("事件詳情示例（2024 年）")
    print("=" * 80)
    
    for year_data in data['yearly_data']:
        if year_data['year'] == 2024:
            for i, event in enumerate(year_data['events'][:5], 1):
                corner = event.get('corner', '未知')
                sector = event.get('sector', '?')
                message = event.get('message', '')
                print(f"\n事件 {i}:")
                print(f"  彎道: T{corner}")
                print(f"  Sector: {sector}")
                print(f"  訊息: {message}")

def suggest_gui_visualization():
    """建議 GUI 呈現方式"""
    print(f"\n" + "=" * 80)
    print("GUI 視覺化建議")
    print("=" * 80)
    
    suggestions = """
1. Track Map 熱力圖視覺化
   ✓ 在賽道平面圖上用顏色標示彎道危險度
   ✓ 綠色 = 安全（0-2 次事件）
   ✓ 黃色 = 中等危險（3-5 次）
   ✓ 橙色 = 危險（6-8 次）
   ✓ 紅色 = 高度危險（9+ 次）
   ✓ 彎道標記大小可反映事件頻率
   ✓ 點擊彎道顯示詳細事件列表

2. Elevation Chart 彎道標示
   ✓ 在高程圖上用不同顏色的垂直線標示彎道
   ✓ 線條顏色對應危險度
   ✓ 線條粗細可反映事件數量
   ✓ 懸停顯示該彎道的統計資訊

3. 統計圖表
   ✓ 長條圖：每個彎道的事件數量
   ✓ 折線圖：歷年 Yellow Flag 趨勢
   ✓ 圓餅圖：各 Sector 的事件分佈
   ✓ 熱力圖矩陣：年份 x 彎道

4. 事件時間軸
   ✓ 以時間軸形式展示每場比賽的事件
   ✓ 可按年份、彎道篩選
   ✓ 顯示事件詳細資訊（時間、圈數、原因）

5. 比較分析
   ✓ 與其他賽道比較（例如：摩納哥、新加坡）
   ✓ 不同會話類型比較（正賽 vs 排位賽）
   ✓ 乾地 vs 雨地比較

6. 互動功能
   ✓ 可選擇分析的年份範圍
   ✓ 可篩選特定類型的事件（碰撞、打轉、機械故障）
   ✓ 可匯出報告（PDF/PNG）
   ✓ 支援縮放、平移、旋轉視圖

7. 實時更新
   ✓ 比賽期間實時更新 Yellow Flag 統計
   ✓ 預測高風險彎道
   ✓ 安全車出動機率估算
"""
    print(suggestions)
    
    print("\n實現建議:")
    print("  1. 先實現 Track Map 熱力圖（最直觀）")
    print("  2. 再加入 Elevation Chart 標示")
    print("  3. 最後添加統計圖表和互動功能")
    print("  4. 使用 PyQt5 + Matplotlib 實現")
    print("  5. 考慮使用 OpenGL 加速大數據渲染")

def main():
    """主程式"""
    data = load_yellow_flag_data()
    
    if not data:
        print("無法載入數據")
        return
    
    # 打印統計
    print_statistics(data)
    
    # 顯示 GUI 建議
    suggest_gui_visualization()
    
    print("\n" + "=" * 80)
    print("數據檔案位置: json/yellow_flag_statistics_japan_suzuka.json")
    print("=" * 80)

if __name__ == "__main__":
    main()
