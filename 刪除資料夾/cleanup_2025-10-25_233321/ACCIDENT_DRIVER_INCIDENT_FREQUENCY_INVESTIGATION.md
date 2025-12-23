# Driver Incident Frequency 功能深度調查報告

## 📋 調查概述

**調查時間**: 2025年10月24日  
**調查目標**: Accident Analysis 模組中的 Driver Incident Frequency 功能  
**調查範圍**: 數據流程、架構設計、實現細節、潛在問題  

---

## 🎯 功能定位

### 基本資訊
- **功能名稱**: Driver Incident Frequency (車手事故頻率)
- **所屬模組**: Accident Analysis (事故分析)
- **CLI Function ID**: 8 (All Incidents Summary)
- **GUI 位置**: `AccidentStatisticsWidget` 第二行組件
- **實現類別**: `DriverIncidentBarChart`

### 功能描述
Driver Incident Frequency 是一個 **ASCII 條形圖組件**，用於統計和顯示每位車手在賽事中涉及的事故數量，並以降序排列顯示前 8 名。

---

## 🏗️ 架構分析

### 1. 數據流程圖

```
API/CLI Backend (Function 8)
    ↓
all_incidents_summary_{year}_{race}_{session}.json
    ↓
AccidentDataManager (API-ONLY 模式)
    ├─ API 請求: /api/v2/analysis/execute?function_id=8
    └─ 本地後備: json/ 目錄 (僅開發模式)
    ↓
Signal: statistics_loaded(dict)
    ↓
AccidentStatisticsWidget.update_statistics_data(json_data)
    ↓
update_driver_incident_chart(json_data)
    ├─ 提取: json_data['data']['all_incidents']
    ├─ 統計: 每個車手的事故數量
    └─ 字典: {driver_code: incident_count}
    ↓
DriverIncidentBarChart.update_chart_data(driver_incidents)
    ↓
_render_chart(data)
    ├─ 排序: 按事故數量降序
    ├─ 限制: 只顯示前 8 名
    └─ 渲染: ASCII 條形圖
    ↓
QLabel 顯示圖表
```

### 2. 核心組件

#### 2.1 數據管理器: AccidentDataManager

**檔案位置**: `modules/gui/accident_analysis/accident_data_manager.py`

**關鍵特性**:
- ✅ 繼承自 `UniversalDataLoader`
- ✅ API-ONLY 模式（強制使用 API 獲取數據）
- ✅ 本地 JSON 後備（僅開發模式，需設置環境變數）
- ✅ 使用 `AccidentAnalysisApiWorker` 背景執行緒

**API 配置**:
```python
"accident_api": AnalysisConfig(
    display_name="事故分析 (API)",
    debug_prefix="ACCIDENT_API",
    data_source="api",
    cli_function="8",
    api_endpoint="/api/v2/analysis/execute",
    api_function_id="8",
    api_timeout=90.0,
    file_patterns=[
        "all_incidents_summary_{year}_{race}_{session}.json",
        "all_incidents_summary_{year}_{race}.json",
        "raw_data_all_incidents_{year}_{race}_*.json",
        "incident_details_{year}_{race}_{session}.json",
        "accident_statistics_summary_{year}_{race}_{session}.json",
    ],
    search_directories=["json", "json_exports", "cache"],
    cache_enabled=True,
)
```

**數據載入方法**:
```python
def loadAccidentStatistics(year, race, session, force_refresh=False):
    # 1. 檢查 API 可用性
    # 2. 啟動 AccidentAnalysisApiWorker 背景執行緒
    # 3. API 成功 → statistics_loaded 信號
    # 4. API 失敗 + 允許後備 → 本地 JSON
    # 5. API 失敗 + 禁用後備 → error_occurred 信號
```

#### 2.2 統計面板: AccidentStatisticsWidget

**檔案位置**: `modules/gui/accident_analysis/accident_analysis_mdi.py` (行 45-700)

**佈局結構**:
```python
QVBoxLayout (垂直堆疊)
├─ 第1行: Flag Statistics Table (固定高度 80px)
├─ 第2行: DriverIncidentBarChart (內容驅動，最小 140px，最大 220px)
└─ 第3行: SafetyPeriodsWidget (可擴展，填充剩餘空間)
```

