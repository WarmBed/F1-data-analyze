#!/usr/bin/env python3
"""
純 FastF1 輪胎策略分析模組 (CLI -f26 FastF1-Only 版本)
FastF1-Only Tire Strategy Analysis Module

不依賴 OpenF1，僅使用 FastF1 快取資料進行輪胎策略分析
基於 test_italy_tire_detailed.py 的成功分析邏輯
適用於 CLI 參數 -f26 的純 FastF1 模式

版本: 2.0 - 純 FastF1 專用版
作者: F1 Analysis Team
"""

import os
import json
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

def run_fastf1_tire_strategy_analysis(data_loader, year: int, race: str, session: str, 
                                      driver: str = None, **kwargs) -> Dict[str, Any]:
    """
    執行純 FastF1 輪胎策略分析
    
    Args:
        data_loader: 資料載入器
        year: 年份
        race: 賽事名稱
        session: 賽段 (R/Q/P)
        driver: 車手代碼 (可選，為 None 時分析所有車手)
        **kwargs: 其他參數
        
    Returns:
        Dict[str, Any]: 分析結果
    """
    
    print(f"\n🏎️ 開始純 FastF1 輪胎策略分析")
    print(f"📊 目標賽事: {year} {race} {session}")
    print(f"👨‍🏎️ 分析車手: {driver if driver else '所有車手'}")
    
    try:
        # 載入 FastF1 快取資料
        cached_data = load_fastf1_cache_data(year, race, session)
        if not cached_data:
            return {
                "success": False,
                "message": "無法載入 FastF1 快取資料",
                "function_id": "26"
            }
        
        # 提取輪胎相關資料
        tire_data = extract_tire_data_from_cache(cached_data)
        if tire_data is None or len(tire_data) == 0:
            return {
                "success": False,
                "message": "無法提取輪胎資料",
                "function_id": "26"
            }
        
        # 分析輪胎策略
        if driver:
            # 單一車手分析
            analysis_result = analyze_single_driver_tire_strategy(tire_data, driver, year, race, session)
        else:
            # 所有車手分析
            analysis_result = analyze_all_drivers_tire_strategy(tire_data, year, race, session)
        
        if not analysis_result:
            return {
                "success": False,
                "message": "輪胎策略分析失敗",
                "function_id": "26"
            }
        
        # 匯出結果為 JSON
        export_result = export_tire_strategy_to_json(analysis_result, year, race, session, driver)
        
        return {
            "success": True,
            "message": f"輪胎策略分析完成 - {'單一車手' if driver else '所有車手'}",
            "data": analysis_result,
            "export_info": export_result,
            "function_id": "26",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 輪胎策略分析發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"輪胎策略分析錯誤: {str(e)}",
            "function_id": "26"
        }

def load_fastf1_cache_data(year: int, race: str, session: str) -> Optional[Dict]:
    """載入 FastF1 快取資料"""
    
    cache_file = f"f1_analysis_cache/f1_data_{year}_{race}_{session}.pkl"
    
    try:
        print(f"📂 正在載入快取檔案: {cache_file}")
        
        if not os.path.exists(cache_file):
            print(f"❌ 快取檔案不存在: {cache_file}")
            return None
        
        with open(cache_file, 'rb') as f:
            cached_data = pickle.load(f)
        
        file_size = os.path.getsize(cache_file)
        print(f"✅ 成功載入快取資料，檔案大小: {file_size:,} bytes")
        return cached_data
    
    except Exception as e:
        print(f"❌ 載入快取時發生錯誤: {str(e)}")
        return None

