#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 Analysis - 全部車手超車視覺化分析模組 (功能 16.3)
All Drivers Overtaking Visualization Analysis Module (Function 16.3)

本模組提供全部車手超車視覺化分析功能，包含：
- [STATS] 超車位置分佈視覺化
- [TARGET] 超車時機分析圖表
- [INFO] 車手超車熱力圖
- JSON格式完整輸出

版本: 1.0
作者: F1 Analysis Team
日期: 2025-08-05
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
from prettytable import PrettyTable


def _make_serializable(obj):
    """將對象轉換為JSON可序列化格式"""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.int64, np.int32, np.float64, np.float32)):
        return float(obj) if 'float' in str(type(obj)) else int(obj)
    elif isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {str(k): _make_serializable(v) for k, v in obj.items()}
    elif pd.api.types.is_scalar(obj) and pd.isna(obj):
        return None
    else:
        return str(obj)


def run_all_drivers_overtaking_visualization_analysis(data_loader, dynamic_team_mapping, f1_analysis_instance):
    """
    執行全部車手超車視覺化分析 (功能 16.3)
    
    Args:
        data_loader: F1數據載入器
        dynamic_team_mapping: 動態車隊映射
        f1_analysis_instance: F1分析實例
    
    Returns:
        bool: 分析是否成功完成
    """
    try:
        print("\n[STATS] 執行全部車手超車視覺化分析...")
        
        # 數據驗證
        if not _validate_data(data_loader):
            return False
        
        # 獲取超車視覺化數據
        visualization_data = _get_overtaking_visualization_data(data_loader, f1_analysis_instance)
        
        if not visualization_data:
            print("[ERROR] 無法獲取超車視覺化數據")
            return False
        
        # 分析超車位置分佈
        position_analysis = _analyze_overtaking_positions(visualization_data)
        _display_position_analysis(position_analysis)
        
        # 分析超車時機
        timing_analysis = _analyze_overtaking_timing(visualization_data)
        _display_timing_analysis(timing_analysis)
        
        # 生成超車熱力圖數據
        heatmap_data = _generate_overtaking_heatmap_data(visualization_data)
        _display_heatmap_summary(heatmap_data)
        
        # 生成JSON輸出
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_output = {
            "analysis_info": {
                "function_id": "16.3",
                "analysis_type": "all_drivers_overtaking_visualization_analysis",
                "timestamp": timestamp,
                "race_info": f"{data_loader.year} {data_loader.race_name}",
                "total_drivers": len(visualization_data)
            },
            "visualization_data": _make_serializable(visualization_data),
            "position_analysis": _make_serializable(position_analysis),
            "timing_analysis": _make_serializable(timing_analysis),
            "heatmap_data": _make_serializable(heatmap_data),
            "chart_recommendations": _generate_chart_recommendations(visualization_data)
        }
        
        # 確保 JSON 輸出目錄存在
        json_dir = "json"
        os.makedirs(json_dir, exist_ok=True)
        
        filename = os.path.join(json_dir, f"all_drivers_overtaking_visualization_analysis_{timestamp}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n[SUCCESS] 全部車手超車視覺化分析完成！JSON輸出已保存到: {filename}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 全部車手超車視覺化分析執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def _validate_data(data_loader):
    """驗證數據完整性"""
    print("[DEBUG] 資料驗證檢查:")
    print("--" * 25)
    
    try:
        if not hasattr(data_loader, 'session') or data_loader.session is None:
            print("[ERROR] 賽段數據未載入")
            return False
        
        print(f"[SUCCESS] 比賽資料: {data_loader.session.event['EventName']} - {data_loader.session.name}")
        print(f"   比賽時間: {data_loader.session.date}")
        
        if hasattr(data_loader, 'laps') and data_loader.laps is not None:
            print(f"[SUCCESS] 圈速資料: {len(data_loader.laps)} 筆記錄")
        
        print("--" * 25)
        return True
        
    except Exception as e:
        print(f"[ERROR] 資料驗證失敗: {e}")
        return False


def _get_overtaking_visualization_data(data_loader, f1_analysis_instance):
    """獲取超車視覺化數據"""
    print("\n[STATS] 收集超車視覺化數據...")
    
    try:
        visualization_data = []
        
        for index, driver_result in data_loader.results.iterrows():
            driver_abbr = driver_result['Abbreviation']
            
            # 安全地獲取車手姓名
            if 'GivenName' in driver_result and 'FamilyName' in driver_result:
                driver_name = f"{driver_result['GivenName']} {driver_result['FamilyName']}"
            elif 'FullName' in driver_result:
                driver_name = driver_result['FullName']
            else:
                driver_name = driver_abbr
                
            team_name = driver_result.get('TeamName', 'Unknown Team')
            
            print(f"   [INFO] 分析車手 {driver_abbr} ({driver_name}) 的超車模式...")
            
            # 收集超車相關數據
            try:
                overtaking_events = _extract_overtaking_events(driver_abbr, data_loader)
                position_changes = _track_position_changes(driver_abbr, data_loader)
                lap_progression = _analyze_lap_progression(driver_abbr, data_loader)
                
                driver_viz_data = {
                    "abbreviation": driver_abbr,
                    "driver_name": driver_name,
                    "team_name": team_name,
                    "car_number": str(driver_result.get('DriverNumber', 'N/A')),
                    "grid_position": int(driver_result.get('GridPosition', 999)) if pd.notna(driver_result.get('GridPosition')) else 999,
                    "finish_position": int(driver_result.get('Position', 999)) if pd.notna(driver_result.get('Position')) else 999,
                    "overtaking_events": overtaking_events,
                    "position_changes": position_changes,
                    "lap_progression": lap_progression,
                    "overtaking_patterns": _identify_overtaking_patterns(overtaking_events),
                    "performance_zones": _identify_performance_zones(lap_progression)
                }
                
                visualization_data.append(driver_viz_data)
                
            except Exception as e:
                print(f"     [WARNING] 分析 {driver_abbr} 視覺化數據時出錯: {e}")
                
                # 添加默認數據
                default_viz_data = {
                    "abbreviation": driver_abbr,
                    "driver_name": driver_name,
                    "team_name": team_name,
                    "car_number": str(driver_result.get('DriverNumber', 'N/A')),
                    "grid_position": int(driver_result.get('GridPosition', 999)) if pd.notna(driver_result.get('GridPosition')) else 999,
                    "finish_position": int(driver_result.get('Position', 999)) if pd.notna(driver_result.get('Position')) else 999,
                    "overtaking_events": [],
                    "position_changes": [],
                    "lap_progression": [],
                    "overtaking_patterns": {},
                    "performance_zones": []
                }
                visualization_data.append(default_viz_data)
        
        print(f"[SUCCESS] 成功收集 {len(visualization_data)} 位車手的視覺化數據")
        return visualization_data
        
    except Exception as e:
        print(f"[ERROR] 獲取超車視覺化數據失敗: {e}")
        return []


def _extract_overtaking_events(driver_abbr, data_loader):
    """提取真實超車事件 - 使用 OpenF1 + FastF1 資料"""
    events = []
    try:
        if hasattr(data_loader, 'f1_analysis_instance') and data_loader.f1_analysis_instance:
            # 使用 F1 分析實例獲取真實超車事件
            overtaking_data = data_loader.f1_analysis_instance.get_overtaking_analysis()
            if overtaking_data and 'overtaking_events' in overtaking_data:
                driver_events = [e for e in overtaking_data['overtaking_events'] 
                               if e.get('driver') == driver_abbr or e.get('target') == driver_abbr]
                return driver_events
        
        # 後備方案：從圈速資料分析位置變化事件
        if hasattr(data_loader, 'laps') and data_loader.laps is not None:
            driver_laps = data_loader.laps[data_loader.laps['Driver'] == driver_abbr]
            if len(driver_laps) > 1:
                for i in range(1, len(driver_laps)):
                    prev_pos = driver_laps.iloc[i-1]['Position'] if pd.notna(driver_laps.iloc[i-1]['Position']) else None
                    curr_pos = driver_laps.iloc[i]['Position'] if pd.notna(driver_laps.iloc[i]['Position']) else None
                    
                    if prev_pos and curr_pos and prev_pos != curr_pos:
                        event = {
                            "lap_number": driver_laps.iloc[i]['LapNumber'],
                            "event_type": "overtake" if curr_pos < prev_pos else "overtaken",
                            "position_before": prev_pos,
                            "position_after": curr_pos,
                            "driver": driver_abbr
                        }
                        events.append(event)
    except Exception as e:
        print(f"[WARNING] 提取 {driver_abbr} 超車事件失敗: {e}")
    
    return events


def _track_position_changes(driver_abbr, data_loader):
    """追蹤真實位置變化 - 使用 FastF1 資料"""
    changes = []
    try:
        if hasattr(data_loader, 'laps') and data_loader.laps is not None:
            driver_laps = data_loader.laps[data_loader.laps['Driver'] == driver_abbr].copy()
            driver_laps = driver_laps.sort_values('LapNumber')
            
            for i in range(1, len(driver_laps)):
                prev_pos = driver_laps.iloc[i-1]['Position'] if pd.notna(driver_laps.iloc[i-1]['Position']) else None
                curr_pos = driver_laps.iloc[i]['Position'] if pd.notna(driver_laps.iloc[i]['Position']) else None
                
                if prev_pos and curr_pos and prev_pos != curr_pos:
                    changes.append({
                        "lap_number": driver_laps.iloc[i]['LapNumber'],
                        "from_position": int(prev_pos),
                        "to_position": int(curr_pos),
                        "change": int(curr_pos) - int(prev_pos)
                    })
    except Exception as e:
        print(f"[WARNING] 追蹤 {driver_abbr} 位置變化失敗: {e}")
    
    return changes


def _analyze_lap_progression(driver_abbr, data_loader):
    """分析真實圈次進程 - 使用 FastF1 資料"""
    progression = []
    try:
        if hasattr(data_loader, 'laps') and data_loader.laps is not None:
            driver_laps = data_loader.laps[data_loader.laps['Driver'] == driver_abbr].copy()
            driver_laps = driver_laps.sort_values('LapNumber')
            
            for _, lap in driver_laps.iterrows():
                lap_data = {
                    "lap_number": lap['LapNumber'],
                    "position": lap['Position'] if pd.notna(lap['Position']) else None,
                    "lap_time": str(lap['LapTime']) if pd.notna(lap['LapTime']) else None,
                    "tire_compound": lap['Compound'] if 'Compound' in lap and pd.notna(lap['Compound']) else None,
                    "sector_1": lap['Sector1Time'] if 'Sector1Time' in lap and pd.notna(lap['Sector1Time']) else None,
                    "sector_2": lap['Sector2Time'] if 'Sector2Time' in lap and pd.notna(lap['Sector2Time']) else None,
                    "sector_3": lap['Sector3Time'] if 'Sector3Time' in lap and pd.notna(lap['Sector3Time']) else None
                }
                progression.append(lap_data)
    except Exception as e:
        print(f"[WARNING] 分析 {driver_abbr} 圈次進程失敗: {e}")
    
    return progression


def _identify_overtaking_patterns(overtaking_events):
    """識別超車模式"""
    if not overtaking_events:
        return {}
    
    patterns = {
        "early_race_activity": len([e for e in overtaking_events if e['lap_number'] <= 10]),
        "mid_race_activity": len([e for e in overtaking_events if 10 < e['lap_number'] <= 40]),
        "late_race_activity": len([e for e in overtaking_events if e['lap_number'] > 40]),
        "aggressive_laps": [],
        "defensive_success_rate": 0.0,
        "preferred_sectors": {}
    }
    
    # 計算首選超車區域 - 使用真實資料分析
    sector_counts = {}
    for event in overtaking_events:
        # 根據圈數推估賽道區域 (真實 OpenF1 資料沒有具體 sector 資訊)
        lap_number = event.get('lap_number', 1)
        if lap_number <= 20:
            sector = "early_race"
        elif lap_number <= 40:
            sector = "mid_race" 
        else:
            sector = "late_race"
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
    
    patterns["preferred_sectors"] = sector_counts
    
    return patterns


def _identify_performance_zones(lap_progression):
    """識別表現區域"""
    if not lap_progression:
        return []
    
    zones = []
    
    # 尋找強勢圈段
    for i in range(0, len(lap_progression), 10):
        zone_laps = lap_progression[i:i+10]
        if zone_laps:
            avg_position = sum(lap['position'] for lap in zone_laps) / len(zone_laps)
            zone = {
                "start_lap": zone_laps[0]['lap_number'],
                "end_lap": zone_laps[-1]['lap_number'],
                "avg_position": avg_position,
                "performance_level": "strong" if avg_position <= 8 else "moderate" if avg_position <= 15 else "weak"
            }
            zones.append(zone)
    
    return zones


def _analyze_overtaking_positions(visualization_data):
    """分析超車位置分佈"""
    print("\n[INFO] 分析超車位置分佈...")
    
    position_stats = {}
    
    for driver_data in visualization_data:
        for event in driver_data['overtaking_events']:
            pos = event['position_before']
            if pos not in position_stats:
                position_stats[pos] = {"overtakes": 0, "overtaken": 0}
            
            if event['event_type'] == "overtake":
                position_stats[pos]["overtakes"] += 1
            else:
                position_stats[pos]["overtaken"] += 1
    
    # 轉換為分析結果
    position_analysis = []
    for pos, stats in sorted(position_stats.items()):
        total_activity = stats["overtakes"] + stats["overtaken"]
        activity_rate = (stats["overtakes"] / total_activity * 100) if total_activity > 0 else 0
        
        position_analysis.append({
            "position": pos,
            "overtakes_made": stats["overtakes"],
            "overtaken_count": stats["overtaken"],
            "total_activity": total_activity,
            "activity_rate": activity_rate
        })
    
    return position_analysis


def _display_position_analysis(position_analysis):
    """顯示位置分析"""
    print("\n[INFO] 超車位置分佈分析")
    print("   • 活躍度: 該位置發生的總超車行為次數")
    print("   • 主動率: 在該位置主動超車的比例")
    
    if not position_analysis:
        print("   暫無超車位置數據")
        return
    
    table = PrettyTable()
    table.field_names = ["位置", "主動超車", "被超車", "總活躍度", "主動率"]
    table.align = "l"
    
    for data in sorted(position_analysis, key=lambda x: x['total_activity'], reverse=True)[:10]:
        table.add_row([
            data['position'],
            data['overtakes_made'],
            data['overtaken_count'],
            data['total_activity'],
            f"{data['activity_rate']:.1f}%"
        ])
    
    print(table)


def _analyze_overtaking_timing(visualization_data):
    """分析超車時機"""
    print("\n⏱️ 分析超車時機分佈...")
    
    timing_stats = {
        "early_race": 0,  # 1-10圈
        "mid_race": 0,    # 11-40圈
        "late_race": 0    # 41+圈
    }
    
    for driver_data in visualization_data:
        for event in driver_data['overtaking_events']:
            lap = event['lap_number']
            if lap <= 10:
                timing_stats["early_race"] += 1
            elif lap <= 40:
                timing_stats["mid_race"] += 1
            else:
                timing_stats["late_race"] += 1
    
    total_events = sum(timing_stats.values())
    
    timing_analysis = {
        "early_race": {
            "count": timing_stats["early_race"],
            "percentage": (timing_stats["early_race"] / total_events * 100) if total_events > 0 else 0
        },
        "mid_race": {
            "count": timing_stats["mid_race"],
            "percentage": (timing_stats["mid_race"] / total_events * 100) if total_events > 0 else 0
        },
        "late_race": {
            "count": timing_stats["late_race"],
            "percentage": (timing_stats["late_race"] / total_events * 100) if total_events > 0 else 0
        },
        "total_events": total_events
    }
    
    return timing_analysis


def _display_timing_analysis(timing_analysis):
    """顯示時機分析"""
    print("\n⏱️ 超車時機分佈分析")
    
    table = PrettyTable()
    table.field_names = ["比賽階段", "圈數範圍", "超車次數", "比例"]
    table.align = "l"
    
    table.add_row([
        "比賽初期", "1-10圈", 
        timing_analysis["early_race"]["count"],
        f"{timing_analysis['early_race']['percentage']:.1f}%"
    ])
    table.add_row([
        "比賽中期", "11-40圈",
        timing_analysis["mid_race"]["count"],
        f"{timing_analysis['mid_race']['percentage']:.1f}%"
    ])
    table.add_row([
        "比賽後期", "41+圈",
        timing_analysis["late_race"]["count"], 
        f"{timing_analysis['late_race']['percentage']:.1f}%"
    ])
    
    print(table)
    print(f"\n[INFO] 總超車事件: {timing_analysis['total_events']} 次")


def _generate_overtaking_heatmap_data(visualization_data):
    """生成超車熱力圖數據"""
    print("\n[HOT] 生成超車熱力圖數據...")
    
    # 創建位置-圈數熱力圖矩陣
    heatmap_matrix = np.zeros((20, 53))  # 20個位置 x 53圈
    
    for driver_data in visualization_data:
        for event in driver_data['overtaking_events']:
            lap = event['lap_number'] - 1  # 轉為0索引
            pos_before = event['position_before']
            
            # 確保位置是整數並在有效範圍內
            try:
                pos = int(pos_before) - 1  # 轉為0索引
                lap = int(lap)
                
                if 0 <= lap < 53 and 0 <= pos < 20:
                    heatmap_matrix[pos][lap] += 1
            except (ValueError, TypeError):
                # 跳過無效的位置或圈數數據
                continue
    
    # 找出熱點區域
    hotspots = []
    for pos in range(20):
        for lap in range(53):
            if heatmap_matrix[pos][lap] > 0:
                hotspots.append({
                    "position": pos + 1,
                    "lap": lap + 1,
                    "intensity": int(heatmap_matrix[pos][lap])
                })
    
    # 按強度排序
    hotspots.sort(key=lambda x: x['intensity'], reverse=True)
    
    return {
        "matrix": heatmap_matrix.tolist(),
        "hotspots": hotspots[:20],  # 前20個熱點
        "total_activity": int(heatmap_matrix.sum()),
        "peak_activity": {
            "lap": int(np.argmax(heatmap_matrix.sum(axis=0))) + 1,
            "position": int(np.argmax(heatmap_matrix.sum(axis=1))) + 1
        }
    }


def _display_heatmap_summary(heatmap_data):
    """顯示熱力圖摘要"""
    print("\n[HOT] 超車熱力圖摘要")
    print(f"   • 總活躍度: {heatmap_data['total_activity']} 次超車事件")
    print(f"   • 最活躍圈數: 第 {heatmap_data['peak_activity']['lap']} 圈")
    print(f"   • 最活躍位置: 第 {heatmap_data['peak_activity']['position']} 位")
    
    if heatmap_data['hotspots']:
        print("\n[HOT] 前5個超車熱點:")
        for i, hotspot in enumerate(heatmap_data['hotspots'][:5], 1):
            print(f"   {i}. 第{hotspot['lap']}圈 位置{hotspot['position']} - {hotspot['intensity']}次")


def _generate_chart_recommendations(visualization_data):
    """生成圖表建議"""
    total_drivers = len(visualization_data)
    total_events = sum(len(d['overtaking_events']) for d in visualization_data)
    
    recommendations = {
        "suggested_charts": [
            {
                "type": "line_chart",
                "title": "車手位置變化趨勢圖",
                "description": "顯示每位車手在比賽過程中的位置變化"
            },
            {
                "type": "heatmap",
                "title": "超車活躍度熱力圖",
                "description": "以圈數和位置為軸的超車頻率分佈"
            },
            {
                "type": "bar_chart",
                "title": "車手超車統計柱狀圖",
                "description": "各車手的超車次數和被超次數對比"
            },
            {
                "type": "scatter_plot",
                "title": "超車效率散點圖",
                "description": "位置變化與超車次數的相關性分析"
            }
        ],
        "data_insights": [
            f"本場比賽共有 {total_drivers} 位車手參與",
            f"總計發生 {total_events} 次超車相關事件",
            f"平均每位車手參與 {total_events/total_drivers:.1f} 次超車行為" if total_drivers > 0 else "無超車數據"
        ]
    }
    
    return recommendations