**數據更新方法**:
```python
def update_statistics_data(self, json_data):
    """主要更新入口點"""
    self.update_statistics_table_from_json(json_data)
    self.update_driver_incident_chart(json_data)  # 🎯 Driver Incident Frequency
    self.update_safety_periods_data(json_data)

def update_driver_incident_chart(self, json_data):
    """車手事故頻率更新邏輯"""
    data_section = json_data.get('data', {})
    all_incidents = data_section.get('all_incidents', [])
    
    # 統計每個車手的事故數量
    driver_incidents = {}
    for incident in all_incidents:
        driver = incident.get('driver_code', '')
        if driver:
            driver_incidents[driver] = driver_incidents.get(driver, 0) + 1
    
    self.driver_chart.update_chart_data(driver_incidents)
```

#### 2.3 圖表組件: DriverIncidentBarChart

**檔案位置**: `modules/gui/accident_analysis/accident_analysis_mdi.py` (行 2575-2670)

**UI 設計**:
```python
QFrame (NoFrame - 無外框)
├─ QVBoxLayout (垂直佈局)
    ├─ QLabel: 標題 "🏆 Driver Incident Frequency"
    └─ QLabel: 圖表區域 (chart_area)
        ├─ 字體: 'Consolas', 'Monaco', monospace (等寬字體)
        ├─ 字體大小: 12px
        ├─ 最小高度: 140px
        ├─ 最大高度: 220px
        └─ 大小策略: Expanding (水平), Minimum (垂直)
```

**ASCII 圖表渲染邏輯**:
```python
def _render_chart(self, data):
    """渲染 ASCII 條形圖"""
    # 1. 排序數據 (降序)
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    max_value = max(data.values()) if data else 1
    
    # 2. 設定條形圖寬度
    max_bar_width = 40  # 字符寬度
    
    # 3. 建立表格標題
    header = f"{'Driver':<6} │ {'Incidents':^40} │ {'Count':>5}"
    separator = "───────┼─" + "─" * 40 + "─┼──────"
    
    # 4. 渲染前 8 名車手
    for driver, count in sorted_data[:8]:
        bar_length = int((count / max_value) * max_bar_width)
        bar = "█" * bar_length
        line = f"{driver:<6} │ {bar:<40} │ {count:>5}"
        chart_lines.append(line)
    
    # 5. 顯示到 QLabel
    self.chart_area.setText("\n".join(chart_lines))
```

**輸出範例**:
```
Driver │             Incidents              │ Count
───────┼────────────────────────────────────┼──────
VER    │ ████████████████████████████████   │    12
HAM    │ ████████████████████████            │     9
LEC    │ ████████████████                    │     6
SAI    │ ████████████                        │     5
PER    │ ██████████                          │     4
NOR    │ ████████                            │     3
RUS    │ ████                                │     2
ALO    │ ██                                  │     1
```

---

## 📊 數據結構分析

### CLI 輸出 JSON 結構

**檔案**: `json/all_incidents_summary_{year}_{race}_{session}.json`

