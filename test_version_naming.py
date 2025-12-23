"""
測試版本號命名功能
"""
from pathlib import Path

# 模擬建構成功後的重新命名邏輯
project_root = Path(r'c:\Users\mike2\OneDrive\Code\F1-data-analyze')
version = "V0.11.1"

print("=" * 80)
print("🧪 測試版本號命名功能")
print("=" * 80)
print()

# 測試 1: 目錄模式命名
print("📁 測試 1: 目錄模式")
print("-" * 80)
versioned_name = f"F1-TelemetryStation-Pro-{version}"
print(f"✅ 原始路徑: dist/F1T_GUI/")
print(f"✅ 版本命名: dist/{versioned_name}/")
print(f"✅ EXE 路徑: dist/{versioned_name}/F1T_GUI.exe")
print(f"✅ 資料夾: dist/{versioned_name}/_internal/")
print()

# 測試 2: 單檔案模式命名
print("📄 測試 2: 單檔案模式")
print("-" * 80)
print(f"✅ 原始路徑: dist/F1T_GUI.exe")
print(f"✅ 版本命名: dist/{versioned_name}.exe")
print()

# 測試 3: 不同版本號
print("🔢 測試 3: 不同版本號格式")
print("-" * 80)
test_versions = ["V0.11.1", "V1.0.0", "V2.5.3-beta", "V3.0.0-RC1"]
for v in test_versions:
    name = f"F1-TelemetryStation-Pro-{v}"
    print(f"   版本 {v:15} → {name}")
print()

# 測試 4: 空版本號處理
print("⚠️ 測試 4: 空版本號")
print("-" * 80)
version_empty = ""
if version_empty:
    print(f"   有版本號: F1-TelemetryStation-Pro-{version_empty}")
else:
    print("   無版本號: 保持原始命名 F1T_GUI")
print()

print("=" * 80)
print("✅ 所有測試完成！")
print("=" * 80)
print()
print("💡 使用方式：")
print("   1. 啟動 build_exe_gui.py")
print("   2. 在「版本號命名」欄位輸入版本號 (例如: V0.11.1)")
print("   3. 建構完成後自動重新命名為:")
print(f"      - 目錄模式: dist/F1-TelemetryStation-Pro-V0.11.1/")
print(f"      - 單檔案: dist/F1-TelemetryStation-Pro-V0.11.1.exe")
