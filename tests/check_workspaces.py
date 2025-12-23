"""查看工作區資料庫內容"""
import sqlite3

conn = sqlite3.connect('workspaces/f1t_workspaces.db')
cur = conn.cursor()

# 查看表結構
print("=" * 60)
print("資料庫結構")
print("=" * 60)
cur.execute("PRAGMA table_info(workspaces)")
for row in cur.fetchall():
    print(f"  {row[1]} ({row[2]})")

# 查看所有工作區
print("\n" + "=" * 60)
print("所有工作區")
print("=" * 60)
cur.execute("SELECT * FROM workspaces LIMIT 20")
cols = [desc[0] for desc in cur.description]
print(f"欄位: {', '.join(cols)}\n")

for row in cur.fetchall():
    data = dict(zip(cols, row))
    print(f"ID: {data.get('id')}")
    print(f"  Name: {data.get('name')}")
    print(f"  Year: {data.get('year')}")
    print(f"  Race: {data.get('race')}")
    print(f"  Session: {data.get('session')}")
    print()

conn.close()
