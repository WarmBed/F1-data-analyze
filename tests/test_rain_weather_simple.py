"""
簡單驗證 rain_weather 支援
"""

def test_window_type_support():
    """驗證 _create_module_instance 中 rain_weather 的邏輯"""
    import inspect
    from core.workspace_serializer import WorkspaceSerializer
    
    print("=" * 60)
    print("驗證 rain_weather 類型支援")
    print("=" * 60)
    
    # 讀取源碼
    source = inspect.getsource(WorkspaceSerializer._create_module_instance)
    
    # 檢查關鍵字
    checks = {
        'rain_weather 在條件中': 'rain_weather' in source,
        'rain_analysis 在條件中': 'rain_analysis' in source,
        '使用 in 運算符': 'in (' in source or 'in ("' in source,
        '導入 RainAnalysisModuleAdapter': 'RainAnalysisModuleAdapter' in source
    }
    
    print("\n[檢查結果]")
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}: {result}")
    
    # 顯示相關代碼片段
    print("\n[相關代碼片段]")
    lines = source.split('\n')
    for i, line in enumerate(lines):
        if 'rain_weather' in line.lower() or ('rain_analysis' in line.lower() and 'rain_weather' not in line.lower()):
            print(f"  Line {i+1}: {line.strip()}")
    
    print("\n" + "=" * 60)
    if all(checks.values()):
        print("✅ 所有檢查通過 - rain_weather 支援已添加")
    else:
        print("⚠️ 某些檢查未通過 - 可能需要進一步修改")
    print("=" * 60)

if __name__ == "__main__":
    test_window_type_support()
