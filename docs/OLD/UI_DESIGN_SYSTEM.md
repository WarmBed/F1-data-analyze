# F1T GUI 使用者介面設計系統
# F1T GUI User Interface Design System

> **版本**: V0.11.0  
> **最後更新**: 2025-10-11  
> **適用範圍**: F1 TelemetryStation Pro GUI 模組

---

## 🎨 設計理念 (Design Philosophy)

F1T GUI 採用**專業賽車分析工作站**設計風格，強調以下核心理念：

1. **數據優先 (Data-First)**: 最小化視覺干擾，突出賽車遙測數據
2. **專業工具感 (Professional Tooling)**: 類似 IDE 和工程軟體的穩定、可靠外觀
3. **高資訊密度 (High Information Density)**: 緊湊的 8pt 字體，充分利用螢幕空間
4. **國際化支援 (Internationalization)**: 完整支援英文/繁中/簡中/日文

---

## 🌈 顏色系統 (Color Palette)

### 主要色彩定義 (Primary Colors)

```css
/* 背景顏色 (Background Colors) */
--app-background: #f0f0f0;          /* 應用程式主背景 */
--control-background: #FFFFFF;      /* 控件背景（按鈕、輸入框） */
--dialog-background: #f0f0f0;       /* 對話框背景 */

/* 文字顏色 (Text Colors) */
--primary-text: #333333;            /* 主要文字 */
--disabled-text: #666666;           /* 禁用狀態文字 */

/* 邊框顏色 (Border Colors) */
--border-default: #AAAAAA;          /* 預設邊框 */
--border-hover: #999999;            /* 滑鼠懸停邊框 */
--border-selected: #a3cfbb;         /* 選中狀態邊框 */

/* 強調色 (Accent Colors) */
--accent-green: #4CAF50;            /* 主要強調色（核取方塊、焦點） */
--accent-green-light: #d1e7dd;      /* 淺綠背景（選中項目） */
--accent-green-border: #a3cfbb;     /* 淺綠邊框（選中項目） */

/* 狀態顏色 (State Colors) */
--hover-background: #F0F0F0;        /* 懸停背景 */
--pressed-background: #E0E0E0;      /* 按下背景 */
--selected-background: #d1e7dd;     /* 選中背景 */
```

### 顏色使用規範 (Color Usage Guidelines)

| 元素類型 | 背景色 | 邊框色 | 文字色 | 特殊狀態 |
|---------|--------|--------|--------|----------|
| **應用程式主視窗** | `#f0f0f0` | - | `#333333` | - |
| **對話框 (QDialog)** | `#f0f0f0` | - | `#333333` | - |
| **按鈕 (QPushButton)** | `#FFFFFF` | `#AAAAAA` | `#333333` | 懸停: `#F0F0F0` / 按下: `#E0E0E0` |
| **下拉選單 (QComboBox)** | `#FFFFFF` | `#AAAAAA` | `#333333` | 焦點: 邊框 `#4CAF50` |
| **輸入框 (QLineEdit)** | `#FFFFFF` | `#AAAAAA` | `#333333` | 焦點: 邊框 `#4CAF50` |
| **核取方塊 (QCheckBox)** | - | - | `#333333` | 勾選: 背景 `#4CAF50` |
| **列表 (QListWidget)** | `#FFFFFF` | `#AAAAAA` | `#333333` | 選中: 背景 `#d1e7dd` |
| **群組框 (QGroupBox)** | `#FFFFFF` | `#CCCCCC` | `#333333` | 標題: 粗體 |

---

## 📝 字型系統 (Typography System)

### 字型堆疊 (Font Stack)

```python
# 主要字型設定 (Application Font)
app_font = QFont("Arial", 8)
app.setFont(app_font)

# CSS 字型堆疊 (CSS Font Family)
font-family: 'Arial', 'Microsoft JhengHei', 'SimHei', 'DejaVu Sans', sans-serif;
```

### 字型階層 (Font Hierarchy)

| 元素類型 | 字型 | 大小 | 粗細 | 用途 |
|---------|------|------|------|------|
| **應用程式基準** | Arial | 8pt | Regular | 所有控件的預設字型 |
| **標題文字** | Arial | 9pt | Bold | 對話框標題、群組框標題 |
| **中文顯示** | Microsoft JhengHei | 8pt | Regular | 繁體中文後備字型 |
| **簡體中文** | SimHei | 8pt | Regular | 簡體中文後備字型 |
| **CJK 圖表** | Microsoft JhengHei | - | - | Matplotlib 中文字體 |

