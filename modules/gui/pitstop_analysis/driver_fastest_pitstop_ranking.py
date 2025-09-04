#!/usr/bin/env python3
"""
F1 車手最快進站時間排行榜模組 (功能3)
Driver Fastest Pitstop Ranking Module

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


def format_time(time_obj):
    """標準時間格式化函數 - 禁止包含 day 或 days"""
    if isinstance(time_obj, (int, float)):
        return f"{time_obj:.1f}秒"
    return str(time_obj)


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
    
    data_count = len(data) if isinstance(data, list) else 0
    print(f"📊 {analysis_type}結果摘要：")
    print(f"   • 車手數量: {data_count}")
    print(f"   • 數據完整性: {'✅ 良好' if data_count > 0 else '❌ 不足'}")
    
    if data_count > 0:
        fastest_time = min(item['fastest_time'] for item in data)
        slowest_time = max(item['fastest_time'] for item in data)
        print(f"   • 最快進站時間: {fastest_time:.1f}秒")
        print(f"   • 最慢進站時間: {slowest_time:.1f}秒")
    
    print(f"✅ {analysis_type}分析完成！")
    return True


def run_driver_fastest_pitstop_ranking(data_loader, show_detailed_output=True):
    """執行車手最快進站時間排行榜分析 - 功能3
    
    Args:
        data_loader: 數據載入器
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
    """
    print("🚀 開始執行車手最快進站時間排行榜分析...")
    print("🏆 車手最快進站時間排行榜 (功能3)")
    print("=" * 60)
    
    try:
        # 獲取基本賽事資訊
        session_info = get_session_info(data_loader)
        cache_key = f"driver_fastest_pitstop_{session_info.get('year')}_{session_info.get('event_name', 'Unknown').replace(' ', '_')}"
        
        # 檢查緩存 - Function 15 標準實現
        cached_data = check_cache(cache_key)
        cache_used = cached_data is not None
        
        if cached_data and not show_detailed_output:
            print("📦 使用緩存數據")
            ranking_data = cached_data
            
            # 結果驗證和反饋
            if not report_analysis_results(ranking_data, "車手最快進站排行榜"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "3"}
            
            print("\n✅ 車手最快進站時間排行榜分析完成！")
            return {
                "success": True,
                "data": ranking_data,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "3"
            }
            
        elif cached_data and show_detailed_output:
            print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
            ranking_data = cached_data
            
            # 結果驗證和反饋
            if not report_analysis_results(ranking_data, "車手最快進站排行榜"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "3"}
                
            # 顯示詳細輸出 - 即使使用緩存
            _display_cached_detailed_output(ranking_data, session_info)
            
            print("\n✅ 車手最快進站時間排行榜分析完成！")
            return {
                "success": True,
                "data": ranking_data,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "3"
            }
        else:
            print("🔄 重新計算 - 開始數據分析...")
            ranking_data = analyze_driver_fastest_pitstops(data_loader, session_info)
            
            if not ranking_data:
                print("❌ 車手最快進站排行榜分析失敗：無可用數據")
                return {"success": False, "message": "無可用數據", "function_id": "3"}
            
            # 保存緩存
            save_cache(ranking_data, cache_key)
            print("💾 分析結果已緩存")
            
            # 結果驗證和反饋
            if not report_analysis_results(ranking_data, "車手最快進站排行榜"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "3"}
            
            # 顯示排行榜
            display_driver_ranking_table(ranking_data)
            
            # 保存 JSON 結果
            save_json_results(ranking_data, session_info, "driver_fastest_pitstop_ranking")
            
            print("\n✅ 車手最快進站時間排行榜分析完成！")
            return {
                "success": True,
                "data": ranking_data,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "3"
            }
        return {
            "success": True,
            "data": ranking_data,
            "cache_used": cache_used,
            "cache_key": cache_key,
            "function_id": "3"
        }
        
    except Exception as e:
        print(f"❌ 車手最快進站排行榜分析失敗: {e}")
        return None


def get_session_info(data_loader):
    """獲取賽事基本信息"""
    session_info = {}
    if hasattr(data_loader, 'session') and data_loader.session is not None:
        # 優先從 data_loader 的屬性獲取年份，因為它是在載入數據時設置的正確年份
        year = getattr(data_loader, 'year', None)
        if year is None:
            # 如果 data_loader 沒有年份屬性，嘗試從 session 獲取
            year = getattr(data_loader.session, 'event', {}).get('year', 2024)
        
        session_info = {
            "event_name": getattr(data_loader.session, 'event', {}).get('EventName', 'Unknown'),
            "circuit_name": getattr(data_loader.session, 'event', {}).get('Location', 'Unknown'),
            "session_type": getattr(data_loader.session, 'session_info', {}).get('Type', 'Unknown'),
            "year": year
        }
    return session_info


def analyze_driver_fastest_pitstops(data_loader, session_info):
    """分析車手最快進站時間數據"""
    if F1OpenDataAnalyzer is None:
        print("[ERROR] OpenF1 數據分析器未可用")
        return None
    
    try:
        # 創建 OpenF1 分析器
        openf1_analyzer = F1OpenDataAnalyzer()
        
        # 賽事名稱映射 - 解決FastF1和OpenF1命名不一致問題
        event_name = session_info.get('event_name', 'Unknown')
        race_name_mapping = {
            'British Grand Prix': 'britain',
            'Japanese Grand Prix': 'japan', 
            'Australian Grand Prix': 'australia',
            'Chinese Grand Prix': 'china',  # 添加中國大獎賽映射
            'Monaco Grand Prix': 'monaco',
            'Spanish Grand Prix': 'spain',
            'Canadian Grand Prix': 'canada',
            'Austrian Grand Prix': 'austria',
            'French Grand Prix': 'france',
            'Hungarian Grand Prix': 'hungary',
            'Belgian Grand Prix': 'belgium',
            'Italian Grand Prix': 'italy',
            'Singapore Grand Prix': 'singapore',
            'Russian Grand Prix': 'russia',
            'Turkish Grand Prix': 'turkey',
            'United States Grand Prix': 'usa',
            'Mexican Grand Prix': 'mexico',
            'Brazilian Grand Prix': 'brazil',
            'Abu Dhabi Grand Prix': 'abu dhabi',
            'Bahrain Grand Prix': 'bahrain',
            'Saudi Arabian Grand Prix': 'saudi arabia'
        }
        
        # 標準化賽事名稱
        search_name = race_name_mapping.get(event_name, event_name.lower())
        print(f"🔍 搜尋賽事會話: '{event_name}' -> '{search_name}'")
        
        # 根據年份和比賽名稱找到對應的 session_key
        race_session = openf1_analyzer.find_race_session_by_name(
            session_info.get('year'), search_name
        )
        
        if not race_session:
            print(f"[ERROR] 無法找到對應的比賽會話: {event_name} ({search_name})")
            return None
        
        session_key = race_session.get('session_key')
        session_type = race_session.get('session_type', 'Unknown')
        session_name = race_session.get('session_name', 'Unknown')
        location = race_session.get('location', 'Unknown')
        
        print(f"✅ 找到比賽會話: {location} | Type: {session_type} | Name: {session_name}")
        print(f"📡 從 OpenF1 API 獲取進站數據 (session_key: {session_key})...")
        
        # 獲取 OpenF1 進站數據
        enhanced_pitstops = openf1_analyzer.get_enhanced_pit_stops(session_key)
        
        if not enhanced_pitstops:
            print("[ERROR] OpenF1 API 未返回進站數據")
            return None
        
        print(f"[SUCCESS] 成功獲取 {len(enhanced_pitstops)} 個進站記錄")
        
        # 分析每位車手的最快進站時間
        driver_best_times = {}
        
        for stop in enhanced_pitstops:
            # 正確提取車手和車隊信息 (從 driver_info 字段中)
            driver_info = stop.get('driver_info', {})
            driver = driver_info.get('name_acronym', 'UNK')
            team = driver_info.get('team_name', 'Unknown Team')
            pit_duration = stop.get('pit_duration')
            
            if pit_duration is not None and pit_duration > 0:
                if driver not in driver_best_times or pit_duration < driver_best_times[driver]['fastest_time']:
                    driver_best_times[driver] = {
                        'driver': driver,
                        'team': team,
                        'fastest_time': float(pit_duration),
                        'lap_number': stop.get('lap_number', 0),
                        'session_time': stop.get('session_time', 'Unknown')
                    }
        
        # 按最快時間排序
        ranking_data = sorted(driver_best_times.values(), key=lambda x: x['fastest_time'])
        
        return ranking_data
        
    except Exception as e:
        print(f"[ERROR] 車手最快進站分析失敗: {e}")
        return None


def display_driver_ranking_table(ranking_data):
    """顯示車手最快進站時間排行榜"""
    if not ranking_data:
        print("[ERROR] 沒有排行榜數據可顯示")
        return
    
    print(f"\n🏆 車手最快進站時間排行榜:")
    print(f"⚡ 全場最快進站: {ranking_data[0]['fastest_time']:.1f}秒 ({ranking_data[0]['driver']})")
    print(f"🐌 全場最慢進站: {ranking_data[-1]['fastest_time']:.1f}秒 ({ranking_data[-1]['driver']})")
    
    table = PrettyTable()
    table.field_names = ["排名", "車手", "車隊", "最快進站時間", "圈數"]
    
    for rank, driver_data in enumerate(ranking_data, 1):
        table.add_row([
            rank,
            driver_data['driver'],
            driver_data['team'],
            f"{driver_data['fastest_time']:.1f}秒",
            driver_data['lap_number']
        ])
    
    print(table)


def save_json_results(ranking_data, session_info, analysis_type):
    """保存 JSON 結果"""
    json_dir = "json"
    os.makedirs(json_dir, exist_ok=True)
    
    result_data = {
        "function_id": 3,
        "function_name": "Driver Fastest Pitstop Ranking",
        "analysis_type": analysis_type,
        "session_info": session_info,
        "timestamp": datetime.now().isoformat(),
        "data": ranking_data
    }
    
    # 修改文件命名格式為：driver_fastest_pitstop_ranking_YYYY_賽事.json
    event_name = session_info.get('event_name', 'Unknown').replace(' ', '_')
    year = session_info.get('year', 'Unknown')
    filename = f"driver_fastest_pitstop_ranking_{year}_{event_name}.json"
    filepath = os.path.join(json_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON結果已保存到: file:///{os.path.abspath(filepath)}")
    except Exception as e:
        print(f"[WARNING] JSON保存失敗: {e}")


def _display_cached_detailed_output(ranking_data, session_info):
    """當使用緩存數據但需要顯示詳細輸出時調用此函數"""
    print("\n📊 顯示緩存的詳細分析結果...")
    
    # 顯示排行榜
    display_driver_ranking_table(ranking_data)
    
    # 保存 JSON 結果（如果需要）
    save_json_results(ranking_data, session_info, "driver_fastest_pitstop_ranking")


if __name__ == "__main__":
    print("車手最快進站時間排行榜模組 - 獨立測試模式")
