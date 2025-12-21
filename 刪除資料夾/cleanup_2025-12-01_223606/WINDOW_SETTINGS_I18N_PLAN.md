# Window Settings 對話框多國語言化計畫

**創建日期**：2025-11-14  
**目標**：將 WindowSettingsDialog 的所有用戶可見字串多國語言化  
**遵循原則**：反幻覺編碼原則 4 - 模組多國語言化

---

## 📋 多國語言化範圍

### 1. 對話框基本元素
- 視窗標題
- 群組標題（QGroupBox）
- 標籤文字（QLabel）
- 勾選框文字（QCheckBox）
- 工具提示（Tooltip）

### 2. 已使用 tr() 的字串（參考）

當前代碼中已經有一些字串使用了 `tr()` 函數：

```python
# Line 5791
tr("sync_checkbox_main", "[LINK] Receive Main Window Sync (Year/Race/Session)")

# Line 5793
tr("sync_checkbox_tooltip_main", "When checked, receive parameters from main window and lock analysis controls")

# Line 5868
tr("year_tooltip", "Set year manually")

# Line 5869
tr("race_tooltip", "Set race manually")

# Line 5870
tr("session_tooltip", "Set session manually")

# Line 6137
tr("season_calendar_placeholder", "[無已完成賽事]")

# Line 6247
tr("driver_lap_sync_control", "車手與圈數同步控制")

# Line 6251
tr("sync_driver_lap_checkbox", "[LINK] 與主視窗同步車手與圈數")

# Line 6261
tr("sync_driver_lap_tooltip", "勾選時車手與圈數由主視窗控制，取消勾選可手動設定")

# ...更多
```

---

## 🔍 需要多國語言化的字串清單

### 類別 1：視窗標題 (Line 5759)

**修復前**：
```python
self.setWindowTitle("Window Settings")
```

**修復後**：
```python
self.setWindowTitle(self.tr("Window Settings"))
```

---

### 類別 2：群組標題

#### 2.1 視窗同步控制 (Line 5779)

**修復前**：
```python
sync_group = QGroupBox("視窗同步控制")
```

**修復後**：
```python
sync_group = QGroupBox(self.tr("視窗同步控制"))
```

---

#### 2.2 分析參數 (Line 5796)

**修復前**：
```python
params_group = QGroupBox("分析參數")
```

**修復後**：
```python
params_group = QGroupBox(self.tr("分析參數"))
```

---

### 類別 3：標籤文字

#### 3.1 年份標籤 (Line 5801)

**修復前**：
```python
params_layout.addWidget(QLabel("年份:"), 0, 0)
```

**修復後**：
```python
params_layout.addWidget(QLabel(self.tr("年份:")), 0, 0)
```

---

#### 3.2 賽事標籤 (Line 5816)

**修復前**：
```python
params_layout.addWidget(QLabel("賽事:"), 1, 0)
```

**修復後**：
```python
params_layout.addWidget(QLabel(self.tr("賽事:")), 1, 0)
```

---

#### 3.3 賽段標籤 (Line 5828)

**修復前**：
```python
params_layout.addWidget(QLabel("賽段:"), 2, 0)
```

**修復後**：
```python
params_layout.addWidget(QLabel(self.tr("賽段:")), 2, 0)
```

---

### 類別 4：標題標籤 (Line 5777)

**修復前**：
```python
title_label = QLabel("[TOOL] 視窗分析設定")
```

**修復後**：
```python
title_label = QLabel(self.tr("[TOOL] 視窗分析設定"))
```

---

### 類別 5：工具提示

#### 5.1 同步狀態工具提示 (Line 5860-5862)

**修復前**：
```python
self.year_combo.setToolTip("已啟用同步接收，參數由主程式控制")
self.race_combo.setToolTip("已啟用同步接收，參數由主程式控制")
self.session_combo.setToolTip("已啟用同步接收，參數由主程式控制")
```

**修復後**：
```python
self.year_combo.setToolTip(self.tr("已啟用同步接收，參數由主程式控制"))
self.race_combo.setToolTip(self.tr("已啟用同步接收，參數由主程式控制"))
self.session_combo.setToolTip(self.tr("已啟用同步接收，參數由主程式控制"))
```

---

### 類別 6：Print 語句中的用戶可見訊息

⚠️ **注意**：Print 語句通常用於調試，不一定需要多國語言化。但如果這些訊息會顯示在 UI 或用戶可見的日誌中，則應該多國語言化。

**建議**：保持 print 語句使用英文或中文，不使用 tr()，因為它們主要用於開發調試。

---

## 📊 修復統計

### 已使用 tr() 的字串
- ✅ Line 5791: sync_checkbox_main
- ✅ Line 5793: sync_checkbox_tooltip_main
- ✅ Line 5868-5870: year/race/session tooltips
- ✅ Line 6137: season_calendar_placeholder
- ✅ Line 6247: driver_lap_sync_control
- ✅ Line 6251: sync_driver_lap_checkbox
- ✅ Line 6261: sync_driver_lap_tooltip
- ✅ Line 6271-6402: 所有車手與圈數控制的標籤

