"""檢查用戶實際保存的 Workspace 數據"""
import sqlite3
import json
import os

db_path = "workspaces/workspaces.db"

if not os.path.exists(db_path):
    print(f"❌ 數據庫不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("🔍 檢查用戶實際保存的 Workspace")
print("=" * 80)

# 獲取最新的 Workspace
cursor.execute("""
    SELECT id, name, config_json, created_at, total_windows
    FROM workspaces
    ORDER BY created_at DESC
    LIMIT 1
""")

workspace = cursor.fetchone()

if not workspace:
    print("❌ 沒有找到任何 Workspace")
    conn.close()
    exit(0)

workspace_id, name, config_json, created_at, total_windows = workspace

print(f"\n📋 最新 Workspace:")
print(f"  - ID: {workspace_id}")
print(f"  - 名稱: {name}")
print(f"  - 創建時間: {created_at}")
print(f"  - 視窗總數: {total_windows}")

# 解析配置
config = json.loads(config_json)

print(f"\n📊 配置詳情:")
print(f"  - 版本: {config.get('version')}")
print(f"  - 分頁數: {len(config.get('tabs', []))}")

# 檢查每個分頁
for idx, tab in enumerate(config.get('tabs', []), 1):
    tab_name = tab.get('tab_name', '未命名')
    mdi_windows = tab.get('mdi_windows', [])
    
    print(f"\n  📑 分頁 [{idx}]: {tab_name}")
    print(f"     - MDI 視窗數量: {len(mdi_windows)}")
    
    # 檢查每個視窗
    for win_idx, window in enumerate(mdi_windows, 1):
        window_type = window.get('window_type', '未知')
        window_title = window.get('window_title', '無標題')
        parameters = window.get('parameters', {})
        
        print(f"\n     🪟 視窗 [{win_idx}]:")
        print(f"       - window_type: '{window_type}'")
        print(f"       - window_title: '{window_title}'")
        print(f"       - parameters: {parameters}")
        
        # 特別標記 Lap Analysis 模組
        lap_analysis_types = ['speed', 'brake', 'throttle', 'rpm', 'acceleration', 
                              'gear', 'Speeddiff', 'distancediff', 'timediff']
        
        if window_type in lap_analysis_types:
            print(f"       ✅ 這是 Lap Analysis 模組")
        elif window_type.endswith('_analysis'):
            print(f"       ⚠️ window_type 以 '_analysis' 結尾（可能不匹配載入邏輯）")

print("\n" + "=" * 80)
print("🎯 關鍵檢查點：")
print("=" * 80)

# 統計 window_type
cursor.execute("""
    SELECT config_json FROM workspaces
    WHERE id = ?
""", (workspace_id,))

config_json = cursor.fetchone()[0]
config = json.loads(config_json)

window_types = []
for tab in config.get('tabs', []):
    for window in tab.get('mdi_windows', []):
        window_types.append(window.get('window_type'))

print(f"\n所有 window_type 列表:")
for wtype in set(window_types):
    count = window_types.count(wtype)
    print(f"  - '{wtype}': {count} 個")

# 檢查是否有 Lap Analysis 模組
lap_types_found = [wt for wt in window_types if wt in lap_analysis_types]
lap_types_wrongformat = [wt for wt in window_types if wt.endswith('_analysis') and wt not in lap_analysis_types]

if lap_types_found:
    print(f"\n✅ 找到正確格式的 Lap Analysis 模組: {lap_types_found}")
if lap_types_wrongformat:
    print(f"\n⚠️ 找到錯誤格式的視窗類型（以 '_analysis' 結尾）: {lap_types_wrongformat}")

conn.close()
print("\n" + "=" * 80)
