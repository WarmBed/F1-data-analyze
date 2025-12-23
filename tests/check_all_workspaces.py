#!/usr/bin/env python3
"""檢查所有 Workspaces"""
import sqlite3
import json

conn = sqlite3.connect('workspaces/workspaces.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 列出所有 Workspaces
cursor.execute('SELECT * FROM workspaces ORDER BY id')
workspaces = cursor.fetchall()

print(f'📊 資料庫中總共有 {len(workspaces)} 個 Workspace:\n')

for ws in workspaces:
    print(f'ID: {ws["id"]}')
    print(f'Name: {ws["name"]}')
    print(f'Description: {ws["description"]}')
    print(f'Created: {ws["created_at"]}')
    print(f'Modified: {ws["modified_at"]}')
    print(f'Tabs: {ws["total_tabs"]}')
    print(f'Windows: {ws["total_windows"]}')
    print(f'Tags: {ws["tags"]}')
    
    # 檢查 config_json
    try:
        config = json.loads(ws["config_json"])
        print(f'Config Keys: {list(config.keys())}')
        if 'tabs' in config:
            print(f'  Tabs in config: {len(config["tabs"])}')
            for i, tab in enumerate(config["tabs"], 1):
                print(f'    Tab {i}: {tab.get("name", "Unnamed")} - {len(tab.get("windows", []))} windows')
                for j, window in enumerate(tab.get("windows", []), 1):
                    print(f'      Window {j}: {window.get("window_type", "Unknown")}')
    except Exception as e:
        print(f'Config Error: {e}')
    
    print('-' * 60)

conn.close()
