# GUI 剩餘中文內容分析報告

## 📋 搜尋結果總結

**搜尋日期**：2025-10-03  
**搜尋範圍**：`f1t_gui_main.py`  
**搜尋條件**：QLabel、setText、setWindowTitle 中的中文

---

## ✅ 已完成國際化

### 1. 樹狀圖標題 "分析模組"
- **位置**：Line 5856
- **修改前**：`QLabel("分析模組")`
- **修改後**：`QLabel(tr("analysis_modules", "Analysis Modules"))`
- **狀態**：✅ 已完成

---

## 🔍 發現的剩餘中文內容

### 分類 A：用戶可見的 UI 元素（建議國際化）

| 行號 | 位置 | 內容 | 類型 | 優先級 |
|------|------|------|------|--------|
| 4376 | 視窗分析設定 | `"[TOOL] 視窗分析設定"` | 標題標籤 | 🔴 高 |
| 4404 | 參數標籤 | `"年份:"` | 表單標籤 | 🔴 高 |
| 4419 | 參數標籤 | `"賽事:"` | 表單標籤 | 🔴 高 |
| 4433 | 參數標籤 | `"賽段:"` | 表單標籤 | 🔴 高 |
| 5946 | 分頁計數器 | `"分頁: 0"` | 狀態標籤 | 🟡 中 |
| 6240 | 主頁面標題 | `"🏠 主頁面"` | 標題標籤 | 🔴 高 |
| 6545 | 圖表標題 | `"[CHART] 單場賽事總攬"` | 標題標籤 | 🔴 高 |
| 6679 | 圖表標題 | `"[FINISH] 圈速比較"` | 標題標籤 | 🔴 高 |
| 6761 | 資訊標籤 | `"[FINISH] 賽道軌跡分析已在新視窗中開啟"` | 資訊標籤 | 🔴 高 |
| 8089 | 警告訊息 | `"[WARNING] 賽道分析模組不可用\n\n請使用菜單中的\n'[FINISH] 賽道軌跡分析'"` | 佔位符 | 🟡 中 |
| 8124 | 錯誤訊息 | `"[ERROR] 進站分析模組不可用\n\n請檢查模組是否正確安裝"` | 佔位符 | 🟡 中 |
| 10026 | 開發中訊息 | `"此圖表類型正在開發中...\n請等待後續版本更新"` | 佔位符 | 🟢 低 |
| 10032 | 狀態標籤 | `"🚧 開發中 🚧"` | 狀態標籤 | 🟢 低 |

---

## 📊 統計分析

### 按優先級分類

| 優先級 | 數量 | 說明 |
|--------|------|------|
| 🔴 高 | 7 | 用戶經常看到的介面元素 |
| 🟡 中 | 3 | 偶爾顯示的狀態訊息 |
| 🟢 低 | 2 | 開發/調試訊息 |
| **總計** | **12** | |

### 按類型分類

| 類型 | 數量 | 範例 |
|------|------|------|
| 標題標籤 | 5 | "主頁面"、"圈速比較" |
| 表單標籤 | 3 | "年份:"、"賽事:"、"賽段:" |
| 狀態標籤 | 2 | "分頁: 0"、"開發中" |
| 警告/錯誤訊息 | 2 | 模組不可用警告 |
| **總計** | **12** | |

---

## 🎯 建議的國際化優先順序

### 第一優先級（立即處理）

這些是用戶經常看到的介面元素：

1. **視窗分析設定對話框** (Line 4376, 4404, 4419, 4433)
   ```python
   # 修改前
   title_label = QLabel("[TOOL] 視窗分析設定")
   params_layout.addWidget(QLabel("年份:"), 0, 0)
   params_layout.addWidget(QLabel("賽事:"), 1, 0)
   params_layout.addWidget(QLabel("賽段:"), 2, 0)
   
   # 修改後
   title_label = QLabel(tr("window_analysis_settings", "[TOOL] Window Analysis Settings"))
   params_layout.addWidget(QLabel(tr("year_label", "Year:")), 0, 0)
   params_layout.addWidget(QLabel(tr("race_label", "Race:")), 1, 0)
   params_layout.addWidget(QLabel(tr("session_label", "Session:")), 2, 0)
   ```

2. **主頁面標題** (Line 6240)
   ```python
   # 修改前
   title_label = QLabel("🏠 主頁面")
   
   # 修改後
   title_label = QLabel(tr("home_page", "🏠 Home Page"))
   ```

3. **圖表標題** (Line 6545, 6679, 6761)
   ```python
   # 修改前
   title_label = QLabel("[CHART] 單場賽事總攬")
   title_label = QLabel("[FINISH] 圈速比較")
   info_label = QLabel("[FINISH] 賽道軌跡分析已在新視窗中開啟")
   
   # 修改後
   title_label = QLabel(tr("race_overview_chart", "[CHART] Single Race Overview"))
   title_label = QLabel(tr("lap_time_comparison", "[FINISH] Lap Time Comparison"))
   info_label = QLabel(tr("track_analysis_opened", "[FINISH] Track trajectory analysis opened in new window"))
   ```

### 第二優先級（建議處理）

這些是狀態和資訊訊息：

4. **分頁計數器** (Line 5946)
   ```python
   # 修改前
   self.tab_count_label = QLabel("分頁: 0")
   
   # 修改後
   self.tab_count_label = QLabel(tr("tab_count", "Tabs: {count}").format(count=0))
   ```

