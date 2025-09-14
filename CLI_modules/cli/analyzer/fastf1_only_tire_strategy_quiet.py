"""
純 FastF1 輪胎策略分析模組 - 簡潔版本
生成與舊格式相容的 JSON 輸出，減少控制台輸出
"""

import os
import json
import pickle
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

def run_fastf1_tire_strategy_analysis(f1_data, year: int, race: str, session: str, driver: str = None) -> Dict[str, Any]:
    """執行純 FastF1 輪胎策略分析的主要函數"""
    
    print(f"🏎️ 純 FastF1 輪胎策略分析: {year} {race} {session}")
    
    try:
        # 載入 FastF1 快取資料
        cached_data = load_fastf1_cache_data(year, race, session)
        if cached_data is None:
            return {"error": "無法載入快取資料"}
        
        # 提取輪胎資料
        tire_data = extract_tire_data_from_cache(cached_data)
        if tire_data is None:
            return {"error": "無法提取輪胎資料"}
        
        # 分析輪胎策略
        if driver:
            print(f"分析車手: {driver}")
            result = analyze_single_driver_tire_strategy(tire_data, driver, year, race, session)
        else:
            print(f"分析所有車手")
            result = analyze_all_drivers_tire_strategy(tire_data, year, race, session)
        
        # 匯出到 JSON
        export_info = export_tire_strategy_to_json(result, year, race, session, driver)
        
        return {
            "status": "success",
            "result": result,
            "export_info": export_info
        }
    
    except Exception as e:
        print(f"❌ 分析錯誤: {str(e)}")
        return {"error": str(e)}

def load_fastf1_cache_data(year: int, race: str, session: str) -> Optional[Dict]:
    """載入 FastF1 快取資料"""
    
    try:
        cache_file = f"f1_analysis_cache/f1_data_{year}_{race}_{session}.pkl"
        
        if not os.path.exists(cache_file):
            print(f"❌ 快取檔案不存在: {cache_file}")
            return None
        
        with open(cache_file, 'rb') as f:
            data = pickle.load(f)
        
        file_size = os.path.getsize(cache_file)
        print(f"✅ 載入成功 ({file_size//1024//1024}MB)")
        return data
    
    except Exception as e:
        print(f"❌ 載入錯誤: {str(e)}")
        return None

def extract_tire_data_from_cache(data: Dict) -> Optional[pd.DataFrame]:
    """從快取資料中提取輪胎相關資料"""
    
    try:
        if 'session' not in data:
            print("❌ 快取資料格式錯誤")
            return None
        
        session = data['session']
        if not hasattr(session, 'laps'):
            print("❌ 找不到圈速資料")
            return None
            
        laps = session.laps
        
        # 檢查輪胎相關欄位
        tire_columns = []
        essential_columns = ['Driver', 'LapNumber', 'LapTime', 'Stint']
        
        for col in laps.columns:
            if any(tire_word in str(col).lower() for tire_word in ['tire', 'compound', 'tyre', 'stint']):
                tire_columns.append(col)
        
        # 獲取所有需要的欄位
        available_cols = [col for col in essential_columns if col in laps.columns]
        all_cols = list(set(available_cols + tire_columns))
        
        tire_data = laps[all_cols].copy()
        
        print(f"✅ 提取完成: {len(tire_data)} 筆記錄")
        
        return tire_data
        
    except Exception as e:
        print(f"❌ 提取錯誤: {str(e)}")
        return None

