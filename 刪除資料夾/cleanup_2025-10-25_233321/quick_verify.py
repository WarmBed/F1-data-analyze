"""快速驗證 f1t_gui_main.py 中的模組實現"""

with open("f1t_gui_main.py", "r", encoding="utf-8") as f:
    content = f.read()

modules = [
    "speed_analysis",
    "rpm_analysis",
    "acceleration_analysis",
    "speeddiff_analysis",
    "distancediff_analysis",
    "timediff_analysis",
]

print("檢查 f1t_gui_main.py 中的模組實現:")
print("=" * 50)

for module in modules:
    check_str = f'elif module_type == "{module}"'
    if check_str in content:
        print(f"✅ {module:30s} - 已實現")
    else:
        print(f"❌ {module:30s} - 未實現")

print("=" * 50)
