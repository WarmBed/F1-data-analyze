# -*- coding: utf-8 -*-
"""
批量修復 manager 檔案中的 self → self.main_window 問題
"""

import re
import os

MANAGERS_DIR = r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\windows\managers"

# 需要替換的模式 (排除 self.main_window 開頭的)
PATTERNS = [
    # QMainWindow 方法
    (r'self\.menuBar\(\)', r'self.main_window.menuBar()'),
    (r'self\.addToolBar', r'self.main_window.addToolBar'),
    (r'self\.setCentralWidget', r'self.main_window.setCentralWidget'),
    (r'self\.close\)', r'self.main_window.close)'),
    (r'self\.statusBar\(\)', r'self.main_window.statusBar()'),
    (r'self\.setWindowTitle', r'self.main_window.setWindowTitle'),
    (r'self\.addDockWidget', r'self.main_window.addDockWidget'),
    (r'self\.removeDockWidget', r'self.main_window.removeDockWidget'),
    
    # 常見的 main_window 屬性
    (r'self\.live_timing_manager(?!\.)', r'self.main_window.live_timing_manager'),
    (r'self\.save_workspace(?!_)', r'self.main_window.save_workspace'),
    (r'self\.load_workspace', r'self.main_window.load_workspace'),
    (r'self\.tile_windows', r'self.main_window.tile_windows'),
    (r'self\.cascade_windows', r'self.main_window.cascade_windows'),
    (r'self\.minimize_all_windows', r'self.main_window.minimize_all_windows'),
    (r'self\.maximize_all_windows', r'self.main_window.maximize_all_windows'),
    (r'self\.restore_all_windows', r'self.main_window.restore_all_windows'),
    (r'self\.close_all_windows', r'self.main_window.close_all_windows'),
    (r'self\.toggle_fullscreen', r'self.main_window.toggle_fullscreen'),
    (r'self\.open_driver_standings', r'self.main_window.open_driver_standings'),
    (r'self\.open_constructor_standings', r'self.main_window.open_constructor_standings'),
    (r'self\.open_parts_analysis', r'self.main_window.open_parts_analysis'),
    (r'self\.open_season_progress', r'self.main_window.open_season_progress'),
    (r'self\.system_settings', r'self.main_window.system_settings'),
    (r'self\.manual_api_health_check', r'self.main_window.manual_api_health_check'),
    (r'self\.set_interface_language', r'self.main_window.set_interface_language'),
    (r'self\.toggle_lap_analysis_linkage', r'self.main_window.toggle_lap_analysis_linkage'),
    (r'self\._open_f1tv_auth_dialog', r'self.main_window._open_f1tv_auth_dialog'),
    (r'self\._logout_f1tv', r'self.main_window._logout_f1tv'),
    (r'self\.show_about_dialog', r'self.main_window.show_about_dialog'),
    (r'self\.live_timing_manager(?!\.)', r'self.main_window.live_timing_manager'),
    
    # 更多遺漏的模式
    (r'self\.check_api_action', r'self.main_window.check_api_action'),
    (r'self\.english_action', r'self.main_window.english_action'),
    (r'self\.chinese_action', r'self.main_window.chinese_action'),
    (r'self\.japanese_action', r'self.main_window.japanese_action'),
    (r'self\.linkage_action', r'self.main_window.linkage_action'),
    (r'self\.f1tv_login_action', r'self.main_window.f1tv_login_action'),
    (r'self\.f1tv_logout_action', r'self.main_window.f1tv_logout_action'),
    
    # QAction 需要 parent
    (r"QAction\(([^,]+),\s*self\)", r"QAction(\1, self.main_window)"),
]

def fix_file(filepath):
    """修復單個檔案"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for pattern, replacement in PATTERNS:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    fixed_count = 0
    for filename in os.listdir(MANAGERS_DIR):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(MANAGERS_DIR, filename)
            if fix_file(filepath):
                print(f"✅ 修復: {filename}")
                fixed_count += 1
    
    print(f"\n共修復 {fixed_count} 個檔案")

if __name__ == '__main__':
    main()
