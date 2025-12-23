"""檢查 Workspace 保存了什麼"""
import sqlite3
import json

try:
    conn = sqlite3.connect('workspaces/workspaces.db')
    cursor = conn.cursor()
    
    # 先檢查所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if not tables:
        print("❌ 數據庫中沒有表！")
        conn.close()
        exit()
    
    print(f"📊 找到 {len(tables)} 個表:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 使用第一個表
    table_name = tables[0][0]
    print(f"\n✅ 使用表: {table_name}")
    
    # 獲取最近的記錄
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT 1")
    columns = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    
    if not row:
        print("❌ 表是空的，沒有保存任何 Workspace")
        conn.close()
        exit()
    
    # 構建字典
    workspace = dict(zip(columns, row))
    
    print(f"\n📋 最近保存的 Workspace:")
    print(f"  ID: {workspace.get('id')}")
    print(f"  名稱: {workspace.get('name')}")
    print(f"  創建時間: {workspace.get('created_at')}")
    
    # 解析配置
    config_json = workspace.get('config_json') or workspace.get('config')
    if config_json:
        config = json.loads(config_json)
        tabs = config.get('tabs', [])
        
        print(f"\n📑 分頁數量: {len(tabs)}")
        
        total_windows = 0
        for i, tab in enumerate(tabs):
            tab_name = tab.get('tab_name', 'Unknown')
            mdi_windows = tab.get('mdi_windows', [])
            print(f"\n  分頁 [{i+1}]: {tab_name}")
            print(f"    - MDI 視窗數量: {len(mdi_windows)}")
            total_windows += len(mdi_windows)
            
            for j, win in enumerate(mdi_windows):
                win_type = win.get('window_type', 'unknown')
                win_title = win.get('window_title', 'No Title')
                analysis_type = win.get('parameters', {}).get('analysis_type', 'N/A')
                print(f"      [{j+1}] type={win_type}, analysis_type={analysis_type}")
                print(f"          title: {win_title}")
        
        print(f"\n🎯 總計: {total_windows} 個 MDI 視窗保存在配置中")
        
        # 檢查是否有 speed
        speed_found = False
        for tab in tabs:
            for win in tab.get('mdi_windows', []):
                if 'speed' in win.get('window_type', '').lower() or 'speed' in win.get('parameters', {}).get('analysis_type', '').lower():
                    speed_found = True
                    print(f"\n✅ 找到 Speed 模組:")
                    print(f"    window_type: {win.get('window_type')}")
                    print(f"    parameters: {win.get('parameters')}")
        
        if not speed_found:
            print(f"\n❌ Workspace 配置中沒有 Speed 模組！")
    else:
        print("❌ 沒有配置 JSON")
    
    conn.close()

except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
