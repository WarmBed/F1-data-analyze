#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 單一車手超車分析模組 (功能16)
Single Driver Overtaking Analysis Module (Function 16)

本模組提供單一車手超車分析功能，包含：
- 車手超車表現統計
- 超車時機和位置分析
- 超車成功率分析
- 超車趨勢分析
- JSON格式完整輸出
- 符合 copilot-instructions 開發核心要求

版本: 1.0
作者: F1 Analysis Team
日期: 2025-08-09
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import pickle
import json
import hashlib
from datetime import datetime
from prettytable import PrettyTable
import pandas as pd
import numpy as np


def check_cache(cache_key):
    """檢查緩存是否存在"""
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{cache_key}.pkl")
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"[WARNING] 緩存載入失敗: {e}")
            return None
    return None


def save_cache(data, cache_key):
    """保存數據到緩存"""
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{cache_key}.pkl")
    
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        print(f"[WARNING] 緩存保存失敗: {e}")


def generate_cache_key(session_info, driver):
    """生成緩存鍵值"""
    params = {
        'function': 'single_driver_overtaking',
        'year': session_info.get('year'),
        'race': session_info.get('event_name'),
        'session': session_info.get('session_type'),
        'driver': driver
    }
    return f"single_driver_overtaking_{hashlib.md5(str(params).encode()).hexdigest()}"


def format_time(time_obj):
    """標準時間格式化函數 - 符合 copilot-instructions 時間格式要求"""
    if pd.isna(time_obj):
        return "N/A"
    
    if hasattr(time_obj, 'total_seconds'):
        total_seconds = time_obj.total_seconds()
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:06.3f}"
    elif isinstance(time_obj, str):
        # 如果已經是字符串，檢查是否包含 "days"
        if "days" in time_obj or "day" in time_obj:
            # 解析並重新格式化
            try:
                import re
import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

                time_match = re.search(r'(\d+):(\d+):(\d+)\.(\d+)', time_obj)
                if time_match:
                    hours, minutes, seconds, milliseconds = time_match.groups()
                    total_minutes = int(hours) * 60 + int(minutes)
                    return f"{total_minutes}:{seconds}.{milliseconds[:3]}"
            except:
                pass
        return time_obj
    else:
        return str(time_obj)


def report_analysis_results(data, analysis_type="analysis"):
    """報告分析結果狀態 - 符合開發核心要求"""
    if not data:
        print(f"❌ {analysis_type}失敗：無可用數據")
        return False
    
    overtaking_count = data.get('total_overtakes', 0) if isinstance(data, dict) else 0
    analysis_sections = len(data) if isinstance(data, dict) else 0
    
    print(f"📊 {analysis_type}結果摘要：")
    print(f"   • 超車次數: {overtaking_count}")
    print(f"   • 分析區塊: {analysis_sections}")
    print(f"   • 數據完整性: {'✅ 良好' if overtaking_count > 0 else '❌ 不足'}")
    
    print(f"✅ {analysis_type}分析完成！")
    return True


