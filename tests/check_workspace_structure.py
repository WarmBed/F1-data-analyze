"""檢查 Workspace 資料庫結構"""
import sqlite3

conn = sqlite3.connect('workspaces/f1t_workspaces.db')
cursor = conn.cursor()

# 獲取表結構
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='workspaces'")
result = cursor.fetchone()

if result:
    print("Workspaces 表結構:")
    print(result[0])
    print()
    
    # 列出所有列名
    cursor.execute("PRAGMA table_info(workspaces)")
    columns = cursor.fetchall()
    print("列名:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    print()
    
    # 獲取最近的記錄
    cursor.execute('SELECT * FROM workspaces ORDER BY created_at DESC LIMIT 1')
    row = cursor.fetchone()
    
    if row:
        print("最近的 Workspace 記錄:")
        for idx, col in enumerate(columns):
            col_name = col[1]
            col_value = row[idx]
            if col_name == 'config_json' and col_value:
                print(f"  {col_name}: (長度 {len(col_value)} 字元)")
            else:
                print(f"  {col_name}: {col_value}")
else:
    print("Workspaces 表不存在")

conn.close()
