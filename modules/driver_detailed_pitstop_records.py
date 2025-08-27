#!/usr/bin/env python3
"""
F1 車手進站詳細記錄模組 (功能5)
Driver Detailed Pitstop Records Module

顯示每位車手的第一次進站時間/圈數、第二次進站時間/圈數等詳細記錄
優先使用 OpenF1 API 獲取準確的進站時間數據
符合 copilot-instructions 開發核心要求

版本: 1.0
作者: F1 Analysis Team
"""

import os
import pickle
import json
from datetime import datetime
from prettytable import PrettyTable

# 導入 OpenF1 分析器
try:
    from .openf1_data_analyzer import F1OpenDataAnalyzer
except ImportError:
    try:
        from openf1_data_analyzer import F1OpenDataAnalyzer
    except ImportError:
        print("[WARNING] 無法導入 OpenF1 數據分析器")
        F1OpenDataAnalyzer = None


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


def report_analysis_results(data, analysis_type="analysis"):
    """報告分析結果狀態"""
    if not data:
        print(f"❌ {analysis_type}失敗：無可用數據")
        return False
    
    driver_count = len(data) if isinstance(data, dict) else 0
    total_stops = sum(len(stops) for stops in data.values()) if isinstance(data, dict) else 0
    
    print(f"📊 {analysis_type}結果摘要：")
    print(f"   • 車手數量: {driver_count}")
    print(f"   • 總進站次數: {total_stops}")
    print(f"   • 數據完整性: {'✅ 良好' if driver_count > 0 else '❌ 不足'}")
    
    if driver_count > 0:
        max_stops = max(len(stops) for stops in data.values())
        print(f"   • 最多進站次數: {max_stops}")
    
    print(f"✅ {analysis_type}分析完成！")
    return True


def run_driver_detailed_pitstop_records(data_loader, show_detailed_output=True):
    """執行車手進站詳細記錄分析 - 功能5 (Function 15 標準)
    
    Args:
        data_loader: 數據載入器
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
    
    Returns:
        dict: 包含成功狀態、數據、緩存狀態和緩存鍵的標準化返回格式
    """
    print("🚀 開始執行車手進站詳細記錄分析...")
    print("📋 車手進站詳細記錄 (功能5)")
    print("=" * 60)
    
    try:
        # 獲取基本賽事資訊
        session_info = get_session_info(data_loader)
        cache_key = f"driver_detailed_pitstops_{session_info.get('year')}_{session_info.get('event_name', 'Unknown').replace(' ', '_')}"
        
        # 檢查緩存 - Function 15 標準實現
        cached_data = check_cache(cache_key)
        cache_used = cached_data is not None
        
        if cached_data and not show_detailed_output:
            print("📦 使用緩存數據")
            detailed_records = cached_data
            
            # 結果驗證和反饋
            if not report_analysis_results(detailed_records, "車手進站詳細記錄"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "5"}
            
            print("\n✅ 車手進站詳細記錄分析完成！")
            return {
                "success": True,
                "data": detailed_records,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "5"
            }
            
        elif cached_data and show_detailed_output:
            print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
            detailed_records = cached_data
            
            # 結果驗證和反饋
            if not report_analysis_results(detailed_records, "車手進站詳細記錄"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "5"}
                
            # 顯示詳細輸出 - 即使使用緩存
            _display_cached_detailed_output(detailed_records, session_info)
            
            print("\n✅ 車手進站詳細記錄分析完成！")
            return {
                "success": True,
                "data": detailed_records,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "5"
            }
        else:
            print("🔄 重新計算 - 開始數據分析...")
            detailed_records = analyze_driver_detailed_pitstops(data_loader, session_info)
            
            if not detailed_records:
                print("❌ 車手進站詳細記錄分析失敗：無可用數據")
                return {"success": False, "message": "無可用數據", "function_id": "5"}
            
            # 保存緩存
            save_cache(detailed_records, cache_key)
            print("💾 分析結果已緩存")
            
            # 結果驗證和反饋
            if not report_analysis_results(detailed_records, "車手進站詳細記錄"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "5"}
            
            # 顯示詳細記錄表格
            display_detailed_pitstop_records(detailed_records)
            
            # 保存 JSON 結果
            save_json_results(detailed_records, session_info, "driver_detailed_pitstop_records")
            
            print("\n✅ 車手進站詳細記錄分析完成！")
            return {
                "success": True,
                "data": detailed_records,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "5"
            }
        
    except Exception as e:
        print(f"❌ 車手進站詳細記錄分析失敗: {e}")
        return {"success": False, "message": f"分析失敗: {str(e)}", "function_id": "5"}


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


