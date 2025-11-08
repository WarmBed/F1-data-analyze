"""
調試 Workspace 載入流程

此腳本會顯示詳細的載入步驟和檢查點
"""

import sys
import json
from pathlib import Path

def analyze_workspace_file(workspace_path):
    """分析 Workspace JSON 檔案內容"""
    print("=" * 80)
    print("📄 Workspace 檔案分析")
    print("=" * 80)
    
    try:
        with open(workspace_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ 檔案載入成功: {workspace_path}")
        print(f"\n📊 Workspace 資訊:")
        print(f"  - Version: {config.get('version', 'N/A')}")
        print(f"  - Timestamp: {config.get('timestamp', 'N/A')}")
        
        # 參數資訊
        params = config.get('parameters', {})
        print(f"\n🎯 儲存的參數:")
        print(f"  - Year: {params.get('year')}")
        print(f"  - Race: {params.get('race_display')} (key: {params.get('race_key')})")
        print(f"  - Session: {params.get('session')}")
        
        # 分頁資訊
        tabs = config.get('tabs', [])
        print(f"\n📑 分頁數量: {len(tabs)}")
        
        for idx, tab in enumerate(tabs):
            tab_name = tab.get('tab_name', 'Unknown')
            windows = tab.get('mdi_windows', [])
            print(f"\n  分頁 {idx + 1}: {tab_name}")
            print(f"    視窗數量: {len(windows)}")
            
            for win_idx, window in enumerate(windows):
                window_type = window.get('window_type', 'Unknown')
                window_title = window.get('window_title', 'Unknown')
                print(f"      視窗 {win_idx + 1}: {window_title}")
                print(f"        類型: {window_type}")
                
                # 檢查參數
                win_params = window.get('parameters', {})
                if win_params:
                    print(f"        參數: {win_params.get('year')} {win_params.get('race')} {win_params.get('session')}")
        
        print("\n" + "=" * 80)
        print("✅ 檔案分析完成")
        print("=" * 80)
        
        return config
        
    except FileNotFoundError:
        print(f"❌ 錯誤: 檔案不存在: {workspace_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ 錯誤: JSON 格式錯誤: {e}")
        return None
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_workspace_serializer():
    """檢查 WorkspaceSerializer 是否正確"""
    print("\n" + "=" * 80)
    print("🔧 WorkspaceSerializer 檢查")
    print("=" * 80)
    
    try:
        from core.workspace_serializer import WorkspaceSerializer
        print("✅ WorkspaceSerializer import 成功")
        
        # 檢查 _rebuild_mdi_window 方法
        import inspect
        method = getattr(WorkspaceSerializer, '_rebuild_mdi_window')
        signature = inspect.signature(method)
        print(f"✅ _rebuild_mdi_window 方法存在")
        print(f"   簽名: _rebuild_mdi_window{signature}")
        
        # 讀取方法源代碼（前幾行）
        source_lines = inspect.getsourcelines(method)[0][:10]
        print(f"\n📜 方法開頭代碼:")
        for line in source_lines:
            print(f"   {line.rstrip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ WorkspaceSerializer 檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_main_window_methods():
    """檢查主視窗方法"""
    print("\n" + "=" * 80)
    print("🖥️ 主視窗方法檢查")
    print("=" * 80)
    
    try:
        # 檢查源代碼中的方法定義
        with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
            source = f.read()
        
        methods = [
            '_create_analysis_module',
            '_get_race_key_from_display',
            '_position_subwindow',
            'on_subwindow_closed'
        ]
        
        for method in methods:
            if f"def {method}(" in source:
                print(f"✅ {method} 方法存在")
            else:
                print(f"❌ {method} 方法不存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 主視窗方法檢查失敗: {e}")
        return False

def main():
    """主程式"""
    print("\n" + "=" * 80)
    print("🔍 Workspace 載入調試工具")
    print("=" * 80)
    
    # 步驟 1: 檢查 WorkspaceSerializer
    if not check_workspace_serializer():
        print("\n❌ WorkspaceSerializer 檢查失敗，停止調試")
        return 1
    
    # 步驟 2: 檢查主視窗方法
    if not check_main_window_methods():
        print("\n❌ 主視窗方法檢查失敗，停止調試")
        return 1
    
    # 步驟 3: 分析 Workspace 檔案（如果提供）
    if len(sys.argv) > 1:
        workspace_path = sys.argv[1]
        config = analyze_workspace_file(workspace_path)
        
        if not config:
            print("\n❌ Workspace 檔案分析失敗")
            return 1
    else:
        print("\n" + "=" * 80)
        print("💡 提示: 可以提供 Workspace 檔案路徑進行分析")
        print("   使用方式: python debug_workspace_load.py workspaces/your_workspace.json")
        print("=" * 80)
    
    print("\n" + "=" * 80)
    print("✅ 所有檢查完成")
    print("=" * 80)
    print("\n📝 下一步:")
    print("  1. 啟動 GUI: python f1t_gui_main.py")
    print("  2. 嘗試載入 Workspace")
    print("  3. 查看終端 log 中的 [WORKSPACE] 訊息")
    print("  4. 尋找錯誤或異常訊息")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
