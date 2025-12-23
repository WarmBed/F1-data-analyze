#!/usr/bin/env python3
"""檢查 f1t_workspaces.db"""
import sqlite3
import json

conn = sqlite3.connect('workspaces/f1t_workspaces.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 列出所有 Workspaces
cursor.execute('SELECT * FROM workspaces ORDER BY id DESC LIMIT 10')
workspaces = cursor.fetchall()

print(f'📊 f1t_workspaces.db 中有 {len(workspaces)} 個 Workspace (最近 10 個):\n')

for ws in workspaces:
    print(f'ID: {ws["id"]} | Name: {ws["name"]} | Windows: {ws["total_windows"]}')
    
    # 檢查 config_json
    try:
        config = json.loads(ws["config_json"])
        if 'tabs' in config:
            for i, tab in enumerate(config["tabs"], 1):
                windows = tab.get("windows", [])
                print(f'  Tab {i}: {tab.get("name", "Unnamed")} - {len(windows)} windows')
                for j, window in enumerate(windows, 1):
                    wtype = window.get("window_type", "Unknown")
                    params = window.get("parameters", {})
                    analysis_type = params.get("analysis_type", wtype)
                    print(f'    [{j}] {analysis_type}')
    except Exception as e:
        print(f'  Config Error: {e}')
    
    print()

# 特別檢查 ID=32
print('\n' + '='*60)
print('🔍 檢查 ID=32 (您剛才載入的):')
print('='*60)
cursor.execute('SELECT * FROM workspaces WHERE id=32')
ws32 = cursor.fetchone()
if ws32:
    config = json.loads(ws32["config_json"])
    print(f'Name: {ws32["name"]}')
    print(f'Total Windows: {ws32["total_windows"]}')
    for i, tab in enumerate(config.get("tabs", []), 1):
        windows = tab.get("windows", [])
        print(f'\nTab {i}: {tab.get("name", "Unnamed")}')
        for j, window in enumerate(windows, 1):
            wtype = window.get("window_type", "Unknown")
            params = window.get("parameters", {})
            print(f'  Window {j}:')
            print(f'    window_type: {wtype}')
            print(f'    parameters: {params}')
else:
    print('❌ ID=32 不存在')

conn.close()
