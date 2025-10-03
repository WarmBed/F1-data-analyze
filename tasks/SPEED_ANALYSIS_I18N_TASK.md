# 速度分析模組國際化任務
## Speed Analysis Module i18n Task

**建立日期**: 2025-10-03  
**優先級**: P1 (高)  
**狀態**: 🔍 分析中

---

## 📋 任務概述

對速度分析模組 (Speed Analysis Module) 進行全面的國際化實施，包括所有用戶界面元素、標籤、按鈕和訊息。

---

## 🔍 現況分析

### 發現的中文文本位置

#### 1. **speed_analysis_chart_widget.py** (16 處)

| 行號 | 類型 | 原始文本 | 位置 |
|-----|------|---------|------|
| 951 | QLabel | 詳細統計信息 | 統計面板標題 |
| 965 | QPushButton | ▼ | 折疊按鈕（註解：向下箭頭表示可以展開）|
| 1021 | QLabel | ⏱️ 圈時間: N/A | 圈時間標籤 |
| 1031 | QLabel | 🛞 輪胎配方: N/A | 輪胎配方標籤 |
| 1047 | QLabel | 🔄 圈數: | 圈數標題 |
| 1113 | setText | ⏱️ 圈時間: {lap_time1} \| {lap_time2} | 雙車手圈時間 |
| 1118 | setText | 🛞 輪胎配方: {compound1} \| {compound2} | 雙車手輪胎配方 |
| 1137 | setText | ⏱️ 圈時間: {lap_time} | 單車手圈時間 |
| 1138 | setText | 🛞 輪胎配方: {compound} | 單車手輪胎配方 |
| 1141 | setText | ⏱️ 圈時間: N/A | 預設圈時間 |
| 1142 | setText | 🛞 輪胎配方: N/A | 預設輪胎配方 |
| 1147 | setText | ⏱️ 圈時間: 錯誤 | 錯誤訊息 |
| 1148 | setText | 🛞 輪胎配方: 錯誤 | 錯誤訊息 |
| 1152 | setHorizontalHeaderLabels | ["項目", "車手1", "車手2", "差值"] | 統計表格標題 |
| 1170 | setText | ▼ | 折疊狀態 |
| 1174 | setText | ▲ | 展開狀態 |

#### 2. **speed_analysis_mdi.py** (多處)

| 行號 | 類型 | 原始文本 | 用途 |
|-----|------|---------|------|
| 59 | emit | 開始載入速度數據... | 狀態訊息 |
| 416 | 變數 | 速度分析 | 模組名稱 |
| 736 | 標題 | 速度分析_{year}_{race}_{session} | 視窗標題 |
| 789 | display_name | 速度分析 | 顯示名稱 |
| 794 | description | F1賽車速度分析模組，支援雙車手圈速對比 | 模組描述 |
| 815 | get_title | 速度分析 - {year} {race} {session} | 動態標題 |

---

## 🎯 需要國際化的項目清單

### A. 標籤和文本 (Labels & Text)

- [ ] **詳細統計信息** → `detailed_statistics`
- [ ] **⏱️ 圈時間** → `lap_time` 
- [ ] **🛞 輪胎配方** → `tire_compound`
- [ ] **🔄 圈數** → `lap_number`
- [ ] **項目** → `item` (表格標題)
- [ ] **車手1** → `driver1` (表格標題)
- [ ] **車手2** → `driver2` (表格標題)
- [ ] **差值** → `difference` (表格標題)

### B. 狀態訊息 (Status Messages)

- [ ] **N/A** → `na` (無數據)
- [ ] **錯誤** → `error` (錯誤訊息)
- [ ] **開始載入速度數據...** → `loading_speed_data`

### C. 模組元數據 (Module Metadata)

- [ ] **速度分析** → `speed_analysis` (display_name)
- [ ] **F1賽車速度分析模組，支援雙車手圈速對比** → `speed_analysis_description`
- [ ] **速度分析 - {year} {race} {session}** → 動態標題模板

### D. 按鈕和控制項 (Buttons & Controls)

- [ ] **▼** → 保持符號，但註解需國際化
- [ ] **▲** → 保持符號，但註解需國際化

---

