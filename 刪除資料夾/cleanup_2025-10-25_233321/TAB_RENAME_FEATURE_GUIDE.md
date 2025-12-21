# 🏷️ 分頁重新命名功能實作報告

## 📅 實作日期
**2025年10月22日**

---

## ✅ **功能規格確認**

### 1️⃣ **重命名觸發方式**
- ✅ 右鍵選單新增「重新命名分頁」選項
- ✅ 點擊後彈出輸入對話框（QInputDialog）

### 2️⃣ **重命名限制**
- ✅ **主頁 (索引 0)** 禁止重命名（不顯示右鍵選單）
- ✅ **已彈出分頁** 允許重命名，同步更新獨立視窗標題

### 3️⃣ **命名規則**
- ✅ 無字元限制（允許任意內容）
- ✅ 重複名稱自動添加 `(1)`, `(2)`, `(3)` 後綴

### 4️⃣ **多語言支援**
- ✅ 中文（zh）
- ✅ 英文（en）
- ✅ 日文（ja）

---

## 📝 **實作細節**

### 1. **新增翻譯鍵** (`core/gui_i18n.py`)

```python
# 右鍵選單
'tab_rename_menu': {
    'zh': '重新命名分頁',
    'en': 'Rename Tab',
    'ja': 'タブ名を変更'
},

# 對話框標題
'tab_rename_dialog_title': {
    'zh': '重新命名分頁',
    'en': 'Rename Tab',
    'ja': 'タブ名を変更'
},

# 對話框提示
'tab_rename_dialog_label': {
    'zh': '請輸入新的分頁名稱:',
    'en': 'Enter new tab name:',
    'ja': '新しいタブ名を入力:'
},

# 成功訊息
'tab_rename_success': {
    'zh': '分頁 {index} 已重新命名為: {name}',
    'en': 'Tab {index} renamed to: {name}',
    'ja': 'タブ {index} の名前を変更: {name}'
},

# 主頁限制
'home_tab_no_rename': {
    'zh': 'HOME 主頁不支援重新命名',
    'en': 'HOME page cannot be renamed',
    'ja': 'HOMEページの名前は変更できません'
}
```

---

### 2. **右鍵選單修改** (`f1t_gui_main.py`)

#### 修改前：
```python
# HOME 主頁不顯示彈出選項
if is_home_tab:
    print(f"[TAB_POPOUT] {tr('home_tab_no_popout')}")
    return

menu = QMenu(self)

if is_popped_out:
    return_action = menu.addAction(tr('tab_return_menu'))
    return_action.triggered.connect(lambda: self.pop_back_in_tab(tab_index))
else:
    popout_action = menu.addAction(tr('tab_popout_menu'))
    popout_action.triggered.connect(lambda: self.pop_out_tab(tab_index))
```

#### 修改後：
```python
# HOME 主頁不顯示任何選單
if is_home_tab:
    print(f"[TAB_MENU] {tr('home_tab_no_popout')} / {tr('home_tab_no_rename')}")
    return

menu = QMenu(self)

if is_popped_out:
    # 已彈出：返回 + 重命名
    return_action = menu.addAction(tr('tab_return_menu'))
    return_action.triggered.connect(lambda: self.pop_back_in_tab(tab_index))
    
    menu.addSeparator()  # 分隔線
    
    rename_action = menu.addAction(tr('tab_rename_menu'))
    rename_action.triggered.connect(lambda: self.rename_tab(tab_index))
else:
    # 未彈出：彈出 + 重命名
    popout_action = menu.addAction(tr('tab_popout_menu'))
    popout_action.triggered.connect(lambda: self.pop_out_tab(tab_index))
    
    menu.addSeparator()  # 分隔線
    
    rename_action = menu.addAction(tr('tab_rename_menu'))
    rename_action.triggered.connect(lambda: self.rename_tab(tab_index))
```

---

### 3. **重命名核心邏輯** (`rename_tab` 方法)

