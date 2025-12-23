import sqlite3

conn = sqlite3.connect('workspaces/f1t_workspaces.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name, total_windows, created_at FROM workspaces ORDER BY id')
print('所有 Workspaces:')
for row in cursor.fetchall():
    print(f'  ID={row[0]}, Name={row[1]}, Windows={row[2]}, Created={row[3]}')

conn.close()
