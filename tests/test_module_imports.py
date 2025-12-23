"""
驗證所有模組導入是否正確
"""

def test_module_imports():
    """測試所有 Workspace 支援的模組是否能正確導入"""
    
    print("=" * 60)
    print("測試模組導入")
    print("=" * 60)
    
    modules_to_test = [
        ("Rain Analysis", "modules.gui.rain_analysis.rain_analysis_module", "RainAnalysisModuleAdapter"),
        ("Tire Analysis", "modules.gui.tire_analysis.tire_analysis_module", "TireAnalysisModuleAdapter"),
        ("Track Analysis", "modules.gui.track_analysis", "TrackAnalysisUniversal"),
        ("Pitstop Analysis", "modules.gui.pitstop_analysis", "PitstopAnalysisModule"),
        ("Accident Analysis", "modules.gui.accident_analysis", "AccidentAnalysisModule"),
        ("Telemetry Analysis", "modules.gui.telemetry_analysis_mdi", "TelemetryAnalysisModule"),
    ]
    
    results = []
    
    for module_name, import_path, class_name in modules_to_test:
        try:
            # 嘗試導入
            if import_path == "modules.gui.track_analysis":
                exec(f"from {import_path} import {class_name}")
            elif import_path == "modules.gui.pitstop_analysis":
                exec(f"from {import_path} import {class_name}")
            elif import_path == "modules.gui.accident_analysis":
                exec(f"from {import_path} import {class_name}")
            else:
                exec(f"from {import_path} import {class_name}")
            
            print(f"✅ {module_name:20s} - 導入成功")
            results.append((module_name, True, None))
            
        except ImportError as e:
            print(f"❌ {module_name:20s} - 導入失敗: {e}")
            results.append((module_name, False, str(e)))
        except Exception as e:
            print(f"⚠️ {module_name:20s} - 其他錯誤: {e}")
            results.append((module_name, False, str(e)))
    
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)
    
    print(f"成功: {success_count}/{total_count}")
    print(f"失敗: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 所有模組導入測試通過！")
    else:
        print("\n⚠️ 部分模組導入失敗，請檢查錯誤訊息")
        for module_name, success, error in results:
            if not success:
                print(f"   - {module_name}: {error}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_module_imports()
