"""
調查 FastF1 circuit_info.corners 返回的數據
"""
import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

print('=' * 70)
print('調查 FastF1 官方彎道數據')
print('=' * 70)

session = fastf1.get_session(2024, 'Japan', 'R')
session.load()

print('\n檢查 1: session.get_circuit_info() 是否存在')
if hasattr(session, 'get_circuit_info'):
    print('✅ session.get_circuit_info() 方法存在')
    
    try:
        circuit_info = session.get_circuit_info()
        print(f'✅ circuit_info 獲取成功: {type(circuit_info)}')
        
        print('\n檢查 2: circuit_info.corners 是否存在')
        if hasattr(circuit_info, 'corners'):
            print(f'✅ circuit_info.corners 存在: {type(circuit_info.corners)}')
            
            print('\n檢查 3: corners 的內容')
            corners = circuit_info.corners
            print(f'Corners 數量: {len(corners)}')
            
            if len(corners) > 0:
                print(f'\nCorners DataFrame 欄位:')
                print(corners.columns.tolist())
                
                print(f'\n完整 Corners 數據:')
                print(corners.to_string())
                
                print(f'\n檢查 4: Distance 欄位')
                if 'Distance' in corners.columns:
                    print(f'✅ Distance 欄位存在')
                    print(f'Distance 範圍: {corners["Distance"].min():.2f} ~ {corners["Distance"].max():.2f} m')
                    print(f'\n各彎道的 Distance:')
                    for idx, row in corners.iterrows():
                        print(f'  T{row["Number"]}: {row["Distance"]:.2f}m ({row["Distance"]/1000:.3f}km)')
                else:
                    print(f'❌ Distance 欄位不存在')
                    print(f'可用欄位: {corners.columns.tolist()}')
            else:
                print('❌ corners 是空的')
        else:
            print('❌ circuit_info.corners 不存在')
            print(f'circuit_info 的屬性: {dir(circuit_info)}')
    except Exception as e:
        print(f'❌ 獲取 circuit_info 失敗: {e}')
        import traceback
        traceback.print_exc()
else:
    print('❌ session.get_circuit_info() 方法不存在')
    print(f'Session 的可用方法: {[m for m in dir(session) if not m.startswith("_")]}')

print('\n' + '=' * 70)
print('結論: 需要確認 FastF1 是否提供官方彎道數據')
print('=' * 70)
