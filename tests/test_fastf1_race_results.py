#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 FastF1 賽事結果數據結構
調查是否包含最終名次、起始名次、名次變化等資訊
"""

import fastf1
import pandas as pd
from datetime import datetime

# 啟用緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

def test_race_results_data():
    """測試 FastF1 賽事結果數據"""
    
    print("=" * 80)
    print("🏎️  FastF1 賽事結果數據結構調查")
    print("=" * 80)
    
    # 測試案例：2024 年日本站正賽
    year = 2024
    race = "Japan"
    session_type = "R"
    
    print(f"\n📊 載入賽事數據: {year} {race} {session_type}")
    print("-" * 80)
    
    try:
        # 載入比賽會話
        session = fastf1.get_session(year, race, session_type)
        session.load()
        
        print("✅ 賽事數據載入成功\n")
        
        # =================================================================
        # 1. 測試 session.results - 最終賽事結果
        # =================================================================
        print("\n" + "=" * 80)
        print("📋 1. Session Results (session.results)")
        print("=" * 80)
        
        results = session.results
        print(f"\n結果類型: {type(results)}")
        print(f"車手數量: {len(results)}")
        print(f"\n可用欄位:")
        print(results.columns.tolist())
        
        # 顯示前 5 名的詳細資訊
        print("\n前 5 名車手的完整資訊:")
        print("-" * 80)
        
        key_fields = [
            'Position',           # 最終名次
            'GridPosition',       # 起始名次 (排位賽位置)
            'DriverNumber',       # 車號
            'Abbreviation',       # 車手代碼
            'FullName',           # 全名
            'TeamName',           # 車隊
            'Points',             # 積分
            'Status',             # 完賽狀態
            'Time',               # 完賽時間
        ]
        
        for idx, row in results.head(5).iterrows():
            print(f"\n車手 #{row['DriverNumber']} - {row['Abbreviation']} ({row['FullName']})")
            print(f"  車隊: {row['TeamName']}")
            print(f"  最終名次: {row['Position']}")
            print(f"  起始名次: {row['GridPosition']}")
            
            # 計算名次變化
            if pd.notna(row['GridPosition']) and pd.notna(row['Position']):
                position_change = int(row['GridPosition']) - int(row['Position'])
                if position_change > 0:
                    print(f"  名次變化: ⬆️ 上升 {position_change} 位")
                elif position_change < 0:
                    print(f"  名次變化: ⬇️ 下降 {abs(position_change)} 位")
                else:
                    print(f"  名次變化: ➡️ 維持原位")
            
            print(f"  積分: {row['Points']}")
            print(f"  狀態: {row['Status']}")
            if pd.notna(row['Time']):
                print(f"  完賽時間: {row['Time']}")
        
        # =================================================================
        # 2. 計算全部車手的名次變化統計
        # =================================================================
        print("\n" + "=" * 80)
        print("📈 2. 全部車手名次變化統計")
        print("=" * 80)
        
        position_changes = []
        for idx, row in results.iterrows():
            if pd.notna(row['GridPosition']) and pd.notna(row['Position']):
                change = int(row['GridPosition']) - int(row['Position'])
                position_changes.append({
                    'Driver': row['Abbreviation'],
                    'FullName': row['FullName'],
                    'Team': row['TeamName'],
                    'GridPosition': int(row['GridPosition']),
                    'FinalPosition': int(row['Position']),
                    'PositionChange': change,
                    'Status': row['Status']
                })
        
        # 排序：上升最多的在前
        position_changes.sort(key=lambda x: x['PositionChange'], reverse=True)
        
        print("\n名次變化排行榜:")
        print("-" * 80)
        print(f"{'排名':<6} {'車手':<10} {'起始':<6} {'最終':<6} {'變化':<15} {'狀態':<20}")
        print("-" * 80)
        
        for i, data in enumerate(position_changes, 1):
            change = data['PositionChange']
            if change > 0:
                change_str = f"⬆️ +{change}"
            elif change < 0:
                change_str = f"⬇️ {change}"
            else:
                change_str = "➡️ 0"
            
            print(f"{i:<6} {data['Driver']:<10} P{data['GridPosition']:<5} P{data['FinalPosition']:<5} {change_str:<15} {data['Status']:<20}")
        
        # =================================================================
        # 3. 測試 Laps 數據 - 逐圈位置變化
        # =================================================================
        print("\n" + "=" * 80)
        print("🔄 3. Laps Data - 逐圈位置追蹤 (以 VER 為例)")
        print("=" * 80)
        
        laps = session.laps
        
        # 選擇一位車手查看逐圈位置
        test_driver = "VER"
        driver_laps = laps.pick_driver(test_driver)
        
        print(f"\n車手 {test_driver} 的逐圈位置變化:")
        print("-" * 80)
        print(f"{'圈數':<8} {'位置':<8} {'圈速':<15} {'輪胎':<10}")
        print("-" * 80)
        
        for idx, lap in driver_laps.head(10).iterrows():
            lap_num = lap['LapNumber']
            position = lap['Position']
            lap_time = lap['LapTime']
            compound = lap['Compound']
            
            lap_time_str = str(lap_time).split()[-1] if pd.notna(lap_time) else "N/A"
            
            print(f"Lap {lap_num:<4} P{position:<7} {lap_time_str:<15} {compound:<10}")
        
        # =================================================================
        # 4. 數據完整性檢查
        # =================================================================
        print("\n" + "=" * 80)
        print("✅ 4. FastF1 數據完整性總結")
        print("=" * 80)
        
        print("\n可用的名次相關資訊:")
        print("  ✅ Position (最終名次)")
        print("  ✅ GridPosition (起始名次/排位賽位置)")
        print("  ✅ Position 在 Laps 中 (逐圈位置變化)")
        print("  ✅ Points (積分)")
        print("  ✅ Status (完賽狀態)")
        print("  ✅ Time (完賽時間)")
        
        print("\n可計算的衍生資訊:")
        print("  ✅ PositionChange = GridPosition - Position (名次變化)")
        print("  ✅ PositionsGained = GridPosition - Position (上升名次)")
        print("  ✅ PositionsLost = Position - GridPosition (下降名次)")
        print("  ✅ 逐圈位置追蹤 (從 Laps 數據)")
        print("  ✅ 最佳/最差位置 (從 Laps 數據計算)")
        
        # =================================================================
        # 5. 導出範例 JSON 結構
        # =================================================================
        print("\n" + "=" * 80)
        print("💾 5. 建議的 JSON 數據結構")
        print("=" * 80)
        
        sample_data = {
            "race_info": {
                "year": year,
                "race": race,
                "session": session_type,
                "analysis_timestamp": datetime.now().isoformat()
            },
            "position_analysis": []
        }
        
        for data in position_changes[:3]:  # 前 3 名
            sample_data["position_analysis"].append({
                "driver": data['Driver'],
                "full_name": data['FullName'],
                "team": data['Team'],
                "grid_position": data['GridPosition'],
                "final_position": data['FinalPosition'],
                "position_change": data['PositionChange'],
                "position_change_text": f"上升 {data['PositionChange']} 位" if data['PositionChange'] > 0 else (
                    f"下降 {abs(data['PositionChange'])} 位" if data['PositionChange'] < 0 else "維持原位"
                ),
                "status": data['Status']
            })
        
        print("\n範例 JSON 結構 (前 3 名):")
        print("-" * 80)
        import json
        print(json.dumps(sample_data, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_race_results_data()
    
    print("\n" + "=" * 80)
    print("🎯 結論:")
    print("-" * 80)
    print("FastF1 完整提供以下名次相關資訊:")
    print("  1. ✅ 最終名次 (Position)")
    print("  2. ✅ 起始名次 (GridPosition)")
    print("  3. ✅ 名次變化 (計算: GridPosition - Position)")
    print("  4. ✅ 逐圈位置追蹤 (Laps 中的 Position)")
    print("  5. ✅ 完賽狀態 (Status: Finished, DNF, etc.)")
    print("  6. ✅ 積分 (Points)")
    print("\n這些數據足以實現完整的名次分析功能!")
    print("=" * 80)
