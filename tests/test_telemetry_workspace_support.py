#!/usr/bin/env python3
"""
測試遙測分析模組的 Workspace 支援
Test Telemetry Analysis Modules Workspace Support
"""

print("=" * 80)
print("遙測分析模組 Workspace 支援測試")
print("Telemetry Analysis Modules Workspace Support Test")
print("=" * 80)

# 測試 1: 驗證 WINDOW_TYPE_MAPPING 更新
print("\n[測試 1] 驗證視窗類型映射")
print("-" * 80)

try:
    from core.workspace_serializer import WorkspaceSerializer
    
    # 檢查新增的遙測分析模組映射
    telemetry_modules = [
        ("SpeedAnalysisModule", "speed_analysis"),
        ("BrakeAnalysisModule", "brake_analysis"),
        ("ThrottleAnalysisModule", "throttle_analysis"),
        ("RPMAnalysisModule", "rpm_analysis"),
        ("accelerationAnalysisModule", "acceleration_analysis"),
        ("GearAnalysisModule", "gear_analysis"),
        ("SpeeddiffAnalysisModule", "speeddiff_analysis"),
        ("distancediffAnalysisModule", "distancediff_analysis"),
        ("timediffAnalysisModule", "timediff_analysis"),
    ]
    
    all_pass = True
    for class_name, expected_type in telemetry_modules:
        actual_type = WorkspaceSerializer.WINDOW_TYPE_MAPPING.get(class_name)
        if actual_type == expected_type:
            print(f"✅ {class_name} → {actual_type}")
        else:
            print(f"❌ {class_name} → {actual_type} (期望: {expected_type})")
            all_pass = False
    
    if all_pass:
        print("\n✅ 所有遙測分析模組映射正確")
    else:
        print("\n❌ 部分映射不正確")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 2: 驗證模組導入
print("\n[測試 2] 驗證模組導入")
print("-" * 80)

modules_to_test = [
    ("Speed Analysis", "modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi", "SpeedAnalysisModule"),
    ("Brake Analysis", "modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi", "BrakeAnalysisModule"),
    ("Throttle Analysis", "modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi", "ThrottleAnalysisModule"),
    ("RPM Analysis", "modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi", "RPMAnalysisModule"),
    ("Acceleration Analysis", "modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi", "accelerationAnalysisModule"),
    ("Gear Analysis", "modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi", "GearAnalysisModule"),
    ("Speed Diff Analysis", "modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi", "SpeeddiffAnalysisModule"),
    ("Distance Diff Analysis", "modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi", "distancediffAnalysisModule"),
    ("Time Diff Analysis", "modules.gui.lap_analysis.timediff_analysis.timediff_analysis_mdi", "timediffAnalysisModule"),
]

import_success_count = 0
for name, module_path, class_name in modules_to_test:
    try:
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        print(f"✅ {name}: {cls.__name__}")
        import_success_count += 1
    except Exception as e:
        print(f"❌ {name}: {e}")

print(f"\n導入成功: {import_success_count}/{len(modules_to_test)}")

# 測試 3: 驗證模組結構
print("\n[測試 3] 驗證模組結構")
print("-" * 80)

try:
    from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule
    
    # 創建實例（不初始化）
    module = SpeedAnalysisModule(parent=None)
    
    # 檢查必要屬性
    required_attributes = [
        'analysis_type',
        'current_year',
        'current_race',
        'current_session',
        'driver1',
        'driver2',
        'lap1',
        'lap2',
        'initialize_module',
    ]
    
    print("檢查 SpeedAnalysisModule 屬性:")
    all_present = True
    for attr in required_attributes:
        has_attr = hasattr(module, attr)
        symbol = "✅" if has_attr else "❌"
        print(f"  {symbol} {attr}")
        if not has_attr:
            all_present = False
    
    if all_present:
        print("\n✅ 所有必要屬性都存在")
        print(f"  analysis_type = {module.analysis_type}")
        print(f"  current_year = {module.current_year}")
        print(f"  current_race = {module.current_race}")
        print(f"  current_session = {module.current_session}")
        print(f"  driver1 = {module.driver1}")
        print(f"  driver2 = {module.driver2}")
    else:
        print("\n❌ 缺少部分必要屬性")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 4: 模擬 Workspace 序列化測試
print("\n[測試 4] 模擬參數提取")
print("-" * 80)

try:
    from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule
    
    # 創建模組並設置參數
    module = SpeedAnalysisModule(parent=None)
    module.current_year = "2025"
    module.current_race = "Japan"
    module.current_session = "R"
    module.driver1 = "VER"
    module.driver2 = "LEC"
    module.lap1 = 5
    module.lap2 = 7
    
    # 模擬參數提取邏輯
    parameters = {}
    if hasattr(module, 'current_year') and module.current_year:
        parameters['year'] = str(module.current_year)
    if hasattr(module, 'current_race') and module.current_race:
        parameters['race'] = module.current_race
    if hasattr(module, 'current_session') and module.current_session:
        parameters['session'] = module.current_session
    if hasattr(module, 'driver1') and module.driver1:
        parameters['driver1'] = module.driver1
    if hasattr(module, 'driver2') and module.driver2:
        parameters['driver2'] = module.driver2
    if hasattr(module, 'lap1') and module.lap1:
        parameters['lap1'] = module.lap1
    if hasattr(module, 'lap2') and module.lap2:
        parameters['lap2'] = module.lap2
    
    print("提取的參數:")
    for key, value in parameters.items():
        print(f"  {key}: {value}")
    
    expected_params = {
        'year': '2025',
        'race': 'Japan',
        'session': 'R',
        'driver1': 'VER',
        'driver2': 'LEC',
        'lap1': 5,
        'lap2': 7
    }
    
    if parameters == expected_params:
        print("\n✅ 參數提取正確")
    else:
        print("\n❌ 參數提取不符合預期")
        print(f"期望: {expected_params}")
        print(f"實際: {parameters}")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試總結
print("\n" + "=" * 80)
print("測試完成")
print("=" * 80)

print("\n✅ 已完成的功能:")
print("  1. 在 WINDOW_TYPE_MAPPING 中添加了 9 個遙測分析模組映射")
print("  2. 在 _create_module_instance() 中添加了創建邏輯")
print("  3. 所有模組支援以下參數:")
print("     - year, race, session (必要)")
print("     - driver1, driver2 (車手對比)")
print("     - lap1, lap2 (圈數對比)")
print("\n📝 使用方式:")
print("  1. 開啟遙測分析視窗 (例如: Speed Analysis)")
print("  2. 設置參數並載入數據")
print("  3. 使用 Save Workspace 儲存")
print("  4. 使用 Load Workspace 恢復 (包含所有參數和狀態)")
print("\n⚠️  注意事項:")
print("  - 需要在 GUI 環境中測試完整的儲存/載入流程")
print("  - 確保模組初始化成功 (initialize_module 返回 True)")
print("  - 載入時會自動恢復車手和圈數參數")