def analyze_driver_detailed_pitstops(data_loader, session_info):
    """分析車手進站詳細記錄數據"""
    if F1OpenDataAnalyzer is None:
        print("[ERROR] OpenF1 數據分析器未可用")
        return None
    
    try:
        # 創建 OpenF1 分析器
        openf1_analyzer = F1OpenDataAnalyzer()
        
        # 根據年份和比賽名稱找到對應的 session_key
        race_session = openf1_analyzer.find_race_session_by_name(
            session_info.get('year'), session_info.get('event_name')
        )
        
        if not race_session:
            print("[ERROR] 無法找到對應的比賽會話")
            return None
        
        session_key = race_session.get('session_key')
        print(f"📡 從 OpenF1 API 獲取進站數據 (session_key: {session_key})...")
        
        # 獲取 OpenF1 進站數據
        enhanced_pitstops = openf1_analyzer.get_enhanced_pit_stops(session_key)
        
        if not enhanced_pitstops:
            print("[ERROR] OpenF1 API 未返回進站數據")
            return None
        
        print(f"[SUCCESS] 成功獲取 {len(enhanced_pitstops)} 個進站記錄")
        
        # 按車手組織進站記錄
        driver_records = {}
        
        for stop in enhanced_pitstops:
            # 正確提取車手和車隊信息 (從 driver_info 字段中)
            driver_info = stop.get('driver_info', {})
            driver = driver_info.get('name_acronym', 'UNK')
            team = driver_info.get('team_name', 'Unknown Team')
            pit_duration = stop.get('pit_duration')
            
            # 只處理有效的進站時間（通常在 15-60 秒之間，過濾掉無效的巨大數值）
            # 同時排除第1圈的起始位置數據
            lap_number = stop.get('lap_number', 0)
            if pit_duration is not None and 15.0 <= pit_duration <= 60.0 and lap_number > 1:
                if driver not in driver_records:
                    driver_records[driver] = []
                
                stop_record = {
                    'pitstop_number': len(driver_records[driver]) + 1,
                    'lap_number': lap_number,
                    'pit_duration': float(pit_duration),
                    'session_time': stop.get('session_time', 'Unknown'),
                    'team': team
                }
                driver_records[driver].append(stop_record)
        
        # 按圈數排序每位車手的進站記錄
        for driver in driver_records:
            driver_records[driver].sort(key=lambda x: x['lap_number'])
            # 重新編號進站次數
            for i, stop in enumerate(driver_records[driver]):
                stop['pitstop_number'] = i + 1
        
        return driver_records
        
    except Exception as e:
        print(f"[ERROR] 車手進站詳細記錄分析失敗: {e}")
        return None