5. **模組不可用警告** (Line 8089, 8124)
   ```python
   # 修改前
   placeholder = QLabel("[WARNING] 賽道分析模組不可用\n\n請使用菜單中的\n'[FINISH] 賽道軌跡分析'")
   placeholder = QLabel("[ERROR] 進站分析模組不可用\n\n請檢查模組是否正確安裝")
   
   # 修改後
   placeholder = QLabel(tr("track_module_warning", "[WARNING] Track analysis module unavailable\n\nPlease use menu item\n'[FINISH] Track Trajectory Analysis'"))
   placeholder = QLabel(tr("pitstop_module_error", "[ERROR] Pitstop analysis module unavailable\n\nPlease check if module is properly installed"))
   ```

### 第三優先級（可選）

這些主要是開發訊息：

6. **開發中訊息** (Line 10026, 10032)
   ```python
   # 修改前
   message_label = QLabel("此圖表類型正在開發中...\n請等待後續版本更新")
   status_label = QLabel("🚧 開發中 🚧")
   
   # 修改後
   message_label = QLabel(tr("chart_under_development", "This chart type is under development...\nPlease wait for future updates"))
   status_label = QLabel(tr("under_development", "🚧 Under Development 🚧"))
   ```

---

## 📝 需要添加的翻譯鍵

### 新增到 core/gui_i18n.py

```python
# 視窗分析設定對話框
'window_analysis_settings': {
    'zh': '[TOOL] 視窗分析設定',
    'en': '[TOOL] Window Analysis Settings',
    'ja': '[TOOL] ウィンドウ分析設定'
},

# 主頁面
'home_page': {
    'zh': '🏠 主頁面',
    'en': '🏠 Home Page',
    'ja': '🏠 ホームページ'
},

# 圖表標題
'race_overview_chart': {
    'zh': '[CHART] 單場賽事總攬',
    'en': '[CHART] Single Race Overview',
    'ja': '[CHART] シングルレース概要'
},
'lap_time_comparison': {
    'zh': '[FINISH] 圈速比較',
    'en': '[FINISH] Lap Time Comparison',
    'ja': '[FINISH] ラップタイム比較'
},
'track_analysis_opened': {
    'zh': '[FINISH] 賽道軌跡分析已在新視窗中開啟',
    'en': '[FINISH] Track trajectory analysis opened in new window',
    'ja': '[FINISH] トラック軌跡分析が新しいウィンドウで開きました'
},

# 分頁計數器
'tab_count': {
    'zh': '分頁: {count}',
    'en': 'Tabs: {count}',
    'ja': 'タブ: {count}'
},

# 警告訊息
'track_module_warning': {
    'zh': '[WARNING] 賽道分析模組不可用\n\n請使用菜單中的\n\'[FINISH] 賽道軌跡分析\'',
    'en': '[WARNING] Track analysis module unavailable\n\nPlease use menu item\n\'[FINISH] Track Trajectory Analysis\'',
    'ja': '[WARNING] トラック分析モジュールは利用できません\n\nメニューの\n\'[FINISH] トラック軌跡分析\'を使用してください'
},
'pitstop_module_error': {
    'zh': '[ERROR] 進站分析模組不可用\n\n請檢查模組是否正確安裝',
    'en': '[ERROR] Pitstop analysis module unavailable\n\nPlease check if module is properly installed',
    'ja': '[ERROR] ピットストップ分析モジュールは利用できません\n\nモジュールが正しくインストールされているか確認してください'
},

# 開發訊息
'chart_under_development': {
    'zh': '此圖表類型正在開發中...\n請等待後續版本更新',
    'en': 'This chart type is under development...\nPlease wait for future updates',
    'ja': 'このチャートタイプは開発中です...\n今後のバージョンをお待ちください'
},
'under_development': {
    'zh': '🚧 開發中 🚧',
    'en': '🚧 Under Development 🚧',
    'ja': '🚧 開発中 🚧'
},

# year_label、race_label、session_label 已經存在
```

---

## 🤔 需要確認的問題

### 1. 這些標籤是否需要國際化？

有些標籤帶有 `[TOOL]`、`[CHART]`、`[FINISH]` 等前綴，這些可能是：
- **開發標記**：用於內部測試和調試
- **功能狀態**：向用戶顯示功能完成度

**建議**：
- 如果是向用戶顯示的，應該國際化
- 如果僅用於開發，可以保留英文前綴

### 2. 分頁計數器是否需要動態更新？

Line 5946 的 `"分頁: 0"` 需要動態顯示分頁數量。

**建議方案**：
```python
# 使用格式化字串
self.tab_count_label = QLabel(tr("tab_count", "Tabs: {count}").format(count=0))

# 更新時
self.tab_count_label.setText(tr("tab_count", "Tabs: {count}").format(count=new_count))
```

---

## 🎯 推薦的執行計劃

### 階段 1：核心 UI 元素（立即執行）
1. ✅ 樹狀圖標題 "分析模組"（已完成）
2. ⏳ 視窗分析設定對話框（4 個標籤）
3. ⏳ 主頁面標題
4. ⏳ 圖表標題（3 個）

### 階段 2：狀態訊息（建議執行）
5. ⏳ 分頁計數器
6. ⏳ 模組警告訊息（2 個）

### 階段 3：開發訊息（可選）
7. ⏳ 開發中訊息（2 個）

---

## ✅ 當前進度

- **已完成**：1/13 項（7.7%）
- **待處理**：12/13 項（92.3%）

---

## 📞 下一步行動

請確認：
1. 是否需要國際化所有 12 個剩餘項目？
2. 還是只需要國際化高優先級項目（7 個）？
3. 是否有其他特定的中文內容需要處理？

**建議**：優先處理第一優先級的 7 個項目，這些是用戶最常看到的介面元素。

---

**報告生成日期**：2025-10-03  
**狀態**：等待用戶確認