```python
def rename_tab(self, tab_index):
    """重新命名分頁"""
    try:
        # 1. 禁止重命名主頁
        if tab_index == 0:
            print(f"[TAB_RENAME] {tr('home_tab_no_rename')}")
            return
        
        # 2. 獲取當前名稱（移除 🔗 圖標）
        current_name = self.tab_widget.tabText(tab_index).replace("🔗 ", "")
        
        # 3. 彈出輸入對話框
        new_name, ok = QInputDialog.getText(
            self,
            tr('tab_rename_dialog_title'),
            tr('tab_rename_dialog_label'),
            QLineEdit.Normal,
            current_name
        )
        
        # 4. 驗證輸入
        if not ok or not new_name:
            return
        
        new_name = new_name.strip()
        
        if new_name == current_name:
            return
        
        # 5. 處理重複名稱
        final_name = self._get_unique_tab_name(new_name)
        
        # 6. 更新分頁名稱
        is_popped_out = (tab_index in self.popped_out_tabs)
        
        if is_popped_out:
            # 已彈出：保留 🔗 圖標 + 同步視窗標題
            self.tab_widget.setTabText(tab_index, f"🔗 {final_name}")
            
            popout_info = self.popped_out_tabs[tab_index]
            standalone_window = popout_info['standalone_window']
            standalone_window.setWindowTitle(f"{final_name} - {APP_FULL_TITLE}")
            popout_info['tab_name'] = final_name
            
            print(f"[TAB_RENAME] {tr('tab_rename_success').format(index=tab_index, name=final_name)} (已彈出)")
        else:
            # 一般分頁
            self.tab_widget.setTabText(tab_index, final_name)
            print(f"[TAB_RENAME] {tr('tab_rename_success').format(index=tab_index, name=final_name)}")
        
    except Exception as e:
        print(f"[TAB_RENAME] ❌ 重新命名失敗: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
```

---

### 4. **唯一名稱生成邏輯** (`_get_unique_tab_name` 方法)

```python
def _get_unique_tab_name(self, base_name):
    """
    獲取唯一的分頁名稱，如果重複則添加 (1), (2), (3) 後綴
    
    Args:
        base_name: 基礎名稱
        
    Returns:
        唯一的分頁名稱
    """
    # 收集所有現有分頁名稱（移除 🔗 圖標）
    existing_names = []
    for i in range(self.tab_widget.count()):
        name = self.tab_widget.tabText(i).replace("🔗 ", "")
        existing_names.append(name)
    
    # 如果基礎名稱不重複，直接返回
    if base_name not in existing_names:
        return base_name
    
    # 名稱重複，添加數字後綴
    counter = 1
    while True:
        new_name = f"{base_name} ({counter})"
        if new_name not in existing_names:
            return new_name
        counter += 1
```

**邏輯範例**：
- 輸入 `"新分頁"`，已存在 `["主頁"]` → 返回 `"新分頁"`（無重複）
- 輸入 `"新分頁"`，已存在 `["新分頁"]` → 返回 `"新分頁 (1)"`
- 輸入 `"新分頁"`，已存在 `["新分頁", "新分頁 (1)"]` → 返回 `"新分頁 (2)"`

---

## 🧪 **測試驗證**

### 1. **語法檢查**
```powershell
✅ python -m py_compile f1t_gui_main.py
✅ python -m py_compile core/gui_i18n.py
```

### 2. **翻譯鍵驗證**
```powershell
# 中文測試
✅ tab_rename_menu: 重新命名分頁
✅ tab_rename_dialog_title: 重新命名分頁
✅ tab_rename_dialog_label: 請輸入新的分頁名稱:
✅ home_tab_no_rename: HOME 主頁不支援重新命名
✅ tab_rename_success: 分頁 2 已重新命名為: 新名稱

# 日文測試
✅ tab_rename_menu: タブ名を変更
✅ tab_rename_dialog_title: タブ名を変更
✅ tab_rename_dialog_label: 新しいタブ名を入力:
✅ home_tab_no_rename: HOMEページの名前は変更できません
✅ tab_rename_success: タブ 1 の名前を変更: 測試
```

---

## 📖 **使用指南**

### **操作步驟**：

1. **啟動 GUI**：
   ```powershell
   python f1t_gui_main.py
   ```

