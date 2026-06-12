"""
建構後重新命名工具
解決 Windows 檔案佔用導致自動重新命名失敗的問題
"""
import shutil
import time
from pathlib import Path

def rename_build_output():
    """重新命名建構輸出資料夾和 EXE"""
    
    # 導入版本號
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config.version import APP_VERSION
    except ImportError:
        APP_VERSION = input("請輸入版本號 (例如 V0.11.1): ").strip()
    
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    
    # 檢查是否有 F1T_GUI 資料夾
    source_dir = dist_dir / "F1T_GUI"
    
    if not source_dir.exists():
        print("❌ 找不到 dist/F1T_GUI 資料夾")
        print("💡 可能原因:")
        print("   1. 尚未建構 EXE")
        print("   2. 已經重新命名過")
        return False
    
    # 目標資料夾
    versioned_name = f"F1-TelemetryStation-Pro-{APP_VERSION}"
    target_dir = dist_dir / versioned_name
    
    print("=" * 70)
    print("📦 建構後重新命名工具")
    print("=" * 70)
    print(f"來源: {source_dir.relative_to(project_root)}")
    print(f"目標: {target_dir.relative_to(project_root)}")
    print()
    
    # 如果目標已存在，詢問是否覆蓋
    if target_dir.exists():
        response = input(f"⚠️  目標資料夾已存在，是否刪除? (y/N): ").strip().lower()
        if response == 'y':
            print(f"🗑️  刪除舊資料夾: {versioned_name}")
            try:
                shutil.rmtree(target_dir)
                time.sleep(1)  # 等待檔案系統
                print("✅ 刪除成功")
            except Exception as e:
                print(f"❌ 刪除失敗: {e}")
                print("💡 請手動刪除後重試")
                return False
        else:
            print("❌ 取消操作")
            return False
    
    # 執行重新命名
    print(f"\n🔄 重新命名資料夾...")
    try:
        shutil.move(str(source_dir), str(target_dir))
        print(f"✅ 資料夾重新命名成功: {versioned_name}")
    except Exception as e:
        print(f"❌ 資料夾重新命名失敗: {e}")
        print("\n💡 可能的解決方案:")
        print("   1. 關閉檔案總管中的 dist/F1T_GUI 視窗")
        print("   2. 關閉可能佔用檔案的程式")
        print("   3. 以系統管理員身分執行此腳本")
        print("   4. 重新啟動電腦後重試")
        return False
    
    # 重新命名 EXE
    print(f"\n🔄 重新命名 EXE 檔案...")
    old_exe = target_dir / "F1T_GUI.exe"
    new_exe = target_dir / f"{versioned_name}.exe"
    
    if old_exe.exists():
        try:
            old_exe.rename(new_exe)
            print(f"✅ EXE 重新命名成功: {versioned_name}.exe")
        except Exception as e:
            print(f"⚠️  EXE 重新命名失敗: {e}")
            print(f"💡 請手動重新命名: F1T_GUI.exe → {versioned_name}.exe")
    else:
        print(f"⚠️  找不到 F1T_GUI.exe")
    
    # 顯示結果
    print("\n" + "=" * 70)
    print("✅ 重新命名完成！")
    print("=" * 70)
    print(f"📍 位置: dist/{versioned_name}/")
    
    if new_exe.exists():
        size_mb = new_exe.stat().st_size / (1024 * 1024)
        print(f"📦 EXE: {versioned_name}.exe ({size_mb:.2f} MB)")
    
    # 計算總大小
    total_size = sum(f.stat().st_size for f in target_dir.rglob('*') if f.is_file())
    total_mb = total_size / (1024 * 1024)
    print(f"📁 總大小: {total_mb:.2f} MB")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    import sys
    
    print("\n")
    success = rename_build_output()
    
    if success:
        print("\n✅ 完成！")
    else:
        print("\n❌ 重新命名失敗，請檢查上述錯誤訊息")
        sys.exit(1)
    
    input("\n按 Enter 鍵退出...")
