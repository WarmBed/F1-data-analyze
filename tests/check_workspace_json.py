"""檢查最近 Workspace 的完整配置"""
import sqlite3
import json

conn = sqlite3.connect('workspaces/f1t_workspaces.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name, config_json FROM workspaces ORDER BY created_at DESC LIMIT 1')
row = cursor.fetchone()

if row:
    workspace_id, workspace_name, config_json = row
    print(f"=== Workspace Info ===")
    print(f"ID: {workspace_id}")
    print(f"Name: {workspace_name}")
    print()
    
    # 解析 JSON
    config = json.loads(config_json)
    
    print(f"=== Config Structure ===")
    print(json.dumps(config, indent=2, ensure_ascii=False))
else:
    print("沒有找到 Workspace")

conn.close()
