"""
測試 FastF1 Ergast API 獲取車手積分榜
驗證改進方案的數據來源可行性
"""

import fastf1
from fastf1.ergast import Ergast

def test_ergast_driver_standings():
    """測試 Ergast API 獲取車手積分榜"""
    print("=" * 70)
    print("測試 FastF1 Ergast API - 車手積分榜")
    print("=" * 70)
    
    ergast = Ergast()
    
    # 測試 1: 獲取 2024 賽季最終積分榜
    print("\n[測試 1] 2024 賽季最終積分榜")
    try:
        standings_2024 = ergast.get_driver_standings(season=2024)
        if standings_2024.content:
            print(f"✅ 成功獲取 2024 積分榜，共 {len(standings_2024.content)} 筆記錄")
            
            # 顯示前 10 名
            print("\n前 10 名車手:")
            for i, driver in enumerate(standings_2024.content[:10], 1):
                print(f"  {i:2d}. {driver['driverCode']:3s} - {driver['points']:3.0f} 分")
        else:
            print("❌ 無數據返回")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
    
    # 測試 2: 獲取特定回合後的積分榜 (Round 10 = Japan)
    print("\n[測試 2] 2024 年第 10 場比賽後的積分榜")
    try:
        standings_round10 = ergast.get_driver_standings(season=2024, round=10)
        if standings_round10.content:
            print(f"✅ 成功獲取第 10 場後積分榜")
            
            # 顯示前 8 名（頂尖車手）
            print("\n前 8 名車手（is_top_driver = 1）:")
            top_8 = []
            for i, driver in enumerate(standings_round10.content[:8], 1):
                code = driver['driverCode']
                points = driver['points']
                print(f"  {i}. {code:3s} - {points:3.0f} 分")
                top_8.append(code)
            
            print(f"\n💡 動態計算結果: is_top_driver = {top_8}")
        else:
            print("❌ 無數據返回")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
    
    # 測試 3: 對比硬編碼 vs 動態計算
    print("\n[測試 3] 硬編碼 vs 動態積分榜對比")
    
    hardcoded = ['VER', 'HAM', 'LEC', 'NOR', 'PIA', 'SAI', 'RUS', 'PER']
    
    if standings_round10.content:
        dynamic = [driver['driverCode'] for driver in standings_round10.content[:8]]
        
        print("\n硬編碼 (V3.8):")
        print(f"  {hardcoded}")
        
        print("\n動態計算 (提案方案):")
        print(f"  {dynamic}")
        
        # 差異分析
        only_in_hardcoded = set(hardcoded) - set(dynamic)
        only_in_dynamic = set(dynamic) - set(hardcoded)
        
        if only_in_hardcoded or only_in_dynamic:
            print("\n⚠️  差異:")
            if only_in_hardcoded:
                print(f"  僅在硬編碼中: {list(only_in_hardcoded)}")
            if only_in_dynamic:
                print(f"  僅在動態計算中: {list(only_in_dynamic)}")
        else:
            print("\n✅ 完全一致！")
    
    # 測試 4: 2022-2024 歷史數據可用性
    print("\n[測試 4] 歷史數據可用性檢查")
    for year in [2022, 2023, 2024]:
        try:
            standings = ergast.get_driver_standings(season=year)
            if standings.content:
                count = len(standings.content)
                top_driver = standings.content[0]['driverCode']
                print(f"  {year}: ✅ {count} 筆記錄 (冠軍: {top_driver})")
            else:
                print(f"  {year}: ❌ 無數據")
        except Exception as e:
            print(f"  {year}: ❌ 錯誤 - {e}")

if __name__ == "__main__":
    test_ergast_driver_standings()