def display_detailed_pitstop_records(driver_records):
    """顯示車手進站詳細記錄表格"""
    if not driver_records:
        print("[ERROR] 沒有進站記錄數據可顯示")
        return
    
    print(f"\n📋 車手進站詳細記錄:")
    
    # 方式1: 按車手分組顯示詳細記錄
    for driver in sorted(driver_records.keys()):
        stops = driver_records[driver]
        if not stops:
            continue
            
        print(f"\n🏎️ {driver} ({stops[0]['team']}) - 共 {len(stops)} 次進站:")
        
        # 車手的進站詳細表格
        driver_table = PrettyTable()
        driver_table.field_names = ["進站次數", "圈數", "進站時間", "備註"]
        
        for i, stop in enumerate(stops, 1):
            driver_table.add_row([
                f"第{i}次",
                stop['lap_number'],
                f"{stop['pit_duration']:.1f}秒",
                "正常進站" if 20 <= stop['pit_duration'] <= 30 else "異常時間"
            ])
        
        print(driver_table)
    
    # 方式2: 匯總表格顯示
    print(f"\n📊 車手進站匯總表格:")
    summary_table = PrettyTable()
    summary_table.field_names = ["車手", "車隊", "總進站次數", "最快時間", "平均時間", "進站圈數列表"]
    
    for driver in sorted(driver_records.keys()):
        stops = driver_records[driver]
        if not stops:
            continue
            
        times = [stop['pit_duration'] for stop in stops]
        laps = [stop['lap_number'] for stop in stops]
        
        summary_table.add_row([
            driver,
            stops[0]['team'][:15],
            len(stops),
            f"{min(times):.1f}秒",
            f"{sum(times)/len(times):.1f}秒",
            ", ".join(map(str, laps))
        ])
    
    print(summary_table)
    
    # 顯示進站策略統計
    print(f"\n🔧 進站策略統計:")
    strategy_stats = {}
    for driver, stops in driver_records.items():
        stop_count = len(stops)
        if stop_count not in strategy_stats:
            strategy_stats[stop_count] = []
        strategy_stats[stop_count].append(driver)
    
    strategy_table = PrettyTable()
    strategy_table.field_names = ["策略", "車手數", "車手列表"]
    
    for stop_count in sorted(strategy_stats.keys()):
        drivers = strategy_stats[stop_count]
        strategy_table.add_row([
            f"{stop_count}停",
            len(drivers),
            ", ".join(drivers[:5]) + (f"... (+{len(drivers)-5})" if len(drivers) > 5 else "")
        ])
    
    print(strategy_table)


def display_json_preview(driver_records):
    """顯示進站記錄前20筆資料預覽"""
    print(f"\n📋 JSON 資料預覽 (前 20 筆詳細進站記錄)：")
    
    # 將所有進站記錄平坦化並排序
    all_records = []
    for driver, stops in driver_records.items():
        for stop in stops:
            record = {
                "車手": driver,
                "車隊": stop['team'],
                "進站次數": f"第{stop['pitstop_number']}次",
                "圈數": stop['lap_number'],
                "時間": f"{stop['pit_duration']:.1f}秒",
                "賽段時間": stop['session_time']
            }
            all_records.append(record)
    
    # 按圈數排序
    all_records.sort(key=lambda x: x['圈數'])
    
    # 顯示前20筆
    preview_table = PrettyTable()
    preview_table.field_names = ["#", "車手", "車隊", "進站次數", "圈數", "時間"]
    
    for i, record in enumerate(all_records[:20], 1):
        preview_table.add_row([
            i,
            record["車手"],
            record["車隊"],
            record["進站次數"],
            record["圈數"],
            record["時間"]
        ])
    
    print(preview_table)
    
    print(f"\n📊 JSON 資料統計摘要：")
    print(f"   • 總進站記錄數量: {len(all_records)}")
    print(f"   • 顯示預覽數量: {min(20, len(all_records))}")
    print(f"   • 剩餘資料: {max(0, len(all_records) - 20)} 筆 (已儲存至JSON檔案)")


def save_json_results(driver_records, session_info, analysis_type):
    """保存 JSON 結果"""
    json_dir = "json"
    os.makedirs(json_dir, exist_ok=True)
    
    result_data = {
        "function_id": 5,
        "function_name": "Driver Detailed Pitstop Records",
        "analysis_type": analysis_type,
        "session_info": session_info,
        "timestamp": datetime.now().isoformat(),
        "data": driver_records
    }
    
    filename = f"{analysis_type}_{session_info.get('year')}_{session_info.get('event_name', 'Unknown').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(json_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON結果已保存到: file:///{os.path.abspath(filepath)}")
    except Exception as e:
        print(f"[WARNING] JSON保存失敗: {e}")


