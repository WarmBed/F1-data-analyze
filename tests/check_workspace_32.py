#!/usr/bin/env python3
"""檢查 Workspace ID=32 的內容"""
import sqlite3
import json

conn = sqlite3.connect('workspaces/workspaces.db')
cursor = conn.cursor()

# 先檢查資料表結構
cursor.execute('PRAGMA table_info(workspace_window_types)')
print('📊 workspace_window_types 欄位:')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')

# 列出最近的 Workspaces
cursor.execute('SELECT id, name, created_at FROM workspaces ORDER BY id DESC LIMIT 5')
print('\n📋 最近的 Workspaces:')
for row in cursor.fetchall():
    print(f'  ID={row[0]}, Name={row[1]}, Created={row[2]}')

# 檢查 Workspace ID=32 的視窗
print('\n🔍 Workspace ID=32 的視窗類型:')
cursor.execute('SELECT * FROM workspace_window_types WHERE workspace_id=32')
windows = cursor.fetchall()

if not windows:
    print('  ❌ 找不到任何視窗！')
else:
    for i, row in enumerate(windows, 1):
        print(f'\n  視窗 {i}: {row}')

print(f'\n總計: {len(windows)} 個視窗')

# 也檢查 Workspace ID=1 (測試Workspace)
print('\n\n🔍 Workspace ID=1 的視窗類型:')
cursor.execute('SELECT * FROM workspace_window_types WHERE workspace_id=1')
windows_1 = cursor.fetchall()
for i, row in enumerate(windows_1, 1):
    print(f'\n  視窗 {i}: {row}')
print(f'\n總計: {len(windows_1)} 個視窗')

conn.close()
