"""查看資料庫結構"""
from modules.gui.live_timing.core.realtime_database import get_realtime_db

db = get_realtime_db()
db.connect()
cursor = db._conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Tables:", tables)

# 查看 drivers 表結構
cursor.execute("PRAGMA table_info(drivers)")
print("\nDrivers columns:")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")