def extract_tire_data_from_cache(data: Dict) -> Optional[pd.DataFrame]:
    """從快取資料中提取輪胎相關資料"""
    
    try:
        print("🔍 開始提取輪胎相關資料...")
        
        if not isinstance(data, dict):
            print("❌ 快取資料格式錯誤")
            return None
        
        # 檢查 session 資料
        if 'session' in data:
            session = data['session']
            if hasattr(session, 'laps'):
                laps = session.laps
                print(f"🏁 找到圈速資料: {laps.shape}")
                
                # 檢查輪胎相關欄位
                tire_columns = []
                essential_columns = ['Driver', 'LapNumber', 'LapTime', 'Stint']
                
                for col in laps.columns:
                    if any(tire_word in str(col).lower() for tire_word in ['tire', 'compound', 'tyre', 'stint']):
                        tire_columns.append(col)
                
                print(f"🛞 輪胎相關欄位: {tire_columns}")
                
                # 獲取所有需要的欄位
                available_cols = [col for col in essential_columns if col in laps.columns]
                all_cols = tire_columns + available_cols
                
                # 去重
                all_cols = list(dict.fromkeys(all_cols))
                
                print(f"📋 提取欄位: {all_cols}")
                
                # 提取資料
                tire_data = laps[all_cols].copy()
                print(f"✅ 成功提取輪胎資料: {len(tire_data)} 筆記錄")
                
                return tire_data
        
        print("❌ 找不到有效的輪胎資料")
        return None
    
    except Exception as e:
        print(f"❌ 提取輪胎資料時發生錯誤: {str(e)}")
        return None

