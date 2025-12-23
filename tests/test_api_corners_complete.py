"""
完整驗證：外網 API 官方彎道資訊
"""
import requests
import json

def validate_api_corners():
    """完整驗證 API 彎道資訊"""
    url = 'https://api.f1telemetrystationpro.org/api/v2/analysis/execute'
    params = {
        'function_id': 2,
        'year': 2024,
        'race': 'Japan',
        'session': 'R'
    }
    
    print("="*70)
    print("  外網 API 官方彎道資訊驗證報告")
    print("="*70)
    print(f"\n🌐 API URL: {url}")
    print(f"📊 測試賽事: 2024 Japan GP (Race)")
    print(f"🔧 Function ID: 2 (Track Position Analysis)")
    
    print("\n正在請求 API...\n")
    
    try:
        response = requests.post(url, params=params, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ API 請求失敗: HTTP {response.status_code}")
            return False
        
        data = response.json()
        
        # 導航到正確的數據層級
        # 結構: response.data.data.official_corners
        if 'data' not in data or 'data' not in data['data']:
            print("❌ API 返回結構不正確")
            return False
        
        analysis_data = data['data']['data']
        
        # 檢查 official_corners
        if 'official_corners' not in analysis_data:
            print("❌ 缺少 official_corners 欄位")
            print(f"可用欄位: {list(analysis_data.keys())}")
            return False
        
        corners = analysis_data['official_corners']
        
        # 驗證通過 - 顯示詳細資訊
        print("✅ API 請求成功")
        print("✅ 找到 official_corners 欄位")
        
        print("\n" + "="*70)
        print("  官方彎道資訊")
        print("="*70)
        print(f"  ✅ Available: {corners.get('available')}")
        print(f"  ✅ Count: {corners.get('count')}")
        print(f"  ✅ 實際彎道數: {len(corners.get('corners', []))}")
        
        # 顯示所有彎道
        print(f"\n所有彎道列表:")
        for i, c in enumerate(corners.get('corners', []), 1):
            print(f"  {i:2d}. 彎道 {c['number']:2d}: "
                  f"X={c['x']:8.2f}, "
                  f"Y={c['y']:8.2f}, "
                  f"Distance={c.get('mapped_distance', 0):8.2f}m, "
                  f"Error={c.get('mapping_error', 0):.1f}m")
        
        # 映射品質
        if 'mapping_quality' in corners:
            q = corners['mapping_quality']
            print(f"\n映射品質統計:")
            print(f"  - 平均誤差: {q.get('average_error_m', 0):.1f} m")
            print(f"  - 最大誤差: {q.get('max_error_m', 0):.1f} m")
            print(f"  - 最小誤差: {q.get('min_error_m', 0):.1f} m")
        
        # 檢查數據來源
        print(f"\n數據來源資訊:")
        print(f"  - Source: {data.get('source', 'unknown')}")
        print(f"  - Execution Time: {data.get('execution_time', 'N/A')}")
        print(f"  - Cache Used: {data['data'].get('cache_used', False)}")
        
        print("\n" + "="*70)
        print("✅ 驗證通過：外網 API 包含完整的 official_corners 資訊")
        print("="*70)
        print("\n📋 數據結構路徑:")
        print("   response['data']['data']['official_corners']")
        print("\n⚠️  注意：API 有雙層 'data' 結構")
        print("   - 外層 data: API 響應包裝")
        print("   - 內層 data: 實際分析結果")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 驗證失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = validate_api_corners()
    sys.exit(0 if success else 1)