**總計**：約 20+ 個字串已經使用 tr()

### 需要添加 tr() 的字串
- ❌ Line 5759: "Window Settings"
- ❌ Line 5777: "[TOOL] 視窗分析設定"
- ❌ Line 5779: "視窗同步控制"
- ❌ Line 5796: "分析參數"
- ❌ Line 5801: "年份:"
- ❌ Line 5816: "賽事:"
- ❌ Line 5828: "賽段:"
- ❌ Line 5860-5862: 工具提示文字（3個）

**總計**：約 10 個字串需要添加 tr()

---

## 🔧 執行步驟

### 步驟 1：讀取目標區域代碼

使用 `read_file` 讀取 Line 5750-5900 的完整代碼。

### 步驟 2：執行批次修復

使用 `replace_string_in_file` 逐一修復每個字串。

**修復順序**：
1. 視窗標題（Line 5759）
2. 標題標籤（Line 5777）
3. 群組標題 1（Line 5779）
4. 群組標題 2（Line 5796）
5. 標籤文字 1-3（Line 5801, 5816, 5828）
6. 工具提示（Line 5860-5862）

### 步驟 3：驗證修復

使用 `read_file` 驗證每個修復是否正確。

---

## ⚠️ 重要注意事項

### 1. 不要修改已經使用 tr() 的字串
已經使用 `tr("key", "default_text")` 格式的字串**不需要再次修復**。

### 2. 使用 self.tr() 而非 tr()
在 QDialog 子類中，應該使用 `self.tr()` 而非全域的 `tr()` 函數。

### 3. 不要修改 print 語句
Print 語句主要用於調試，不需要多國語言化。

### 4. 保持 Tooltip 的一致性
同樣的 tooltip 文字應該使用相同的翻譯鍵值。

---

## 📝 修復範例

### 範例 1：視窗標題

**修復前**：
```python
        self._display_to_race_key: Dict[str, str] = {}
        self.setWindowTitle("Window Settings")
        self.setObjectName("SettingsDialog")
```

**修復後**：
```python
        self._display_to_race_key: Dict[str, str] = {}
        self.setWindowTitle(self.tr("Window Settings"))
        self.setObjectName("SettingsDialog")
```

---

### 範例 2：群組標題和標籤

**修復前**：
```python
        # 標題
        title_label = QLabel("[TOOL] 視窗分析設定")
        title_label.setObjectName("DialogTitle")
        layout.addWidget(title_label)
        
        # 連動控制區域
        sync_group = QGroupBox("視窗同步控制")
        sync_group.setObjectName("SettingsGroup")
```

**修復後**：
```python
        # 標題
        title_label = QLabel(self.tr("[TOOL] 視窗分析設定"))
        title_label.setObjectName("DialogTitle")
        layout.addWidget(title_label)
        
        # 連動控制區域
        sync_group = QGroupBox(self.tr("視窗同步控制"))
        sync_group.setObjectName("SettingsGroup")
```

---

### 範例 3：工具提示

**修復前**：
```python
        if is_sync_enabled:
            self.year_combo.setToolTip("已啟用同步接收，參數由主程式控制")
            self.race_combo.setToolTip("已啟用同步接收，參數由主程式控制")
            self.session_combo.setToolTip("已啟用同步接收，參數由主程式控制")
```

**修復後**：
```python
        if is_sync_enabled:
            self.year_combo.setToolTip(self.tr("已啟用同步接收，參數由主程式控制"))
            self.race_combo.setToolTip(self.tr("已啟用同步接收，參數由主程式控制"))
            self.session_combo.setToolTip(self.tr("已啟用同步接收，參數由主程式控制"))
```

---

## ✅ 完成檢查清單

修復完成後，必須檢查：

- [ ] 所有 QLabel 的文字都使用 self.tr()
- [ ] 所有 QGroupBox 的標題都使用 self.tr()
- [ ] 所有 QCheckBox 的文字都使用 self.tr()（或已使用 tr()）
- [ ] 所有 setToolTip() 的文字都使用 self.tr()（或已使用 tr()）
- [ ] 所有 setWindowTitle() 的文字都使用 self.tr()
- [ ] Print 語句保持不變（不需要 tr()）
- [ ] 已經使用 tr() 的字串保持不變

---

## 🎯 預期效果

修復後，Window Settings 對話框的所有用戶可見文字都可以通過 Qt 的翻譯系統進行多國語言化，支援：
- 繁體中文（默認）
- 英文（通過翻譯文件）
- 其他語言（未來擴展）

---

**版本**：v1.0  
**創建日期**：2025-11-14  
**維護者**：AI 編程助手  
**適用範圍**：WindowSettingsDialog 類別的完整多國語言化
