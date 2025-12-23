import sqlite3
import json

conn = sqlite3.connect('workspaces/f1t_workspaces.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name, config_json FROM workspaces WHERE id=30')
ws = cursor.fetchone()

if ws:
    print(f'Workspace ID={ws[0]}, Name={ws[1]}')
    print('\nconfig_json 原始內容:')
    print('-' * 70)
    
    config = json.loads(ws[2])
    print(json.dumps(config, indent=2, ensure_ascii=False))

conn.close()
