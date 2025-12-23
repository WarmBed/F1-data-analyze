"""
驗證 DataManager cleanup 修復
檢查所有 Diff 模組的 cleanup 是否清理了正確的 loader
"""

import re
from pathlib import Path

# 檢查的模組列表
modules_to_check = [
    ("timediff_analysis", "timediff_loader", "timediffDataManager"),
    ("speeddiff_analysis", "speeddiff_loader", "speeddiffDataManager"),
    ("distancediff_analysis", "distancediff_loader", "distancediffDataManager"),
]

def check_module_cleanup(module_dir, expected_loader_name, manager_class_name):
    """檢查模組的 cleanup 方法是否清理了正確的 loader"""
    mdi_file = Path(f"modules/gui/lap_analysis/{module_dir}/{module_dir}_mdi.py")
    
    if not mdi_file.exists():
        print(f"❌ 檔案不存在: {mdi_file}")
        return False
    
    content = mdi_file.read_text(encoding='utf-8')
    
    # 檢查是否創建了正確的 loader
    loader_creation_pattern = rf'self\.{expected_loader_name}\s*='
    if not re.search(loader_creation_pattern, content):
        print(f"❌ {module_dir}: 找不到 self.{expected_loader_name} 的創建")
        return False
    
    # 找到 DataManager 的 cleanup 方法
    manager_start = content.find(f"class {manager_class_name}(QObject):")
    if manager_start == -1:
        print(f"❌ {module_dir}: 找不到 {manager_class_name} 類別")
        return False
    
    # 找到 cleanup 方法（在 DataManager 類別內）
    cleanup_start = content.find("def cleanup(self):", manager_start)
    if cleanup_start == -1:
        print(f"❌ {module_dir}: 找不到 cleanup 方法")
        return False
    
    # 提取 cleanup 方法內容（找到下一個同級方法）
    next_method = content.find("\n    def ", cleanup_start + 1)
    cleanup_content = content[cleanup_start:next_method] if next_method != -1 else content[cleanup_start:]
    
    # 檢查是否清理了正確的 loader
    correct_cleanup_pattern = rf'self\.{expected_loader_name}\.cleanup\(\)'
    if re.search(correct_cleanup_pattern, cleanup_content):
        print(f"✅ {module_dir}: cleanup 方法正確清理 self.{expected_loader_name}")
        return True
    
    # 檢查是否仍然使用錯誤的 _speed_loader
    wrong_cleanup_pattern = r'self\._speed_loader\.cleanup\(\)'
    if re.search(wrong_cleanup_pattern, cleanup_content):
        print(f"❌ {module_dir}: cleanup 方法仍然使用錯誤的 self._speed_loader")
        print(f"   應該使用: self.{expected_loader_name}")
        return False
    
    print(f"⚠️  {module_dir}: cleanup 方法中沒有找到 loader.cleanup() 調用")
    return False

def main():
    print("=" * 80)
    print("🔍 檢查 Diff 模組的 cleanup 方法修復")
    print("=" * 80)
    
    all_passed = True
    
    for module_dir, loader_name, manager_class in modules_to_check:
        result = check_module_cleanup(module_dir, loader_name, manager_class)
        if not result:
            all_passed = False
        print()
    
    print("=" * 80)
    if all_passed:
        print("🎉 所有模組的 cleanup 方法都已正確修復！")
    else:
        print("⚠️  部分模組的 cleanup 方法仍需修復")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
