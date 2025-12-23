import sqlite3
import json

conn = sqlite3.connect('workspaces/f1t_workspaces.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

for ws_id in [30, 35]:
    print(f'\n{"="*70}')
    print(f'Workspace ID={ws_id}')
    print(f'{"="*70}')
    
    cursor.execute('SELECT * FROM workspaces WHERE id=?', (ws_id,))
    ws = cursor.fetchone()
    
    if ws:
        print(f'Name: {ws["name"]}')
        print(f'Total Windows: {ws["total_windows"]}')
        
        config = json.loads(ws["config_json"])
        
        all_windows = []
        for i, tab in enumerate(config.get("tabs", []), 1):
            windows = tab.get("windows", [])
            print(f'\nTab {i}: {tab.get("name", "Unnamed")} - {len(windows)} windows')
            
            for j, window in enumerate(windows, 1):
                wtype = window.get("window_type", "Unknown")
                params = window.get("parameters", {})
                analysis_type = params.get("analysis_type", wtype)
                all_windows.append(analysis_type)
                print(f'  [{j}] {analysis_type}')
        
        print(f'\n✅ 所有視窗類型: {set(all_windows)}')
        
        # 檢查是否有 Speed
        if 'speed' in [w.lower() for w in all_windows]:
            print('🎯 包含 Speed 模組！')
        else:
            print('❌ 沒有 Speed 模組')

conn.close()
