#!/usr/bin/env python3
"""
全部車手輪胎策略分析模組 (CLI -f26 增強版)
Enhanced All Drivers Tire Strategy Analysis Module

整合 OpenF1 進站數據到輪胎策略分析中
- 使用 OpenF1 API 獲取精確的進站時間和圈數
- 結合 FastF1 輪胎配方數據進行完整分析
- 解決 FastF1 進站數據不準確的問題

版本: 2.0 - OpenF1 整合版
作者: F1 Analysis Team
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
        print("[WARNING] 無法導入必要模組")
        F1OpenDataAnalyzer = None


class EnhancedAllDriversTireStrategy:
    """增強版全部車手輪胎策略分析器"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化 OpenF1 分析器
        self.openf1_analyzer = F1OpenDataAnalyzer() if F1OpenDataAnalyzer else None
    
    def analyze_all_drivers_tire_strategy(self, **kwargs) -> Dict[str, Any]:
        """分析所有車手的輪胎策略 (整合 OpenF1 進站數據)"""
        print("🛞 開始執行全部車手輪胎策略分析 (OpenF1 進站數據整合版)...")
        print("=" * 80)
        
        try:
            # 獲取基本賽事資訊
            session_info = get_session_info(self.data_loader, **kwargs)
            
            # 生成緩存鍵
            event_name_clean = session_info.get('event_name', 'Unknown').replace(' ', '_')
            cache_key = f"tire_strategy_{session_info.get('year')}_{event_name_clean}_{session_info.get('session')}_all_drivers"
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            json_file = os.path.join("json", f"{cache_key}.json")
            
            # 檢查緩存
            if os.path.exists(json_file):
                print(f"📦 從緩存載入輪胎策略數據: {json_file}")
                with open(json_file, 'r', encoding='utf-8') as f:
                    cached_result = json.load(f)
                
                self._display_enhanced_tire_strategy_summary(cached_result)
                return cached_result
            
            # 步驟1: 獲取 OpenF1 進站數據
            print("🔄 步驟1: 獲取 OpenF1 進站數據...")
            pitstop_records = self._get_openf1_pitstop_data(session_info)
            
            # 步驟2: 獲取 FastF1 輪胎數據
            print("🔄 步驟2: 獲取 FastF1 輪胎配方數據...")
            tire_compound_data = self._get_fastf1_tire_data(session_info)
            
            # 步驟3: 整合數據分析
            print("🔄 步驟3: 整合 OpenF1 進站數據與 FastF1 輪胎數據...")
            integrated_analysis = self._integrate_pitstop_and_tire_data(
                pitstop_records, tire_compound_data, session_info
            )
            
            # 保存結果
            result = {
                "success": True,
                "year": session_info.get('year'),
                "race": session_info.get('event_name'),
                "session": session_info.get('session'),
                "analysis_mode": "all_drivers_enhanced",
                "analysis_timestamp": datetime.now().isoformat(),
                "drivers_analyzed": list(integrated_analysis.keys()),
                "all_drivers_tire_strategy": integrated_analysis,
                "data_sources": {
                    "pitstop_data": "OpenF1 API",
                    "tire_compounds": "FastF1",
                    "integration_method": "enhanced_correlation"
                }
            }
            
            # 保存到緩存和 JSON
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"💾 分析結果已保存: {json_file}")
            
            # 顯示分析結果
            self._display_enhanced_tire_strategy_summary(result)
            
            return result
            
        except Exception as e:
            print(f"❌ 全部車手輪胎策略分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }\n    \n    def _get_openf1_pitstop_data(self, session_info: Dict[str, Any]) -> Dict[str, List[Dict]]:\n        \"\"\"獲取 OpenF1 進站數據\"\"\"\n        if not self.openf1_analyzer:\n            print(\"[WARNING] OpenF1 分析器不可用，跳過進站數據獲取\")\n            return {}\n        \n        try:\n            # 使用與功能5相同的邏輯獲取進站數據\n            pitstop_records = analyze_driver_detailed_pitstops(self.data_loader, session_info)\n            \n            if pitstop_records:\n                print(f\"✅ 成功獲取 {len(pitstop_records)} 位車手的進站記錄\")\n                total_stops = sum(len(stops) for stops in pitstop_records.values())\n                print(f\"📊 總進站次數: {total_stops}\")\n                return pitstop_records\n            else:\n                print(\"⚠️ 未獲取到 OpenF1 進站數據\")\n                return {}\n                \n        except Exception as e:\n            print(f\"[ERROR] 獲取 OpenF1 進站數據失敗: {e}\")\n            return {}\n    \n    def _get_fastf1_tire_data(self, session_info: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"獲取 FastF1 輪胎配方數據\"\"\"\n        try:\n            # 載入比賽數據\n            session = self.data_loader.load_session()\n            laps_data = session.laps\n            \n            if laps_data.empty:\n                print(\"[ERROR] FastF1 數據為空\")\n                return {}\n            \n            # 獲取所有車手的輪胎配方數據\n            drivers = laps_data['Driver'].unique()\n            tire_data = {}\n            \n            for driver in drivers:\n                if driver and str(driver) != 'nan':\n                    driver_laps = laps_data.pick_driver(driver)\n                    \n                    if not driver_laps.empty and 'Compound' in driver_laps.columns:\n                        # 分析輪胎使用\n                        compounds_used = driver_laps['Compound'].dropna().unique().tolist()\n                        \n                        # 分析每種配方的表現\n                        tire_performance = {}\n                        for compound in compounds_used:\n                            compound_laps = driver_laps[driver_laps['Compound'] == compound]\n                            valid_times = compound_laps['LapTime'].dropna()\n                            \n                            if len(valid_times) > 0:\n                                tire_performance[compound] = {\n                                    'laps_used': len(compound_laps),\n                                    'average_lap_time': valid_times.dt.total_seconds().mean(),\n                                    'best_lap_time': valid_times.dt.total_seconds().min(),\n                                    'first_lap': int(compound_laps['LapNumber'].min()),\n                                    'last_lap': int(compound_laps['LapNumber'].max())\n                                }\n                        \n                        tire_data[driver] = {\n                            'tire_compounds_used': compounds_used,\n                            'tire_performance': tire_performance,\n                            'total_laps': len(driver_laps)\n                        }\n            \n            print(f\"✅ 成功獲取 {len(tire_data)} 位車手的輪胎配方數據\")\n            return tire_data\n            \n        except Exception as e:\n            print(f\"[ERROR] 獲取 FastF1 輪胎數據失敗: {e}\")\n            return {}\n    \n    def _integrate_pitstop_and_tire_data(self, pitstop_records: Dict, tire_data: Dict, session_info: Dict) -> Dict[str, Any]:\n        \"\"\"整合進站數據與輪胎數據\"\"\"\n        integrated_data = {}\n        \n        # 獲取所有車手列表\n        all_drivers = set(list(pitstop_records.keys()) + list(tire_data.keys()))\n        \n        print(f\"🔄 開始整合 {len(all_drivers)} 位車手的數據...\")\n        \n        for driver in all_drivers:\n            driver_pitstops = pitstop_records.get(driver, [])\n            driver_tires = tire_data.get(driver, {})\n            \n            # 基本輪胎配方信息\n            compounds_used = driver_tires.get('tire_compounds_used', [])\n            tire_performance = driver_tires.get('tire_performance', {})\n            \n            # 進站信息 (來自 OpenF1)\n            pit_stops = {\n                'total_pit_stops': len(driver_pitstops),\n                'pit_stop_details': []\n            }\n            \n            # 處理每個進站記錄\n            for i, stop in enumerate(driver_pitstops):\n                pit_detail = {\n                    'lap': stop.get('lap_number', 0),\n                    'pit_duration': stop.get('pit_duration', 0),\n                    'session_time': stop.get('session_time', 'Unknown')\n                }\n                \n                # 🔧 關鍵改進：根據進站圈數推斷輪胎更換\n                pit_lap = stop.get('lap_number', 0)\n                if pit_lap > 0:\n                    # 分析進站前後的輪胎配方變化\n                    tire_change = self._infer_tire_change_from_pitstop(pit_lap, tire_performance)\n                    if tire_change:\n                        pit_detail['from_compound'] = tire_change.get('from')\n                        pit_detail['to_compound'] = tire_change.get('to')\n                \n                pit_stops['pit_stop_details'].append(pit_detail)\n            \n            # 計算平均進站間隔\n            if len(driver_pitstops) > 0:\n                pit_laps = [stop.get('lap_number', 0) for stop in driver_pitstops]\n                if len(pit_laps) > 1:\n                    intervals = [pit_laps[i] - pit_laps[i-1] for i in range(1, len(pit_laps))]\n                    pit_stops['average_pit_window'] = sum(intervals) / len(intervals)\n            \n            # Stint 分析 (基於進站數據)\n            stint_analysis = self._analyze_stints_with_pitstops(driver_pitstops, tire_performance)\n            \n            # 輪胎衰退分析\n            tire_degradation = self._analyze_tire_degradation_enhanced(tire_performance, driver_pitstops)\n            \n            # 策略效果評估\n            strategy_effectiveness = self._evaluate_strategy_enhanced(compounds_used, driver_pitstops, tire_performance)\n            \n            # 整合所有數據\n            integrated_data[driver] = {\n                'tire_compounds_used': compounds_used,\n                'pit_stops': pit_stops,\n                'tire_performance': tire_performance,\n                'stint_analysis': stint_analysis,\n                'tire_degradation': tire_degradation,\n                'strategy_effectiveness': strategy_effectiveness\n            }\n        \n        print(f\"✅ 數據整合完成，共處理 {len(integrated_data)} 位車手\")\n        return integrated_data\n    \n    def _infer_tire_change_from_pitstop(self, pit_lap: int, tire_performance: Dict) -> Optional[Dict[str, str]]:\n        \"\"\"根據進站圈數推斷輪胎更換情況\"\"\"\n        try:\n            # 找到進站圈數前後的輪胎配方\n            compounds_by_lap = []\n            \n            for compound, perf_data in tire_performance.items():\n                first_lap = perf_data.get('first_lap', 0)\n                last_lap = perf_data.get('last_lap', 0)\n                \n                if first_lap <= pit_lap <= last_lap:\n                    compounds_by_lap.append({\n                        'compound': compound,\n                        'first_lap': first_lap,\n                        'last_lap': last_lap\n                    })\n            \n            # 按圈數排序\n            compounds_by_lap.sort(key=lambda x: x['first_lap'])\n            \n            # 找到進站前後的配方變化\n            for i in range(len(compounds_by_lap) - 1):\n                current = compounds_by_lap[i]\n                next_compound = compounds_by_lap[i + 1]\n                \n                # 如果進站圈數在兩個配方的交界處\n                if (current['last_lap'] <= pit_lap <= next_compound['first_lap'] + 2):  # 允許2圈誤差\n                    return {\n                        'from': current['compound'],\n                        'to': next_compound['compound']\n                    }\n            \n            return None\n            \n        except Exception as e:\n            print(f\"[DEBUG] 輪胎更換推斷失敗: {e}\")\n            return None\n    \n    def _analyze_stints_with_pitstops(self, pitstops: List[Dict], tire_performance: Dict) -> List[Dict[str, Any]]:\n        \"\"\"基於進站數據分析 stint\"\"\"\n        stints = []\n        \n        if not pitstops:\n            # 沒有進站，整場比賽是一個 stint\n            if tire_performance:\n                compound = list(tire_performance.keys())[0]\n                perf = tire_performance[compound]\n                stints.append({\n                    'stint_number': 1,\n                    'start_lap': perf.get('first_lap', 1),\n                    'end_lap': perf.get('last_lap', 1),\n                    'length': perf.get('laps_used', 1),\n                    'compound': compound,\n                    'average_lap_time': perf.get('average_lap_time', 0)\n                })\n            return stints\n        \n        # 有進站記錄，根據進站分析 stint\n        pit_laps = [stop.get('lap_number', 0) for stop in pitstops]\n        pit_laps.sort()\n        \n        # 第一個 stint (開始到第一次進站)\n        stint_num = 1\n        start_lap = 1\n        \n        for pit_lap in pit_laps:\n            # 找到這個 stint 使用的輪胎配方\n            stint_compound = None\n            stint_performance = None\n            \n            for compound, perf in tire_performance.items():\n                if perf.get('first_lap', 0) <= start_lap <= perf.get('last_lap', 0):\n                    stint_compound = compound\n                    stint_performance = perf\n                    break\n            \n            if stint_compound:\n                stints.append({\n                    'stint_number': stint_num,\n                    'start_lap': start_lap,\n                    'end_lap': pit_lap,\n                    'length': pit_lap - start_lap + 1,\n                    'compound': stint_compound,\n                    'average_lap_time': stint_performance.get('average_lap_time', 0)\n                })\n            \n            stint_num += 1\n            start_lap = pit_lap + 1\n        \n        # 最後一個 stint (最後進站到結束)\n        if tire_performance:\n            # 找到最後使用的配方\n            last_compounds = [(c, p) for c, p in tire_performance.items() \n                             if p.get('last_lap', 0) >= pit_laps[-1]]\n            \n            if last_compounds:\n                last_compound, last_perf = max(last_compounds, key=lambda x: x[1].get('last_lap', 0))\n                stints.append({\n                    'stint_number': stint_num,\n                    'start_lap': start_lap,\n                    'end_lap': last_perf.get('last_lap', start_lap),\n                    'length': last_perf.get('last_lap', start_lap) - start_lap + 1,\n                    'compound': last_compound,\n                    'average_lap_time': last_perf.get('average_lap_time', 0)\n                })\n        \n        return stints\n    \n    def _analyze_tire_degradation_enhanced(self, tire_performance: Dict, pitstops: List[Dict]) -> Dict[str, Any]:\n        \"\"\"增強版輪胎衰退分析\"\"\"\n        degradation = {}\n        \n        for compound, perf in tire_performance.items():\n            laps_used = perf.get('laps_used', 0)\n            avg_time = perf.get('average_lap_time', 0)\n            best_time = perf.get('best_lap_time', 0)\n            \n            if laps_used > 0 and avg_time > 0 and best_time > 0:\n                # 計算衰退程度\n                degradation_rate = (avg_time - best_time) / laps_used if laps_used > 0 else 0\n                \n                degradation[compound] = {\n                    'degradation_per_lap': degradation_rate,\n                    'total_degradation': avg_time - best_time,\n                    'degradation_percentage': ((avg_time - best_time) / best_time * 100) if best_time > 0 else 0,\n                    'laps_used': laps_used,\n                    'compound_longevity': 'High' if degradation_rate < 0.1 else 'Medium' if degradation_rate < 0.2 else 'Low'\n                }\n        \n        return degradation\n    \n    def _evaluate_strategy_enhanced(self, compounds: List[str], pitstops: List[Dict], tire_performance: Dict) -> Dict[str, Any]:\n        \"\"\"增強版策略效果評估\"\"\"\n        effectiveness = {\n            'pit_stop_efficiency': 'N/A',\n            'tire_strategy_diversity': len(compounds),\n            'compound_utilization': {},\n            'strategy_complexity': 'Single-stop' if len(pitstops) <= 1 else f'{len(pitstops)}-stop'\n        }\n        \n        # 進站效率評估\n        if pitstops:\n            pit_times = [stop.get('pit_duration', 0) for stop in pitstops if stop.get('pit_duration', 0) > 0]\n            if pit_times:\n                avg_pit_time = sum(pit_times) / len(pit_times)\n                \n                if avg_pit_time < 3.0:\n                    effectiveness['pit_stop_efficiency'] = 'Excellent'\n                elif avg_pit_time < 4.0:\n                    effectiveness['pit_stop_efficiency'] = 'Good'\n                elif avg_pit_time < 5.0:\n                    effectiveness['pit_stop_efficiency'] = 'Average'\n                else:\n                    effectiveness['pit_stop_efficiency'] = 'Poor'\n        \n        # 配方利用率\n        total_laps = sum(perf.get('laps_used', 0) for perf in tire_performance.values())\n        for compound, perf in tire_performance.items():\n            laps_used = perf.get('laps_used', 0)\n            utilization_rate = (laps_used / total_laps * 100) if total_laps > 0 else 0\n            effectiveness['compound_utilization'][compound] = f\"{utilization_rate:.1f}%\"\n        \n        return effectiveness\n    \n    def _display_enhanced_tire_strategy_summary(self, result: Dict[str, Any]):\n        \"\"\"顯示增強版輪胎策略分析摘要\"\"\"\n        if not result.get('success'):\n            print(f\"❌ 分析失敗: {result.get('error', '未知錯誤')}\")\n            return\n        \n        drivers_data = result.get('all_drivers_tire_strategy', {})\n        drivers_count = len(drivers_data)\n        \n        print(f\"\\n🛞 全部車手輪胎策略分析結果 (OpenF1 進站數據整合版)\")\n        print(\"=\" * 100)\n        \n        print(f\"📊 分析概況:\")\n        print(f\"   • 賽事: {result.get('year')} 年 {result.get('race')} {result.get('session')}\")\n        print(f\"   • 車手數量: {drivers_count}\")\n        print(f\"   • 數據來源: {result.get('data_sources', {}).get('pitstop_data', 'Unknown')} + {result.get('data_sources', {}).get('tire_compounds', 'Unknown')}\")\n        \n        # 統計摘要\n        total_pitstops = sum(len(data.get('pit_stops', {}).get('pit_stop_details', [])) for data in drivers_data.values())\n        compounds_used = set()\n        for data in drivers_data.values():\n            compounds_used.update(data.get('tire_compounds_used', []))\n        \n        print(f\"\\n📈 統計摘要:\")\n        print(f\"   • 總進站次數: {total_pitstops}\")\n        print(f\"   • 使用的輪胎配方: {', '.join(sorted(compounds_used))}\")\n        print(f\"   • 平均每車手進站: {total_pitstops/drivers_count:.1f} 次\" if drivers_count > 0 else \"\")\n        \n        # 顯示前10位車手的詳細信息\n        print(f\"\\n🏎️ 車手輪胎策略詳情 (前10位):\")\n        \n        strategy_table = PrettyTable()\n        strategy_table.field_names = [\"車手\", \"配方\", \"進站次數\", \"策略\", \"效率\"]\n        strategy_table.align[\"車手\"] = \"l\"\n        \n        for i, (driver, data) in enumerate(list(drivers_data.items())[:10], 1):\n            compounds = ' + '.join(data.get('tire_compounds_used', []))\n            pit_stops = data.get('pit_stops', {}).get('total_pit_stops', 0)\n            strategy = data.get('strategy_effectiveness', {}).get('strategy_complexity', 'Unknown')\n            efficiency = data.get('strategy_effectiveness', {}).get('pit_stop_efficiency', 'N/A')\n            \n            strategy_table.add_row([\n                driver,\n                compounds[:20],  # 限制長度\n                pit_stops,\n                strategy,\n                efficiency\n            ])\n        \n        print(strategy_table)\n        \n        print(f\"\\n💾 完整數據已保存至 JSON 檔案\")\n        print(f\"🔧 數據整合方法: OpenF1 進站時間 + FastF1 輪胎配方 + 智能關聯分析\")\n        print(\"✅ 增強版輪胎策略分析完成！\")\n\n\ndef run_enhanced_all_drivers_tire_strategy(data_loader, **kwargs):\n    \"\"\"執行增強版全部車手輪胎策略分析的入口函數\"\"\"\n    analyzer = EnhancedAllDriversTireStrategy(data_loader)\n    return analyzer.analyze_all_drivers_tire_strategy(**kwargs)\n\n\nif __name__ == \"__main__\":\n    # 測試用途\n    print(\"增強版全部車手輪胎策略分析模組\")\n    print(\"整合 OpenF1 進站數據與 FastF1 輪胎配方數據\")\n