```json
{
  "function_id": 8,
  "function_name": "All Incidents Summary",
  "analysis_type": "all_incidents_summary",
  "session_info": {
    "event_name": "Japan",
    "circuit_name": "Suzuka",
    "session_type": "R",
    "year": 2025
  },
  "timestamp": "2025-10-24T10:30:00",
  "data": {
    "all_incidents": [
      {
        "sequence": 1,
        "time": "0:05:23.456",
        "lap": 3,
        "category": "TRACK_LIMITS",
        "impact": "LOW",
        "severity": "LOW",
        "message": "TRACK LIMITS - CAR 1 (VER)",
        "driver_code": "VER",
        "car_number": "1",
        "flags_mentioned": []
      },
      {
        "sequence": 2,
        "time": "0:12:45.678",
        "lap": 8,
        "category": "YELLOW_FLAG",
        "impact": "MEDIUM",
        "severity": "MEDIUM",
        "message": "YELLOW FLAG - SECTOR 2 - CAR 44 (HAM) INCIDENT",
        "driver_code": "HAM",
        "car_number": "44",
        "flags_mentioned": [
          {
            "type": "YELLOW_FLAG",
            "sector": 2
          }
        ]
      }
      // ... 更多事故記錄
    ],
    "incident_summary": {
      "total_count": 45,
      "by_category": {
        "TRACK_LIMITS": 15,
        "YELLOW_FLAG": 12,
        "INVESTIGATION": 8,
        "PENALTY": 5,
        "RED_FLAG": 2,
        "ACCIDENT": 3
      },
      "by_impact": {
        "LOW": 20,
        "MEDIUM": 15,
        "HIGH": 8,
        "CRITICAL": 2
      },
      "involved_drivers": ["VER", "HAM", "LEC", "SAI", "PER"],
      "flag_statistics": {
        "yellow_flags": {...},
        "red_flags": {...},
        "safety_car_events": {...}
      }
    },
    "driver_involvement": {
      "VER": [
        {
          "sequence": 1,
          "category": "TRACK_LIMITS",
          "severity": "LOW",
          "lap": 3
        }
        // ... VER 的所有事故
      ],
      "HAM": [...]
      // ... 其他車手
    },
    "safety_periods": [...],
    "chronological_sequence": [...]
  }
}
```

### 關鍵欄位說明

| 欄位路徑 | 類型 | 用途 | Driver Incident Frequency 使用 |
|---------|------|------|-------------------------------|
| `data.all_incidents` | List[Dict] | 所有事故詳細列表 | ✅ **主要數據來源** |
| `data.all_incidents[].driver_code` | String | 車手代碼 (3字母) | ✅ **統計鍵值** |
| `data.all_incidents[].category` | String | 事故類別 | ❌ 不使用（僅統計數量） |
| `data.all_incidents[].severity` | String | 嚴重程度 | ❌ 不使用（僅統計數量） |
| `data.incident_summary` | Dict | 統計摘要 | ❌ 不使用（自行統計） |
| `data.driver_involvement` | Dict | 車手涉及詳情 | ❌ 不使用（自行統計） |

---

## 🔍 實現細節分析

### 1. 數據統計邏輯

**位置**: `accident_analysis_mdi.py:590-603`

```python
def update_driver_incident_chart(self, json_data):
    """更新車手事故頻率圖表"""
    try:
        # Step 1: 提取數據區塊
        data_section = json_data.get('data', {})
        all_incidents = data_section.get('all_incidents', [])
        
        # Step 2: 統計每個車手的事故數量
        driver_incidents = {}
        for incident in all_incidents:
            driver = incident.get('driver_code', '')
            if driver:  # 只統計有明確車手代碼的事故
                driver_incidents[driver] = driver_incidents.get(driver, 0) + 1
        
        # Step 3: 傳遞給圖表組件
        self.driver_chart.update_chart_data(driver_incidents)
        
    except Exception as e:
        print(f"[AccidentStatisticsWidget] 車手事故圖表更新失敗: {e}")
```

**邏輯評估**:
- ✅ **簡潔高效**: 使用字典累加，時間複雜度 O(n)
- ✅ **容錯處理**: 檢查 `driver_code` 是否存在
- ✅ **異常捕捉**: 避免單個組件錯誤影響整體
- ⚠️ **潛在問題**: 
  - 未過濾空字串 `''` 的車手代碼（可能統計到無效數據）
  - 未過濾 `'UNK'` 等未知車手代碼
  - 未考慮大小寫不一致問題（雖然實務上應該都是大寫）

### 2. 圖表渲染邏輯

**位置**: `accident_analysis_mdi.py:2634-2668`

