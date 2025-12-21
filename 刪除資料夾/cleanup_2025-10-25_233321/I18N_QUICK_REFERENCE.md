# F1T GUI 多國語言化快速參考
## Quick Reference Guide for i18n

---

## 🌐 已支援的語言 (Supported Languages)

| 代碼 | 語言 | Language |
|------|------|----------|
| `zh` | 中文 | Chinese (Traditional) |
| `en` | 英文 | English |
| `ja` | 日文 | Japanese |

---

## 📋 翻譯條目索引 (Translation Keys Index)

### 分頁右鍵選單 (Tab Context Menu)

| 鍵值 Key | 中文 zh | 英文 en | 日文 ja |
|----------|---------|---------|---------|
| `tab_popout_menu` | 彈出為獨立視窗 | Pop Out as Independent Window | 独立ウィンドウとして表示 |
| `tab_return_menu` | 返回主視窗 | Return to Main Window | メインウィンドウに戻す |
| `tab_already_popped` | 已彈出為獨立視窗 | Already popped out | 既に独立ウィンドウとして表示 |
| `home_tab_no_popout` | HOME 主頁不支援彈出功能 | HOME page does not support pop-out | HOMEページはポップアウトをサポートしていません |
| `popout_tooltip` | 彈出為獨立視窗 | Pop out as independent window | Pop out as independent window |
| `close_tooltip` | 關閉 | Close | 閉じる |

### Workspace 對話框 (Workspace Dialog)

#### 對話框標題和標籤

| 鍵值 Key | 中文 zh | 英文 en | 日文 ja |
|----------|---------|---------|---------|
| `load_workspace_title` | 載入 Workspace | Load Workspace | ワークスペース読込 |
| `available_workspaces` | 可用的 Workspace | Available Workspaces | 利用可能なワークスペース |
| `workspace_details` | Workspace 詳細資訊 | Workspace Details | ワークスペース詳細 |
| `workspace_search` | 搜尋: | Search: | 検索: |

#### 表格標題

| 鍵值 Key | 中文 zh | 英文 en | 日文 ja |
|----------|---------|---------|---------|
| `workspace_id` | ID | ID | ID |
| `workspace_name` | 名稱 | Name | 名前 |
| `tab_count` | 分頁數 | Tabs | タブ数 |
| `window_count` | 視窗數 | Windows | ウィンドウ数 |
| `created_time` | 建立時間 | Created | 作成日時 |
| `description` | 描述 | Description | 説明 |

#### 按鈕

| 鍵值 Key | 中文 zh | 英文 en | 日文 ja |
|----------|---------|---------|---------|
| `load_workspace_btn` | 載入 Workspace | Load Workspace | ワークスペース読込 |
| `delete` | 刪除 | Delete | 削除 |
| `cancel` | 取消 | Cancel | キャンセル |
| `refresh` | 重新整理 | Refresh | 更新 |

---

## 💻 使用範例 (Usage Examples)

### 1. 基本使用

```python
from core.gui_i18n import tr

# 在 GUI 元件中使用
button = QPushButton(tr('load_workspace_btn'))
label = QLabel(tr('workspace_details'))
```

### 2. 格式化字串

```python
from core.gui_i18n import tr

# 單一參數
message = tr('tab_popout_success').format(index=2)
# 結果 (zh): "分頁 2 已成功彈出"

# 多個參數
message = tr('confirm_load_workspace').format(
    name='Test Workspace',
    tabs=3,
    windows=5
)
# 結果 (zh): "確定要載入 Workspace 'Test Workspace' 嗎？\n\n..."
```

### 3. 在 QMessageBox 中使用

```python
from core.gui_i18n import tr

QMessageBox.critical(
    self,
    tr('load_failed'),
    tr('load_workspace_error').format(error=str(e))
)
```

### 4. 切換語言

```python
from core.gui_i18n import set_gui_language, get_gui_language

# 切換為中文
set_gui_language('zh')

# 切換為英文
set_gui_language('en')

# 切換為日文
set_gui_language('ja')

# 獲取當前語言
current_lang = get_gui_language()
print(f"Current language: {current_lang}")
```

---

## 🔧 添加新翻譯 (Adding New Translations)

