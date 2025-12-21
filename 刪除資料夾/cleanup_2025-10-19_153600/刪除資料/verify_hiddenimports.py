#!/usr/bin/env python3
"""
驗證 F1T_GUI.spec 中的所有 hiddenimports 是否可以正確導入
用於 EXE 打包前的檢查
"""
import sys
import re
from pathlib import Path

def extract_hiddenimports(spec_file: str) -> list:
    """從 .spec 文件中提取 hiddenimports 列表"""
    with open(spec_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 hiddenimports 區塊
    match = re.search(r'hiddenimports=\[(.*?)\]', content, re.DOTALL)
    if not match:
        print("[ERROR] 無法找到 hiddenimports")
        return []
    
    hidden_str = match.group(1)
    # 提取所有引號內的模組名稱
    imports = re.findall(r"'([^']+)'", hidden_str)
    return imports

def test_import(module_name: str) -> tuple[bool, str]:
    """測試單個模組是否可以導入"""
    try:
        __import__(module_name)
        return True, "[OK]"
    except ModuleNotFoundError as e:
        return False, f"[FAIL] ModuleNotFoundError: {e}"
    except ImportError as e:
        return False, f"[WARN] ImportError: {e}"
    except Exception as e:
        return False, f"[WARN] {type(e).__name__}: {e}"

def main():
    # 設置 UTF-8 輸出
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 80)
    print("F1T GUI - PyInstaller HiddenImports 驗證工具")
    print("=" * 80)
    print()
    
    # 提取 hiddenimports
    spec_file = "F1T_GUI.spec"
    if not Path(spec_file).exists():
        print(f"[ERROR] 找不到 {spec_file}")
        sys.exit(1)
    
    imports = extract_hiddenimports(spec_file)
    print(f"[INFO] 從 {spec_file} 中提取到 {len(imports)} 個 hiddenimports")
    print()
    
    # 測試每個模組
    results = []
    failed = []
    
    print("[INFO] 開始測試導入...")
    print("-" * 80)
    
    for i, module_name in enumerate(imports, 1):
        success, message = test_import(module_name)
        results.append((module_name, success, message))
        
        if not success:
            failed.append(module_name)
            print(f"{i:3d}. {message} {module_name}")
    
    # 輸出摘要
    print()
    print("=" * 80)
    print("[SUMMARY] 測試摘要")
    print("=" * 80)
    print(f"總計模組數: {len(imports)}")
    print(f"[OK] 成功導入: {len(imports) - len(failed)}")
    print(f"[FAIL] 導入失敗: {len(failed)}")
    print()
    
    if failed:
        print("[ERROR] 失敗的模組列表:")
        for module in failed:
            print(f"   - {module}")
        print()
        print("[WARNING] 有模組無法導入，可能導致 EXE 打包後功能異常")
        sys.exit(1)
    else:
        print("[SUCCESS] 所有模組都可以正確導入！")
        print("[OK] 可以安全進行 PyInstaller 打包")
        sys.exit(0)

if __name__ == "__main__":
    main()