```python
def _render_chart(self, data):
    """渲染 ASCII 條形圖 - 放大1px，完美對齊線條"""
    if not data:
        self.chart_area.setText(tr('no_data_available', 'No incident data available'))
        return
        
    # 排序數據
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    max_value = max(data.values()) if data else 1
    
    # 放大條形圖寬度 - 增加1px效果
    max_bar_width = 40  # 從35增加到40
    
    chart_lines = []
    
    # 添加標題行 - 使用固定寬度確保完美對齊
    header = f"{'Driver':<6} │ {'Incidents':^40} │ {'Count':>5}"
    separator = "───────┼─" + "─" * 40 + "─┼──────"
    
    chart_lines.append(header)
    chart_lines.append(separator)
    
    for driver, count in sorted_data[:8]:  # 只顯示前8名
        # 計算條形長度
        bar_length = int((count / max_value) * max_bar_width) if max_value > 0 else 0
        bar = "█" * bar_length
        
        # 格式化輸出 - 完美對齊所有列
        # Driver: 左對齊6字符, Bar: 左對齊40字符, Count: 右對齊5字符
        line = f"{driver:<6} │ {bar:<40} │ {count:>5}"
        chart_lines.append(line)
    
    chart_text = "\n".join(chart_lines)
    self.chart_area.setText(chart_text)
```

**設計評估**:
- ✅ **視覺對齊**: 使用等寬字體 + 精確的格式化字串
- ✅ **排序展示**: 降序排列，一目了然
- ✅ **限制數量**: 只顯示前 8 名，避免過長
- ✅ **比例縮放**: 最大值對應 40 字符寬度
- ✅ **國際化**: 使用 `tr()` 函數包裹提示訊息
- ⚠️ **潛在問題**:
  - 未處理車手代碼超過 6 字符的情況（實務上不會發生）
  - 未處理事故數量超過 99999 的情況（實務上不會發生）
  - `int()` 向下取整可能導致相同數量的車手條形長度不同

### 3. 無數據處理

**位置**: `accident_analysis_mdi.py:2626-2632`

```python
def update_chart_data(self, driver_incidents):
    """更新圖表數據 - 僅使用真實數據"""
    if not driver_incidents:
        # ⚠️ 禁用模擬數據政策：顯示無數據訊息
        self.chart_area.setText(tr(
            'no_incident_data', 
            'No driver incident data available\n\nPlease load accident analysis data from API or CLI'
        ))
        return
        
    self._render_chart(driver_incidents)
```

**評估**:
- ✅ **遵循政策**: 完全符合「禁用模擬數據政策」
- ✅ **用戶引導**: 提示用戶如何獲取數據
- ✅ **國際化**: 使用 `tr()` 函數
- ✅ **清晰提示**: 明確說明問題和解決方案

---

## 🧪 測試建議

### 測試場景 1: 正常數據流程

**步驟**:
1. 啟動 API 服務器 (`python refactored_api.py`)
2. 在 GUI 中打開 Accident Analysis
3. 選擇賽事參數 (例如: 2025, Japan, R)
4. 點擊載入數據

**預期結果**:
- ✅ API 請求成功
- ✅ `statistics_loaded` 信號觸發
- ✅ Driver Incident Frequency 圖表顯示前 8 名車手
- ✅ 條形長度正確對應事故數量
- ✅ 對齊完美無錯位

### 測試場景 2: API 不可用（本地後備）

**步驟**:
1. 確保 API 服務器未啟動
2. 設置環境變數: `F1T_ALLOW_ACCIDENT_JSON_FALLBACK=1`
3. 手動執行 CLI 生成 JSON: 
   ```powershell
   python f1_analysis_modular_main.py -f 8 -y 2025 -r Japan -s R
   ```
4. 在 GUI 中載入數據

**預期結果**:
- ✅ API 請求失敗
- ✅ 自動切換到本地 JSON 後備
- ✅ 成功讀取 `json/all_incidents_summary_2025_Japan_R.json`
- ✅ Driver Incident Frequency 圖表正常顯示

### 測試場景 3: 無數據處理

**步驟**:
1. 確保 API 不可用且未設置後備環境變數
2. 未生成對應的 JSON 檔案
3. 在 GUI 中載入數據

**預期結果**:
- ✅ 顯示錯誤訊息
- ✅ Driver Incident Frequency 顯示:
  ```
  No driver incident data available
  
  Please load accident analysis data from API or CLI
  ```

### 測試場景 4: 邊界條件

**子場景 4.1: 少於 8 名車手**
- 預期: 只顯示實際數量的車手（例如 5 名）

**子場景 4.2: 超過 8 名車手**
- 預期: 只顯示前 8 名，其餘被截斷

