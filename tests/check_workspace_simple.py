"""簡單檢查 Workspace 數據庫"""
import sqlite3
import json
import os
import sys

# 強制 UTF-8 輸出
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

db_path = "workspaces/workspaces.db"

if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 獲取最新的 Workspace
cursor.execute("""
    SELECT id, name, config_json
    FROM workspaces
    ORDER BY created_at DESC
    LIMIT 1
""")

row = cursor.fetchone()

if not row:
    print("No workspace found")
    conn.close()
    sys.exit(0)

workspace_id, name, config_json = row

print(f"Latest Workspace ID: {workspace_id}")
print(f"Name: {name}")
print("")

# 解析配置
config = json.loads(config_json)

# 提取所有 window_type
window_types = []
for tab in config.get('tabs', []):
    for window in tab.get('mdi_windows', []):
        wtype = window.get('window_type')
        title = window.get('window_title', '')
        params = window.get('parameters', {})
        
        print(f"Window:")
        print(f"  window_type: {wtype}")
        print(f"  title: {title}")
        print(f"  parameters: {params}")
        print("")
        
        window_types.append(wtype)

print(f"All window_type values: {set(window_types)}")

conn.close()
