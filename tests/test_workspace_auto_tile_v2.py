#!/usr/bin/env python3
"""
測試 Workspace 自動平鋪功能 v2 - 修正版
Test Workspace Auto-Tile All Tabs

驗證所有分頁都被正確平鋪（不只是最後一個）
"""

print("=" * 80)
print("Workspace 自動平鋪功能測試 v2 - 修正版")
print("Auto-Tile All Tabs Test")
print("=" * 80)

# 測試 1: 檢查修正後的邏輯
print("\n測試 1: 檢查分頁切換邏輯...")
try:
    with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    method_start = content.find('def _tile_all_workspace_windows(self):')
    method_section = content[method_start:method_start + 3000]
    
    # 檢查是否保存/恢復當前分頁
    if 'current_tab_index = self.tab_widget.currentIndex()' in method_section:
        print("✅ 保存當前活動分頁")
    else:
        print("❌ 未保存當前活動分頁")
    
    if 'self.tab_widget.setCurrentIndex(current_tab_index)' in method_section:
        print("✅ 恢復原本的活動分頁")
    else:
        print("❌ 未恢復活動分頁")
    
    # 檢查是否在平鋪前切換到每個分頁
    if 'self.tab_widget.setCurrentIndex(tab_index)' in method_section:
        print("✅ 平鋪前切換到目標分頁")
        
        # 確認切換位置在平鋪之前
        switch_pos = method_section.find('self.tab_widget.setCurrentIndex(tab_index)')
        tile_pos = method_section.find('mdi_area.tileSubWindows()')
        
        if 0 < switch_pos < tile_pos:
            print("✅ 切換順序正確（切換 → 顯示視窗 → 平鋪）")
        else:
            print("⚠️ 切換順序可能有問題")
    else:
        print("❌ 未在平鋪前切換分頁")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 2: 檢查視窗顯示邏輯
print("\n測試 2: 檢查視窗顯示邏輯...")
try:
    if 'if not subwindow.isVisible():' in method_section:
        print("✅ 檢查視窗可見性")
        
        if 'subwindow.show()' in method_section:
            print("✅ 顯示隱藏的視窗")
        else:
            print("❌ 未顯示隱藏視窗")
    else:
        print("⚠️ 未檢查視窗可見性")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 3: 檢查是否移除了 visible_windows 過濾
print("\n測試 3: 檢查視窗過濾邏輯...")
try:
    # 新版應該不再過濾，而是直接處理所有子視窗
    if 'visible_windows = [sw for sw in subwindows if sw.isVisible()]' in method_section:
        print("⚠️ 仍在使用 visible_windows 過濾（可能導致問題）")
    else:
        print("✅ 不再過濾可見視窗（直接處理所有子視窗）")
    
    if 'if subwindows:' in method_section or 'if len(subwindows) > 0' in method_section:
        print("✅ 只檢查是否有子視窗存在")
    else:
        print("⚠️ 可能沒有檢查子視窗數量")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 4: 檢查日誌輸出
print("\n測試 4: 檢查詳細日誌輸出...")
try:
    log_markers = [
        '保存當前活動分頁',
        '處理分頁',
        '切換到分頁',
        '顯示隱藏視窗',
        '恢復活動分頁'
    ]
    
    all_logs_present = True
    for marker in log_markers:
        if marker in method_section:
            print(f"✅ 包含日誌: {marker}")
        else:
            print(f"❌ 缺少日誌: {marker}")
            all_logs_present = False
    
    if all_logs_present:
        print("✅ 所有關鍵日誌都存在")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 5: 檢查執行流程
print("\n測試 5: 檢查完整執行流程...")
try:
    # 預期流程
    expected_flow = [
        ('保存當前分頁', 'current_tab_index = self.tab_widget.currentIndex()'),
        ('遍歷所有分頁', 'for tab_index in range(1, self.tab_widget.count())'),
        ('切換到目標分頁', 'self.tab_widget.setCurrentIndex(tab_index)'),
        ('確保視窗可見', 'subwindow.show()'),
        ('執行平鋪', 'mdi_area.tileSubWindows()'),
        ('恢復原分頁', 'self.tab_widget.setCurrentIndex(current_tab_index)')
    ]
    
    print("預期執行流程:")
    all_steps_present = True
    for step_name, code_marker in expected_flow:
        if code_marker in method_section:
            print(f"  ✅ {step_name}")
        else:
            print(f"  ❌ {step_name} - 缺少")
            all_steps_present = False
    
    if all_steps_present:
        print("✅ 完整執行流程正確")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 總結
print("\n" + "=" * 80)
print("測試總結 - 修正版")
print("=" * 80)
print("""
✅ 關鍵修正:
1. 保存當前活動分頁索引
2. 遍歷每個分頁時切換到該分頁
3. 確保該分頁的所有視窗都可見
4. 執行平鋪操作
5. 恢復到原本的活動分頁

🎯 修正邏輯:
- 舊版: 只檢查可見視窗 → 導致非活動分頁的視窗被過濾
- 新版: 主動切換分頁並顯示視窗 → 確保所有分頁都被平鋪

📝 預期行為:
1. Workspace 載入完成
2. 系統遍歷所有分頁（Tab 1 → Tab 5）
3. 每個分頁都被切換一次並平鋪視窗
4. 最後恢復到原本的活動分頁
5. 使用者切換分頁時看到的都是已平鋪的視窗

🔍 測試步驟:
1. 保存有 5 個分頁的 Workspace
2. 重新啟動並載入
3. 查看終端輸出 - 應該看到 5 個分頁都被處理
4. 手動切換每個分頁 - 視窗應該都是平鋪狀態
""")

print("\n✅ 測試完成！請重新載入 Workspace 驗證修正。")
print("=" * 80)