### 步驟 1: 在 `core/gui_i18n.py` 添加翻譯條目

```python
# 在 _load_translations() 方法中添加
'my_new_key': {
    'zh': '中文翻譯',
    'en': 'English translation',
    'ja': '日本語翻訳'
}
```

### 步驟 2: 在程式碼中使用

```python
from core.gui_i18n import tr

text = tr('my_new_key')
```

### 步驟 3: 測試

```python
from core.gui_i18n import tr, set_gui_language

# 測試中文
set_gui_language('zh')
print(tr('my_new_key'))  # 應輸出: "中文翻譯"

# 測試英文
set_gui_language('en')
print(tr('my_new_key'))  # 應輸出: "English translation"

# 測試日文
set_gui_language('ja')
print(tr('my_new_key'))  # 應輸出: "日本語翻訳"
```

---

## ⚠️ 注意事項 (Important Notes)

### 1. 格式化字串規範

使用 Python 的 `.format()` 方法，不要使用 f-string：

✅ **正確**:
```python
tr('message_key').format(name='John', count=5)
```

❌ **錯誤**:
```python
f"{tr('message_key')}"  # 不支援動態插值
```

### 2. 命名規範

- 使用小寫字母和底線
- 使用描述性名稱
- 分組使用前綴（如 `tab_`, `workspace_`, `preview_`）

✅ **正確**:
```python
'tab_popout_menu'
'workspace_details'
'preview_placeholder'
```

❌ **錯誤**:
```python
'TabPopoutMenu'  # 不要使用駝峰命名
'ws_details'     # 縮寫不清楚
'placeholder'    # 缺少前綴，難以分組
```

### 3. 不要在翻譯中使用 Emoji

根據**原則 4**，翻譯鍵值中不應包含 emoji：

✅ **正確**:
```python
'tab_popout_menu': {
    'zh': '彈出為獨立視窗',
    'en': 'Pop Out as Independent Window'
}
```

❌ **錯誤**:
```python
'tab_popout_menu': {
    'zh': '⧉ 彈出為獨立視窗',  # 不要包含 emoji
    'en': '⧉ Pop Out'
}
```

---

## 🧪 測試清單 (Testing Checklist)

在添加新翻譯後，請執行以下測試：

- [ ] 執行 `python test_tab_i18n.py` 測試分頁相關翻譯
- [ ] 執行 `python test_workspace_i18n.py` 測試 Workspace 相關翻譯
- [ ] 執行 `python test_comprehensive_i18n.py` 綜合測試
- [ ] 在 GUI 中手動測試三種語言
- [ ] 檢查格式化字串是否正確顯示
- [ ] 確認沒有硬編碼的文字

---

## 📚 相關檔案 (Related Files)

| 檔案 | 說明 |
|------|------|
| `core/gui_i18n.py` | 翻譯系統核心檔案 |
| `core/gui_language_config.json` | 語言設定檔 |
| `f1t_gui_main.py` | 主 GUI 檔案 |
| `windows/load_workspace_dialog.py` | Workspace 對話框 |
| `test_tab_i18n.py` | 分頁翻譯測試 |
| `test_workspace_i18n.py` | Workspace 翻譯測試 |
| `test_comprehensive_i18n.py` | 綜合翻譯測試 |
| `I18N_COMPLETION_REPORT.md` | 完成報告 |

---

## 🎯 快速故障排除 (Quick Troubleshooting)

### 問題 1: 翻譯沒有生效

**解決方案**:
1. 檢查是否正確導入 `tr`
2. 確認翻譯鍵值拼寫正確
3. 重啟 GUI 應用程式

### 問題 2: 格式化字串報錯

**解決方案**:
1. 確認使用 `.format()` 而非 f-string
2. 檢查參數名稱是否與翻譯定義一致
3. 確認所有佔位符都有對應的參數

### 問題 3: 顯示錯誤的語言

**解決方案**:
1. 檢查 `gui_language_config.json` 中的設定
2. 使用 `set_gui_language()` 重新設定語言
3. 確認語言代碼正確 (zh/en/ja)

---

**最後更新**: 2025-10-22  
**版本**: 1.0