**子場景 4.3: 所有車手事故數量相同**
- 預期: 所有條形長度相同（都是 40 字符）

**子場景 4.4: 只有 1 起事故**
- 預期: 只有 1 名車手，條形長度為 40 字符

**子場景 4.5: 事故數量差距極大**
- 例如: VER=50, HAM=1
- 預期: VER 條形長度 40, HAM 條形長度 0 或 1（取決於 `int()` 結果）

---

## 🐛 已識別問題

### 問題 1: 未過濾無效車手代碼

**嚴重程度**: 🟡 中等

**位置**: `accident_analysis_mdi.py:590-603`

**問題描述**:
```python
for incident in all_incidents:
    driver = incident.get('driver_code', '')
    if driver:  # ❌ 只檢查是否存在，未檢查是否有效
        driver_incidents[driver] = driver_incidents.get(driver, 0) + 1
```

**潛在影響**:
- 可能統計到空字串 `''` 的車手（雖然 `if driver` 會過濾）
- 可能統計到 `'UNK'` (Unknown) 車手代碼
- 圖表顯示無意義的 "UNK" 或其他無效代碼

**建議修復**:
```python
for incident in all_incidents:
    driver = incident.get('driver_code', '').strip().upper()
    if driver and driver != 'UNK' and len(driver) == 3:  # ✅ 嚴格驗證
        driver_incidents[driver] = driver_incidents.get(driver, 0) + 1
```

### 問題 2: 整數向下取整導致精度損失

**嚴重程度**: 🟢 低

**位置**: `accident_analysis_mdi.py:2655`

**問題描述**:
```python
bar_length = int((count / max_value) * max_bar_width)  # ❌ 向下取整
```

**潛在影響**:
- 事故數量接近的車手可能顯示相同長度的條形
- 例如: max_value=10, VER=9 → 36字符, HAM=8 → 32字符
- 但 SAI=7 和 PER=6 可能都顯示 28 字符（取決於計算結果）

**建議修復**:
```python
bar_length = round((count / max_value) * max_bar_width)  # ✅ 四捨五入
```

### 問題 3: 未使用 CLI 預先統計的 driver_involvement

**嚴重程度**: 🟡 中等（效能優化）

**問題描述**:
CLI 已經在 `data.driver_involvement` 中提供了每個車手的詳細事故列表，但 GUI 選擇重新遍歷 `all_incidents` 進行統計。

**當前實現**:
```python
# ❌ 重新統計（O(n) 複雜度）
for incident in all_incidents:
    driver = incident.get('driver_code', '')
    if driver:
        driver_incidents[driver] = driver_incidents.get(driver, 0) + 1
```

**優化建議**:
```python
# ✅ 直接使用預先統計的數據（O(m) 複雜度，m << n）
driver_involvement = data_section.get('driver_involvement', {})
driver_incidents = {
    driver: len(incidents) 
    for driver, incidents in driver_involvement.items()
}
```

**性能對比**:
- 當前: 遍歷所有事故 (例如 150 個) → 150 次迭代
- 優化: 遍歷涉及車手 (例如 20 個) → 20 次迭代

### 問題 4: 未處理多車手事故的重複計數

**嚴重程度**: 🔴 高（數據準確性）

**問題描述**:
當一個事故涉及多位車手時（例如碰撞事故），CLI 可能為每位車手都創建一條記錄，導致同一事故被重複計數。

**範例數據**:
```json
{
  "all_incidents": [
    {
      "sequence": 15,
      "message": "INCIDENT INVOLVING CAR 1 (VER) AND CAR 44 (HAM)",
      "driver_code": "VER",  // ❌ VER 被計入 1 次
      "category": "ACCIDENT"
    },
    {
      "sequence": 16,
      "message": "INCIDENT INVOLVING CAR 1 (VER) AND CAR 44 (HAM)",
      "driver_code": "HAM",  // ❌ HAM 被計入 1 次
      "category": "ACCIDENT"
    }
  ]
}
```

**影響**:
- **這可能是預期行為**：每位車手都應該被記錄參與事故
- **或者是數據錯誤**：CLI 不應該為同一事故創建多條記錄

