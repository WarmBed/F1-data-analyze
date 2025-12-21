#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function 98/99 API 測試腳本
驗證賽季級別分析功能的緩存搜尋
"""

import sys
import os

# 設定 UTF-8 輸出
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

from api.services.cache_service import F1AnalysisCacheService

def test_function_98():
    """測試 Function 98 (Team Colors)"""
    print("\n" + "=" * 80)
    print("測試 Function 98: Team Color Export")
    print("=" * 80)
    
    cache_service = F1AnalysisCacheService()
    
    # 測試 1: 檢查配置
    print("\n[1] 檢查配置")
    print("-" * 80)
    if "98" in cache_service.function_file_patterns:
        patterns = cache_service.function_file_patterns["98"]
        print(f"[OK] Function 98 已配置")
        print(f"     檔案模式: {patterns}")
    else:
        print(f"[ERROR] Function 98 未配置")
        return False
    
    # 測試 2: 搜尋緩存 (year=2025, colormap=fastf1)
    print("\n[2] 搜尋緩存: year=2025, colormap=fastf1")
    print("-" * 80)
    result = cache_service.search_cached_analysis(
        function_id="98",
        year=2025,
        colormap="fastf1"
    )
    
    if result:
        print("[OK] 緩存搜尋成功")
        
        # 驗證數據結構
        data = result.get("data", {})
        teams = data.get("teams", {})
        drivers = data.get("drivers", {})
        
        print(f"     找到 {len(teams)} 個車隊")
        print(f"     找到 {len(drivers)} 個車手")
        
        # 顯示前3個車隊
        if teams:
            print("\n     車隊範例:")
            for i, (team, color) in enumerate(list(teams.items())[:3]):
                print(f"       - {team}: {color}")
        
        return True
    else:
        print("[ERROR] 緩存搜尋失敗")
        return False

def test_function_99():
    """測試 Function 99 (Season Calendar)"""
    print("\n" + "=" * 80)
    print("測試 Function 99: Season Calendar Overview")
    print("=" * 80)
    
    cache_service = F1AnalysisCacheService()
    
    # 測試 1: 檢查配置
    print("\n[1] 檢查配置")
    print("-" * 80)
    if "99" in cache_service.function_file_patterns:
        patterns = cache_service.function_file_patterns["99"]
        print(f"[OK] Function 99 已配置")
        print(f"     檔案模式: {patterns}")
    else:
        print(f"[ERROR] Function 99 未配置")
        return False
    
    # 測試 2: 搜尋緩存 (year=2025)
    print("\n[2] 搜尋緩存: year=2025")
    print("-" * 80)
    result = cache_service.search_cached_analysis(
        function_id="99",
        year=2025
    )
    
    if result:
        print("[OK] 緩存搜尋成功")
        
        # 驗證數據結構
        data = result.get("data", {})
        
        # 檢查多年格式
        if isinstance(data, dict) and "2025" in data:
            print("     格式: 多年賽季日曆")
            events_2025 = data.get("2025", [])
            print(f"     2025年賽事數量: {len(events_2025)}")
        else:
            print("     格式: 單年賽季日曆")
        
        return True
    else:
        print("[ERROR] 緩存搜尋失敗")
        return False

if __name__ == "__main__":
    try:
        # 測試 Function 98
        f98_success = test_function_98()
        
        # 測試 Function 99
        f99_success = test_function_99()
        
        # 總結
        print("\n" + "=" * 80)
        print("測試總結")
        print("=" * 80)
        print(f"Function 98 (Team Colors):    {'[OK]' if f98_success else '[FAIL]'}")
        print(f"Function 99 (Season Calendar): {'[OK]' if f99_success else '[FAIL]'}")
        
        if f98_success and f99_success:
            print("\n[SUCCESS] 所有測試通過")
            sys.exit(0)
        else:
            print("\n[FAILED] 部分測試失敗")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] 測試異常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
