#!/usr/bin/env python3
"""
增強版全部車手輪胎策略分析模組 (CLI -f26 OpenF1 整合版)
Enhanced All Drivers Tire Strategy Analysis with OpenF1 Integration

整合 OpenF1 進站數據到輪胎策略分析中，解決 FastF1 進站數據不準確的問題
- 使用 OpenF1 API 獲取精確的進站時間和圈數
- 結合 FastF1 輪胎配方數據進行完整分析
- 智能關聯進站時機與輪胎更換

版本: 2.0 - OpenF1 整合版
作者: F1 Analysis Team
日期: 2025-09-10
"""

import os
import json
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional
from prettytable import PrettyTable

# 導入必要模組
try:
    from ..core.openf1_data_analyzer import F1OpenDataAnalyzer
    from ..analyzer.driver_detailed_pitstop_records import analyze_driver_detailed_pitstops, get_session_info
except ImportError:
    try:
        from CLI_modules.cli.core.openf1_data_analyzer import F1OpenDataAnalyzer
        from CLI_modules.cli.analyzer.driver_detailed_pitstop_records import analyze_driver_detailed_pitstops, get_session_info
    except ImportError:
        print("[WARNING] 無法導入必要模組，某些功能可能不可用")
        F1OpenDataAnalyzer = None
        analyze_driver_detailed_pitstops = None
        get_session_info = None