def _display_cached_detailed_output(driver_records, session_info):
    """顯示緩存數據的詳細輸出 - Function 15 標準
    
    Args:
        driver_records: 車手進站詳細記錄數據 (dict格式)
        session_info: 賽事基本信息
    """
    print("\n📊 詳細車手進站記錄 (緩存數據)")
    print("=" * 80)
    
    if not isinstance(driver_records, dict):
        print("❌ 數據格式錯誤：期望 dict 格式")
        return
    
    total_drivers = len(driver_records)
    print(f"🏆 總車手數量: {total_drivers}")
    
    # 統計分析
    total_pitstops = sum(len(stops) for stops in driver_records.values())
    drivers_with_pitstops = sum(1 for stops in driver_records.values() if stops)
    
    print(f"📋 總進站次數: {total_pitstops}")
    print(f"👨‍🏎️ 有進站記錄的車手數: {drivers_with_pitstops}")
    
    if drivers_with_pitstops > 0:
        avg_pitstops_per_driver = total_pitstops / drivers_with_pitstops
        print(f"📊 平均每車手進站次數: {avg_pitstops_per_driver:.1f}")
    
    # 詳細記錄表格
    detailed_table = PrettyTable()
    detailed_table.field_names = [
        "車手", "車隊", "總進站次數", "最快時間", "平均時間", 
        "最慢時間", "時間差", "表現評級"
    ]
    
    # 處理前15位車手
    driver_list = list(driver_records.items())[:15]
    for driver, stops in driver_list:
        if stops:
            times = [stop.get('pit_duration', 0) for stop in stops if stop.get('pit_duration')]
            if times:
                fastest = min(times)
                slowest = max(times)
                average = sum(times) / len(times)
                time_diff = slowest - fastest
                
                # 表現評級
                if time_diff <= 2.0:
                    performance = "穩定"
                elif time_diff <= 4.0:
                    performance = "一般"
                else:
                    performance = "不穩定"
                
                team = stops[0].get('team', 'Unknown') if stops else 'Unknown'
                    
                detailed_table.add_row([
                    driver[:10],
                    team[:10],
                    len(stops),
                    f"{fastest:.2f}秒",
                    f"{average:.2f}秒",
                    f"{slowest:.2f}秒",
                    f"{time_diff:.2f}秒",
                    performance
                ])
            else:
                team = stops[0].get('team', 'Unknown') if stops else 'Unknown'
                detailed_table.add_row([
                    driver[:10],
                    team[:10],
                    len(stops),
                    "無數據", "無數據", "無數據", "無數據", "無法評估"
                ])
        else:
            detailed_table.add_row([
                driver[:10],
                "Unknown",
                0,
                "無進站", "無進站", "無進站", "無進站", "無進站"
            ])
    
    print(detailed_table)
    
    # 統計摘要
    print("\n📈 統計摘要:")
    all_times = []
    for driver, stops in driver_records.items():
        for stop in stops:
            if stop.get('pit_duration'):
                all_times.append(stop['pit_duration'])
    
    if all_times:
        print(f"   • 最快進站時間: {min(all_times):.2f}秒")
        print(f"   • 最慢進站時間: {max(all_times):.2f}秒") 
        print(f"   • 平均進站時間: {sum(all_times)/len(all_times):.2f}秒")
        print(f"   • 時間範圍: {max(all_times) - min(all_times):.2f}秒")
    
    print("\n💾 數據來源: 緩存檔案")
    print(f"📅 賽事: {session_info.get('year', 'Unknown')} {session_info.get('event_name', 'Unknown')}")
    print(f"🏁 賽段: {session_info.get('session', 'Unknown')}")
    print("✅ 緩存數據詳細輸出完成")


if __name__ == "__main__":
    print("車手進站詳細記錄模組 - 獨立測試模式")
