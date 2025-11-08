"""
調查 2025 Australia R 是否有 Safety Car 事件
"""
import fastf1
import pandas as pd

# 設定緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

try:
    print("=" * 80)
    print("載入 2025 Australia R 賽事數據...")
    print("=" * 80)
    
    session = fastf1.get_session(2025, 'Australia', 'R')
    session.load()
    
    # 獲取 race control messages
    race_control = session.race_control_messages
    
    if race_control is not None and not race_control.empty:
        print(f"\n✅ 成功載入 {len(race_control)} 筆 race control messages")
        
        # 搜索 Safety Car 相關訊息
        safety_keywords = ['SAFETY CAR', 'VIRTUAL SAFETY', 'VSC']
        
        print("\n" + "=" * 80)
        print("搜索 Safety Car 相關訊息...")
        print("=" * 80)
        
        for keyword in safety_keywords:
            messages = race_control[race_control['Message'].str.contains(keyword, case=False, na=False)]
            
            if len(messages) > 0:
                print(f"\n🚨 找到 {len(messages)} 筆包含 '{keyword}' 的訊息:")
                print("-" * 80)
                
                for idx, row in messages.iterrows():
                    lap = row.get('Lap', 'N/A')
                    time = row.get('Time', 'N/A')
                    message = row.get('Message', 'N/A')
                    category = row.get('Category', 'N/A')
                    status = row.get('Status', 'N/A')
                    
                    print(f"\nLap {lap} | {time}")
                    print(f"Message:  {message}")
                    print(f"Category: {category}")
                    print(f"Status:   {status}")
                    print("-" * 80)
            else:
                print(f"\n❌ 沒有找到包含 '{keyword}' 的訊息")
        
        # 總結
        print("\n" + "=" * 80)
        print("總結分析")
        print("=" * 80)
        
        all_safety = race_control[
            race_control['Message'].str.contains('SAFETY|VSC', case=False, na=False, regex=True)
        ]
        
        if len(all_safety) > 0:
            print(f"✅ 2025 Australia R 有 Safety Car/VSC 事件")
            print(f"   總共 {len(all_safety)} 筆相關訊息")
            
            # 檢查是否能配對成 periods
            deployed = all_safety[all_safety['Message'].str.contains('DEPLOYED', case=False, na=False)]
            ending = all_safety[all_safety['Message'].str.contains('IN THIS LAP|ENDING', case=False, na=False, regex=True)]
            
            print(f"\n   DEPLOYED 訊息: {len(deployed)} 筆")
            print(f"   ENDING 訊息:   {len(ending)} 筆")
            
            if len(deployed) > 0 and len(ending) > 0:
                print(f"\n   ✅ 可以配對成 {min(len(deployed), len(ending))} 個 Safety Period(s)")
            else:
                print(f"\n   ⚠️  無法配對（缺少 DEPLOYED 或 ENDING 訊息）")
        else:
            print(f"❌ 2025 Australia R 沒有 Safety Car/VSC 事件")
            print(f"   這是一場沒有安全車干預的比賽")
        
    else:
        print("❌ 無法載入 race_control_messages")
        
except Exception as e:
    print(f"\n❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