class EnhancedTireStrategyAnalyzer:
    """增強版輪胎策略分析器 - 整合 OpenF1 進站數據"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化 OpenF1 分析器
        self.openf1_analyzer = F1OpenDataAnalyzer() if F1OpenDataAnalyzer else None
    
    def run_enhanced_tire_analysis(self, **kwargs):
        """執行增強版輪胎策略分析"""
        print("🛞 開始執行增強版全部車手輪胎策略分析...")
        print("🔧 整合 OpenF1 進站數據 + FastF1 輪胎配方數據")
        print("=" * 80)
        
        try:
            # 步驟1: 獲取賽事信息
            session_info = self._get_session_info(**kwargs)
            print(f"📊 賽事: {session_info.get('year')} {session_info.get('event_name')} {session_info.get('session')}")
            
            # 步驟2: 檢查緩存
            cache_result = self._check_cache(session_info)
            if cache_result:
                return cache_result
            
            # 步驟3: 獲取 OpenF1 進站數據
            print("\n🔄 獲取 OpenF1 進站數據...")
            pitstop_data = self._get_openf1_pitstops(session_info)
            
            # 步驟4: 獲取 FastF1 輪胎數據
            print("🔄 獲取 FastF1 輪胎配方數據...")
            tire_data = self._get_fastf1_tires(session_info)
            
            # 步驟5: 數據整合與分析
            print("🔄 整合數據並進行分析...")
            integrated_result = self._integrate_and_analyze(pitstop_data, tire_data, session_info)
            
            # 步驟6: 保存結果
            self._save_results(integrated_result, session_info)
            
            # 步驟7: 顯示摘要
            self._display_summary(integrated_result)
            
            return integrated_result
            
        except Exception as e:
            print(f"❌ 分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _get_session_info(self, **kwargs):
        """獲取賽事信息"""
        if get_session_info:
            return get_session_info(self.data_loader, **kwargs)
        else:
            # 備用方案
            return {
                "year": kwargs.get('year', 2025),
                "event_name": kwargs.get('race', 'Japan'),
                "session": kwargs.get('session', 'R')
            }
    
    def _check_cache(self, session_info):
        """檢查緩存"""
        event_clean = session_info.get('event_name', 'Unknown').replace(' ', '_')
        cache_key = f"enhanced_tire_strategy_{session_info.get('year')}_{event_clean}_{session_info.get('session')}_all_drivers"
        json_file = os.path.join("json", f"{cache_key}.json")
        
        if os.path.exists(json_file):
            print(f"📦 從緩存載入: {json_file}")
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    cached_result = json.load(f)
                self._display_summary(cached_result)
                return cached_result
            except Exception as e:
                print(f"[WARNING] 緩存載入失敗: {e}")
        
        return None
    
    def _get_openf1_pitstops(self, session_info):
        """獲取 OpenF1 進站數據"""
        if not analyze_driver_detailed_pitstops:
            print("⚠️ OpenF1 進站分析模組不可用")
            return {}
        
        try:
            pitstop_records = analyze_driver_detailed_pitstops(self.data_loader, session_info)
            if pitstop_records:
                total_stops = sum(len(stops) for stops in pitstop_records.values())
                print(f"✅ OpenF1 進站數據: {len(pitstop_records)} 位車手, {total_stops} 次進站")
                return pitstop_records
            else:
                print("⚠️ 未獲取到 OpenF1 進站數據")
                return {}
        except Exception as e:
            print(f"[ERROR] OpenF1 進站數據獲取失敗: {e}")
            return {}
    
    def _get_fastf1_tires(self, session_info):
        """獲取 FastF1 輪胎配方數據"""
        try:
            session = self.data_loader.load_session()
            laps_data = session.laps
            
            if laps_data.empty:
                print("❌ FastF1 數據為空")
                return {}
            
            drivers = laps_data['Driver'].unique()
            tire_data = {}
            
            for driver in drivers:
                if driver and str(driver) != 'nan':
                    driver_laps = laps_data.pick_driver(driver)
                    
                    if not driver_laps.empty and 'Compound' in driver_laps.columns:
                        # 輪胎配方統計
                        compounds = driver_laps['Compound'].dropna().unique().tolist()
                        
                        # 各配方性能數據
                        compound_performance = {}
                        for compound in compounds:
                            compound_laps = driver_laps[driver_laps['Compound'] == compound]
                            valid_times = compound_laps['LapTime'].dropna()
                            
                            if len(valid_times) > 0:
                                times_seconds = valid_times.dt.total_seconds()
                                compound_performance[compound] = {
                                    'laps_used': len(compound_laps),
                                    'average_lap_time': times_seconds.mean(),
                                    'best_lap_time': times_seconds.min(),
                                    'first_lap': int(compound_laps['LapNumber'].min()),
                                    'last_lap': int(compound_laps['LapNumber'].max())
                                }
                        
                        tire_data[driver] = {
                            'tire_compounds_used': compounds,
                            'tire_performance': compound_performance,
                            'total_laps': len(driver_laps)
                        }
            
            print(f"✅ FastF1 輪胎數據: {len(tire_data)} 位車手")
            return tire_data
            
        except Exception as e:
            print(f"[ERROR] FastF1 輪胎數據獲取失敗: {e}")
            return {}
    
    def _integrate_and_analyze(self, pitstop_data, tire_data, session_info):
        """整合數據並進行分析"""
        # 合併車手列表
        all_drivers = set(list(pitstop_data.keys()) + list(tire_data.keys()))
        integrated_analysis = {}
        
        print(f"🔄 整合 {len(all_drivers)} 位車手的數據...")
        
        for driver in all_drivers:
            driver_pitstops = pitstop_data.get(driver, [])
            driver_tires = tire_data.get(driver, {})
            
            # 基本信息
            compounds_used = driver_tires.get('tire_compounds_used', [])
            tire_performance = driver_tires.get('tire_performance', {})
            
            # 進站策略 (OpenF1 數據)
            pit_stops = self._analyze_pit_stops(driver_pitstops, tire_performance)
            
            # Stint 分析 (基於進站和輪胎數據)
            stint_analysis = self._analyze_stints(driver_pitstops, tire_performance)
            
            # 輪胎衰退分析
            tire_degradation = self._analyze_degradation(tire_performance)
            
            # 策略效果評估
            strategy_effectiveness = self._evaluate_strategy(compounds_used, driver_pitstops, tire_performance)
            
            # 整合車手數據
            integrated_analysis[driver] = {
                'tire_compounds_used': compounds_used,
                'pit_stops': pit_stops,
                'tire_performance': tire_performance,
                'stint_analysis': stint_analysis,
                'tire_degradation': tire_degradation,
                'strategy_effectiveness': strategy_effectiveness
            }
        
        # 構建完整結果
        result = {
            'success': True,
            'year': session_info.get('year'),
            'race': session_info.get('event_name'),
            'session': session_info.get('session'),
            'analysis_mode': 'enhanced_all_drivers',
            'analysis_timestamp': datetime.now().isoformat(),
            'drivers_analyzed': list(integrated_analysis.keys()),
            'all_drivers_tire_strategy': integrated_analysis,
            'data_sources': {
                'pitstop_data': 'OpenF1 API',
                'tire_compounds': 'FastF1',
                'integration_method': 'enhanced_correlation'
            }
        }
        
        print(f"✅ 數據整合完成: {len(integrated_analysis)} 位車手")
        return result
    
    def _analyze_pit_stops(self, pitstops, tire_performance):
        """分析進站策略"""
        pit_stop_details = []
        
        for i, stop in enumerate(pitstops):
            pit_detail = {
                'lap': stop.get('lap_number', 0),
                'pit_duration': stop.get('pit_duration', 0),
                'session_time': stop.get('session_time', 'Unknown')
            }
            
            # 推斷輪胎更換
            tire_change = self._infer_tire_change(stop.get('lap_number', 0), tire_performance)
            if tire_change:
                pit_detail['from_compound'] = tire_change.get('from')
                pit_detail['to_compound'] = tire_change.get('to')
            
            pit_stop_details.append(pit_detail)
        
        return {
            'total_pit_stops': len(pitstops),
            'pit_stop_details': pit_stop_details,
            'average_pit_window': self._calculate_avg_window(pitstops)
        }
    
    def _infer_tire_change(self, pit_lap, tire_performance):
        """推斷輪胎更換"""
        try:
            compounds_by_time = []
            
            for compound, perf in tire_performance.items():
                first_lap = perf.get('first_lap', 0)
                last_lap = perf.get('last_lap', 0)
                compounds_by_time.append({
                    'compound': compound,
                    'first_lap': first_lap,
                    'last_lap': last_lap
                })
            
            # 按開始圈數排序
            compounds_by_time.sort(key=lambda x: x['first_lap'])
            
            # 尋找進站前後的配方
            for i in range(len(compounds_by_time) - 1):
                current = compounds_by_time[i]
                next_compound = compounds_by_time[i + 1]
                
                if (current['last_lap'] <= pit_lap <= next_compound['first_lap'] + 2):
                    return {
                        'from': current['compound'],
                        'to': next_compound['compound']
                    }
            
            return None
        except:
            return None
    
    def _calculate_avg_window(self, pitstops):
        """計算平均進站間隔"""
        if len(pitstops) <= 1:
            return None
        
        pit_laps = [stop.get('lap_number', 0) for stop in pitstops]
        pit_laps.sort()
        
        intervals = [pit_laps[i] - pit_laps[i-1] for i in range(1, len(pit_laps))]
        return sum(intervals) / len(intervals) if intervals else None
    
    def _analyze_stints(self, pitstops, tire_performance):
        """分析 stint"""
        stints = []
        
        if not pitstops:
            # 無進站情況
            if tire_performance:
                compound = list(tire_performance.keys())[0]
                perf = tire_performance[compound]
                stints.append({
                    'stint_number': 1,
                    'start_lap': perf.get('first_lap', 1),
                    'end_lap': perf.get('last_lap', 1),
                    'length': perf.get('laps_used', 1),
                    'compound': compound,
                    'average_lap_time': perf.get('average_lap_time', 0)
                })
            return stints
        
        # 有進站情況
        pit_laps = sorted([stop.get('lap_number', 0) for stop in pitstops])
        
        # 分析各 stint
        stint_num = 1
        start_lap = 1
        
        for pit_lap in pit_laps:
            # 找到對應的輪胎配方
            compound, perf = self._find_compound_for_stint(start_lap, pit_lap, tire_performance)
            
            if compound:
                stints.append({
                    'stint_number': stint_num,
                    'start_lap': start_lap,
                    'end_lap': pit_lap,
                    'length': pit_lap - start_lap + 1,
                    'compound': compound,
                    'average_lap_time': perf.get('average_lap_time', 0)
                })
            
            stint_num += 1
            start_lap = pit_lap + 1
        
        # 最後一個 stint
        if tire_performance:
            last_compound, last_perf = self._find_last_compound(pit_laps[-1], tire_performance)
            if last_compound:
                stints.append({
                    'stint_number': stint_num,
                    'start_lap': start_lap,
                    'end_lap': last_perf.get('last_lap', start_lap),
                    'length': last_perf.get('last_lap', start_lap) - start_lap + 1,
                    'compound': last_compound,
                    'average_lap_time': last_perf.get('average_lap_time', 0)
                })
        
        return stints
    
    def _find_compound_for_stint(self, start_lap, end_lap, tire_performance):
        """為 stint 找到對應的輪胎配方"""
        for compound, perf in tire_performance.items():
            first_lap = perf.get('first_lap', 0)
            last_lap = perf.get('last_lap', 0)
            
            if first_lap <= start_lap <= last_lap:
                return compound, perf
        
        return None, {}
    
    def _find_last_compound(self, last_pit_lap, tire_performance):
        """找到最後使用的配方"""
        candidates = []
        
        for compound, perf in tire_performance.items():
            if perf.get('last_lap', 0) > last_pit_lap:
                candidates.append((compound, perf))
        
        if candidates:
            return max(candidates, key=lambda x: x[1].get('last_lap', 0))
        
        return None, {}
    
    def _analyze_degradation(self, tire_performance):
        """分析輪胎衰退"""
        degradation = {}
        
        for compound, perf in tire_performance.items():
            laps_used = perf.get('laps_used', 0)
            avg_time = perf.get('average_lap_time', 0)
            best_time = perf.get('best_lap_time', 0)
            
            if laps_used > 0 and avg_time > 0 and best_time > 0:
                degradation_rate = (avg_time - best_time) / laps_used
                
                degradation[compound] = {
                    'degradation_per_lap': degradation_rate,
                    'total_degradation': avg_time - best_time,
                    'degradation_percentage': ((avg_time - best_time) / best_time * 100),
                    'laps_used': laps_used,
                    'compound_longevity': self._rate_longevity(degradation_rate)
                }
        
        return degradation
    
    def _rate_longevity(self, degradation_rate):
        """評估輪胎耐久性"""
        if degradation_rate < 0.1:
            return 'High'
        elif degradation_rate < 0.2:
            return 'Medium'
        else:
            return 'Low'
    
    def _evaluate_strategy(self, compounds, pitstops, tire_performance):
        """評估策略效果"""
        effectiveness = {
            'pit_stop_efficiency': self._rate_pit_efficiency(pitstops),
            'tire_strategy_diversity': len(compounds),
            'compound_utilization': self._calculate_utilization(tire_performance),
            'strategy_complexity': f'{len(pitstops)}-stop' if pitstops else 'No-stop'
        }
        
        return effectiveness
    
    def _rate_pit_efficiency(self, pitstops):
        """評估進站效率"""
        if not pitstops:
            return 'N/A'
        
        pit_times = [stop.get('pit_duration', 0) for stop in pitstops if stop.get('pit_duration', 0) > 0]
        
        if not pit_times:
            return 'N/A'
        
        avg_time = sum(pit_times) / len(pit_times)
        
        if avg_time < 3.0:
            return 'Excellent'
        elif avg_time < 4.0:
            return 'Good'
        elif avg_time < 5.0:
            return 'Average'
        else:
            return 'Poor'
    
    def _calculate_utilization(self, tire_performance):
        """計算配方利用率"""
        total_laps = sum(perf.get('laps_used', 0) for perf in tire_performance.values())
        utilization = {}
        
        for compound, perf in tire_performance.items():
            laps_used = perf.get('laps_used', 0)
            rate = (laps_used / total_laps * 100) if total_laps > 0 else 0
            utilization[compound] = f"{rate:.1f}%"
        
        return utilization
    
    def _save_results(self, result, session_info):
        """保存結果"""
        event_clean = session_info.get('event_name', 'Unknown').replace(' ', '_')
        cache_key = f"enhanced_tire_strategy_{session_info.get('year')}_{event_clean}_{session_info.get('session')}_all_drivers"
        
        # 保存 pickle 緩存
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
        
        # 保存 JSON
        json_file = os.path.join("json", f"{cache_key}.json")
        os.makedirs(os.path.dirname(json_file), exist_ok=True)
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 結果已保存: {json_file}")
    
    def _display_summary(self, result):
        """顯示分析摘要"""
        if not result.get('success'):
            print(f"❌ 分析失敗: {result.get('error')}")
            return
        
        drivers_data = result.get('all_drivers_tire_strategy', {})
        
        print(f"\n🛞 增強版輪胎策略分析結果")
        print("=" * 80)
        print(f"📊 賽事: {result.get('year')} {result.get('race')} {result.get('session')}")
        print(f"🏎️ 車手數量: {len(drivers_data)}")
        print(f"🔧 數據來源: {result.get('data_sources', {}).get('pitstop_data')} + {result.get('data_sources', {}).get('tire_compounds')}")
        
        # 統計摘要
        total_stops = sum(data.get('pit_stops', {}).get('total_pit_stops', 0) for data in drivers_data.values())
        compounds_used = set()
        for data in drivers_data.values():
            compounds_used.update(data.get('tire_compounds_used', []))
        
        print(f"\n📈 統計摘要:")
        print(f"   • 總進站次數: {total_stops}")
        print(f"   • 輪胎配方: {', '.join(sorted(compounds_used))}")
        print(f"   • 平均進站: {total_stops/len(drivers_data):.1f} 次/車手" if drivers_data else "")
        
        # 前10位車手詳情
        print(f"\n🏁 車手策略詳情 (前10位):")
        
        table = PrettyTable()
        table.field_names = ["車手", "配方", "進站", "策略", "效率"]
        
        for driver, data in list(drivers_data.items())[:10]:
            compounds = '+'.join(data.get('tire_compounds_used', []))
            stops = data.get('pit_stops', {}).get('total_pit_stops', 0)
            complexity = data.get('strategy_effectiveness', {}).get('strategy_complexity', 'Unknown')
            efficiency = data.get('strategy_effectiveness', {}).get('pit_stop_efficiency', 'N/A')
            
            table.add_row([driver, compounds[:15], stops, complexity, efficiency])
        
        print(table)
        print("\n✅ 增強版輪胎策略分析完成！")


def run_enhanced_tire_strategy_analysis(data_loader, **kwargs):
    """執行增強版輪胎策略分析的入口函數"""
    analyzer = EnhancedTireStrategyAnalyzer(data_loader)
    return analyzer.run_enhanced_tire_analysis(**kwargs)


if __name__ == "__main__":
    print("增強版輪胎策略分析模組")
    print("整合 OpenF1 進站數據與 FastF1 輪胎配方數據")
