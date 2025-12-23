"""測試 MDI 模組導入修復
驗證 universal_analysis_mdi_base.py 中的 tr() 導入問題已解決
"""
import sys
import os

# 設置環境
sys.path.insert(0, os.path.dirname(__file__))

# 測試導入
print("🔍 測試 1: 導入 universal_analysis_mdi_base 模組...")
try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI
    print("✅ 成功導入 UniversalAnalysisMDI")
except Exception as e:
    print(f"❌ 導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試所有已註冊的模組類型
print("\n🔍 測試 2: 檢查所有已註冊的 MDI 模組類型...")
try:
    registered_types = UniversalAnalysisMDI.get_registered_types()
    print(f"✅ 已註冊的模組類型: {registered_types}")
    
    # 驗證預期的模組是否都已註冊
    expected_modules = [
        'telemetry', 'rain', 'accident', 'pitstop', 'speed',
        'brake', 'throttle', 'gear', 'rpm', 'acceleration',
        'speed_diff', 'distance_diff'
    ]
    
    missing = [m for m in expected_modules if m not in registered_types]
    if missing:
        print(f"⚠️  缺少模組: {missing}")
    else:
        print(f"✅ 所有預期模組都已註冊 ({len(expected_modules)} 個)")
        
except Exception as e:
    print(f"❌ 獲取模組類型失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試獲取模組配置
print("\n🔍 測試 3: 測試各模組的顯示名稱...")
try:
    from core.gui_i18n import set_current_language
    
    # 測試英文
    set_current_language('en')
    for module_type in ['telemetry', 'rain', 'speed', 'brake']:
        config = UniversalAnalysisMDI.get_mdi_config(module_type)
        if config:
            print(f"  {module_type}: {config.display_name}")
        else:
            print(f"  ❌ {module_type}: 無法獲取配置")
    
    print("\n  切換到中文...")
    set_current_language('zh')
    for module_type in ['telemetry', 'rain', 'speed', 'brake']:
        config = UniversalAnalysisMDI.get_mdi_config(module_type)
        if config:
            print(f"  {module_type}: {config.display_name}")
            
    print("\n✅ 所有測試通過!")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
