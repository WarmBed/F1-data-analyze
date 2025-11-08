"""檢查 Workspace 資料庫中保存的資料"""
import sqlite3
import json

conn = sqlite3.connect('workspaces/f1t_workspaces.db')
cursor = conn.cursor()

# 獲取最近的 Workspace
cursor.execute('SELECT id, name, config FROM workspaces ORDER BY created_at DESC LIMIT 1')
row = cursor.fetchone()

if row:
    workspace_id, workspace_name, config_json = row
    print(f"最近的 Workspace:")
    print(f"  ID: {workspace_id}")
    print(f"  Name: {workspace_name}")
    print()
    
    # 解析配置
    config = json.loads(config_json)
    
    # 檢查分頁和視窗
    tabs = config.get('tabs', [])
    print(f"分頁數量: {len(tabs)}")
    
    for tab_idx, tab in enumerate(tabs):
        tab_name = tab.get('tab_name', 'Unknown')
        windows = tab.get('mdi_windows', [])
        print(f"\n分頁 {tab_idx + 1}: {tab_name}")
        print(f"  視窗數量: {len(windows)}")
        
        for win_idx, window in enumerate(windows):
            window_type = window.get('window_type', 'Unknown')
            window_title = window.get('window_title', 'Unknown')
            print(f"    視窗 {win_idx + 1}:")
            print(f"      標題: {window_title}")
            print(f"      類型: {window_type}")
else:
    print("沒有找到 Workspace")

conn.close()
