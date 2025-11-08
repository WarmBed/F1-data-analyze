"""
測試 FastF1 circuit_info 提供的賽道特徵數據
"""
import fastf1
import pandas as pd

# 設置顯示選項
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

print("=" * 80)
print("FastF1 Circuit Info 賽道特徵探索")
print("=" * 80)

# 測試多個賽道
test_tracks = [
    (2024, 'Japan', 'R'),      # 鈴鹿
    (2024, 'Monaco', 'R'),     # 摩納哥
    (2024, 'Italy', 'R'),      # 蒙扎
]

for year, race, session_type in test_tracks:
    print(f"\n{'=' * 80}")
    print(f"📍 賽道: {year} {race} {session_type}")
    print("=" * 80)
    
    try:
        # 載入會話
        session = fastf1.get_session(year, race, session_type)
        session.load()
        
        # 獲取賽道資訊
        circuit_info = session.get_circuit_info()
        
        print(f"\n✅ Session Info:")
        print(f"   - 賽事名稱: {session.event['EventName']}")
        print(f"   - 賽道名稱: {session.event.get('Location', 'N/A')}")
        print(f"   - 國家: {session.event.get('Country', 'N/A')}")
        
        print(f"\n🔍 Circuit Info 可用屬性:")
        attrs = [attr for attr in dir(circuit_info) if not attr.startswith('_')]
        print(f"   {', '.join(attrs)}")
        
        # 檢查 corners
        if hasattr(circuit_info, 'corners') and circuit_info.corners is not None:
            corners_df = circuit_info.corners
            print(f"\n🎯 彎道資訊 (Corners DataFrame):")
            print(f"   - 彎道總數: {len(corners_df)}")
            print(f"   - 可用欄位: {list(corners_df.columns)}")
            
            print(f"\n📊 前 5 個彎道詳細資訊:")
            print(corners_df.head())
            
            print(f"\n🔢 第 1 個彎道完整資訊:")
            first_corner = corners_df.iloc[0]
            for col in corners_df.columns:
                print(f"   - {col}: {first_corner[col]}")
            
            # 統計分析
            print(f"\n📈 彎道統計:")
            print(f"   - 角度範圍: {corners_df['Angle'].min():.1f}° ~ {corners_df['Angle'].max():.1f}°")
            print(f"   - 距離範圍: {corners_df['Distance'].min():.1f}m ~ {corners_df['Distance'].max():.1f}m")
            
        else:
            print(f"\n⚠️  無 corners 資料")
        
        # 檢查 rotation
        if hasattr(circuit_info, 'rotation'):
            print(f"\n🔄 賽道旋轉角: {circuit_info.rotation}")
        
        # 檢查其他可能的屬性
        if hasattr(circuit_info, 'x'):
            print(f"\n📍 X 座標範圍: {circuit_info.x.min():.1f} ~ {circuit_info.x.max():.1f}")
        if hasattr(circuit_info, 'y'):
            print(f"📍 Y 座標範圍: {circuit_info.y.min():.1f} ~ {circuit_info.y.max():.1f}")
            
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'=' * 80}")
print("測試完成")
print("=" * 80)
