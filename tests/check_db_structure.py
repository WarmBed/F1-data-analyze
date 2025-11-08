"""檢查 Workspace 數據庫結構"""
import sqlite3

conn = sqlite3.connect('workspaces/workspaces.db')
cursor = conn.cursor()

# 獲取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("📊 數據庫中的表:")
for table in tables:
    print(f"  - {table[0]}")
    
    # 獲取表結構
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"    欄位:")
    for col in columns:
        print(f"      - {col[1]} ({col[2]})")
    
    # 獲取記錄數
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"    記錄數: {count}")

conn.close()
