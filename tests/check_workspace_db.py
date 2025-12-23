import sqlite3
import json

conn = sqlite3.connect('workspaces/f1t_workspaces.db')
cursor = conn.cursor()
cursor.execute('SELECT id, name, config_json FROM workspaces ORDER BY id DESC LIMIT 1')
row = cursor.fetchone()

if row:
    config = json.loads(row[2])
    print(f'ID: {row[0]}, Name: {row[1]}')
    print(f'Tabs: {len(config.get("tabs", []))}')
    
    if config.get("tabs"):
        first_tab = config["tabs"][0]
        windows = first_tab.get("mdi_windows", [])
        print(f'First tab windows: {len(windows)}')
        
        if windows:
            first_window = windows[0]
            print(f'\n第一個視窗資訊:')
            print(f'  window_type: {first_window.get("window_type")}')
            print(f'  window_title: {first_window.get("window_title")}')
            print(f'  parameters: {first_window.get("parameters")}')
            print(f'\n所有視窗類型:')
            for idx, w in enumerate(windows):
                print(f'  {idx+1}. {w.get("window_type")} - {w.get("window_title")}')
else:
    print('沒有找到 Workspace')

conn.close()
