"""檢查 Workspace 數據庫"""
import sqlite3
import json

conn = sqlite3.connect('workspaces/workspaces.db')
cursor = conn.cursor()

# 獲取最近的 Workspace
cursor.execute('SELECT id, name, description, config_json, created_at FROM workspaces ORDER BY created_at DESC LIMIT 1')
row = cursor.fetchone()

if row:
    workspace_id, name, desc, config_json, created_at = row
    print(f"📊 最近的 Workspace:")
    print(f"  ID: {workspace_id}")
    print(f"  名稱: {name}")
    print(f"  描述: {desc}")
    print(f"  創建時間: {created_at}")
    
    # 解析配置
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
            print(f"      [{j+1}] {win_type}: {win_title}")
    
    print(f"\n🎯 總計: {total_windows} 個 MDI 視窗")
else:
    print("❌ 沒有找到任何 Workspace")

conn.close()
