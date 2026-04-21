"""
測試外網 API 是否返回 official_corners 彎道資訊
"""
import requests
import json
import sys

def test_api_corners():
    """測試 API 彎道資訊"""
    url = 'http://localhost:8000/api/v2/analysis/execute'
    params = {
        'function_id': 2,
        'year': 2024,
        'race': 'Japan',
        'session': 'R'
    }
    
    print("="*70)
    print("  測試外網 API 彎道資訊")
    print("="*70)
    print(f"\nAPI URL: {url}")
    print(f"參數: {json.dumps(params, indent=2)}")
    print("\n正在請求...")
    
    try:
        response = requests.post(url, params=params, timeout=60)
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API 請求成功")
            
            # 檢查 official_corners 欄位
            if 'data' in data and 'official_corners' in data['data']:
                corners = data['data']['official_corners']
                
                print("\n" + "="*70)
                print("  官方彎道資訊")
                print("="*70)
                print(f"  - available: {corners.get('available')}")
                print(f"  - count: {corners.get('count')}")
                print(f"  - 實際彎道數量: {len(corners.get('corners', []))}")
                
                # 顯示前 5 個彎道
                if corners.get('corners'):
                    print(f"\n前 5 個彎道詳情:")
                    for c in corners['corners'][:5]:
                        print(f"    彎道 {c['number']}: "
                              f"X={c['x']:.2f}, "
                              f"Y={c['y']:.2f}, "
                              f"Distance={c.get('distance', 'N/A')}, "
                              f"Sector={c.get('sector', 'N/A')}")
                
                # 映射品質
                if 'mapping_quality' in corners:
                    q = corners['mapping_quality']
                    print(f"\n映射品質指標:")
                    print(f"  - 平均誤差: {q.get('average_error_m', 'N/A')} m")
                    print(f"  - 最大誤差: {q.get('max_error_m', 'N/A')} m")
                    print(f"  - 最小誤差: {q.get('min_error_m', 'N/A')} m")
                
                print("\n" + "="*70)
                print("✅ 外網 API 包含完整的 official_corners 資訊")
                print("="*70)
                return True
            else:
                print("\n" + "="*70)
                print("❌ API 返回數據中缺少 official_corners 欄位")
                print("="*70)
                print(f"\n可用的 keys: {list(data.get('data', {}).keys())}")
                return False
        else:
            print(f"\n❌ API 請求失敗")
            print(f"錯誤訊息: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ API 請求超時 (60秒)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API 請求錯誤: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ 未預期錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_corners()
    sys.exit(0 if success else 1)