## 📝 實施計劃

### Phase 1: 準備翻譯鍵 ✅ (已完成參考)

在 `core/gui_i18n.py` 添加所有需要的翻譯鍵：

```python
# 速度分析模組
'speed_analysis': {'zh': '速度分析', 'en': 'Speed Analysis', 'ja': '速度分析'},
'speed_analysis_description': {
    'zh': 'F1賽車速度分析模組，支援雙車手圈速對比',
    'en': 'F1 racing speed analysis module with dual driver comparison',
    'ja': 'F1レーシング速度分析モジュール、2ドライバー比較対応'
},

# 統計面板
'detailed_statistics': {'zh': '詳細統計信息', 'en': 'Detailed Statistics', 'ja': '詳細統計情報'},
'lap_time': {'zh': '圈時間', 'en': 'Lap Time', 'ja': 'ラップタイム'},
'tire_compound': {'zh': '輪胎配方', 'en': 'Tire Compound', 'ja': 'タイヤコンパウンド'},
'lap_number_short': {'zh': '圈數', 'en': 'Lap', 'ja': 'ラップ'},

# 表格標題
'item': {'zh': '項目', 'en': 'Item', 'ja': '項目'},
'driver1': {'zh': '車手1', 'en': 'Driver 1', 'ja': 'ドライバー1'},
'driver2': {'zh': '車手2', 'en': 'Driver 2', 'ja': 'ドライバー2'},
'difference': {'zh': '差值', 'en': 'Difference', 'ja': '差分'},

# 狀態訊息
'na': {'zh': 'N/A', 'en': 'N/A', 'ja': 'N/A'},
'error': {'zh': '錯誤', 'en': 'Error', 'ja': 'エラー'},
'loading_speed_data': {'zh': '開始載入速度數據...', 'en': 'Loading speed data...', 'ja': '速度データを読み込み中...'},
```

### Phase 2: 修改 speed_analysis_chart_widget.py

#### 2.1 添加導入語句
```python
# 在文件頂部添加
from core.gui_i18n import tr
```

#### 2.2 替換靜態標籤
```python
# Line 951: 統計面板標題
title_label = QLabel(tr("detailed_statistics", "詳細統計信息"))

# Line 1021: 圈時間標籤
self.lap_time_label = QLabel(f"⏱️ {tr('lap_time', '圈時間')}: N/A")

# Line 1031: 輪胎配方標籤
self.tyre_compound_label = QLabel(f"🛞 {tr('tire_compound', '輪胎配方')}: N/A")

# Line 1047: 圈數標題
tyre_life_title = QLabel(f"🔄 {tr('lap_number_short', '圈數')}:")
```

#### 2.3 替換動態文本
```python
# Line 1113: 雙車手圈時間
self.lap_time_label.setText(f"⏱️ {tr('lap_time', '圈時間')}: {lap_time1} | {lap_time2}")

# Line 1118: 雙車手輪胎配方
self.tyre_compound_label.setText(f"🛞 {tr('tire_compound', '輪胎配方')}: {compound1} | {compound2}")

# Line 1137-1138: 單車手模式
self.lap_time_label.setText(f"⏱️ {tr('lap_time', '圈時間')}: {lap_time}")
self.tyre_compound_label.setText(f"🛞 {tr('tire_compound', '輪胎配方')}: {compound}")

# Line 1141-1142: 預設值
self.lap_time_label.setText(f"⏱️ {tr('lap_time', '圈時間')}: {tr('na', 'N/A')}")
self.tyre_compound_label.setText(f"🛞 {tr('tire_compound', '輪胎配方')}: {tr('na', 'N/A')}")

# Line 1147-1148: 錯誤訊息
self.lap_time_label.setText(f"⏱️ {tr('lap_time', '圈時間')}: {tr('error', '錯誤')}")
self.tyre_compound_label.setText(f"🛞 {tr('tire_compound', '輪胎配方')}: {tr('error', '錯誤')}")
```

#### 2.4 替換表格標題
```python
# Line 1152: 統計表格標題
headers = [
    tr("item", "項目"),
    tr("driver1", "車手1"),
    tr("driver2", "車手2"),
    tr("difference", "差值")
]
self.stats_table.setHorizontalHeaderLabels(headers)
```

