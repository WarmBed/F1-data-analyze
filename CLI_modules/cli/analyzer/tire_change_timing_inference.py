#!/usr/bin/env python3
"""
輪胎更換時機推算模組 (CLI -f26 修正版)
Tire Change Timing Inference Module

專門解決 FastF1 stint_analysis 不完整的問題
- 使用 OpenF1 進站數據推算輪胎更換的確切圈數
- 修正 STR、ALO 等車手的輪胎使用時序問題
- 重建完整的輪胎策略時間線

版本: 1.0 - 輪胎更換時機推算專用版
作者: F1 Analysis Team
"""

import os
import json
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from prettytable import PrettyTable

# 導入必要模組
try:
    from ..analyzer.driver_detailed_pitstop_records import analyze_driver_detailed_pitstops, get_session_info
except ImportError:
    try:
        from CLI_modules.cli.analyzer.driver_detailed_pitstop_records import analyze_driver_detailed_pitstops, get_session_info
        # 直接使用 f1_analysis_modular_main 中的函數  
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from f1_analysis_modular_main import get_tire_strategy_data_all_drivers
    except ImportError:
        print("[WARNING] 無法導入必要模組")
        get_tire_strategy_data_all_drivers = None


class TireChangeTimingInference:
    """輪胎更換時機推算器"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def analyze_tire_change_timing(self, **kwargs) -> Dict[str, Any]:
        """分析輪胎更換時機 - 修正 stint_analysis 缺失問題"""
        print("🔍 開始輪胎更換時機推算分析...")
        print("🎯 目標：解決 STR、ALO 等車手的輪胎使用時序問題")
        print("=" * 80)
        
        try:
            # 獲取基本賽事資訊
            session_info = get_session_info(self.data_loader, **kwargs)
            
            # 🔧 統一使用 CLI 參數格式 (與 -f1 保持一致)
            # 優先使用 CLI 參數，如果沒有則使用 session_info
            year = kwargs.get('year', session_info.get('year'))
            race = kwargs.get('race', 'Japan')  # 預設使用簡潔格式
            session_type = kwargs.get('session', session_info.get('session'))
            
            # 生成簡潔的檔名格式 (與 -f1 統一)
            cache_key = f"tire_strategy_{year}_{race}_{session_type}_all_drivers"
            json_file = os.path.join("json", f"{cache_key}.json")
            
            # 步驟1: 獲取 FastF1 輪胎配方數據
            print("🔄 步驟1: 載入 FastF1 輪胎配方數據...")
            tire_data = self._get_fastf1_tire_data(session_info)
            if not tire_data or not tire_data.get('success'):
                print("[ERROR] FastF1 輪胎數據載入失敗")
                return {"success": False, "error": "FastF1 數據載入失敗"}
            
            # 步驟2: 獲取 OpenF1 進站數據
            print("🔄 步驟2: 獲取 OpenF1 進站數據...")
            pitstop_records = analyze_driver_detailed_pitstops(self.data_loader, session_info)
            if not pitstop_records:
                print("[WARNING] 未獲取到 OpenF1 進站數據，將使用 FastF1 原始數據")
                pitstop_records = {}
            
            # 步驟3: 推算輪胎更換時機
            print("🔄 步驟3: 推算輪胎更換時機...")
            corrected_analysis = self._infer_tire_change_timing(
                tire_data.get('all_drivers_tire_strategy', {}), 
                pitstop_records,
                session_info
            )
            
            # 生成修正後的結果
            result = {
                "success": True,
                "year": session_info.get('year'),
                "race": session_info.get('event_name'),
                "session": session_info.get('session'),
                "analysis_mode": "tire_timing_inference",
                "analysis_timestamp": datetime.now().isoformat(),
                "drivers_analyzed": list(corrected_analysis.keys()),
                "tire_timing_corrected": corrected_analysis,
                "correction_method": {
                    "primary_data": "FastF1 tire compounds + performance",
                    "timing_inference": "OpenF1 pitstop data correlation",
                    "problem_solved": "Missing stint_analysis timing reconstruction"
                }
            }
            
            # 保存結果
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"💾 輪胎更換時機分析結果已保存: {json_file}")
            
            # 顯示分析結果
            self._display_tire_timing_analysis(result)
            
            return result
            
        except Exception as e:
            print(f"❌ 輪胎更換時機推算失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def _infer_tire_change_timing(self, tire_data: Dict, pitstop_records: Dict, session_info: Dict) -> Dict[str, Any]:
        """推算每位車手的輪胎更換時機"""
        corrected_data = {}
        
        print(f"🔍 開始分析 {len(tire_data)} 位車手的輪胎更換時機...")
        
        for driver, original_data in tire_data.items():
            print(f"\\n🏎️ 分析車手: {driver}")
            
            # 原始數據
            compounds_used = original_data.get('tire_compounds_used', [])
            tire_performance = original_data.get('tire_performance', {})
            original_stint = original_data.get('stint_analysis', [])
            
            # OpenF1 進站數據
            driver_pitstops = pitstop_records.get(driver, [])
            
            print(f"   📊 使用配方: {compounds_used}")
            print(f"   🔧 進站次數: {len(driver_pitstops)}")
            print(f"   📝 原始 stint 記錄: {len(original_stint)}")
            
            # 🎯 核心功能：重建輪胎使用時序
            corrected_stints = self._reconstruct_tire_timeline(
                compounds_used, tire_performance, driver_pitstops, original_stint
            )
            
            # 分析輪胎更換策略
            tire_changes = self._analyze_tire_changes(corrected_stints, driver_pitstops)
            
            # 計算修正統計
            correction_stats = self._calculate_correction_stats(original_stint, corrected_stints)
            
            # 保存修正後的數據
            corrected_data[driver] = {
                'tire_compounds_used': compounds_used,
                'tire_performance': tire_performance,
                'original_stint_analysis': original_stint,
                'corrected_stint_analysis': corrected_stints,
                'tire_changes_inferred': tire_changes,
                'correction_applied': correction_stats,
                'pit_stops_openf1': {
                    'total_pit_stops': len(driver_pitstops),
                    'pit_stop_details': [
                        {
                            'lap': stop.get('lap_number', 0),
                            'pit_duration': stop.get('pit_duration', 0),
                            'session_time': stop.get('session_time', 'Unknown')
                        }
                        for stop in driver_pitstops
                    ]
                }
            }
            
            # 顯示修正結果
            if correction_stats.get('correction_needed'):
                print(f"   ✅ 修正完成: {correction_stats.get('description')}")
            else:
                print(f"   ℹ️ 無需修正: 數據已完整")
        
        return corrected_data
    
    def _get_fastf1_tire_data(self, session_info: Dict) -> Dict[str, Any]:
        """獲取 FastF1 輪胎策略數據"""
        try:
            print("🔄 從 FastF1 載入輪胎數據...")
            
            # 獲取已載入的數據
            data = self.data_loader.get_loaded_data()
            if not data:
                raise ValueError("沒有可用的 FastF1 數據")
            
            laps = data.get('laps')
            session = data.get('session')
            
            if laps is None:
                raise ValueError("無法找到圈速數據")
            
            # 獲取所有車手列表
            all_drivers = sorted(laps['Driver'].unique())
            print(f"📊 找到 {len(all_drivers)} 位車手: {all_drivers}")
            
            all_drivers_tire_strategy = {}
            
            for driver in all_drivers:
                print(f"   分析車手: {driver}")
                
                # 獲取車手圈速數據
                driver_laps = laps[laps['Driver'] == driver].copy()
                
                if driver_laps.empty:
                    continue
                
                # 分析輪胎策略
                driver_analysis = self._analyze_driver_tire_strategy_fastf1(driver_laps, driver)
                
                if driver_analysis:
                    all_drivers_tire_strategy[driver] = driver_analysis
            
            return {
                "success": True,
                "year": session_info.get('year'),
                "race": session_info.get('event_name'),
                "session": session_info.get('session'),
                "analysis_mode": "fastf1_tire_data",
                "analysis_timestamp": datetime.now().isoformat(),
                "drivers_analyzed": list(all_drivers_tire_strategy.keys()),
                "all_drivers_tire_strategy": all_drivers_tire_strategy
            }
            
        except Exception as e:
            print(f"❌ FastF1 輪胎數據獲取失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_driver_tire_strategy_fastf1(self, driver_laps, driver: str) -> Dict[str, Any]:
        """分析單一車手的 FastF1 輪胎策略"""
        try:
            # 輪胎配方使用
            compounds_used = []
            if 'Compound' in driver_laps.columns:
                compounds_used = [c for c in driver_laps['Compound'].dropna().unique() if c != 'UNKNOWN']
            
            # 輪胎性能分析
            tire_performance = {}
            for compound in compounds_used:
                compound_laps = driver_laps[driver_laps['Compound'] == compound]
                
                if not compound_laps.empty and 'LapTime' in compound_laps.columns:
                    valid_times = compound_laps['LapTime'].dropna()
                    
                    if len(valid_times) > 0:
                        # 轉換為秒數
                        lap_times_seconds = []
                        for lap_time in valid_times:
                            if hasattr(lap_time, 'total_seconds'):
                                lap_times_seconds.append(lap_time.total_seconds())
                            else:
                                lap_times_seconds.append(float(lap_time))
                        
                        if lap_times_seconds:
                            tire_performance[compound] = {
                                'laps_used': len(lap_times_seconds),
                                'average_lap_time': sum(lap_times_seconds) / len(lap_times_seconds),
                                'fastest_lap_time': min(lap_times_seconds),
                                'slowest_lap_time': max(lap_times_seconds)
                            }
            
            # Stint 分析 (原始 FastF1 數據)
            stint_analysis = []
            if 'Stint' in driver_laps.columns:
                for stint_num in sorted(driver_laps['Stint'].dropna().unique()):
                    stint_laps = driver_laps[driver_laps['Stint'] == stint_num]
                    
                    if not stint_laps.empty:
                        compound = stint_laps['Compound'].iloc[0] if 'Compound' in stint_laps.columns else 'UNKNOWN'
                        start_lap = stint_laps['LapNumber'].min() if 'LapNumber' in stint_laps.columns else 1
                        end_lap = stint_laps['LapNumber'].max() if 'LapNumber' in stint_laps.columns else 1
                        
                        stint_analysis.append({
                            'stint_number': int(stint_num),
                            'tire_compound': compound,
                            'start_lap': int(start_lap),
                            'end_lap': int(end_lap),
                            'laps_count': int(end_lap - start_lap + 1)
                        })
            
            return {
                'tire_compounds_used': compounds_used,
                'tire_performance': tire_performance,
                'stint_analysis': stint_analysis,
                'pit_stops': {
                    'total_pit_stops': len(stint_analysis) - 1 if len(stint_analysis) > 1 else 0,
                    'pit_stop_details': []
                }
            }
            
        except Exception as e:
            print(f"❌ 車手 {driver} 輪胎分析失敗: {e}")
            return None
    
    def _reconstruct_tire_timeline(self, compounds: List[str], tire_performance: Dict, 
                                 pitstops: List[Dict], original_stint: List[Dict]) -> List[Dict]:
        """重建輪胎使用時間線"""
        
        # 如果只使用一種配方，直接返回原始數據
        if len(compounds) <= 1:
            return original_stint
        
        # 如果原始 stint_analysis 已經完整，且圈數合理，並且沒有進站數據需要校正，保留原始數據
        if (len(original_stint) >= len(compounds) and 
            self._is_stint_data_complete(original_stint, tire_performance) and
            len(pitstops) == 0):  # 只有在沒有進站數據時才跳過重建
            return original_stint
        
        print(f"   🔧 需要重建輪胎時間線: {len(compounds)} 種配方 vs {len(original_stint)} 個 stint")
        
        # 獲取進站圈數
        pit_laps = sorted([stop.get('lap_number', 0) for stop in pitstops if stop.get('lap_number', 0) > 0])
        
        # 重建 stint
        reconstructed_stints = []
        
        # 根據輪胎性能數據和進站數據重建時間線
        if tire_performance:
            # 按照輪胎配方的使用順序排列
            compound_timeline = self._determine_compound_sequence(tire_performance, pit_laps)
            
            stint_number = 1
            for compound_info in compound_timeline:
                compound = compound_info['compound']
                perf_data = tire_performance.get(compound, {})
                
                reconstructed_stint = {
                    'stint_number': stint_number,
                    'start_lap': compound_info['estimated_start_lap'],
                    'end_lap': compound_info['estimated_end_lap'],
                    'length': compound_info['estimated_end_lap'] - compound_info['estimated_start_lap'] + 1,
                    'compound': compound,
                    'average_lap_time': perf_data.get('average_lap_time', 0),
                    'inference_method': compound_info.get('method', 'pit_correlation')
                }
                
                reconstructed_stints.append(reconstructed_stint)
                stint_number += 1
        
        # 後處理：確保最後一個stint延續到比賽結束
        final_stints = reconstructed_stints if reconstructed_stints else original_stint
        
        if final_stints:
            # 找出比賽的實際結束圈數 - 限制在合理範圍內
            race_end_lap = 53  # F1標準比賽圈數
            
            # 從輪胎性能數據中找最大圈數，但不超過55圈
            if tire_performance:
                for perf in tire_performance.values():
                    if 'last_lap' in perf:
                        race_end_lap = max(race_end_lap, min(perf['last_lap'], 55))
            
            # 從進站數據中估算，但設定上限
            if pitstops:
                pit_laps = [stop.get('lap_number', 0) for stop in pitstops if stop.get('lap_number', 0) > 0]
                if pit_laps:
                    # 最後進站+5圈作為合理的比賽結束點，最多不超過55圈
                    estimated_end = max(pit_laps) + 5
                    race_end_lap = max(race_end_lap, min(estimated_end, 55))
            
            # 修正最後一個stint的結束圈數
            last_stint = final_stints[-1]
            original_end = last_stint.get('end_lap', 0)
            
            if original_end < race_end_lap:
                print(f"   🔧 修正最後stint結束圈數: {original_end} -> {race_end_lap}")
                last_stint['end_lap'] = race_end_lap
                if 'length' in last_stint:
                    last_stint['length'] = race_end_lap - last_stint.get('start_lap', 1) + 1
                if 'inference_method' not in last_stint:
                    last_stint['inference_method'] = 'race_end_extension'
        
        return final_stints
    
    def _determine_compound_sequence(self, tire_performance: Dict, pit_laps: List[int]) -> List[Dict]:
        """確定輪胎配方使用順序"""
        compound_sequence = []
        
        # 按照每種配方的首次使用圈數排序
        compounds_by_first_lap = []
        for compound, perf in tire_performance.items():
            first_lap = perf.get('first_lap', 1)
            last_lap = perf.get('last_lap', 1)
            laps_used = perf.get('laps_used', 0)
            
            compounds_by_first_lap.append({
                'compound': compound,
                'first_lap': first_lap,
                'last_lap': last_lap,
                'laps_used': laps_used
            })
        
        # 按首次使用圈數排序
        compounds_by_first_lap.sort(key=lambda x: x['first_lap'])
        
        # 根據進站數據調整配方順序
        if pit_laps:
            # 有進站記錄的情況
            current_lap = 1
            
            for i, compound_info in enumerate(compounds_by_first_lap):
                if i < len(pit_laps):
                    # 這個配方在下一次進站前結束
                    end_lap = pit_laps[i]
                    method = f'pit_stop_correlation'
                else:
                    # 最後一個配方使用到比賽結束
                    # 修正：確保最後一個stint延續到比賽結束
                    original_last_lap = compound_info['last_lap']
                    
                    # 找出比賽的實際結束圈數 - 限制在合理範圍內
                    # 優先使用原始數據中的最大圈數，但設定上限
                    race_end_lap = max(
                        min(original_last_lap, 55),  # 原始數據的最後一圈，但不超過55
                        max(pit_laps) + 5 if pit_laps else 53,  # 最後進站 + 5圈
                        53  # F1 標準比賽圈數
                    )
                    
                    # 確保不超過合理的上限
                    end_lap = min(race_end_lap, 55)
                    method = f'race_end_extension'
                
                compound_sequence.append({
                    'compound': compound_info['compound'],
                    'estimated_start_lap': current_lap,
                    'estimated_end_lap': end_lap,
                    'original_first_lap': compound_info['first_lap'],
                    'original_last_lap': compound_info['last_lap'],
                    'method': method
                })
                
                current_lap = end_lap + 1
        else:
            # 沒有進站記錄，使用原始性能數據
            for compound_info in compounds_by_first_lap:
                compound_sequence.append({
                    'compound': compound_info['compound'],
                    'estimated_start_lap': compound_info['first_lap'],
                    'estimated_end_lap': compound_info['last_lap'],
                    'original_first_lap': compound_info['first_lap'],
                    'original_last_lap': compound_info['last_lap'],
                    'method': 'original_data'
                })
        
        # 確保最後一個 stint 延續到比賽結束，但限制在合理範圍內
        if compound_sequence:
            # 找出比賽實際結束圈數，設定合理上限
            race_end_lap = 53  # F1 標準比賽圈數
            if pit_laps:
                # 最後進站 + 5圈，最多不超過55圈
                estimated_end = max(pit_laps) + 5
                race_end_lap = max(race_end_lap, min(estimated_end, 55))
            
            # 檢查所有配方的最後使用圈數，但不超過55圈
            for compound_info in compounds_by_first_lap:
                original_last = compound_info.get('last_lap', 53)
                race_end_lap = max(race_end_lap, min(original_last, 55))
            
            # 最終確保不超過55圈
            race_end_lap = min(race_end_lap, 55)
            
            # 修正最後一個 stint 的結束圈數
            last_stint = compound_sequence[-1]
            if last_stint['estimated_end_lap'] < race_end_lap:
                print(f"   🔧 修正最後 stint 結束圈數: {last_stint['estimated_end_lap']} -> {race_end_lap}")
                last_stint['estimated_end_lap'] = race_end_lap
                last_stint['method'] = 'race_end_correction'
        
        return compound_sequence
    
    def _is_stint_data_complete(self, stint_data: List[Dict], tire_performance: Dict) -> bool:
        """檢查 stint 數據是否完整"""
        if not stint_data or not tire_performance:
            return False
        
        # 檢查是否所有輪胎配方都有對應的 stint
        stint_compounds = {stint.get('compound') for stint in stint_data}
        performance_compounds = set(tire_performance.keys())
        
        return stint_compounds >= performance_compounds  # stint 包含所有性能數據中的配方
    
    def _analyze_tire_changes(self, corrected_stints: List[Dict], pitstops: List[Dict]) -> List[Dict]:
        """分析輪胎更換詳情"""
        tire_changes = []
        
        if len(corrected_stints) <= 1:
            return tire_changes
        
        pit_laps = [stop.get('lap_number', 0) for stop in pitstops]
        
        for i in range(len(corrected_stints) - 1):
            current_stint = corrected_stints[i]
            next_stint = corrected_stints[i + 1]
            
            change_lap = current_stint.get('end_lap', 0)
            
            # 找到對應的進站記錄
            matching_pitstop = None
            for pit_lap in pit_laps:
                if abs(pit_lap - change_lap) <= 1:  # 允許1圈誤差
                    matching_pitstop = next((p for p in pitstops if p.get('lap_number') == pit_lap), None)
                    break
            
            tire_change = {
                'change_number': i + 1,
                'lap': change_lap,
                'from_compound': current_stint.get('compound'),
                'to_compound': next_stint.get('compound'),
                'pitstop_duration': matching_pitstop.get('pit_duration') if matching_pitstop else None,
                'inference_confidence': 'High' if matching_pitstop else 'Medium'
            }
            
            tire_changes.append(tire_change)
        
        return tire_changes
    
    def _calculate_correction_stats(self, original_stint: List[Dict], corrected_stints: List[Dict]) -> Dict[str, Any]:
        """計算修正統計信息"""
        
        original_count = len(original_stint)
        corrected_count = len(corrected_stints)
        
        correction_needed = corrected_count > original_count
        
        if not correction_needed:
            return {
                'correction_needed': False,
                'description': f'原始數據完整 ({original_count} stints)',
                'original_stints': original_count,
                'corrected_stints': corrected_count
            }
        
        added_stints = corrected_count - original_count
        
        return {
            'correction_needed': True,
            'description': f'新增 {added_stints} 個 stint ({original_count} → {corrected_count})',
            'original_stints': original_count,
            'corrected_stints': corrected_count,
            'stints_added': added_stints,
            'correction_method': 'pitstop_correlation'
        }
    
    def _display_tire_timing_analysis(self, result: Dict[str, Any]):
        """顯示輪胎更換時機分析結果"""
        if not result.get('success'):
            print(f"❌ 分析失敗: {result.get('error', '未知錯誤')}")
            return
        
        corrected_data = result.get('tire_timing_corrected', {})
        
        print(f"\\n🎯 輪胎更換時機推算結果")
        print("=" * 100)
        
        print(f"📊 分析概況:")
        print(f"   • 賽事: {result.get('year')} 年 {result.get('race')} {result.get('session')}")
        print(f"   • 車手數量: {len(corrected_data)}")
        
        # 統計需要修正的車手
        drivers_corrected = []
        drivers_complete = []
        
        for driver, data in corrected_data.items():
            if data.get('correction_applied', {}).get('correction_needed'):
                drivers_corrected.append(driver)
            else:
                drivers_complete.append(driver)
        
        print(f"\\n🔧 修正統計:")
        print(f"   • 需要修正的車手: {len(drivers_corrected)} 位")
        print(f"   • 數據完整的車手: {len(drivers_complete)} 位")
        
        if drivers_corrected:
            print(f"   • 修正車手列表: {', '.join(drivers_corrected[:10])}")
            if len(drivers_corrected) > 10:
                print(f"     ... 等共 {len(drivers_corrected)} 位車手")
        
        # 顯示重點案例分析
        print(f"\\n🔍 重點案例分析:")
        
        # 重點關注 STR, ALO, BEA 等問題車手
        focus_drivers = ['STR', 'ALO', 'BEA', 'DOO']
        
        for driver in focus_drivers:
            if driver in corrected_data:
                self._display_driver_tire_correction(driver, corrected_data[driver])
        
        # 顯示整體輪胎更換統計
        self._display_tire_change_summary(corrected_data)
        
        print(f"\\n✅ 輪胎更換時機推算完成！")
        print(f"💡 解決方案：OpenF1 進站數據 + FastF1 配方數據 = 完整輪胎策略時間線")
    
    def _display_driver_tire_correction(self, driver: str, driver_data: Dict):
        """顯示單一車手的輪胎修正詳情"""
        correction = driver_data.get('correction_applied', {})
        
        if not correction.get('correction_needed'):
            return
        
        print(f"\\n  🏎️ {driver} - {correction.get('description')}")
        
        compounds = driver_data.get('tire_compounds_used', [])
        tire_changes = driver_data.get('tire_changes_inferred', [])
        
        print(f"     📊 使用配方: {' → '.join(compounds)}")
        
        if tire_changes:
            print(f"     🔄 輪胎更換:")
            for change in tire_changes:
                lap = change.get('lap', 0)
                from_compound = change.get('from_compound', 'Unknown')
                to_compound = change.get('to_compound', 'Unknown')
                confidence = change.get('inference_confidence', 'Unknown')
                
                print(f"        第{lap}圈: {from_compound} → {to_compound} ({confidence})")
    
    def _display_tire_change_summary(self, corrected_data: Dict):
        """顯示輪胎更換摘要統計"""
        print(f"\\n📈 輪胎更換統計摘要:")
        
        total_changes = 0
        compound_changes = {}
        change_timing = []
        
        for driver, data in corrected_data.items():
            tire_changes = data.get('tire_changes_inferred', [])
            total_changes += len(tire_changes)
            
            for change in tire_changes:
                from_comp = change.get('from_compound', 'Unknown')
                to_comp = change.get('to_compound', 'Unknown')
                change_key = f"{from_comp}→{to_comp}"
                
                compound_changes[change_key] = compound_changes.get(change_key, 0) + 1
                change_timing.append(change.get('lap', 0))
        
        print(f"   • 總輪胎更換次數: {total_changes}")
        
        if compound_changes:
            print(f"   • 常見更換模式:")
            for pattern, count in sorted(compound_changes.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"     - {pattern}: {count} 次")
        
        if change_timing:
            avg_change_lap = sum(change_timing) / len(change_timing)
            print(f"   • 平均更換圈數: 第 {avg_change_lap:.1f} 圈")


def run_tire_change_timing_inference(data_loader, **kwargs):
    """執行輪胎更換時機推算分析的入口函數"""
    analyzer = TireChangeTimingInference(data_loader)
    return analyzer.analyze_tire_change_timing(**kwargs)


if __name__ == "__main__":
    # 測試用途
    print("輪胎更換時機推算模組")
    print("專門解決 FastF1 stint_analysis 不完整的問題")