def analyze_single_driver_tire_strategy(tire_data: pd.DataFrame, driver: str, year: int, race: str, session: str) -> Dict[str, Any]:
    """分析單一車手的輪胎策略"""
    
    driver_data = tire_data[tire_data['Driver'] == driver].copy()
    
    if len(driver_data) == 0:
        return {"error": f"找不到車手 {driver} 的資料"}
    
    # 基本統計
    total_laps = len(driver_data)
    stints = sorted(driver_data['Stint'].dropna().unique())
    
    if 'Compound' in driver_data.columns:
        compounds_used = driver_data['Compound'].dropna().unique().tolist()
    else:
        compounds_used = ['UNKNOWN']
    
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
        
        stint_info = {
            'stint_number': int(stint),
            'compound': compound,
            'start_lap': start_lap,
            'end_lap': end_lap,
            'length': stint_length
        }
        
        stint_analysis.append(stint_info)
        
        # 檢查是否有輪胎更換
        if prev_stint is not None and prev_compound is not None and compound != prev_compound:
            tire_change = {
                'lap': start_lap - 1,
                'from_compound': prev_compound,
                'to_compound': compound
            }
            tire_changes.append(tire_change)
        
        prev_stint = stint
        prev_compound = compound
    
    # 輪胎配方使用統計
    compound_stats = {}
    if 'Compound' in driver_data.columns:
        compound_counts = driver_data['Compound'].value_counts()
        for compound, count in compound_counts.items():
            percentage = (count / total_laps) * 100
            compound_stats[compound] = {
                'laps': int(count),
                'percentage': round(percentage, 1)
            }
    
    # 生成與舊格式相容的結果
    result = {
        "race_info": {
            "year": year,
            "race": race,
            "session": session
        },
        "drivers_analysis": {
            driver: {
                "driver": driver,
                "race_info": {
                    "year": year,
                    "race": race,
                    "session": session
                },
                "stint_analysis": stint_analysis,
                "tire_changes": tire_changes,
                "summary": {
                    "total_laps": total_laps,
                    "stint_count": len(stints),
                    "tire_changes": len(tire_changes),
                    "compounds_used": compounds_used,
                    "compound_stats": compound_stats
                }
            }
        },
        "analysis_timestamp": datetime.now().isoformat()
    }
    
    return result

def analyze_all_drivers_tire_strategy(tire_data: pd.DataFrame, year: int, race: str, session: str) -> Dict[str, Any]:
    """分析所有車手的輪胎策略"""
    
    drivers = sorted(tire_data['Driver'].unique())
    
    drivers_analysis = {}
    total_laps = 0
    all_compound_stats = {}
    stint_range = [float('inf'), 0]
    
    for driver in drivers:
        driver_result = analyze_single_driver_tire_strategy(tire_data, driver, year, race, session)
        if "error" not in driver_result:
            driver_info = driver_result["drivers_analysis"][driver]
            drivers_analysis[driver] = driver_info
            
            # 統計資料
            total_laps += driver_info["summary"]["total_laps"]
            
            # Stint 範圍
            stint_count = driver_info["summary"]["stint_count"]
            if stint_count > 0:
                stint_range[0] = min(stint_range[0], stint_count)
                stint_range[1] = max(stint_range[1], stint_count)
            
            # 配方統計
            for compound, stats in driver_info["summary"]["compound_stats"].items():
                if compound not in all_compound_stats:
                    all_compound_stats[compound] = {"total_laps": 0}
                all_compound_stats[compound]["total_laps"] += stats["laps"]
    
    # 計算配方百分比
    for compound in all_compound_stats:
        percentage = (all_compound_stats[compound]["total_laps"] / total_laps) * 100 if total_laps > 0 else 0
        all_compound_stats[compound]["percentage"] = round(percentage, 1)
    
    # 生成與舊格式相容的結果
    result = {
        "race_info": {
            "year": year,
            "race": race,
            "session": session
        },
        "overall_summary": {
            "total_drivers": len(drivers),
            "total_laps": total_laps,
            "stint_range": f"{stint_range[0]} - {stint_range[1]}" if stint_range[0] != float('inf') else "0",
            "compound_distribution": all_compound_stats
        },
        "drivers_analysis": drivers_analysis,
        "analysis_timestamp": datetime.now().isoformat()
    }
    
    return result

def export_tire_strategy_to_json(analysis_result: Dict[str, Any], year: int, race: str, session: str, driver: str = None) -> Dict[str, str]:
    """匯出輪胎策略分析結果為 JSON 格式"""
    
    if driver:
        filename = f"tire_strategy_{year}_{race}_{session}_{driver}.json"
    else:
        filename = f"tire_strategy_{year}_{race}_{session}_all_drivers.json"
    
    # 確保 json 目錄存在
    os.makedirs('json', exist_ok=True)
    filepath = os.path.join('json', filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False, default=str)
        
        file_size = os.path.getsize(filepath)
        print(f"✅ 匯出完成: {filename} ({file_size:,} bytes)")
        
        return {
            "filename": filename,
            "filepath": filepath,
            "file_size": file_size
        }
        
    except Exception as e:
        print(f"❌ 匯出錯誤: {str(e)}")
        return {"error": str(e)}