### Phase 3: 修改 speed_analysis_mdi.py

#### 3.1 添加導入語句
```python
from core.gui_i18n import tr
```

#### 3.2 替換模組元數據
```python
# Line 789: display_name
@property
def display_name(self) -> str:
    return tr("speed_analysis", "速度分析")

# Line 794: description
@property
def description(self) -> str:
    return tr("speed_analysis_description", "F1賽車速度分析模組，支援雙車手圈速對比")

# Line 815: get_title
def get_title(self) -> str:
    return f"{tr('speed_analysis', '速度分析')} - {self.current_year} {self.current_race} {self.current_session}"
```

#### 3.3 替換狀態訊息
```python
# Line 59: 狀態訊息
self.status_changed.emit(tr("loading_speed_data", "開始載入速度數據..."))
```

---

## ✅ 驗證檢查清單

完成後需要驗證：

- [ ] 所有 QLabel 文本已使用 tr() 包裹
- [ ] 所有 setText() 調用已使用 tr() 包裹
- [ ] 表格標題已國際化
- [ ] 模組元數據已國際化
- [ ] 檔案導入了 `from core.gui_i18n import tr`
- [ ] 沒有語法錯誤（Pylance 檢查通過）
- [ ] 三種語言的翻譯都已添加（zh, en, ja）
- [ ] 動態文本格式化正確（f-string 中的 tr() 調用）

---

## 🌍 翻譯對照表

### 英文翻譯
| 中文 | 英文 | 用途 |
|-----|------|------|
| 速度分析 | Speed Analysis | 模組名稱 |
| 詳細統計信息 | Detailed Statistics | 面板標題 |
| 圈時間 | Lap Time | 數據標籤 |
| 輪胎配方 | Tire Compound | 數據標籤 |
| 圈數 | Lap | 簡短標籤 |
| 項目 | Item | 表格標題 |
| 車手1 | Driver 1 | 表格標題 |
| 車手2 | Driver 2 | 表格標題 |
| 差值 | Difference | 表格標題 |
| 開始載入速度數據... | Loading speed data... | 狀態訊息 |

### 日文翻譯
| 中文 | 日文 | 用途 |
|-----|------|------|
| 速度分析 | 速度分析 | 模組名稱 |
| 詳細統計信息 | 詳細統計情報 | 面板標題 |
| 圈時間 | ラップタイム | 數據標籤 |
| 輪胎配方 | タイヤコンパウンド | 數據標籤 |
| 圈數 | ラップ | 簡短標籤 |
| 項目 | 項目 | 表格標題 |
| 車手1 | ドライバー1 | 表格標題 |
| 車手2 | ドライバー2 | 表格標題 |
| 差值 | 差分 | 表格標題 |
| 開始載入速度數據... | 速度データを読み込み中... | 狀態訊息 |

---

## 🔄 相關模組

這個任務完成後，可以套用類似模式到其他圈速分析模組：

1. **Throttle Analysis** (油門分析)
2. **Brake Analysis** (煞車分析)
3. **RPM Analysis** (轉速分析)
4. **Gear Analysis** (檔位分析)
5. **Speed Diff Analysis** (速度差異分析)
6. **Distance Diff Analysis** (距離差異分析)
7. **Acceleration Analysis** (加速度分析)

每個模組的結構相似，可以使用相同的國際化模式。

---

## 📊 預計工作量

- **翻譯鍵準備**: 20 分鐘
- **speed_analysis_chart_widget.py 修改**: 30 分鐘
- **speed_analysis_mdi.py 修改**: 15 分鐘
- **測試和驗證**: 15 分鐘
- **總計**: 約 1.5 小時

---

## 🚀 下一步

1. ✅ 添加翻譯鍵到 `core/gui_i18n.py`
2. ⏳ 修改 `speed_analysis_chart_widget.py`
3. ⏳ 修改 `speed_analysis_mdi.py`
4. ⏳ 執行語法檢查
5. ⏳ 測試三種語言的顯示效果
6. ⏳ 更新任務狀態為完成

---

**準備開始實施嗎？** 請確認後我將開始執行具體的程式碼修改。