### 字型使用規範 (Font Usage Guidelines)

```python
# ✅ 正確：應用程式啟動時設定全域字型
app = QApplication(sys.argv)
font = QFont("Arial", 8)
app.setFont(font)

# ✅ 正確：CSS 中指定字型堆疊（支援多語言）
setStyleSheet("font-family: 'Arial', 'Microsoft JhengHei', sans-serif; font-size: 8pt;")

# ✅ 正確：標題文字使用粗體 9pt
title_label.setStyleSheet("font-size: 9pt; font-weight: bold;")

# ❌ 錯誤：硬編碼單一字型（無中文支援）
setStyleSheet("font-family: 'Arial';")

# ❌ 錯誤：使用過大字型（破壞資訊密度）
setStyleSheet("font-size: 12pt;")
```

---

## 🧩 元件樣式 (Component Styles)

### 1. 對話框 (QDialog)

```css
QDialog {
    background-color: #f0f0f0;
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}
```

**使用場景**: 所有彈出式對話框、設定視窗、選擇器  
**關鍵特性**: 淺灰背景，與主視窗一致

---

### 2. 列表小工具 (QListWidget)

```css
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #AAAAAA;
    border-radius: 3px;
    padding: 2px;
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QListWidget::item:selected {
    background-color: #d1e7dd;  /* 淺綠背景 */
    color: #333333;
    border: 1px solid #a3cfbb;
}

QListWidget::item:hover {
    background-color: #F0F0F0;
}
```

**使用場景**: 
- 遙測圖表選擇器 (Telemetry Chart Selector)
- 車手列表 (Driver List)
- 分析功能樹 (Analysis Function Tree)

**關鍵特性**:
- 白底黑字，清晰易讀
- 選中項目淺綠背景（與強調色一致）
- 懸停時灰色背景提供即時反饋

---

### 3. 按鈕 (QPushButton)

```css
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #AAAAAA;
    border-radius: 3px;
    padding: 5px 10px;
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QPushButton:hover {
    background-color: #F0F0F0;
    border: 1px solid #999999;
}

QPushButton:pressed {
    background-color: #E0E0E0;
}
```

**使用場景**: 所有按鈕（確定、取消、快速選擇）  
**關鍵特性**: 
- 3px 圓角提供現代感
- 懸停/按下有明確的視覺反饋

---

### 4. 下拉選單 (QComboBox)

```css
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #AAAAAA;
    border-radius: 3px;
    padding: 2px 5px;
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QComboBox:hover {
    border: 1px solid #999999;
}

QComboBox:focus {
    border: 1px solid #4CAF50;  /* 焦點時綠色邊框 */
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #AAAAAA;
}
```

**特殊案例: Race ComboBox**

```python
# Race 下拉選單的特殊配置
self.race_combo = AnalysisComboBox()
self.race_combo.setFixedWidth(250)  # 固定寬度容納日期

# 顯示格式: "賽事名稱 (日期)"
# 範例: "Japan (2025-04-06)"
display_text = f"{race_key} ({race_date})"

# 智慧分組顯示
# 1. 已完賽賽事（依時間順序）
# 2. 分隔線 "────────────────"
# 3. 未來賽事（顯示 "[未開賽]" 後綴）
```

**使用場景**: 
- 年份選擇 (Year Selector)
- 賽事選擇 (Race Selector) - **最複雜**
- 賽段選擇 (Session Selector)
- 車手選擇 (Driver Selector)

**關鍵特性**:
- Race ComboBox 寬度 250px（容納日期）
- 智慧分組（已完賽/未來賽事）
- 自動更新（賽季進行時每 12 小時刷新）

---

### 5. 輸入框 (QLineEdit)

```css
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #AAAAAA;
    border-radius: 3px;
    padding: 3px;
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QLineEdit:focus {
    border: 1px solid #4CAF50;  /* 焦點時綠色邊框 */
}
```

**使用場景**: 圈數輸入、搜尋框  
**關鍵特性**: 焦點時綠色邊框提供清晰回饋

---

### 6. 核取方塊 (QCheckBox)

```css
QCheckBox {
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QCheckBox::indicator {
    width: 13px;
    height: 13px;
    border: 1px solid #AAAAAA;
    border-radius: 2px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #4CAF50;  /* 綠色勾選 */
    border: 1px solid #4CAF50;
}

QCheckBox::indicator:hover {
    border: 1px solid #999999;
}
```

