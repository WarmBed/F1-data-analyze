"""
測試 Lap Analysis 模組工廠修復
驗證6個新添加的模組是否正確實現
"""

print("=" * 60)
print("🔧 Lap Analysis 模組工廠測試")
print("=" * 60)

# 測試模組導入
modules_to_test = [
    ("speed_analysis", "modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi", "SpeedAnalysisModule"),
    ("rpm_analysis", "modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi", "RPMAnalysisModule"),
    ("acceleration_analysis", "modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi", "accelerationAnalysisModule"),
    ("speeddiff_analysis", "modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi", "SpeeddiffAnalysisModule"),
    ("distancediff_analysis", "modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi", "distancediffAnalysisModule"),
    ("timediff_analysis", "modules.gui.lap_analysis.timediff_analysis.timediff_analysis_mdi", "timediffAnalysisModule"),
]

print("\n📋 測試階段 1: 模組導入驗證")
print("-" * 60)

success_count = 0
for module_name, import_path, class_name in modules_to_test:
    try:
        module = __import__(import_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        print(f"✅ {module_name:25s} - 導入成功 ({class_name})")
        success_count += 1
    except ImportError as e:
        print(f"❌ {module_name:25s} - 導入失敗: {e}")
    except AttributeError as e:
        print(f"❌ {module_name:25s} - 類別不存在: {e}")
    except Exception as e:
        print(f"❌ {module_name:25s} - 未知錯誤: {e}")

print("-" * 60)
print(f"📊 結果: {success_count}/{len(modules_to_test)} 個模組導入成功")

# 檢查 module_alias_groups 映射
print("\n📋 測試階段 2: module_alias_groups 映射驗證")
print("-" * 60)

module_alias_groups = {
    "speed_analysis": ["speed", "速度分析"],
    "rpm_analysis": ["rpm", "RPM分析"],
    "acceleration_analysis": ["acceleration", "加速度分析"],
    "speeddiff_analysis": ["Speeddiff", "speed_diff", "速度差分析"],
    "distancediff_analysis": ["distancediff", "distance_diff", "距離差分析"],
    "timediff_analysis": ["timediff", "time_diff", "時間差分析"],
}

for module_type, aliases in module_alias_groups.items():
    print(f"✅ {module_type:25s} - 別名: {', '.join(aliases)}")

print("-" * 60)

# 檢查 f1t_gui_main.py 中的實現
print("\n📋 測試階段 3: f1t_gui_main.py 實現驗證")
print("-" * 60)

try:
    with open("f1t_gui_main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    implementation_checks = [
        ("speed_analysis", 'elif module_type == "speed_analysis"'),
        ("rpm_analysis", 'elif module_type == "rpm_analysis"'),
        ("acceleration_analysis", 'elif module_type == "acceleration_analysis"'),
        ("speeddiff_analysis", 'elif module_type == "speeddiff_analysis"'),
        ("distancediff_analysis", 'elif module_type == "distancediff_analysis"'),
        ("timediff_analysis", 'elif module_type == "timediff_analysis"'),
    ]
    
    for module_name, check_str in implementation_checks:
        if check_str in content:
            print(f"✅ {module_name:25s} - 實現存在")
        else:
            print(f"❌ {module_name:25s} - 實現不存在！")
    
    print("-" * 60)
except Exception as e:
    print(f"❌ 無法讀取 f1t_gui_main.py: {e}")

print("\n" + "=" * 60)
print("✅ 測試完成！")
print("=" * 60)
print("\n💡 提示: 請重啟 GUI 並載入 Workspace ID=36 驗證修復")
print("   預期結果: 9 個 Lap Analysis 模組應該全部載入成功")