**建議調查**:
1. 檢查 CLI 的 `all_incidents_summary.py` 中 `extract_driver_info()` 的實現
2. 確認是否應該為每位涉及車手創建獨立記錄
3. 如果是預期行為，則當前 GUI 實現正確
4. 如果不是預期行為，需要修復 CLI 的數據生成邏輯

---

## 💡 改進建議

### 建議 1: 增加事故類型篩選

**優先級**: 🟡 中等

**功能描述**:
允許用戶選擇只統計特定類型的事故（例如只統計碰撞事故，排除賽道邊界違規）。

**實現方案**:
```python
class DriverIncidentBarChart(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.filter_categories = set()  # 空集合 = 統計所有類型
        
    def set_category_filter(self, categories: Set[str]):
        """設置事故類型篩選"""
        self.filter_categories = categories
        
    def update_chart_data(self, driver_incidents, all_incidents=None):
        """支援類型篩選的數據更新"""
        if self.filter_categories and all_incidents:
            # 重新統計，只計算指定類型
            driver_incidents = {}
            for incident in all_incidents:
                if incident['category'] in self.filter_categories:
                    driver = incident.get('driver_code', '')
                    if driver:
                        driver_incidents[driver] = driver_incidents.get(driver, 0) + 1
        
        self._render_chart(driver_incidents)
```

### 建議 2: 顯示事故嚴重程度

**優先級**: 🟢 低（視覺增強）

**功能描述**:
在條形圖中使用不同顏色或字符表示事故的嚴重程度分佈。

**實現方案**:
```python
def _render_chart_with_severity(self, driver_data):
    """
    driver_data = {
        'VER': {
            'total': 12,
            'severity': {'LOW': 5, 'MEDIUM': 4, 'HIGH': 2, 'CRITICAL': 1}
        }
    }
    """
    severity_chars = {
        'LOW': '░',      # 淺灰
        'MEDIUM': '▒',   # 中灰
        'HIGH': '▓',     # 深灰
        'CRITICAL': '█'  # 黑色
    }
    
    for driver, data in sorted_driver_data[:8]:
        bar_parts = []
        for severity in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            count = data['severity'].get(severity, 0)
            bar_parts.append(severity_chars[severity] * count)
        
        bar = ''.join(bar_parts)
        line = f"{driver:<6} │ {bar:<40} │ {data['total']:>5}"
        chart_lines.append(line)
```

### 建議 3: 支援點擊查看詳情

**優先級**: 🟡 中等（互動性增強）

**功能描述**:
點擊車手條形時，彈出對話框顯示該車手的所有事故詳情。

**實現方案**:
```python
class DriverIncidentBarChart(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_incidents = []  # 儲存完整數據
        
        # 改用 QTextBrowser 支援點擊
        self.chart_area = QTextBrowser()
        self.chart_area.anchorClicked.connect(self._on_driver_clicked)
        
    def _render_chart(self, data):
        """渲染帶超連結的條形圖"""
        for driver, count in sorted_data[:8]:
            bar = "█" * bar_length
            # 使用 HTML 超連結
            line = f"<a href='{driver}'>{driver:<6}</a> │ {bar:<40} │ {count:>5}"
            chart_lines.append(line)
        
    def _on_driver_clicked(self, url):
        """點擊車手時顯示詳情"""
        driver = url.toString()
        incidents = [inc for inc in self.all_incidents if inc['driver_code'] == driver]
        self._show_driver_detail_dialog(driver, incidents)
```

### 建議 4: 導出圖表為圖片

**優先級**: 🟢 低

**功能描述**:
支援將 ASCII 圖表轉換為 PNG 圖片導出。

**實現方案**:
使用 `matplotlib` 生成靜態條形圖：
```python
import matplotlib.pyplot as plt

def export_chart_as_image(self, filepath: str):
    """導出圖表為 PNG"""
    if not self.incident_data:
        return
        
    sorted_data = sorted(self.incident_data.items(), key=lambda x: x[1], reverse=True)
    drivers = [d[0] for d in sorted_data[:8]]
    counts = [d[1] for d in sorted_data[:8]]
    
    plt.figure(figsize=(10, 6))
    plt.barh(drivers, counts, color='#3b82f6')
    plt.xlabel('Incident Count')
    plt.title('Driver Incident Frequency')
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()
```

