#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
純 FastF1 輪胎策略分析模組 (CLI -f26 FastF1-Only 版本)
FastF1-Only Tire Strategy Ana        print(f"[CACHE] 載入快取: {cache_file}")
        
        if not os.path.exists(cache_file):
            print(f"[ERROR] 快取檔案不存在: {cache_file}")
            return None
        
        with open(cache_file, 'rb') as f:
            data = pickle.load(f)
        
        file_size = os.path.getsize(cache_file)
        print(f"[OK] 快取載入成功 ({file_size:,} bytes)")e

不依賴 OpenF1，僅使用 FastF1 快取資料進行輪胎策略分析
基於 test_italy_tire_detailed.py 的成功分析邏輯
適用於 CLI 參數 -f26 的純 FastF1 模式

版本: 2.0 - 純 FastF1 專用版
作者: F1 Analysis Team  
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import json
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

def run_fastf1_tire_strategy_analysis(f1_data, year: int, race: str, session: str, 
                                      driver: str = None, verbose: bool = False, **kwargs) -> Dict[str, Any]:
    """
    執行純 FastF1 輪胎策略分析
    
    Args:
        f1_data: F1 資料 (純 FastF1 模組不需要，僅為相容性)
        year: 年份
        race: 賽事名稱  
        session: 賽段 (R/Q/P)
        driver: 車手代碼 (可選，為 None 時分析所有車手)
        verbose: 是否顯示詳細輸出 (預設: False)
        **kwargs: 其他參數
        
    Returns:
        Dict[str, Any]: 分析結果
    """
    
    if verbose:
        print(f"🏎️ 開始純 FastF1 輪胎策略分析 - {year} {race} {session}")
        print(f"👨‍🏎️ 分析目標: {driver if driver else '所有車手'}")
    
    try:
        # 載入 FastF1 快取資料
        cached_data = load_fastf1_cache_data(year, race, session, verbose)
        if not cached_data:
            return {
                "success": False,
                "message": "無法載入 FastF1 快取資料",
                "function_id": "26"
            }
        
        # 提取輪胎相關資料
        tire_data = extract_tire_data_from_cache(cached_data, verbose)
        if tire_data is None or len(tire_data) == 0:
            return {
                "success": False,
                "message": "無法提取輪胎資料",
                "function_id": "26"
            }
        
        # 分析輪胎策略
        if driver:
            # 單一車手分析
            analysis_result = analyze_single_driver_tire_strategy(tire_data, driver, year, race, session, verbose)
        else:
            # 所有車手分析
            analysis_result = analyze_all_drivers_tire_strategy(tire_data, year, race, session, verbose)
        
        if not analysis_result:
            return {
                "success": False,
                "message": "輪胎策略分析失敗",
                "function_id": "26"
            }
        
        # 匯出結果為 JSON
        export_result = export_tire_strategy_to_json(analysis_result, year, race, session, driver, verbose)
        
        return {
            "success": True,
            "message": f"輪胎策略分析完成 - {'單一車手' if driver else '所有車手'}",
            "data": analysis_result,
            "export_info": export_result,
            "function_id": "26",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        if verbose:
            print(f"❌ 輪胎策略分析發生錯誤: {str(e)}")
            import traceback
import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

            traceback.print_exc()
        return {
            "success": False,
            "message": f"輪胎策略分析錯誤: {str(e)}",
            "function_id": "26"
        }

def load_fastf1_cache_data(year: int, race: str, session: str, verbose: bool = False) -> Optional[Dict]:
    """載入 FastF1 快取資料"""
    
    cache_file = f"f1_analysis_cache/f1_data_{year}_{race}_{session}.pkl"
    
    try:
        if verbose:
            print(f"📂 正在載入快取檔案: {cache_file}")
        
        if not os.path.exists(cache_file):
            if verbose:
                print(f"❌ 快取檔案不存在: {cache_file}")
            return None
        
        with open(cache_file, 'rb') as f:
            cached_data = pickle.load(f)
        
        file_size = os.path.getsize(cache_file)
        if verbose:
            print(f"✅ 成功載入快取資料，檔案大小: {file_size:,} bytes")
        return cached_data
    
    except Exception as e:
        if verbose:
            print(f"❌ 載入快取時發生錯誤: {str(e)}")
        return None

def extract_tire_data_from_cache(data: Dict, verbose: bool = False) -> Optional[pd.DataFrame]:
    """從快取資料中提取輪胎相關資料"""
    
    try:
        if verbose:
            print("🔍 開始提取輪胎相關資料...")
        
        if not isinstance(data, dict):
            if verbose:
                print("❌ 快取資料格式錯誤")
            return None
        
        # 檢查 session 資料
        if 'session' in data:
            session = data['session']
            if hasattr(session, 'laps'):
                laps = session.laps
                if verbose:
                    print(f"🏁 找到圈速資料: {laps.shape}")
                
                # 檢查輪胎相關欄位
                tire_columns = []
                essential_columns = ['Driver', 'LapNumber', 'LapTime', 'Stint']
                
                for col in laps.columns:
                    if any(tire_word in str(col).lower() for tire_word in ['tire', 'compound', 'tyre', 'stint']):
                        tire_columns.append(col)
                
                if verbose:
                    print(f"🛞 輪胎相關欄位: {tire_columns}")
                
                # 獲取所有需要的欄位
                available_cols = [col for col in essential_columns if col in laps.columns]
                all_cols = tire_columns + available_cols
                
                # 去重
                all_cols = list(dict.fromkeys(all_cols))
                
                if verbose:
                    print(f"📋 提取欄位: {all_cols}")
                
                # 提取資料
                tire_data = laps[all_cols].copy()
                if verbose:
                    print(f"✅ 成功提取輪胎資料: {len(tire_data)} 筆記錄")
                
                return tire_data
        
        if verbose:
            print("❌ 找不到有效的輪胎資料")
        return None
    
    except Exception as e:
        if verbose:
            print(f"❌ 提取輪胎資料時發生錯誤: {str(e)}")
        return None

def analyze_single_driver_tire_strategy(df: pd.DataFrame, driver: str, year: int, race: str, session: str, verbose: bool = False) -> Dict[str, Any]:
    """分析單一車手的輪胎策略"""
    
    if verbose:
        print(f"\n🏎️ 分析車手 {driver} 的輪胎策略")
        print("-" * 60)
    
    # 篩選該車手的資料
    driver_data = df[df['Driver'] == driver].sort_values('LapNumber').copy()
    
    if len(driver_data) == 0:
        if verbose:
            print(f"❌ 找不到車手 {driver} 的資料")
        return None
    
    # 基本統計
    total_laps = len(driver_data)
    stints = sorted(driver_data['Stint'].unique()) if 'Stint' in driver_data.columns else [1]
    compounds_used = list(driver_data['Compound'].unique()) if 'Compound' in driver_data.columns else ['UNKNOWN']
    
    if verbose:
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
        }
        
        stint_analysis.append(stint_info)
        
        # 檢查是否有輪胎更換
        if prev_stint is not None and prev_compound is not None and compound != prev_compound:
            tire_change = {
                'lap': start_lap - 1,  # 進站是在前一圈後
                'from_compound': prev_compound,
                'to_compound': compound,
                'from_stint': int(prev_stint),
                'to_stint': int(stint)
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
    
    result = {
        'tire_timing_corrected': {
            'year': year,
            'race': race,
            'session': session,
            'analysis_timestamp': datetime.now().isoformat()
        },
        'all_drivers_tire_strategy': {
            'total_drivers': 1,
            'total_laps': total_laps,
            'compound_distribution': compound_stats,
            'race_info': {
                'year': year,
                'race': race,
                'session': session
            }
        },
        'corrected_stint_analysis': {
            driver: {
                'driver': driver,
                'race_info': {
                    'year': year,
                    'race': race,
                    'session': session
                },
                'summary': {
                    'total_laps': total_laps,
                    'stint_count': len(stints),
                    'tire_changes': len(tire_changes),
                    'compounds_used': compounds_used
                },
                'stint_analysis': stint_analysis,
                'tire_changes': tire_changes,
                'compound_usage': compound_stats
            }
        }
    }
    
    # 顯示分析結果
    print_driver_tire_analysis(result, driver, verbose)
    
    return result

def analyze_all_drivers_tire_strategy(df: pd.DataFrame, year: int, race: str, session: str, verbose: bool = False) -> Dict[str, Any]:
    """分析所有車手的輪胎策略"""
    
    if verbose:
        print(f"\n🏎️ 分析所有車手的輪胎策略")
        print("-" * 80)
    
    drivers = sorted(df['Driver'].unique())
    if verbose:
        print(f"👥 發現 {len(drivers)} 位車手: {', '.join(drivers)}")
    
    all_drivers_analysis = {}
    
    for driver in drivers:
        if verbose:
            print(f"\n📊 正在分析車手: {driver}")
        driver_result = analyze_single_driver_tire_strategy(df, driver, year, race, session, verbose)
        if driver_result:
            all_drivers_analysis[driver] = driver_result
    
    # 整體統計
    total_laps = len(df)
    
    if 'Compound' in df.columns:
        compound_distribution = df['Compound'].value_counts().to_dict()
        compound_stats = {}
        for compound, count in compound_distribution.items():
            compound_stats[compound] = {
                'total_laps': int(count),
                'percentage': round((count / total_laps) * 100, 1)
            }
    else:
        compound_stats = {}
    
    result = {
        'tire_timing_corrected': {
            'year': year,
            'race': race,
            'session': session,
            'analysis_timestamp': datetime.now().isoformat()
        },
        'all_drivers_tire_strategy': {
            'total_drivers': len(drivers),
            'total_laps': total_laps,
            'stint_range': f"{int(df['Stint'].min())} - {int(df['Stint'].max())}" if 'Stint' in df.columns else "N/A",
            'compound_distribution': compound_stats,
            'race_info': {
                'year': year,
                'race': race,
                'session': session
            }
        },
        'corrected_stint_analysis': all_drivers_analysis
    }
    
    return result

def print_driver_tire_analysis(result: Dict[str, Any], driver_id: str, verbose: bool = False):
    """顯示單一車手輪胎分析結果"""
    
    # 在新格式中，車手資訊在 corrected_stint_analysis 下
    driver_data = result['corrected_stint_analysis'][driver_id]
    driver = driver_data['driver']
    summary = driver_data['summary']
    
    if verbose:
        print(f"\n📋 {driver} 輪胎策略分析結果:")
        print(f"   總圈數: {summary['total_laps']}")
        print(f"   Stint 數量: {summary['stint_count']}")
        print(f"   換胎次數: {summary['tire_changes']}")
        print(f"   使用輪胎: {', '.join(summary['compounds_used'])}")
        
        # Stint 詳細資訊
        print(f"\n🔄 Stint 詳細分析:")
        for stint in driver_data['stint_analysis']:
            print(f"   Stint {stint['stint_number']}: {stint['compound']}, 第{stint['start_lap']}-{stint['end_lap']}圈 ({stint['length']}圈)")
        
        # 換胎記錄
        if driver_data['tire_changes']:
            print(f"\n🔧 換胎記錄:")
            for i, change in enumerate(driver_data['tire_changes'], 1):
                print(f"   換胎 {i}: 第{change['lap']}圈後, {change['from_compound']} → {change['to_compound']}")
        else:
            print(f"\n🔧 未檢測到換胎 (可能為單一配方策略)")

def export_tire_strategy_to_json(analysis_result: Dict[str, Any], year: int, race: str, session: str, driver: str = None, verbose: bool = False) -> Dict[str, str]:
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
        print(f"✅ 分析結果已匯出: {filepath} ({file_size:,} bytes)")
        
        return {
            'filename': filename,
            'filepath': filepath,
            'size': file_size
        }
        
    except Exception as e:
        print(f"❌ 匯出 JSON 時發生錯誤: {str(e)}")
        return {
            'error': str(e)
        }

# 別名函數，保持與現有系統的相容性
def run_tire_change_timing_inference(data_loader, **kwargs):
    """別名函數，用於相容性"""
    return run_fastf1_tire_strategy_analysis(data_loader, **kwargs)