**使用場景**: 
- 最速圈選項 (Fastest Lap Option)
- 遙測圖表選擇 (Telemetry Chart Selection)
- 功能開關 (Feature Toggles)

**關鍵特性**: 勾選時顯示品牌綠色 `#4CAF50`

---

### 7. 群組框 (QGroupBox)

```css
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 5px;
    margin-top: 10px;
    padding: 10px;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #333333;
    font-weight: bold;
}
```

**使用場景**: 
- 車手選擇區域 (Driver Selection)
- 遙測選項 (Telemetry Options)
- 參數群組 (Parameter Groups)

**關鍵特性**: 粗體標題，白色背景區分內容

---

## 🏗️ 佈局系統 (Layout System)

### 主視窗結構 (Main Window Structure)

```
┌──────────────────────────────────────────────────────────────┐
│ 選單列 (Menu Bar): 檔案 / 工具 / F1TV Account / 說明      │
├──────────────────────────────────────────────────────────────┤
│ 工具列 (Toolbar): 年份 / 賽事 / 賽段 / 車手 / 快速分析   │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────┬─────────────────────────────────────────────┐ │
│ │ 功能樹   │ MDI 工作區 (Multiple Document Interface)   │ │
│ │          │                                             │ │
│ │ (200px)  │ ┌─────────────┐  ┌─────────────┐          │ │
│ │          │ │ 分析視窗 1  │  │ 分析視窗 2  │          │ │
│ │          │ └─────────────┘  └─────────────┘          │ │
│ └──────────┴─────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│ 狀態列 (Status Bar): API 狀態 / F1TV 狀態 / 時間          │
└──────────────────────────────────────────────────────────────┘
```

### 間距與邊距標準 (Spacing & Margins)

```python
# 主佈局間距 (Main Layout Spacing)
main_layout.setContentsMargins(1, 1, 1, 1)  # 極緊湊邊距
main_layout.setSpacing(1)                   # 最小元件間距

# 對話框佈局間距 (Dialog Layout Spacing)
layout.setSpacing(10)                       # 舒適的元件間距
layout.setContentsMargins(15, 15, 15, 15)   # 標準對話框邊距

# 網格佈局間距 (Grid Layout Spacing)
grid_layout.setSpacing(8)                   # 表單控件間距
```

**設計原則**:
- **主視窗**: 極緊湊（1px），最大化數據顯示空間
- **對話框**: 舒適間距（10-15px），提升可讀性
- **表單**: 中等間距（8px），平衡美觀與效率

---

## 🎯 Race ComboBox 專題 (Race ComboBox Deep Dive)

Race 下拉選單是系統中最複雜的 UI 元件，值得單獨說明。

### 資料結構 (Data Structure)

```python
@dataclass
class SeasonEvent:
    """賽季賽事資料"""
    round_number: int           # 賽事輪次（例如 4）
    race_key: str              # 賽事名稱（例如 "Japan"）
    race_date: str             # 賽事日期（例如 "2025-04-06"）
    is_completed: bool         # 是否已完賽
    sessions: Dict[str, str]   # 可用賽段（例如 {"R": "Race", "Q": "Qualifying"}）
    display_label: str         # 顯示標籤（例如 "Japan (2025-04-06)"）
```

### 顯示邏輯 (Display Logic)

```python
# 步驟 1: 載入賽季資料
events = self._season_provider.get_season_calendar(year)

# 步驟 2: 分組排序
completed_events = [e for e in events if e.is_completed]
upcoming_events = [e for e in events if not e.is_completed]

# 步驟 3: 填充下拉選單
self.race_combo.clear()

# 已完賽賽事
for event in completed_events:
    display = f"{event.race_key} ({event.race_date})"
    self.race_combo.addItem(display, event)

# 分隔線
if completed_events and upcoming_events:
    self.race_combo.addItem("────────────────", None)

# 未來賽事
for event in upcoming_events:
    display = f"{event.race_key} ({event.race_date}) [未開賽]"
    self.race_combo.addItem(display, event)
```

### 智慧選擇 (Smart Selection)

```python
# 優先順序:
# 1. 使用者手動選擇的賽事（年份切換時保留）
# 2. 最近完賽的賽事
# 3. 第一場即將舉行的賽事

if completed_events:
    # 預設選擇最近完賽的賽事
    self.race_combo.setCurrentIndex(len(completed_events) - 1)
elif upcoming_events:
    # 如果沒有已完賽，選擇第一場未來賽事
    self.race_combo.setCurrentIndex(0)
```