2. **創建分頁**：
   - 點擊右上角的 `[+]` 按鈕
   - 創建多個分頁（Tab 1, Tab 2, Tab 3...）

3. **重命名分頁**：
   - 在分頁標籤上按**右鍵**
   - 選擇「**重新命名分頁**」（中文）/ "**Rename Tab**"（英文）/ "**タブ名を変更**"（日文）
   - 輸入新名稱
   - 點擊「確定」

4. **測試重複名稱**：
   - 嘗試輸入已存在的名稱（如 "Tab 1"）
   - 系統自動添加後綴（變成 "Tab 1 (1)"）

5. **測試彈出視窗同步**：
   - 將分頁彈出為獨立視窗
   - 在已彈出的分頁標籤上按右鍵
   - 重新命名分頁
   - 確認獨立視窗標題同步更新

6. **測試主頁限制**：
   - 在「主頁」標籤上按右鍵
   - 確認沒有顯示任何選單（禁止重命名和彈出）

---

## 🎨 **UI 範例**

### **右鍵選單（未彈出分頁）**：
```
┌─────────────────────────────┐
│ 彈出為獨立視窗              │
├─────────────────────────────┤
│ 重新命名分頁                │
└─────────────────────────────┘
```

### **右鍵選單（已彈出分頁）**：
```
┌─────────────────────────────┐
│ 返回主視窗                  │
├─────────────────────────────┤
│ 重新命名分頁                │
└─────────────────────────────┘
```

### **重命名對話框**：
```
┌─────────────────────────────────┐
│ 重新命名分頁                    │
├─────────────────────────────────┤
│ 請輸入新的分頁名稱:             │
│ ┌─────────────────────────────┐ │
│ │ Tab 1                       │ │
│ └─────────────────────────────┘ │
│                                 │
│        [確定]  [取消]           │
└─────────────────────────────────┘
```

---

## 🔧 **技術細節**

### **檔案修改**：
1. ✅ `core/gui_i18n.py` - 新增 5 個翻譯鍵
2. ✅ `f1t_gui_main.py` - 新增 2 個方法 + 修改 1 個方法
   - `rename_tab(tab_index)` - 重命名核心邏輯
   - `_get_unique_tab_name(base_name)` - 唯一名稱生成
   - `_show_tab_context_menu(pos)` - 右鍵選單更新

### **導入新增**：
```python
from PyQt5.QtWidgets import QInputDialog  # 新增
```

### **特殊處理**：
- ✅ 移除 🔗 圖標後比較名稱
- ✅ 已彈出分頁保留 🔗 圖標
- ✅ 同步更新獨立視窗標題
- ✅ 同步更新追蹤字典 `popped_out_tabs`

---

## ✅ **功能檢查清單**

- [x] 右鍵選單顯示「重新命名分頁」選項
- [x] 主頁禁止重命名（不顯示右鍵選單）
- [x] 彈出輸入對話框（預設填入當前名稱）
- [x] 重複名稱自動添加 `(1)`, `(2)`, `(3)` 後綴
- [x] 已彈出分頁重命名後，獨立視窗標題同步更新
- [x] 已彈出分頁保留 🔗 圖標
- [x] 多語言支援（中文/英文/日文）
- [x] 語法檢查通過
- [x] 翻譯鍵驗證通過

---

## 🚀 **下一步建議**

1. **手動測試**：
   - 啟動 GUI 進行完整的使用者測試
   - 驗證所有邊界情況（空名稱、超長名稱、特殊符號）

2. **可能的增強功能**：
   - 雙擊分頁標籤直接編輯（類似檔案總管）
   - 重命名歷史記錄
   - 快捷鍵支援（如 F2）
   - Workspace 序列化時保存自訂名稱

3. **用戶反饋**：
   - 收集實際使用體驗
   - 調整 UI/UX 細節

---

## 📄 **相關文件**

- `f1t_gui_main.py` - 主程式檔案
- `core/gui_i18n.py` - 國際化翻譯檔案
- `.github/copilot-instructions.md` - 開發指導原則

---

**🎉 功能實作完成！** 🎉
