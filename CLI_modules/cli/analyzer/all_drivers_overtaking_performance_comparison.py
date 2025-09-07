#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 Analysis - 全部車手超車表現對比模組 (功能 16.2)
All Drivers Overtaking Performance Comparison Module (Function 16.2)

本模組提供全部車手超車表現對比功能，包含：
- 🆚 車手間超車表現對比
- [INFO] 車隊超車效率分析
- [FINISH] 賽道超車難易度評估
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
        return {key: _make_serializable(value) for key, value in obj.items()}
    else:
        try:
            # 安全檢查是否為標量值，避免在陣列上使用 pd.isna
            if hasattr(pd, 'isna') and not hasattr(obj, '__len__'):
                if pd.isna(obj):
                    return None
        except (ValueError, TypeError):
            pass
        return str(obj)


def run_all_drivers_overtaking_performance_comparison(data_loader, dynamic_team_mapping, f1_analysis_instance):
    """
    執行全部車手超車表現對比分析 (功能 16.2)
    
    Args:
        data_loader: F1數據載入器
        dynamic_team_mapping: 動態車隊映射
        f1_analysis_instance: F1分析實例
    
    Returns:
        bool: 分析是否成功完成
    """
    try:
        print("\n🆚 執行全部車手超車表現對比分析...")
        
        # 數據驗證
        if not _validate_data(data_loader):
            return False
        
        # 獲取超車表現對比數據
        performance_comparison = _get_overtaking_performance_comparison(data_loader, f1_analysis_instance)
        
        if not performance_comparison:
            print("[ERROR] 無法獲取超車表現對比數據")
            return False
        
        # 顯示對比分析表格
        _display_performance_comparison_table(performance_comparison)
        
        # 顯示車隊分析
        team_analysis = _analyze_team_performance(performance_comparison)
        _display_team_analysis_table(team_analysis)
        
        # 生成JSON輸出
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_output = {
            "analysis_info": {
                "function_id": "16.2",
                "analysis_type": "all_drivers_overtaking_performance_comparison",
                "timestamp": timestamp,
                "race_info": f"{data_loader.year} {data_loader.race_name}",
                "total_drivers": len(performance_comparison)
            },
            "performance_comparison": _make_serializable(performance_comparison),
            "team_analysis": _make_serializable(team_analysis),
            "track_difficulty": _analyze_track_difficulty(performance_comparison)
        }
        
        # 確保 JSON 輸出目錄存在
        json_dir = "json"
        os.makedirs(json_dir, exist_ok=True)
        
        filename = os.path.join(json_dir, f"all_drivers_overtaking_performance_comparison_{timestamp}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n[SUCCESS] 全部車手超車表現對比分析完成！JSON輸出已保存到: {filename}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 全部車手超車表現對比分析執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def _validate_data(data_loader):
    """驗證數據完整性"""
    print("[DEBUG] 資料驗證檢查:")
    print("--" * 25)
    
    try:
        # 檢查基本數據
        if not hasattr(data_loader, 'session') or data_loader.session is None:
            print("[ERROR] 賽段數據未載入")
            return False
        
        print(f"[SUCCESS] 比賽資料: {data_loader.session.event['EventName']} - {data_loader.session.name}")
        print(f"   比賽時間: {data_loader.session.date}")
        
        if hasattr(data_loader, 'results') and data_loader.results is not None:
            print(f"[SUCCESS] 車手資訊: {len(data_loader.results)} 位車手")
        
        print("--" * 25)
        return True
        
    except Exception as e:
        print(f"[ERROR] 資料驗證失敗: {e}")
        return False


def _get_overtaking_performance_comparison(data_loader, f1_analysis_instance):
    """獲取超車表現對比數據"""
    print("\n🆚 分析車手超車表現對比...")
    
    try:
        performance_data = []
        
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
            
            print(f"   [INFO] 分析車手 {driver_abbr} ({driver_name}) 的表現指標...")
            
            # 計算表現指標
            try:
                # 基本超車數據
                overtakes_made = _calculate_overtakes_made(driver_abbr, data_loader)
                overtaken_by = _calculate_overtaken_by(driver_abbr, data_loader)
                
                # 計算表現指標
                position_gained = _calculate_position_gain(driver_result)
                lap_consistency = _calculate_lap_consistency(driver_abbr, data_loader)
                aggressive_index = _calculate_aggressive_index(overtakes_made, overtaken_by)
                defensive_rating = _calculate_defensive_rating(overtaken_by, overtakes_made)
                
                performance_metrics = {
                    "abbreviation": driver_abbr,
                    "driver_name": driver_name,
                    "team_name": team_name,
                    "car_number": str(driver_result.get('DriverNumber', 'N/A')),
                    "grid_position": int(driver_result.get('GridPosition', 999)) if pd.notna(driver_result.get('GridPosition')) else 999,
                    "finish_position": int(driver_result.get('Position', 999)) if pd.notna(driver_result.get('Position')) else 999,
                    "position_gained": position_gained,
                    "overtakes_made": overtakes_made,
                    "overtaken_by": overtaken_by,
                    "net_overtaking": overtakes_made - overtaken_by,
                    "aggressive_index": aggressive_index,
                    "defensive_rating": defensive_rating,
                    "lap_consistency": lap_consistency,
                    "overall_performance_score": 0.0
                }
                
                # 計算綜合表現分數
                performance_metrics["overall_performance_score"] = _calculate_overall_score(performance_metrics)
                
                performance_data.append(performance_metrics)
                
            except Exception as e:
                print(f"     [WARNING] 計算 {driver_abbr} 表現指標時出錯: {e}")
                
                # 添加默認數據
                default_metrics = {
                    "abbreviation": driver_abbr,
                    "driver_name": driver_name,
                    "team_name": team_name,
                    "car_number": str(driver_result.get('DriverNumber', 'N/A')),
                    "grid_position": int(driver_result.get('GridPosition', 999)) if pd.notna(driver_result.get('GridPosition')) else 999,
                    "finish_position": int(driver_result.get('Position', 999)) if pd.notna(driver_result.get('Position')) else 999,
                    "position_gained": 0,
                    "overtakes_made": 0,
                    "overtaken_by": 0,
                    "net_overtaking": 0,
                    "aggressive_index": 0.0,
                    "defensive_rating": 0.0,
                    "lap_consistency": 0.0,
                    "overall_performance_score": 0.0
                }
                performance_data.append(default_metrics)
        
        print(f"[SUCCESS] 成功分析 {len(performance_data)} 位車手的表現對比")
        return performance_data
        
    except Exception as e:
        print(f"[ERROR] 獲取超車表現對比數據失敗: {e}")
        return []


def _calculate_overtakes_made(driver_abbr, data_loader):
    """計算車手完成的超車次數 - 使用真實 OpenF1 + FastF1 資料"""
    try:
        if hasattr(data_loader, 'f1_analysis_instance') and data_loader.f1_analysis_instance:
            # 使用 F1 分析實例獲取真實超車資料
            overtaking_data = data_loader.f1_analysis_instance.get_overtaking_analysis()
            if overtaking_data and 'drivers_overtaking' in overtaking_data:
                driver_stats = overtaking_data['drivers_overtaking'].get(driver_abbr, {})
                return driver_stats.get('overtakes_made', 0)
        
        # 後備方案：從位置變化分析超車
        if hasattr(data_loader, 'laps') and data_loader.laps is not None:
            driver_laps = data_loader.laps[data_loader.laps['Driver'] == driver_abbr]
            if len(driver_laps) > 1:
                position_changes = driver_laps['Position'].diff().fillna(0)
                # 負數表示位置前進（超車）
                overtakes = len(position_changes[position_changes < 0])
                return overtakes
        
        return 0
    except Exception as e:
        print(f"[WARNING] 計算 {driver_abbr} 超車次數失敗: {e}")
        return 0


def _calculate_overtaken_by(driver_abbr, data_loader):
    """計算車手被超車次數 - 使用真實 OpenF1 + FastF1 資料"""
    try:
        if hasattr(data_loader, 'f1_analysis_instance') and data_loader.f1_analysis_instance:
            # 使用 F1 分析實例獲取真實超車資料
            overtaking_data = data_loader.f1_analysis_instance.get_overtaking_analysis()
            if overtaking_data and 'drivers_overtaking' in overtaking_data:
                driver_stats = overtaking_data['drivers_overtaking'].get(driver_abbr, {})
                return driver_stats.get('overtaken_by', 0)
        
        # 後備方案：從位置變化分析被超車
        if hasattr(data_loader, 'laps') and data_loader.laps is not None:
            driver_laps = data_loader.laps[data_loader.laps['Driver'] == driver_abbr]
            if len(driver_laps) > 1:
                position_changes = driver_laps['Position'].diff().fillna(0)
                # 正數表示位置後退（被超車）
                overtaken = len(position_changes[position_changes > 0])
                return overtaken
        
        return 0
    except Exception as e:
        print(f"[WARNING] 計算 {driver_abbr} 被超車次數失敗: {e}")
        return 0


def _calculate_position_gain(driver_result):
    """計算位置變化"""
    try:
        grid_pos = int(driver_result.get('GridPosition', 999)) if pd.notna(driver_result.get('GridPosition')) else 999
        finish_pos = int(driver_result.get('Position', 999)) if pd.notna(driver_result.get('Position')) else 999
        
        if grid_pos == 999 or finish_pos == 999:
            return 0
        
        return grid_pos - finish_pos  # 正數表示前進，負數表示後退
    except:
        return 0


def _calculate_lap_consistency(driver_abbr, data_loader):
    """計算圈速一致性"""
    try:
        if hasattr(data_loader, 'laps') and data_loader.laps is not None:
            driver_laps = data_loader.laps[data_loader.laps['Driver'] == driver_abbr]
            if len(driver_laps) > 0:
                lap_times = driver_laps['LapTime'].dropna()
                if len(lap_times) > 1:
                    # 計算變異係數 (CV = 標準差/平均值)
                    lap_times_seconds = lap_times.dt.total_seconds()
                    cv = lap_times_seconds.std() / lap_times_seconds.mean()
                    # 轉換為 0-100 的一致性分數（越低越好，所以用 100 - cv*100）
                    return max(0, 100 - cv * 100)
        return 50.0  # 默認中等一致性
    except:
        return 50.0


def _calculate_aggressive_index(overtakes_made, overtaken_by):
    """計算積極性指數"""
    total_actions = overtakes_made + overtaken_by
    if total_actions == 0:
        return 0.0
    return (overtakes_made / total_actions) * 100


def _calculate_defensive_rating(overtaken_by, overtakes_made):
    """計算防守評級"""
    total_defensive_opportunities = overtaken_by + overtakes_made
    if total_defensive_opportunities == 0:
        return 100.0
    # 防守成功率 = 未被超車的機會 / 總防守機會
    return max(0, 100 - (overtaken_by / total_defensive_opportunities) * 100)


def _calculate_overall_score(metrics):
    """計算綜合表現分數"""
    # 加權計算綜合分數
    position_score = max(0, metrics['position_gained'] * 10)  # 位置變化權重
    net_overtaking_score = metrics['net_overtaking'] * 5  # 淨超車權重
    aggressive_score = metrics['aggressive_index'] * 0.3  # 積極性權重
    defensive_score = metrics['defensive_rating'] * 0.2  # 防守權重
    consistency_score = metrics['lap_consistency'] * 0.1  # 一致性權重
    
    return position_score + net_overtaking_score + aggressive_score + defensive_score + consistency_score


def _display_performance_comparison_table(performance_data):
    """顯示超車表現對比表格"""
    print("\n🆚 全部車手超車表現對比")
    print("[INFO] 數據說明:")
    print("   • 位置變化: 發車位置 - 完賽位置 (正數=前進)")
    print("   • 積極指數: 主動超車在總超車行為中的比例")
    print("   • 防守評級: 成功防守被超車的能力評分")
    print("   • 綜合分數: 考慮所有因素的整體表現評分")
    
    # 按綜合分數排序
    sorted_data = sorted(performance_data, key=lambda x: x['overall_performance_score'], reverse=True)
    
    table = PrettyTable()
    table.field_names = ["排名", "車手", "車隊", "位置變化", "淨超車", "積極指數", "防守評級", "綜合分數"]
    table.align = "l"
    
    for rank, data in enumerate(sorted_data, 1):
        table.add_row([
            rank,
            data['driver_name'],
            data['team_name'],
            f"{data['position_gained']:+d}",
            f"{data['net_overtaking']:+d}",
            f"{data['aggressive_index']:.1f}%",
            f"{data['defensive_rating']:.1f}",
            f"{data['overall_performance_score']:.1f}"
        ])
    
    print(table)


def _analyze_team_performance(performance_data):
    """分析車隊表現"""
    print("\n[FINISH] 分析車隊超車表現...")
    
    team_stats = {}
    
    for driver_data in performance_data:
        team = driver_data['team_name']
        
        if team not in team_stats:
            team_stats[team] = {
                "team_name": team,
                "drivers": [],
                "total_overtakes": 0,
                "total_overtaken": 0,
                "total_position_gained": 0,
                "avg_aggressive_index": 0.0,
                "avg_defensive_rating": 0.0,
                "team_performance_score": 0.0
            }
        
        team_stats[team]['drivers'].append(driver_data['driver_name'])
        team_stats[team]['total_overtakes'] += driver_data['overtakes_made']
        team_stats[team]['total_overtaken'] += driver_data['overtaken_by']
        team_stats[team]['total_position_gained'] += driver_data['position_gained']
    
    # 計算平均值
    for team, stats in team_stats.items():
        driver_count = len(stats['drivers'])
        if driver_count > 0:
            team_drivers = [d for d in performance_data if d['team_name'] == team]
            stats['avg_aggressive_index'] = sum(d['aggressive_index'] for d in team_drivers) / driver_count
            stats['avg_defensive_rating'] = sum(d['defensive_rating'] for d in team_drivers) / driver_count
            stats['team_performance_score'] = sum(d['overall_performance_score'] for d in team_drivers) / driver_count
    
    return list(team_stats.values())


def _display_team_analysis_table(team_analysis):
    """顯示車隊分析表格"""
    print("\n[FINISH] 車隊超車表現分析")
    
    # 按車隊表現分數排序
    sorted_teams = sorted(team_analysis, key=lambda x: x['team_performance_score'], reverse=True)
    
    table = PrettyTable()
    table.field_names = ["排名", "車隊", "車手數", "總超車", "總被超", "位置變化", "平均積極性", "平均防守", "車隊分數"]
    table.align = "l"
    
    for rank, team in enumerate(sorted_teams, 1):
        table.add_row([
            rank,
            team['team_name'],
            len(team['drivers']),
            team['total_overtakes'],
            team['total_overtaken'],
            f"{team['total_position_gained']:+d}",
            f"{team['avg_aggressive_index']:.1f}%",
            f"{team['avg_defensive_rating']:.1f}",
            f"{team['team_performance_score']:.1f}"
        ])
    
    print(table)


def _analyze_track_difficulty(performance_data):
    """分析賽道超車難易度"""
    total_overtaking_actions = sum(d['overtakes_made'] + d['overtaken_by'] for d in performance_data)
    total_drivers = len(performance_data)
    
    if total_drivers == 0:
        return {"difficulty_level": "未知", "overtaking_frequency": 0}
    
    avg_actions_per_driver = total_overtaking_actions / total_drivers
    
    # 根據平均超車行為判定難易度
    if avg_actions_per_driver < 2:
        difficulty = "極困難"
    elif avg_actions_per_driver < 4:
        difficulty = "困難"
    elif avg_actions_per_driver < 6:
        difficulty = "中等"
    elif avg_actions_per_driver < 8:
        difficulty = "容易"
    else:
        difficulty = "非常容易"
    
    return {
        "difficulty_level": difficulty,
        "overtaking_frequency": round(avg_actions_per_driver, 2),
        "total_actions": total_overtaking_actions,
        "analysis": f"平均每位車手參與 {avg_actions_per_driver:.1f} 次超車行為，賽道超車難度評級為：{difficulty}"
    }