### 自動更新機制 (Auto-Refresh)

```python
# 正常模式: 7 天更新一次
cache_duration = timedelta(days=7)

# 賽事接近時: 12 小時更新一次（下一場賽事 7 天內）
if upcoming_events and (datetime.now() - upcoming_events[0].race_date).days <= 7:
    cache_duration = timedelta(hours=12)
```

**關鍵設計決策**:
- **固定寬度 250px**: 確保日期完整顯示
- **分隔線視覺化**: 清楚區分已完賽/未來賽事
- **智慧預設值**: 自動選擇最相關的賽事
- **動態更新**: 賽事接近時提高刷新頻率

---

## 🌐 國際化支援 (Internationalization)

### 語言支援 (Supported Languages)

| 語言 | 代碼 | 字型 | 狀態 |
|------|------|------|------|
| **English** | `en` | Arial | ✅ 完整支援 |
| **繁體中文** | `zh` | Microsoft JhengHei | ✅ 完整支援 |
| **簡體中文** | `zh-CN` | SimHei | ✅ 完整支援 |
| **日本語** | `ja` | Microsoft JhengHei | ⚠️ 部分支援 |

### 翻譯函數使用 (Translation Function Usage)

```python
from core.gui_i18n import tr

# ✅ 正確：提供翻譯鍵與預設文字
label = QLabel(tr("driver1_required", "Driver 1 (Required)"))

# ✅ 正確：格式化翻譯
message = tr('f1tv_already_logged_in', 
             'You are already logged in.\n\nProduct: {product}\nExpires: {exp_str}')
message_formatted = message.format(product="F1TV", exp_str="2025-12-31")

# ❌ 錯誤：硬編碼文字（無法翻譯）
label = QLabel("Driver 1 (Required)")
```

### Matplotlib 中文支援 (Matplotlib Chinese Support)

```python
# 設定 Matplotlib 字型（支援 CJK 字符）
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = [
    'Microsoft JhengHei',  # 繁體中文
    'SimHei',              # 簡體中文
    'DejaVu Sans'          # 英文後備
]
plt.rcParams['axes.unicode_minus'] = False  # 修正負號顯示
```

---

## 📏 尺寸規範 (Size Specifications)

### 控件尺寸標準 (Widget Size Standards)

| 控件類型 | 寬度 | 高度 | 說明 |
|---------|------|------|------|
| **Race ComboBox** | 250px | - | 固定寬度，容納日期 |
| **Driver ComboBox** | 100px | - | 固定寬度，3 字母代碼 |
| **Lap Input** | 50px | - | 固定寬度，1-2 位數字 |
| **Quick Select Button** | - | 28px | 固定高度 |
| **Dialog Button** | 60px | 26px | 確定/取消按鈕 |
| **Function Tree Panel** | 200px | - | 左側功能樹寬度 |
| **MDI Workspace** | 1400px | - | 主工作區寬度（比例分配） |

### 視窗最小尺寸 (Window Minimum Sizes)

```python
# ❌ 已移除所有最小尺寸限制（允許完全自由縮放）
# self.setMinimumSize(1600, 900)  # 已移除
# self.setMinimumSize(400, 200)   # 已移除
```

**設計決策**: 
- V0.11.0 版本移除所有最小尺寸限制
- 允許使用者完全自由調整視窗大小
- 佈局系統自適應調整

---

## 🎨 完整 QSS 樣式表 (Complete QSS Stylesheet)

以下是主視窗的完整 QSS 定義（位於 `f1t_gui_main.py` lines 1624-1750）:

```css
QDialog {
    background-color: #f0f0f0;
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #AAAAAA;
    border-radius: 3px;
    padding: 2px;
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QListWidget::item:selected {
    background-color: #d1e7dd;
    color: #333333;
    border: 1px solid #a3cfbb;
}

QListWidget::item:hover {
    background-color: #F0F0F0;
}

QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #AAAAAA;
    border-radius: 3px;
    padding: 5px 10px;
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QPushButton:hover {
    background-color: #F0F0F0;
    border: 1px solid #999999;
}

QPushButton:pressed {
    background-color: #E0E0E0;
}

QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #AAAAAA;
    border-radius: 3px;
    padding: 2px 5px;
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QComboBox:hover {
    border: 1px solid #999999;
}

QComboBox:focus {
    border: 1px solid #4CAF50;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #AAAAAA;
}

QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #AAAAAA;
    border-radius: 3px;
    padding: 3px;
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QLineEdit:focus {
    border: 1px solid #4CAF50;
}

QCheckBox {
    color: #333333;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QCheckBox::indicator {
    width: 13px;
    height: 13px;
    border: 1px solid #AAAAAA;
    border-radius: 2px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #4CAF50;
    border: 1px solid #4CAF50;
}

QCheckBox::indicator:hover {
    border: 1px solid #999999;
}

QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 5px;
    margin-top: 10px;
    padding: 10px;
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #333333;
    font-weight: bold;
}
```

