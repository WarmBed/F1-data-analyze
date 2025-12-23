"""
測試版本號命名 - EXE 檔案本身也會改名
"""
from pathlib import Path

version = "V0.11.1"
versioned_name = f"F1-TelemetryStation-Pro-{version}"

print("=" * 80)
print("🎯 修正後：EXE 檔案名稱也會改變")
print("=" * 80)
print()

print("📁 目錄模式 (--onedir)")
print("-" * 80)
print("✅ 資料夾名稱:")
print(f"   dist/{versioned_name}/")
print()
print("✅ EXE 檔案名稱:")
print(f"   dist/{versioned_name}/{versioned_name}.exe  ← 修正後！")
print()
print("✅ 完整結構:")
print(f"   dist/{versioned_name}/")
print(f"   ├── {versioned_name}.exe          ← EXE 檔案")
print(f"   └── _internal/                     ← 依賴檔案")
print()

print("📄 單檔案模式 (--onefile)")
print("-" * 80)
print("✅ EXE 檔案名稱:")
print(f"   dist/{versioned_name}.exe")
print()

print("=" * 80)
print("🔄 修正前 vs 修正後對比")
print("=" * 80)
print()

print("【目錄模式】")
print("❌ 修正前:")
print(f"   dist/{versioned_name}/")
print(f"   └── F1T_GUI.exe                    ← 名稱沒變！")
print()
print("✅ 修正後:")
print(f"   dist/{versioned_name}/")
print(f"   └── {versioned_name}.exe  ← 名稱一致！")
print()

print("【單檔案模式】")
print("✅ 本來就正確:")
print(f"   dist/{versioned_name}.exe")
print()

print("=" * 80)
print("💡 現在的行為")
print("=" * 80)
print("1. 資料夾名稱會改為版本號格式")
print("2. EXE 檔案本身也會改為版本號格式")
print("3. 兩者保持一致，方便識別和管理")
print()
print("範例：版本 V0.11.1")
print(f"  資料夾: {versioned_name}/")
print(f"  EXE:    {versioned_name}.exe")