---

## 🔄 與其他模組的對比

### Rain Analysis 的 Rainfall Intensity Chart

**相似點**:
- ✅ 都是數據視覺化組件
- ✅ 都繼承自 `QFrame`
- ✅ 都使用 `UniversalDataLoader` 載入數據
- ✅ 都支援 API-ONLY 模式

**不同點**:

| 特性 | Driver Incident Frequency | Rain Analysis |
|------|--------------------------|---------------|
| 圖表類型 | ASCII 條形圖 | `UniversalChartWidget` (Matplotlib) |
| 數據來源 | `all_incidents` 列表 | Weather API |
| 更新頻率 | 靜態（載入一次） | 實時（每次切換賽事） |
| 互動性 | 無 | 支援縮放、導出 |
| 國際化 | 完整支援 | 完整支援 |

**建議**:
考慮將 Driver Incident Frequency 也改用 `UniversalChartWidget`，以獲得更好的視覺效果和互動性：

```python
class DriverIncidentBarChart(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_widget = UniversalChartWidget(
            chart_type="bar",
            title="Driver Incident Frequency"
        )
        
    def _render_chart(self, data):
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
        drivers = [d[0] for d in sorted_data[:8]]
        counts = [d[1] for d in sorted_data[:8]]
        
        self.chart_widget.plot_bar(
            x=drivers,
            y=counts,
            xlabel="Driver",
            ylabel="Incident Count",
            color='#ef4444'
        )
```

---

## 📝 總結

### ✅ 功能優點

1. **架構清晰**: 遵循 `UniversalDataLoader` 架構，代碼結構良好
2. **API-ONLY 模式**: 正確實現 API 優先策略
3. **視覺對齊**: ASCII 圖表對齊精確，使用等寬字體
4. **國際化完整**: 所有用戶可見字串都使用 `tr()` 函數
5. **錯誤處理**: 異常捕捉完善，不影響整體功能
6. **無模擬數據**: 完全遵循「禁用模擬數據政策」

### ⚠️ 潛在問題

1. **中等嚴重**: 未過濾無效車手代碼（UNK）
2. **低嚴重**: 整數向下取整導致精度損失
3. **中等嚴重**: 未使用 CLI 預先統計的數據（效能損失）
4. **高嚴重**: 可能存在多車手事故的重複計數問題（需調查 CLI）

### 🎯 改進優先級

1. **高優先級**: 調查並修復多車手事故的計數邏輯
2. **中優先級**: 過濾無效車手代碼
3. **中優先級**: 使用 `driver_involvement` 優化性能
4. **低優先級**: 使用四捨五入替代向下取整
5. **低優先級**: 考慮改用 `UniversalChartWidget` 提升視覺效果

### 📊 測試覆蓋率建議

- [ ] 單元測試: `update_driver_incident_chart()` 數據統計邏輯
- [ ] 單元測試: `_render_chart()` ASCII 圖表生成
- [ ] 整合測試: API 載入 → 圖表顯示完整流程
- [ ] 整合測試: 本地 JSON 後備流程
- [ ] UI 測試: 無數據時的提示訊息顯示
- [ ] 邊界測試: 少於/等於/多於 8 名車手的情況

---

## 🔗 相關檔案

### 核心實現
- `modules/gui/accident_analysis/accident_analysis_mdi.py` (行 2575-2670)
- `modules/gui/accident_analysis/accident_data_manager.py`
- `CLI_modules/cli/analyzer/all_incidents_summary.py`

### 配置和工具
- `core/gui_i18n.py` - 國際化函數
- `core/api_base_url.py` - API URL 解析
- `core/api_runtime_state.py` - API 健康檢查
- `modules/gui/base/universal_data_loader_base.py` - 數據載入基類

### 測試檔案（建議創建）
- `tests/gui/accident_analysis/test_driver_incident_chart.py`
- `tests/integration/test_accident_api_flow.py`

---

**報告結束**

調查完成時間: 2025年10月24日  
調查人員: GitHub Copilot AI Assistant  
報告版本: 1.0
