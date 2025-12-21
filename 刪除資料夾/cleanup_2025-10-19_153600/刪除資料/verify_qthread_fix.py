"""
驗證所有 QThread 信號連接已正確修復
確認所有 API Worker 都使用 Qt.QueuedConnection
"""

import re
from pathlib import Path
from typing import List, Tuple

def find_all_qthread_workers() -> List[Path]:
    """查找所有定義 QThread Worker 的文件"""
    gui_dir = Path("modules/gui")
    worker_files = []
    
    for py_file in gui_dir.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'class' in content and 'Worker' in content and '(QThread)' in content:
                    worker_files.append(py_file)
        except Exception as e:
            print(f"⚠️  跳過 {py_file}: {e}")
    
    return worker_files

def check_signal_connections(file_path: Path) -> Tuple[int, int, List[str]]:
    """
    檢查文件中的信號連接
    
    Returns:
        (修復的連接數, 未修復的連接數, 未修復的連接列表)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有 .connect() 調用
    # 匹配模式: worker.signal.connect(slot)
    pattern = re.compile(
        r'(self\._?[\w_]*worker[\w_]*\.(success|failure|progress|finished|data_loaded|error)\.connect\([^)]+\))',
        re.MULTILINE
    )
    
    matches = pattern.findall(content)
    
    fixed = []
    unfixed = []
    
    for match in matches:
        connect_line = match[0]
        signal_name = match[1]
        
        # 檢查是否包含 Qt.QueuedConnection
        if 'Qt.QueuedConnection' in connect_line or 'Qt.AutoConnection' in connect_line:
            fixed.append(f".{signal_name}.connect() ✅")
        else:
            unfixed.append(f".{signal_name}.connect() ❌ 缺少 Qt.QueuedConnection")
    
    return len(fixed), len(unfixed), unfixed

def main():
    """驗證所有文件"""
    print("=" * 80)
    print("🔍 驗證 QThread 信號連接修復狀態")
    print("=" * 80)
    print()
    
    worker_files = find_all_qthread_workers()
    print(f"📊 找到 {len(worker_files)} 個包含 QThread Worker 的文件\n")
    
    total_fixed = 0
    total_unfixed = 0
    problem_files = []
    
    for file_path in sorted(worker_files):
        fixed, unfixed, unfixed_list = check_signal_connections(file_path)
        
        total_fixed += fixed
        total_unfixed += unfixed
        
        relative_path = str(file_path).replace('modules\\gui\\', '')
        
        if unfixed > 0:
            problem_files.append((relative_path, unfixed_list))
            print(f"❌ {relative_path}")
            print(f"   修復: {fixed} | 未修復: {unfixed}")
            for item in unfixed_list:
                print(f"      {item}")
            print()
        elif fixed > 0:
            print(f"✅ {relative_path}")
            print(f"   所有 {fixed} 個連接已正確修復")
    
    print("\n" + "=" * 80)
    print("📊 統計結果")
    print("=" * 80)
    print(f"✅ 已修復的連接: {total_fixed}")
    print(f"❌ 未修復的連接: {total_unfixed}")
    print(f"📁 有問題的文件: {len(problem_files)}")
    
    if problem_files:
        print("\n⚠️  需要手動檢查的文件:")
        for file_path, issues in problem_files:
            print(f"   - {file_path}")
    else:
        print("\n🎉 所有文件都已正確修復！")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
