#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
單一車手比賽位置分析模組
提供車手在比賽中的位置變化分析
"""

import os
import json
import pickle
from datetime import datetime
from typing import Dict, Any, Optional
from prettytable import PrettyTable

class SingleDriverPositionAnalysis:
    """單一車手比賽位置分析器"""
    
    def __init__(self, data_loader, year: int, race: str, session: str):
        self.data_loader = data_loader
        self.year = year
        self.race = race
        self.session = session
        self.cache_dir = "cache"
        
        # 確保緩存目錄存在
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def analyze_position_changes(self, driver: str, **kwargs) -> Dict[str, Any]:
        """分析車手位置變化
        
        Args:
            driver: 車手代碼 (如 'VER', 'LEC')
            
        Returns:
            Dict: 包含位置分析結果的字典
        """
        print(f"🏁 開始分析車手 {driver} 的比賽位置變化...")
        
        try:
            # 生成緩存鍵
            cache_key = f"position_analysis_{self.year}_{self.race}_{self.session}_{driver}"
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            
            # 檢查緩存
            if os.path.exists(cache_file):
                print("📦 從緩存載入位置分析數據...")
                with open(cache_file, 'rb') as f:
                    cached_result = pickle.load(f)
                
                # 顯示對應的 JSON 檔案路徑
                json_file = cache_file.replace('.pkl', '.json')
                if os.path.exists(json_file):
                    print(f"📄 對應 JSON 檔案: {json_file}")
                
                # 顯示位置變化表格
                self._display_position_analysis_table(cached_result, driver)
                
                print("✅ 位置分析完成 (使用緩存)")
                return cached_result
            
            # 載入賽事數據
            session_data = self.data_loader.get_loaded_data()
            
            if session_data is None:
                raise ValueError("無法載入賽事數據")
            
            # 從數據字典中獲取圈速數據
            if isinstance(session_data, dict):
                laps_data = session_data.get('laps')
                if laps_data is None:
                    raise ValueError("無法找到圈速數據")
            else:
                laps_data = getattr(session_data, 'laps', None)
                if laps_data is None:
                    raise ValueError("無法找到圈速數據")
            
            # 獲取車手數據
            driver_data = laps_data.pick_driver(driver)
            
            if driver_data.empty:
                raise ValueError(f"找不到車手 {driver} 的數據")
            
            # 分析位置變化
            result = {
                "success": True,
                "driver": driver,
                "year": self.year,
                "race": self.race,
                "session": self.session,
                "analysis_timestamp": datetime.now().isoformat(),
                "position_analysis": {
                    "starting_position": self._get_starting_position(driver_data),
                    "finishing_position": self._get_finishing_position(driver_data),
                    "position_changes": self._analyze_position_changes(driver_data),
                    "best_position": self._get_best_position(driver_data),
                    "worst_position": self._get_worst_position(driver_data),
                    "total_laps": len(driver_data),
                    "position_statistics": self._calculate_position_statistics(driver_data)
                }
            }
            
            # 保存到緩存
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            
            # 同時保存為 JSON
            json_file = cache_file.replace('.pkl', '.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"💾 JSON 分析結果已保存: {json_file}")
            
            # 顯示位置變化表格
            self._display_position_analysis_table(result, driver)
            
            print("✅ 車手比賽位置分析完成")
            return result
            
        except Exception as e:
            print(f"❌ 位置分析失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "driver": driver,
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def _get_starting_position(self, driver_data) -> Optional[int]:
        """獲取起始位置"""
        try:
            if not driver_data.empty:
                return int(driver_data.iloc[0]['Position'])
        except:
            pass
        return None
    
    def _get_finishing_position(self, driver_data) -> Optional[int]:
        """獲取完賽位置"""
        try:
            if not driver_data.empty:
                return int(driver_data.iloc[-1]['Position'])
        except:
            pass
        return None
    
    def _get_best_position(self, driver_data) -> Optional[int]:
        """獲取最佳位置"""
        try:
            if not driver_data.empty:
                return int(driver_data['Position'].min())
        except:
            pass
        return None
    
    def _get_worst_position(self, driver_data) -> Optional[int]:
        """獲取最差位置"""
        try:
            if not driver_data.empty:
                return int(driver_data['Position'].max())
        except:
            pass
        return None
    
    def _analyze_position_changes(self, driver_data) -> Dict[str, Any]:
        """分析位置變化詳細"""
        try:
            positions = driver_data['Position'].tolist()
            changes = []
            
            for i in range(1, len(positions)):
                change = positions[i-1] - positions[i]  # 正數為進步，負數為退步
                changes.append({
                    "lap": i + 1,
                    "from_position": positions[i-1],
                    "to_position": positions[i],
                    "change": change
                })
            
            return {
                "lap_by_lap_changes": changes,
                "total_changes": len([c for c in changes if c['change'] != 0]),
                "positions_gained": sum([c['change'] for c in changes if c['change'] > 0]),
                "positions_lost": abs(sum([c['change'] for c in changes if c['change'] < 0]))
            }
        except:
            return {"error": "無法分析位置變化"}
    
    def _calculate_position_statistics(self, driver_data) -> Dict[str, Any]:
        """計算位置統計"""
        try:
            positions = driver_data['Position']
            return {
                "average_position": float(positions.mean()),
                "median_position": float(positions.median()),
                "position_variance": float(positions.var()),
                "time_in_top_5": len(positions[positions <= 5]),
                "time_in_top_10": len(positions[positions <= 10]),
                "time_in_points": len(positions[positions <= 10])  # 前10名得分
            }
        except:
            return {"error": "無法計算位置統計"}
    
    def _display_position_analysis_table(self, result: Dict[str, Any], driver: str):
        """顯示位置分析結果表格"""
        try:
            position_data = result.get('position_analysis', {})
            
            print(f"\n🏁 車手 {driver} 比賽位置分析結果")
            print("=" * 80)
            
            # 基本位置信息表格
            basic_table = PrettyTable()
            basic_table.field_names = ["項目", "位置", "說明"]
            basic_table.align["項目"] = "l"
            basic_table.align["說明"] = "l"
            
            start_pos = position_data.get('starting_position', 'N/A')
            finish_pos = position_data.get('finishing_position', 'N/A')
            best_pos = position_data.get('best_position', 'N/A')
            worst_pos = position_data.get('worst_position', 'N/A')
            total_laps = position_data.get('total_laps', 0)
            
            basic_table.add_row(["起始位置", start_pos, "比賽開始時的位置"])
            basic_table.add_row(["完賽位置", finish_pos, "比賽結束時的位置"])
            basic_table.add_row(["最佳位置", best_pos, "比賽中達到的最高位置"])
            basic_table.add_row(["最差位置", worst_pos, "比賽中的最低位置"])
            basic_table.add_row(["總圈數", total_laps, "完成的總圈數"])
            
            if start_pos != 'N/A' and finish_pos != 'N/A':
                position_change = start_pos - finish_pos
                change_desc = f"進步 {position_change} 位" if position_change > 0 else f"退步 {abs(position_change)} 位" if position_change < 0 else "位置無變化"
                basic_table.add_row(["總位置變化", f"{position_change:+d}", change_desc])
            
            print("\n📊 基本位置統計:")
            print(basic_table)
            
            # 位置變化詳細表格 (顯示前 20 圈的變化)
            position_changes = position_data.get('position_changes', {})
            lap_changes = position_changes.get('lap_by_lap_changes', [])
            
            if lap_changes:
                change_table = PrettyTable()
                change_table.field_names = ["圈數", "從位置", "到位置", "變化", "說明"]
                change_table.align["說明"] = "l"
                
                # 只顯示前 20 圈或有變化的圈數
                display_changes = [c for c in lap_changes[:20] if c.get('change', 0) != 0][:15]
                
                for change in display_changes:
                    lap_num = change.get('lap', 0)
                    from_pos = change.get('from_position', 0)
                    to_pos = change.get('to_position', 0)
                    pos_change = change.get('change', 0)
                    
                    if pos_change > 0:
                        change_desc = f"超越 {pos_change} 位"
                        change_str = f"+{pos_change}"
                    elif pos_change < 0:
                        change_desc = f"被超 {abs(pos_change)} 位"
                        change_str = str(pos_change)
                    else:
                        change_desc = "位置保持"
                        change_str = "0"
                    
                    change_table.add_row([lap_num, from_pos, to_pos, change_str, change_desc])
                
                if display_changes:
                    print(f"\n📈 位置變化詳細 (顯示前 {len(display_changes)} 個變化):")
                    print(change_table)
                else:
                    print("\n📈 位置變化: 比賽中位置保持穩定，無重大位置變化")
            
            # 位置統計摘要
            stats = position_data.get('position_statistics', {})
            if stats and not stats.get('error'):
                stats_table = PrettyTable()
                stats_table.field_names = ["統計項目", "數值", "說明"]
                stats_table.align["統計項目"] = "l"
                stats_table.align["說明"] = "l"
                
                avg_pos = stats.get('average_position', 0)
                median_pos = stats.get('median_position', 0)
                top5_time = stats.get('time_in_top_5', 0)
                top10_time = stats.get('time_in_top_10', 0)
                points_time = stats.get('time_in_points', 0)
                
                stats_table.add_row(["平均位置", f"{avg_pos:.1f}", "整場比賽的平均位置"])
                stats_table.add_row(["中位數位置", f"{median_pos:.1f}", "位置分布的中位數"])
                stats_table.add_row(["前5位圈數", f"{top5_time} 圈", f"在前5位的圈數 ({top5_time/total_laps*100:.1f}%)" if total_laps > 0 else "在前5位的圈數"])
                stats_table.add_row(["前10位圈數", f"{top10_time} 圈", f"在前10位的圈數 ({top10_time/total_laps*100:.1f}%)" if total_laps > 0 else "在前10位的圈數"])
                stats_table.add_row(["得分區圈數", f"{points_time} 圈", f"在得分區的圈數 ({points_time/total_laps*100:.1f}%)" if total_laps > 0 else "在得分區的圈數"])
                
                print(f"\n📊 位置統計摘要:")
                print(stats_table)
            
            # 位置變化總結
            if position_changes:
                total_changes = position_changes.get('total_changes', 0)
                positions_gained = position_changes.get('positions_gained', 0)
                positions_lost = position_changes.get('positions_lost', 0)
                
                print(f"\n📋 位置變化總結:")
                print(f"   • 總位置變化次數: {total_changes} 次")
                print(f"   • 累積進步位置: {positions_gained} 位")
                print(f"   • 累積退步位置: {positions_lost} 位")
                print(f"   • 淨位置變化: {int(positions_gained - positions_lost):+d} 位")
            
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ 顯示位置分析表格失敗: {e}")
            # 顯示基本信息作為備用
            print(f"\n🏁 車手 {driver} 比賽位置分析結果 (簡化版)")
            print(f"分析時間: {result.get('analysis_timestamp', 'Unknown')}")
            print(f"分析狀態: {'成功' if result.get('success') else '失敗'}")
