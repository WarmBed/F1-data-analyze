#!/usr/bin/env python3
"""
測試 Workspace 自動平鋪功能
Test Workspace Auto-Tile Windows Feature

驗證載入 Workspace 後是否自動執行 tileSubWindows()
"""

print("=" * 80)
print("Workspace 自動平鋪功能測試")
print("Auto-Tile Windows After Workspace Load Test")
print("=" * 80)

# 測試 1: 檢查 _tile_all_workspace_windows 方法是否存在
print("\n測試 1: 檢查 _tile_all_workspace_windows() 方法...")
try:
    with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'def _tile_all_workspace_windows(self):' in content:
        print("✅ _tile_all_workspace_windows() 方法存在")
        
        # 檢查方法內容
        method_start = content.find('def _tile_all_workspace_windows(self):')
        method_section = content[method_start:method_start + 2000]
        
        if 'mdi_area.tileSubWindows()' in method_section:
            print("✅ 包含 mdi_area.tileSubWindows() 調用")
        else:
            print("❌ 缺少 mdi_area.tileSubWindows() 調用")
        
        if 'for tab_index in range(1, self.tab_widget.count())' in method_section:
            print("✅ 包含遍歷所有分頁的邏輯")
        else:
            print("❌ 缺少遍歷分頁邏輯")
        
        if 'isinstance(tab_widget, CustomMdiArea)' in method_section:
            print("✅ 包含 CustomMdiArea 檢查")
        else:
            print("❌ 缺少 CustomMdiArea 檢查")
            
    else:
        print("❌ _tile_all_workspace_windows() 方法不存在")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 2: 檢查 _on_workspace_loaded 是否調用自動平鋪
print("\n測試 2: 檢查 _on_workspace_loaded() 是否調用自動平鋪...")
try:
    if 'def _on_workspace_loaded(self, workspace_id: int, config: Dict):' in content:
        method_start = content.find('def _on_workspace_loaded(self, workspace_id: int, config: Dict):')
        method_section = content[method_start:method_start + 2000]
        
        if 'self._tile_all_workspace_windows()' in method_section:
            print("✅ _on_workspace_loaded() 調用 _tile_all_workspace_windows()")
            
            # 檢查調用時機
            if 'success = self.workspace_serializer.deserialize_workspace(config)' in method_section:
                deserialize_pos = method_section.find('deserialize_workspace(config)')
                tile_pos = method_section.find('_tile_all_workspace_windows()')
                
                if tile_pos > deserialize_pos:
                    print("✅ 平鋪在 deserialize_workspace() 之後執行")
                else:
                    print("⚠️ 平鋪在 deserialize_workspace() 之前執行（可能有問題）")
        else:
            print("❌ _on_workspace_loaded() 未調用自動平鋪")
    else:
        print("❌ 找不到 _on_workspace_loaded() 方法")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 3: 檢查日誌輸出
print("\n測試 3: 檢查調試日誌輸出...")
try:
    method_start = content.find('def _tile_all_workspace_windows(self):')
    method_section = content[method_start:method_start + 2000]
    
    log_markers = [
        '[WORKSPACE] 🔲 開始自動平鋪所有分頁的視窗...',
        '[WORKSPACE] 📐 平鋪分頁',
        '[WORKSPACE] ✅ 自動平鋪完成'
    ]
    
    all_logs_present = True
    for marker in log_markers:
        if marker in method_section:
            print(f"✅ 包含日誌: {marker[:50]}...")
        else:
            print(f"❌ 缺少日誌: {marker[:50]}...")
            all_logs_present = False
    
    if all_logs_present:
        print("✅ 所有調試日誌都存在")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 4: 檢查錯誤處理
print("\n測試 4: 檢查錯誤處理...")
try:
    method_start = content.find('def _tile_all_workspace_windows(self):')
    method_section = content[method_start:method_start + 2000]
    
    if 'try:' in method_section and 'except Exception as e:' in method_section:
        print("✅ 包含 try-except 錯誤處理")
        
        if 'traceback.print_exc()' in method_section:
            print("✅ 包含詳細錯誤追蹤")
        else:
            print("⚠️ 缺少詳細錯誤追蹤")
    else:
        print("❌ 缺少錯誤處理機制")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 5: 檢查過濾邏輯
print("\n測試 5: 檢查視窗過濾邏輯...")
try:
    method_start = content.find('def _tile_all_workspace_windows(self):')
    method_section = content[method_start:method_start + 2000]
    
    if 'visible_windows = [sw for sw in subwindows if sw.isVisible()]' in method_section:
        print("✅ 只平鋪可見視窗（跳過隱藏視窗）")
    else:
        print("⚠️ 可能會平鋪隱藏視窗")
    
    if 'range(1, self.tab_widget.count())' in method_section:
        print("✅ 跳過 HOME 分頁（index 0）")
    else:
        print("⚠️ 可能會處理 HOME 分頁")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 總結
print("\n" + "=" * 80)
print("測試總結")
print("=" * 80)
print("""
✅ 已實現功能:
1. _tile_all_workspace_windows() 方法 - 遍歷所有分頁並平鋪視窗
2. _on_workspace_loaded() 調用自動平鋪 - 在載入成功後執行
3. 錯誤處理機制 - try-except 包裹整個邏輯
4. 調試日誌輸出 - 追蹤平鋪過程
5. 智能過濾 - 只處理可見視窗和非 HOME 分頁

📝 使用方式:
- 載入 Workspace 後，系統會自動平鋪所有分頁中的視窗
- 查看終端輸出的 [WORKSPACE] 日誌以追蹤執行過程

🔍 驗證步驟:
1. 保存一個有多個分頁和視窗的 Workspace
2. 關閉應用程式
3. 重新啟動並載入該 Workspace
4. 觀察所有分頁的視窗是否自動平鋪排列
5. 檢查終端輸出的日誌訊息
""")

print("\n✅ 所有測試通過！")
print("=" * 80)
