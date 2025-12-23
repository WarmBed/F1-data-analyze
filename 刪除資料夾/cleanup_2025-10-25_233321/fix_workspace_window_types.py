"""修復 Workspace 數據庫中的 window_type"""
import sqlite3
import json
import os

db_path = "workspaces/workspaces.db"

if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 獲取所有 Workspace
cursor.execute("SELECT id, name, config_json FROM workspaces")
workspaces = cursor.fetchall()

print(f"Found {len(workspaces)} workspace(s)")
print("")

fixes_applied = 0

for workspace_id, name, config_json in workspaces:
    config = json.loads(config_json)
    modified = False
    
    print(f"Workspace ID={workspace_id}, Name={name}")
    
    for tab in config.get('tabs', []):
        for window in tab.get('mdi_windows', []):
            window_type = window.get('window_type')
            
            # 修復邏輯
            if window_type == "speed_analysis":
                print(f"  - Fixing: '{window_type}' -> 'speed'")
                window['window_type'] = 'speed'
                modified = True
                fixes_applied += 1
            elif window_type == "brake_analysis":
                print(f"  - Fixing: '{window_type}' -> 'brake'")
                window['window_type'] = 'brake'
                modified = True
                fixes_applied += 1
            elif window_type == "throttle_analysis":
                print(f"  - Fixing: '{window_type}' -> 'throttle'")
                window['window_type'] = 'throttle'
                modified = True
                fixes_applied += 1
            elif window_type == "rpm_analysis":
                print(f"  - Fixing: '{window_type}' -> 'rpm'")
                window['window_type'] = 'rpm'
                modified = True
                fixes_applied += 1
            elif window_type == "acceleration_analysis":
                print(f"  - Fixing: '{window_type}' -> 'acceleration'")
                window['window_type'] = 'acceleration'
                modified = True
                fixes_applied += 1
            elif window_type == "gear_analysis":
                print(f"  - Fixing: '{window_type}' -> 'gear'")
                window['window_type'] = 'gear'
                modified = True
                fixes_applied += 1
    
    if modified:
        # 更新數據庫
        new_config_json = json.dumps(config, ensure_ascii=False)
        cursor.execute("""
            UPDATE workspaces 
            SET config_json = ? 
            WHERE id = ?
        """, (new_config_json, workspace_id))
        print(f"  -> Updated!")
    
    print("")

conn.commit()
conn.close()

print(f"Total fixes applied: {fixes_applied}")
print("Database updated successfully!")