def run_single_driver_overtaking_analysis(data_loader, f1_analysis_instance=None, 
                                        show_detailed_output=True, driver=None, **kwargs):
    """執行單一車手超車分析 - Function 16 (Function 15 標準)
    
    Args:
        data_loader: 數據載入器
        f1_analysis_instance: F1分析實例
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
        driver: 車手代碼
        **kwargs: 額外參數
    
    Returns:
        dict: 包含成功狀態、數據、緩存狀態和緩存鍵的標準化返回格式
    """
    print("🚀 開始執行單一車手超車分析...")
    print("📋 單一車手超車分析 (功能16)")
    print("=" * 60)
    
    try:
        # 獲取基本賽事資訊
        session_info = get_session_info(data_loader)
        
        # 確定車手
        if not driver:
            driver = kwargs.get('driver') or get_default_driver(data_loader)
        
        if not driver:
            return {
                "success": False,
                "message": "未指定車手，無法執行單一車手分析",
                "function_id": "16"
            }
        
        print(f"🏎️ 分析車手: {driver}")
        
        # 生成緩存鍵值
        cache_key = generate_cache_key(session_info, driver)
        
        # 檢查緩存 - Function 15 標準實現
        cached_data = check_cache(cache_key)
        cache_used = cached_data is not None
        
        if cached_data and not show_detailed_output:
            print("📦 使用緩存數據")
            
            # 結果驗證和反饋
            if not report_analysis_results(cached_data, "單一車手超車分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "16"}
            
            return {
                "success": True,
                "data": cached_data,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "16"
            }
            
        elif cached_data and show_detailed_output:
            print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
            
            # 結果驗證和反饋
            if not report_analysis_results(cached_data, "單一車手超車分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "16"}
                
            # 顯示詳細輸出 - 即使使用緩存
            _display_cached_detailed_output(cached_data, session_info, driver)
            
            return {
                "success": True,
                "data": cached_data,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "16"
            }
        else:
            print("🔄 重新計算 - 開始數據分析...")
            overtaking_analysis = analyze_single_driver_overtaking(data_loader, session_info, driver, f1_analysis_instance)
            
            if not overtaking_analysis:
                print("❌ 單一車手超車分析失敗：無可用數據")
                return {"success": False, "message": "無可用數據", "function_id": "16"}
            
            # 保存緩存
            save_cache(overtaking_analysis, cache_key)
            print("💾 分析結果已緩存")
            
            # 結果驗證和反饋
            if not report_analysis_results(overtaking_analysis, "單一車手超車分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "16"}
            
            # 顯示詳細分析表格
            display_detailed_overtaking_analysis(overtaking_analysis, driver)
            
            # 保存 JSON 結果
            save_json_results(overtaking_analysis, session_info, driver, "single_driver_overtaking_analysis")
            
            return {
                "success": True,
                "data": overtaking_analysis,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "16"
            }
        
    except Exception as e:
        print(f"❌ 單一車手超車分析失敗: {e}")
        return {"success": False, "message": f"分析失敗: {str(e)}", "function_id": "16"}


def get_session_info(data_loader):
    """獲取賽事基本信息"""
    session_info = {}
    if hasattr(data_loader, 'session') and data_loader.session is not None:
        session_info = {
            "event_name": getattr(data_loader.session, 'event', {}).get('EventName', 'Unknown'),
            "circuit_name": getattr(data_loader.session, 'event', {}).get('Location', 'Unknown'),
            "session_type": getattr(data_loader.session, 'session_info', {}).get('Type', 'Unknown'),
            "year": getattr(data_loader.session, 'event', {}).get('year', 2024)
        }
    return session_info


def get_default_driver(data_loader):
    """獲取默認車手（第一位車手）"""
    try:
        data = data_loader.get_loaded_data()
        if data and 'laps' in data:
            laps = data['laps']
            available_drivers = sorted(laps['Driver'].unique())
            return available_drivers[0] if available_drivers else None
    except:
        return None


def analyze_single_driver_overtaking(data_loader, session_info, driver, f1_analysis_instance):
    """分析單一車手超車數據"""
    try:
        # 獲取數據
        data = data_loader.get_loaded_data()
        if not data:
            print("[ERROR] 無法獲取賽事數據")
            return None
        
        laps = data['laps']
        session = data['session']
        
        # 過濾指定車手的數據
        driver_laps = laps[laps['Driver'] == driver].copy()
        
        if driver_laps.empty:
            print(f"[ERROR] 車手 {driver} 沒有圈速數據")
            return None
        
        print(f"🔄 分析 {driver} 的超車表現...")
        
        # 基本統計
        total_laps = len(driver_laps)
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        
        # 位置變化分析（模擬超車檢測）
        overtaking_data = analyze_position_changes(driver_laps, driver)
        
        # 車手超車分析結果
        analysis_result = {
            "driver_info": {
                "driver_code": driver,
                "total_laps": total_laps,
                "valid_laps": len(valid_laps)
            },
            "overtaking_statistics": overtaking_data.get('statistics', {}),
            "position_analysis": overtaking_data.get('position_changes', []),
            "performance_metrics": calculate_performance_metrics(driver_laps, driver),
            "total_overtakes": overtaking_data.get('total_overtakes', 0),
            "overtaking_success_rate": overtaking_data.get('success_rate', 0)
        }
        
        return analysis_result
        
    except Exception as e:
        print(f"[ERROR] 超車分析失敗: {e}")
        return None


def analyze_position_changes(driver_laps, driver):
    """分析位置變化和超車"""
    try:
        # 按圈數排序
        driver_laps_sorted = driver_laps.sort_values('LapNumber')
        
        overtakes_made = 0
        overtakes_received = 0
        position_changes = []
        
        # 分析相鄰圈次的位置變化
        for i in range(1, len(driver_laps_sorted)):
            current_lap = driver_laps_sorted.iloc[i]
            previous_lap = driver_laps_sorted.iloc[i-1]
            
            current_pos = getattr(current_lap, 'Position', None)
            previous_pos = getattr(previous_lap, 'Position', None)
            
            if current_pos and previous_pos:
                pos_change = previous_pos - current_pos  # 正數表示位置提升
                
                if pos_change > 0:  # 位置提升
                    overtakes_made += pos_change
                    position_changes.append({
                        'lap_number': current_lap['LapNumber'],
                        'from_position': previous_pos,
                        'to_position': current_pos,
                        'change': pos_change,
                        'type': 'overtake_made'
                    })
                elif pos_change < 0:  # 位置下降
                    overtakes_received += abs(pos_change)
                    position_changes.append({
                        'lap_number': current_lap['LapNumber'],
                        'from_position': previous_pos,
                        'to_position': current_pos,
                        'change': pos_change,
                        'type': 'overtaken'
                    })
        
        total_overtakes = overtakes_made + overtakes_received
        success_rate = (overtakes_made / total_overtakes * 100) if total_overtakes > 0 else 0
        
        return {
            'statistics': {
                'overtakes_made': overtakes_made,
                'overtakes_received': overtakes_received,
                'net_position_change': overtakes_made - overtakes_received
            },
            'position_changes': position_changes,
            'total_overtakes': total_overtakes,
            'success_rate': success_rate
        }
        
    except Exception as e:
        print(f"[WARNING] 位置變化分析失敗: {e}")
        return {
            'statistics': {'overtakes_made': 0, 'overtakes_received': 0, 'net_position_change': 0},
            'position_changes': [],
            'total_overtakes': 0,
            'success_rate': 0
        }


def calculate_performance_metrics(driver_laps, driver):
    """計算車手表現指標"""
    try:
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        
        if valid_laps.empty:
            return {}
        
        # 計算基本指標
        lap_times = valid_laps['LapTime']
        fastest_lap = lap_times.min()
        average_lap = lap_times.mean()
        
        return {
            'fastest_lap_time': format_time(fastest_lap),
            'average_lap_time': format_time(average_lap),
            'total_valid_laps': len(valid_laps),
            'lap_time_consistency': lap_times.std().total_seconds() if len(lap_times) > 1 else 0
        }
        
    except Exception as e:
        print(f"[WARNING] 表現指標計算失敗: {e}")
        return {}


def display_detailed_overtaking_analysis(analysis_data, driver):
    """顯示詳細超車分析表格"""
    if not analysis_data:
        print("[ERROR] 沒有超車分析數據可顯示")
        return
    
    print(f"\n📋 {driver} 超車分析詳細結果:")
    
    # 基本統計表格
    stats_table = PrettyTable()
    stats_table.field_names = ["統計項目", "數值", "說明"]
    
    driver_info = analysis_data.get('driver_info', {})
    stats = analysis_data.get('overtaking_statistics', {})
    
    stats_table.add_row(["總圈數", driver_info.get('total_laps', 0), "完成的總圈數"])
    stats_table.add_row(["有效圈數", driver_info.get('valid_laps', 0), "有圈速記錄的圈數"])
    stats_table.add_row(["超車次數", stats.get('overtakes_made', 0), "成功超越其他車手"])
    stats_table.add_row(["被超次數", stats.get('overtakes_received', 0), "被其他車手超越"])
    stats_table.add_row(["淨位置變化", stats.get('net_position_change', 0), "正數表示位置提升"])
    stats_table.add_row(["超車成功率", f"{analysis_data.get('overtaking_success_rate', 0):.1f}%", "超車成功的百分比"])
    
    print(stats_table)
    
    # 位置變化詳細記錄
    position_changes = analysis_data.get('position_analysis', [])
    if position_changes:
        print(f"\n📈 位置變化詳細記錄:")
        changes_table = PrettyTable()
        changes_table.field_names = ["圈數", "起始位置", "結束位置", "變化", "類型"]
        
        for change in position_changes[:10]:  # 顯示前10項變化
            change_type = "超車" if change['type'] == 'overtake_made' else "被超"
            change_value = int(change['change'])  # 確保為整數
            changes_table.add_row([
                change['lap_number'],
                change['from_position'],
                change['to_position'],
                f"{change_value:+d}",
                change_type
            ])
        
        print(changes_table)
        
        if len(position_changes) > 10:
            print(f"📝 註: 共 {len(position_changes)} 次位置變化，僅顯示前10次")
    
    # 表現指標
    performance = analysis_data.get('performance_metrics', {})
    if performance:
        print(f"\n🏁 表現指標:")
        perf_table = PrettyTable()
        perf_table.field_names = ["指標", "數值"]
        
        perf_table.add_row(["最快圈速", format_time(performance.get('fastest_lap_time', 'N/A'))])
        perf_table.add_row(["平均圈速", format_time(performance.get('average_lap_time', 'N/A'))])
        perf_table.add_row(["圈速一致性", f"{performance.get('lap_time_consistency', 0):.3f}s"])
        
        print(perf_table)


def save_json_results(analysis_data, session_info, driver, analysis_type):
    """保存 JSON 結果 - 符合開發核心要求"""
    json_dir = "json"
    os.makedirs(json_dir, exist_ok=True)
    
    result_data = {
        "function_id": 16,
        "function_name": "Single Driver Overtaking Analysis",
        "analysis_type": analysis_type,
        "session_info": session_info,
        "driver": driver,
        "timestamp": datetime.now().isoformat(),
        "data": analysis_data
    }
    
    filename = f"{analysis_type}_{driver}_{session_info.get('year')}_{session_info.get('event_name', 'Unknown').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(json_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"💾 JSON結果已保存到: file:///{os.path.abspath(filepath)}")
        print(f"📄 文件名: {filename}")
    except Exception as e:
        print(f"[WARNING] JSON保存失敗: {e}")


def _display_cached_detailed_output(analysis_data, session_info, driver):
    """顯示緩存數據的詳細輸出 - Function 15 標準
    
    Args:
        analysis_data: 超車分析數據
        session_info: 賽事基本信息
        driver: 車手代碼
    """
    print("\n📊 詳細單一車手超車分析 (緩存數據)")
    print("=" * 80)
    
    print(f"🏎️ 車手: {driver}")
    print(f"🏁 賽事: {session_info.get('year', 'Unknown')} {session_info.get('event_name', 'Unknown')}")
    print(f"📍 賽道: {session_info.get('circuit_name', 'Unknown')}")
    
    if not isinstance(analysis_data, dict):
        print("❌ 數據格式錯誤：期望 dict 格式")
        return
    
    # 統計摘要
    stats = analysis_data.get('overtaking_statistics', {})
    driver_info = analysis_data.get('driver_info', {})
    
    print(f"\n📋 超車統計摘要:")
    print(f"   • 總圈數: {driver_info.get('total_laps', 0)}")
    print(f"   • 超車次數: {stats.get('overtakes_made', 0)}")
    print(f"   • 被超次數: {stats.get('overtakes_received', 0)}")
    print(f"   • 淨位置變化: {stats.get('net_position_change', 0)}")
    print(f"   • 超車成功率: {analysis_data.get('overtaking_success_rate', 0):.1f}%")
    
    # 詳細位置變化表格
    position_changes = analysis_data.get('position_analysis', [])
    if position_changes:
        print(f"\n📈 位置變化詳細記錄 (前15次):")
        changes_table = PrettyTable()
        changes_table.field_names = ["圈數", "起始位置", "結束位置", "變化", "類型", "評估"]
        
        for change in position_changes[:15]:
            change_type = "超車" if change['type'] == 'overtake_made' else "被超"
            change_value = int(change['change'])  # 確保為整數
            
            if change_value > 0:
                assessment = "優秀" if change_value >= 3 else "良好"
            elif change_value < 0:
                assessment = "需改進" if change_value <= -3 else "一般"
            else:
                assessment = "持平"
            
            changes_table.add_row([
                change['lap_number'],
                change['from_position'],
                change['to_position'],
                f"{change_value:+d}",
                change_type,
                assessment
            ])
        
        print(changes_table)
    
    # 表現指標
    performance = analysis_data.get('performance_metrics', {})
    if performance:
        print(f"\n🏁 表現指標:")
        print(f"   • 最快圈速: {format_time(performance.get('fastest_lap_time', 'N/A'))}")
        print(f"   • 平均圈速: {format_time(performance.get('average_lap_time', 'N/A'))}")
        print(f"   • 圈速穩定性: {performance.get('lap_time_consistency', 0):.3f}秒")
    
    print("\n💾 數據來源: 緩存檔案")
    print("✅ 緩存數據詳細輸出完成")


if __name__ == "__main__":
    print("單一車手超車分析模組 - 獨立測試模式")
    print("此模組需要配合 F1 數據載入器使用")