def analyze_single_driver_tire_strategy(df: pd.DataFrame, driver: str, year: int, race: str, session: str) -> Dict[str, Any]:
    """分析單一車手的輪胎策略"""
    
    print(f"\n🏎️ 分析車手 {driver} 的輪胎策略")
    print("-" * 60)
    
    # 篩選該車手的資料
    driver_data = df[df['Driver'] == driver].sort_values('LapNumber').copy()
    
    if len(driver_data) == 0:
        print(f"❌ 找不到車手 {driver} 的資料")
        return None
    
    # 基本統計
    total_laps = len(driver_data)
    stints = sorted(driver_data['Stint'].unique()) if 'Stint' in driver_data.columns else [1]
    compounds_used = list(driver_data['Compound'].unique()) if 'Compound' in driver_data.columns else ['UNKNOWN']
    
    print(f"📊 基本統計:")
    print(f"   總圈數: {total_laps}")
    print(f"   Stint 數量: {len(stints)} ({stints})")
    print(f"   使用輪胎: {', '.join(compounds_used)}")
    
    # Stint 分析
    stint_analysis = []
    tire_changes = []
    
    prev_stint = None
    prev_compound = None
    
    for stint in stints:
        stint_data = driver_data[driver_data['Stint'] == stint]
        
        if len(stint_data) == 0:
            continue
        
        compound = stint_data['Compound'].iloc[0] if 'Compound' in stint_data.columns else 'UNKNOWN'
        start_lap = int(stint_data['LapNumber'].min())
        end_lap = int(stint_data['LapNumber'].max())
        stint_length = len(stint_data)
        
        if 'TyreLife' in stint_data.columns:
            tyre_life_start = int(stint_data['TyreLife'].min())
            tyre_life_end = int(stint_data['TyreLife'].max())
        else:
            tyre_life_start = 1
            tyre_life_end = stint_length
        
        stint_info = {
            'stint_number': int(stint),
            'compound': compound,
            'start_lap': start_lap,
            'end_lap': end_lap,
            'length': stint_length,
            'tyre_life_start': tyre_life_start,
            'tyre_life_end': tyre_life_end
        }\n        \n        stint_analysis.append(stint_info)\n        \n        # 檢查是否有輪胎更換\n        if prev_stint is not None and prev_compound is not None and compound != prev_compound:\n            tire_change = {\n                'lap': start_lap - 1,  # 進站是在前一圈後\n                'from_compound': prev_compound,\n                'to_compound': compound,\n                'from_stint': int(prev_stint),\n                'to_stint': int(stint)\n            }\n            tire_changes.append(tire_change)\n        \n        prev_stint = stint\n        prev_compound = compound\n    \n    # 輪胎配方使用統計\n    compound_stats = {}\n    if 'Compound' in driver_data.columns:\n        compound_counts = driver_data['Compound'].value_counts()\n        for compound, count in compound_counts.items():\n            percentage = (count / total_laps) * 100\n            compound_stats[compound] = {\n                'laps': int(count),\n                'percentage': round(percentage, 1)\n            }\n    \n    # 圈速分析\n    laptime_analysis = None\n    if 'LapTime' in driver_data.columns:\n        valid_times = driver_data.dropna(subset=['LapTime'])\n        if len(valid_times) > 0:\n            # 轉換時間格式\n            times_seconds = []\n            for lt in valid_times['LapTime']:\n                if pd.notna(lt):\n                    try:\n                        # 處理時間格式\n                        time_str = str(lt).replace('0 days ', '')\n                        if ':' in time_str:\n                            parts = time_str.split(':')\n                            if len(parts) == 3:\n                                minutes = int(parts[1])\n                                seconds = float(parts[2])\n                                total_seconds = minutes * 60 + seconds\n                                times_seconds.append(total_seconds)\n                    except:\n                        continue\n            \n            if times_seconds:\n                laptime_analysis = {\n                    'fastest_lap': min(times_seconds),\n                    'average_lap': sum(times_seconds) / len(times_seconds),\n                    'slowest_lap': max(times_seconds),\n                    'valid_laps': len(times_seconds)\n                }\n    \n    result = {\n        'driver': driver,\n        'race_info': {\n            'year': year,\n            'race': race,\n            'session': session\n        },\n        'summary': {\n            'total_laps': total_laps,\n            'stint_count': len(stints),\n            'tire_changes': len(tire_changes),\n            'compounds_used': compounds_used\n        },\n        'stint_analysis': stint_analysis,\n        'tire_changes': tire_changes,\n        'compound_usage': compound_stats,\n        'laptime_summary': laptime_analysis,\n        'analysis_timestamp': datetime.now().isoformat()\n    }\n    \n    # 顯示分析結果\n    print_driver_tire_analysis(result)\n    \n    return result\n\ndef analyze_all_drivers_tire_strategy(df: pd.DataFrame, year: int, race: str, session: str) -> Dict[str, Any]:\n    \"\"\"分析所有車手的輪胎策略\"\"\"\n    \n    print(f\"\\n🏎️ 分析所有車手的輪胎策略\")\n    print(\"-\" * 80)\n    \n    drivers = sorted(df['Driver'].unique())\n    print(f\"👥 發現 {len(drivers)} 位車手: {', '.join(drivers)}\")\n    \n    all_drivers_analysis = {}\n    \n    for driver in drivers:\n        print(f\"\\n📊 正在分析車手: {driver}\")\n        driver_result = analyze_single_driver_tire_strategy(df, driver, year, race, session)\n        if driver_result:\n            all_drivers_analysis[driver] = driver_result\n    \n    # 整體統計\n    total_laps = len(df)\n    total_stints = df['Stint'].nunique() if 'Stint' in df.columns else 0\n    \n    if 'Compound' in df.columns:\n        compound_distribution = df['Compound'].value_counts().to_dict()\n        for compound in compound_distribution:\n            compound_distribution[compound] = {\n                'total_laps': int(compound_distribution[compound]),\n                'percentage': round((compound_distribution[compound] / total_laps) * 100, 1)\n            }\n    else:\n        compound_distribution = {}\n    \n    result = {\n        'race_info': {\n            'year': year,\n            'race': race,\n            'session': session\n        },\n        'overall_summary': {\n            'total_drivers': len(drivers),\n            'total_laps': total_laps,\n            'stint_range': f\"{int(df['Stint'].min())} - {int(df['Stint'].max())}\" if 'Stint' in df.columns else \"N/A\",\n            'compound_distribution': compound_distribution\n        },\n        'drivers_analysis': all_drivers_analysis,\n        'analysis_timestamp': datetime.now().isoformat()\n    }\n    \n    # 顯示整體分析結果\n    print_overall_tire_analysis(result)\n    \n    return result\n\ndef print_driver_tire_analysis(result: Dict[str, Any]):\n    \"\"\"顯示單一車手輪胎分析結果\"\"\"\n    \n    driver = result['driver']\n    summary = result['summary']\n    \n    print(f\"\\n📋 {driver} 輪胎策略分析結果:\")\n    print(f\"   總圈數: {summary['total_laps']}\")\n    print(f\"   Stint 數量: {summary['stint_count']}\")\n    print(f\"   換胎次數: {summary['tire_changes']}\")\n    print(f\"   使用輪胎: {', '.join(summary['compounds_used'])}\")\n    \n    # Stint 詳細資訊\n    print(f\"\\n🔄 Stint 詳細分析:\")\n    for stint in result['stint_analysis']:\n        print(f\"   Stint {stint['stint_number']}: {stint['compound']}, 第{stint['start_lap']}-{stint['end_lap']}圈 ({stint['length']}圈)\")\n    \n    # 換胎記錄\n    if result['tire_changes']:\n        print(f\"\\n🔧 換胎記錄:\")\n        for i, change in enumerate(result['tire_changes'], 1):\n            print(f\"   換胎 {i}: 第{change['lap']}圈後, {change['from_compound']} → {change['to_compound']}\")\n    else:\n        print(f\"\\n🔧 未檢測到換胎 (可能為單一配方策略)\")\n    \n    # 輪胎使用統計\n    if result['compound_usage']:\n        print(f\"\\n🛞 輪胎使用統計:\")\n        for compound, stats in result['compound_usage'].items():\n            print(f\"   {compound}: {stats['laps']} 圈 ({stats['percentage']}%)\")\n\ndef print_overall_tire_analysis(result: Dict[str, Any]):\n    \"\"\"顯示整體輪胎分析結果\"\"\"\n    \n    summary = result['overall_summary']\n    \n    print(f\"\\n📊 整體輪胎策略分析結果:\")\n    print(f\"   參賽車手: {summary['total_drivers']} 位\")\n    print(f\"   總圈數: {summary['total_laps']} 圈\")\n    print(f\"   Stint 範圍: {summary['stint_range']}\")\n    \n    if summary['compound_distribution']:\n        print(f\"\\n🛞 整體輪胎配方分佈:\")\n        for compound, stats in summary['compound_distribution'].items():\n            print(f\"   {compound}: {stats['total_laps']} 圈 ({stats['percentage']}%)\")\n    \n    print(f\"\\n👥 各車手策略摘要:\")\n    for driver, analysis in result['drivers_analysis'].items():\n        stint_count = analysis['summary']['stint_count']\n        tire_changes = analysis['summary']['tire_changes']\n        compounds = ', '.join(analysis['summary']['compounds_used'])\n        print(f\"   {driver}: {stint_count}段Stint, {tire_changes}次換胎, 使用 {compounds}\")\n\ndef export_tire_strategy_to_json(analysis_result: Dict[str, Any], year: int, race: str, session: str, driver: str = None) -> Dict[str, str]:\n    \"\"\"匯出輪胎策略分析結果為 JSON 格式\"\"\"\n    \n    timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")\n    \n    if driver:\n        filename = f\"tire_strategy_{year}_{race}_{session}_{driver}_fastf1_only_{timestamp}.json\"\n    else:\n        filename = f\"tire_strategy_{year}_{race}_{session}_all_drivers_fastf1_only_{timestamp}.json\"\n    \n    # 確保 json_exports 目錄存在\n    os.makedirs('json_exports', exist_ok=True)\n    filepath = os.path.join('json_exports', filename)\n    \n    try:\n        with open(filepath, 'w', encoding='utf-8') as f:\n            json.dump(analysis_result, f, indent=2, ensure_ascii=False, default=str)\n        \n        file_size = os.path.getsize(filepath)\n        print(f\"\\n✅ 分析結果已匯出: {filepath} ({file_size:,} bytes)\")\n        \n        return {\n            'filename': filename,\n            'filepath': filepath,\n            'size': file_size\n        }\n        \n    except Exception as e:\n        print(f\"❌ 匯出 JSON 時發生錯誤: {str(e)}\")\n        return {\n            'error': str(e)\n        }\n\n# 別名函數，保持與現有系統的相容性\ndef run_tire_change_timing_inference(data_loader, **kwargs):\n    \"\"\"別名函數，用於相容性\"\"\"\n    return run_fastf1_tire_strategy_analysis(data_loader, **kwargs)\n\nif __name__ == \"__main__\":\n    # 測試程式\n    print(\"🧪 純 FastF1 輪胎策略分析模組測試\")\n    # 可以在這裡添加測試代碼
