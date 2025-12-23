"""測試數據庫連接和保存"""
import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.workspace_database import WorkspaceDatabase
import json

try:
    print("🔧 創建數據庫實例...")
    db = WorkspaceDatabase()
    
    print("✅ 數據庫實例創建成功")
    
    # 創建測試配置
    test_config = {
        "version": 2,
        "tabs": [
            {
                "tab_name": "詳細圈速分析",
                "mdi_windows": [
                    {
                        "window_type": "speed_analysis",
                        "window_title": "Speed Analysis_2025_United States_R",
                        "parameters": {
                            "analysis_type": "speed"
                        }
                    }
                ]
            }
        ]
    }
    
    print("\n💾 測試保存 Workspace...")
    workspace_id = db.create_workspace(
        name="測試Workspace",
        config_json=test_config,
        description="測試用",
        tags="test",
        active_tab_index=0,
        total_tabs=1,
        total_windows=1
    )
    
    print(f"✅ Workspace 保存成功！ID = {workspace_id}")
    
    # 讀取驗證
    print("\n📖 讀取保存的 Workspace...")
    workspace = db.get_workspace(workspace_id)
    
    if workspace:
        print(f"✅ 讀取成功:")
        print(f"  - ID: {workspace['id']}")
        print(f"  - 名稱: {workspace['name']}")
        print(f"  - 視窗數: {workspace['total_windows']}")
        
        # 檢查配置
        config = json.loads(workspace['config_json'])
        print(f"  - 分頁數: {len(config.get('tabs', []))}")
        
        for tab in config.get('tabs', []):
            mdi_wins = tab.get('mdi_windows', [])
            print(f"  - 分頁 '{tab.get('tab_name')}': {len(mdi_wins)} 個視窗")
            for win in mdi_wins:
                print(f"      - {win.get('window_type')}: {win.get('window_title')}")
    else:
        print("❌ 讀取失敗！")
    
    # 清理
    print(f"\n🧹 清理測試數據...")
    db.delete_workspace(workspace_id)
    print("✅ 測試完成")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