---

## 🔍 設計決策記錄 (Design Decision Records)

### DDR-001: 8pt 字型選擇 (2024-2025)

**決策**: 採用 8pt Arial 作為基準字型  
**理由**:
- 最大化資訊密度（專業工具標準）
- 在 1080p 螢幕上清晰可讀
- 類似 Visual Studio Code / JetBrains IDE 的字型大小

**影響**: 所有 UI 元件使用 8pt，標題使用 9pt bold

---

### DDR-002: 淺色主題 (2024-2025)

**決策**: 採用淺色主題（`#f0f0f0` 背景 + `#FFFFFF` 控件）  
**理由**:
- 減少螢幕眩光（長時間數據分析）
- 提供更好的顏色對比度（圖表視覺化）
- 符合專業工程軟體習慣（MATLAB, Tableau）

**影響**: 所有對話框、控件統一使用淺色配色

---

### DDR-003: Race ComboBox 固定 250px (2025-09)

**決策**: Race 下拉選單固定 250px 寬度  
**理由**:
- 容納最長賽事名稱 + 日期格式 `"Great Britain (2025-07-06)"`
- 防止佈局因賽事切換而跳動
- 確保日期完整可見（用戶體驗）

**影響**: 所有年份的 Race ComboBox 寬度一致

---

### DDR-004: 移除最小視窗尺寸 (2025-10)

**決策**: V0.11.0 移除所有 `setMinimumSize()` 限制  
**理由**:
- 支援小螢幕設備（筆記型電腦 1366x768）
- 允許使用者完全自由調整佈局
- 現代佈局引擎足夠智慧（自適應調整）

**影響**: 主視窗、對話框、MDI 子視窗可任意縮放

---

### DDR-005: 綠色強調色 #4CAF50 (2024-2025)

**決策**: 採用 Material Design Green 500 作為品牌色  
**理由**:
- 賽車運動的「綠燈」聯想（起跑信號）
- 高可見度（焦點、選中狀態）
- Material Design 成熟配色（可訪問性佳）

**影響**: 核取方塊勾選、輸入框焦點、選中項目背景統一使用綠色系

---

## 📚 參考資源 (References)

### 內部文件 (Internal Documentation)
- `f1t_gui_main.py` (lines 1624-1750) - 完整 QSS 樣式表定義
- `f1t_gui_main.py` (lines 8777-9300) - 主視窗 UI 初始化
- `season_calendar_provider.py` - Race ComboBox 資料提供者
- `core/gui_i18n.py` - 國際化翻譯系統

### 外部參考 (External References)
- [Material Design Color System](https://material.io/design/color)
- [Qt Style Sheets Reference](https://doc.qt.io/qt-5/stylesheet-reference.html)
- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)

---

## 🚀 未來改進 (Future Improvements)

### 計劃中的功能 (Planned Features)
- [ ] **暗色主題 (Dark Theme)**: 可選擇的暗色模式（保護夜間使用者視力）
- [ ] **自訂配色 (Custom Color Schemes)**: 允許使用者自訂強調色
- [ ] **字型縮放 (Font Scaling)**: 支援 9pt/10pt 大字型模式（可訪問性）
- [ ] **高 DPI 支援 (High DPI Support)**: 4K 螢幕優化（目前僅測試 1080p）

### 實驗性功能 (Experimental Features)
- [ ] **動態主題切換 (Runtime Theme Switching)**: 無需重啟即可切換主題
- [ ] **車隊配色方案 (Team Color Schemes)**: 預設 Red Bull、Ferrari 等車隊配色

---

**文件維護者**: Telemetry Station 核心團隊  
**最後審核**: 2025-10-11  
**版本歷史**: 
- V1.0 (2025-10-11): 初始版本，完整記錄 V0.11.0 UI 設計系統
