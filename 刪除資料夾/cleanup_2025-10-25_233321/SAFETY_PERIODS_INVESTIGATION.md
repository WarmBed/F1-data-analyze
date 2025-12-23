# Safety Periods 功能深度調查報告

## 📋 調查概述

**調查時間**: 2025年10月24日  
**調查目標**: Accident Analysis 模組中的 Safety Periods 功能  
**調查範圍**: 數據流程、架構設計、實現細節、潛在問題  

---

## 🎯 功能定位

### 基本資訊
- **功能名稱**: Safety Periods (安全車時段統計)
- **所屬模組**: Accident Analysis (事故分析)
- **CLI Function ID**: 8 (All Incidents Summary)
- **GUI 位置**: `AccidentStatisticsWidget` 第三行組件
- **實現類別**: `SafetyPeriodsWidget`

### 功能描述
Safety Periods 是一個 **可擴展表格組件**，用於顯示比賽中安全車（Safety Car）或虛擬安全車（Virtual Safety Car）的部署時段，包括開始圈數、結束圈數、類型和原因。

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
update_safety_periods_data(json_data)
    ├─ 提取: json_data['data']['safety_periods']  ⚠️ 此欄位可能不存在！
    └─ 列表: [{type, start_lap, end_lap, reason}]
    ↓
SafetyPeriodsWidget.update_safety_periods_data(safety_periods)
    ↓
顯示到 QTableWidget
```

### 2. 核心組件

#### 2.1 數據提取

**位置**: `accident_analysis_mdi.py:610-619`

```python
def update_safety_periods_data(self, json_data):
    """更新安全車時段數據"""
    try:
        data_section = json_data.get('data', {})
        safety_periods = data_section.get('safety_periods', [])  # ⚠️ 可能不存在
        
        self.safety_periods_widget.update_safety_periods_data(safety_periods)
        
    except Exception as e:
        print(f"[AccidentStatisticsWidget] Safety Periods 更新失敗: {e}")
```

#### 2.2 Widget 組件

**位置**: `accident_analysis_mdi.py:2344-2433`

**UI 結構**:
```python
QWidget
├─ QVBoxLayout
    ├─ QLabel: 標題 "🏁 Safety Periods (2 total)"
    └─ QTableWidget (可擴展)
        ├─ 列 1: Period (類型)
        ├─ 列 2: Start Lap (開始圈數)
        ├─ 列 3: End Lap (結束圈數)
        └─ 列 4: Reason (原因)
```

**關鍵特性**:
```python
# 可擴展設計
self.safety_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
self.safety_table.setMinimumHeight(100)  # 最小高度
# 無最大高度限制 - 可隨視窗擴展

# 表格設定
self.safety_table.setColumnCount(4)
self.safety_table.setAlternatingRowColors(True)  # 交替行顏色
self.safety_table.setSelectionBehavior(QAbstractItemView.SelectRows)
self.safety_table.horizontalHeader().setStretchLastSection(True)  # 最後一列自動延展
```

#### 2.3 數據更新邏輯

**位置**: `accident_analysis_mdi.py:2415-2433`

```python
def update_safety_periods_data(self, safety_periods_data):
    """更新 Safety Periods 數據 - 僅使用真實數據"""
    if not safety_periods_data:
        # ⚠️ 禁用模擬數據政策：顯示無數據訊息
        self.safety_table.setRowCount(1)
        self.safety_table.setItem(0, 0, QTableWidgetItem("-"))
        self.safety_table.setItem(0, 1, QTableWidgetItem("-"))
        self.safety_table.setItem(0, 2, QTableWidgetItem("-"))
        self.safety_table.setItem(0, 3, QTableWidgetItem(
            tr('no_safety_periods', 'No safety car periods in this session')
        ))
        return
        
    # 處理實際數據
    self.safety_table.setRowCount(len(safety_periods_data))
    
    for row, period in enumerate(safety_periods_data):
        self.safety_table.setItem(row, 0, QTableWidgetItem(period.get('type', 'SC')))
        self.safety_table.setItem(row, 1, QTableWidgetItem(str(period.get('start_lap', ''))))
        self.safety_table.setItem(row, 2, QTableWidgetItem(str(period.get('end_lap', '')))) 
        self.safety_table.setItem(row, 3, QTableWidgetItem(period.get('reason', '')))
```

---

## 📊 數據結構分析

### GUI 期望的數據格式

```json
{
  "data": {
    "safety_periods": [
      {
        "type": "SC",
        "start_lap": 12,
        "end_lap": 15,
        "reason": "Accident at Turn 3 - CAR 4 (NOR)"
      },
      {
        "type": "VSC",
        "start_lap": 28,
        "end_lap": 30,
        "reason": "Debris on track"
      }
    ]
  }
}
```

**欄位說明**:

| 欄位 | 類型 | 說明 | 範例 |
|------|------|------|------|
| `type` | String | 安全車類型 | `"SC"` (Safety Car), `"VSC"` (Virtual Safety Car) |
| `start_lap` | Integer | 開始圈數 | `12` |
| `end_lap` | Integer | 結束圈數 | `15` |
| `reason` | String | 部署原因 | `"Accident at Turn 3"` |

### CLI 實際輸出的數據格式

**⚠️ 重大發現**: CLI (`all_incidents_summary.py`) **並未生成** `safety_periods` 陣列！

**CLI 實際生成的數據結構**:
```json
{
  "data": {
    "all_incidents": [...],
    "incident_summary": {
      "flag_statistics": {
        "safety_car_events": {
          "total_count": 2,
          "details": [
            {
              "sequence": 45,
              "lap": 12,
              "timestamp": "0:15:32.456",
              "status": "ACTIVE",
              "message": "SAFETY CAR DEPLOYED"
            },
            {
              "sequence": 48,
              "lap": 15,
              "timestamp": "0:18:45.678",
              "status": "IN",
              "message": "SAFETY CAR IN THIS LAP"
            }
          ]
        }
      }
    }
  }
}
```

**問題**: 
- GUI 期望: `data.safety_periods[]`
- CLI 提供: `data.incident_summary.flag_statistics.safety_car_events.details[]`
- **結果**: GUI 永遠收到空陣列 `[]`，表格顯示 "No safety car periods in this session"

---

## 🐛 已識別問題

### 問題 1: CLI 未生成 safety_periods 數據 🔴 嚴重

**嚴重程度**: 🔴 高（功能完全失效）

**問題描述**:
CLI 的 `all_incidents_summary.py` 沒有生成 `safety_periods` 陣列，而是將安全車事件記錄在 `safety_car_events.details` 中。

**位置**:
- GUI 讀取: `accident_analysis_mdi.py:614`
- CLI 輸出: `all_incidents_summary.py:213-217` (safety_car_events 結構)

**影響**:
- Safety Periods 表格**永遠顯示空白**
- 用戶無法查看安全車部署時段
- 功能形同虛設

**根本原因**:
1. CLI 只記錄**個別安全車事件**（部署、收回）
2. 沒有將多個事件**配對成時段**（start_lap + end_lap）
3. GUI 期望的數據格式與 CLI 實際輸出不匹配

### 問題 2: 數據配對邏輯缺失 🟡 中等

**問題描述**:
要生成 `safety_periods`，需要將 "SAFETY CAR DEPLOYED" 和 "SAFETY CAR IN THIS LAP" 配對成一個時段，但 CLI 沒有實現此邏輯。

**範例**:
```
事件 1: Lap 12 - "SAFETY CAR DEPLOYED"        → start_lap = 12
事件 2: Lap 15 - "SAFETY CAR IN THIS LAP"     → end_lap = 15
結果: {type: "SC", start_lap: 12, end_lap: 15, reason: "..."}
```

**挑戰**:
1. 需要識別 SC 部署訊息關鍵字
2. 需要配對部署和收回事件
3. 需要處理多次 SC 部署
4. 需要處理 VSC (Virtual Safety Car)
5. 需要提取部署原因

### 問題 3: 無數據驗證 🟡 中等

**問題描述**:
`update_safety_periods_data` 假設數據格式正確，沒有驗證欄位是否存在。

**潛在錯誤**:
```python
# ❌ 如果 period 缺少某些欄位會發生什麼？
period.get('type', 'SC')       # 如果 type 是 None？
str(period.get('start_lap', ''))  # 如果 start_lap 是字串？
```

### 問題 4: 類型標記不一致 🟢 低

**問題描述**:
GUI 期望 `type` 為 `"SC"` 或 `"VSC"`，但沒有標準化處理。

**建議**:
```python
# 標準化類型
type_mapping = {
    'SAFETY CAR': 'SC',
    'VIRTUAL SAFETY CAR': 'VSC',
    'SC': 'SC',
    'VSC': 'VSC'
}
period_type = type_mapping.get(period.get('type', '').upper(), 'SC')
```

---

## 💡 修復方案

### 方案 A: CLI 生成 safety_periods（推薦）✅

**優點**:
- 一次性解決問題
- 數據在後端處理，邏輯集中
- GUI 簡單讀取即可

**實現步驟**:

1. **在 CLI 中添加 safety_periods 生成邏輯**

在 `all_incidents_summary.py` 的 `analyze_all_incidents` 函數中添加：

```python
def analyze_all_incidents(session):
    # ... 現有代碼 ...
    
    incidents_data = {
        'all_incidents': [],
        'incident_summary': {...},
        'safety_periods': [],  # ✅ 新增欄位
        'chronological_sequence': [],
        'driver_involvement': {},
        'lap_analysis': {}
    }
    
    # ... 處理所有事件 ...
    
    # ✅ 在返回前生成 safety_periods
    incidents_data['safety_periods'] = _generate_safety_periods(
        incidents_data['all_incidents']
    )
    
    return incidents_data
```

2. **實現 safety_periods 生成函數**

```python
def _generate_safety_periods(all_incidents):
    """從所有事件中提取並配對安全車時段"""
    safety_periods = []
    
    # SC 部署/收回配對
    sc_deployed_lap = None
    sc_reason = None
    
    # VSC 部署/收回配對
    vsc_deployed_lap = None
    vsc_reason = None
    
    for incident in all_incidents:
        message = incident.get('message', '').upper()
        lap = incident.get('lap', 0)
        category = incident.get('category', '')
        
        # 檢測 Safety Car 部署
        if 'SAFETY CAR DEPLOYED' in message:
            sc_deployed_lap = lap
            sc_reason = message
            
        # 檢測 Safety Car 收回
        elif ('SAFETY CAR IN THIS LAP' in message or 
              'SAFETY CAR WILL RETURN TO PITS' in message):
            if sc_deployed_lap is not None:
                safety_periods.append({
                    'type': 'SC',
                    'start_lap': sc_deployed_lap,
                    'end_lap': lap,
                    'reason': _extract_sc_reason(sc_reason)
                })
                sc_deployed_lap = None
                sc_reason = None
        
        # 檢測 Virtual Safety Car 部署
        elif 'VIRTUAL SAFETY CAR DEPLOYED' in message or 'VSC DEPLOYED' in message:
            vsc_deployed_lap = lap
            vsc_reason = message
            
        # 檢測 Virtual Safety Car 結束
        elif 'VIRTUAL SAFETY CAR ENDING' in message or 'VSC ENDING' in message:
            if vsc_deployed_lap is not None:
                safety_periods.append({
                    'type': 'VSC',
                    'start_lap': vsc_deployed_lap,
                    'end_lap': lap,
                    'reason': _extract_sc_reason(vsc_reason)
                })
                vsc_deployed_lap = None
                vsc_reason = None
    
    # 處理未配對的部署（比賽結束時仍在 SC/VSC 狀態）
    if sc_deployed_lap is not None:
        safety_periods.append({
            'type': 'SC',
            'start_lap': sc_deployed_lap,
            'end_lap': 'End',
            'reason': _extract_sc_reason(sc_reason)
        })
    
    if vsc_deployed_lap is not None:
        safety_periods.append({
            'type': 'VSC',
            'start_lap': vsc_deployed_lap,
            'end_lap': 'End',
            'reason': _extract_sc_reason(vsc_reason)
        })
    
    return safety_periods

def _extract_sc_reason(message):
    """從訊息中提取安全車部署原因"""
    if not message:
        return "Unknown"
    
    # 移除前綴
    message = message.replace('SAFETY CAR DEPLOYED', '').strip()
    message = message.replace('VIRTUAL SAFETY CAR DEPLOYED', '').strip()
    message = message.replace('VSC DEPLOYED', '').strip()
    
    # 移除多餘字元
    message = message.lstrip('-').lstrip(':').strip()
    
    # 限制長度
    if len(message) > 100:
        message = message[:97] + "..."
    
    return message or "No specific reason provided"
```

### 方案 B: GUI 自行配對（次優）

**優點**:
- 不需修改 CLI
- GUI 自主性高

**缺點**:
- 邏輯複雜度高
- 每次載入都要重新處理
- 效能較差

**實現範例**:

```python
def update_safety_periods_data(self, json_data):
    """更新安全車時段數據"""
    try:
        data_section = json_data.get('data', {})
        
        # 優先使用 CLI 提供的 safety_periods
        safety_periods = data_section.get('safety_periods', [])
        
        # ✅ 後備方案：從 safety_car_events 提取並配對
        if not safety_periods:
            safety_events = (
                data_section.get('incident_summary', {})
                .get('flag_statistics', {})
                .get('safety_car_events', {})
                .get('details', [])
            )
            safety_periods = self._pair_safety_events(safety_events)
        
        self.safety_periods_widget.update_safety_periods_data(safety_periods)
        
    except Exception as e:
        print(f"[AccidentStatisticsWidget] Safety Periods 更新失敗: {e}")

def _pair_safety_events(self, safety_events):
    """配對安全車事件為時段"""
    periods = []
    deployed_lap = None
    reason = None
    
    for event in safety_events:
        message = event.get('message', '').upper()
        lap = event.get('lap', 0)
        
        if 'DEPLOYED' in message:
            deployed_lap = lap
            reason = message
        elif 'IN THIS LAP' in message or 'RETURN TO PITS' in message:
            if deployed_lap:
                periods.append({
                    'type': 'SC',
                    'start_lap': deployed_lap,
                    'end_lap': lap,
                    'reason': reason
                })
                deployed_lap = None
    
    return periods
```

---

## 🔄 與其他模組的對比

### Driver Incident Frequency vs Safety Periods

| 特性 | Driver Incident Frequency | Safety Periods |
|------|--------------------------|----------------|
| 顯示類型 | ASCII 條形圖 | QTableWidget 表格 |
| 數據來源 | `all_incidents[].driver_codes` | `safety_periods[]` (不存在) |
| 數據處理 | GUI 自行統計 | 期望 CLI 提供 |
| Bug 狀態 | ✅ 已修復 | 🔴 功能失效 |
| 國際化 | ✅ 完整 | ✅ 完整 |

**相似點**:
- 都是數據視覺化組件
- 都依賴 CLI Function 8 的數據
- 都支援無數據時顯示提示訊息

**不同點**:
- Driver Incident Frequency: GUI 自行從 `all_incidents` 統計
- Safety Periods: 期望 CLI 提供已處理的 `safety_periods`

---

## 🧪 測試建議

### 測試場景 1: 有安全車的賽事

**步驟**:
1. 選擇有安全車部署的賽事（例如: 2024 Singapore GP）
2. 執行修復後的 CLI 生成數據
3. 在 GUI 中載入並檢查 Safety Periods 表格

**預期結果**:
```
Period │ Start Lap │ End Lap │ Reason
───────┼───────────┼─────────┼────────────────────────────
SC     │     12    │   15    │ Accident at Turn 3 - CAR 4
VSC    │     28    │   30    │ Debris on track
```

### 測試場景 2: 無安全車的賽事

**步驟**:
1. 選擇無安全車的賽事
2. 載入數據

**預期結果**:
```
Period │ Start Lap │ End Lap │ Reason
───────┼───────────┼─────────┼────────────────────────────
  -    │     -     │    -    │ No safety car periods in this session
```

### 測試場景 3: 比賽結束時仍在 SC 狀態

**步驟**:
1. 選擇在 SC 狀態下結束的賽事
2. 檢查 end_lap 是否顯示為 "End"

**預期結果**:
```
Period │ Start Lap │ End Lap │ Reason
───────┼───────────┼─────────┼────────────────────────────
SC     │     45    │   End   │ Race finished under SC
```

---

## 📝 總結

### ✅ 功能優點

1. **UI 設計良好**: 可擴展表格，適應不同視窗大小
2. **國際化完整**: 所有字串使用 `tr()` 函數
3. **無模擬數據**: 遵循禁用模擬數據政策
4. **錯誤處理**: 異常捕捉完善

### 🔴 嚴重問題

1. **功能完全失效**: CLI 未生成 `safety_periods` 數據
2. **數據結構不匹配**: GUI 期望的欄位不存在
3. **配對邏輯缺失**: 無法將 SC 事件配對成時段

### 🎯 修復優先級

1. **高優先級**: 在 CLI 中實現 `safety_periods` 生成邏輯（方案 A）
2. **中優先級**: 添加數據驗證和錯誤處理
3. **低優先級**: 標準化類型標記
4. **低優先級**: 改進原因訊息提取

### 📊 修復預估

| 項目 | 工作量 | 複雜度 |
|------|--------|--------|
| CLI 生成 safety_periods | 2-3 小時 | 中 |
| 測試和驗證 | 1 小時 | 低 |
| 數據驗證增強 | 30 分鐘 | 低 |
| **總計** | **3.5-4.5 小時** | **中** |

---

## 📚 相關檔案

### 核心實現
- `modules/gui/accident_analysis/accident_analysis_mdi.py` (行 2344-2433)
- `modules/gui/accident_analysis/accident_data_manager.py`
- `CLI_modules/cli/analyzer/all_incidents_summary.py`

### 配置和工具
- `core/gui_i18n.py` - 國際化函數
- `core/api_base_url.py` - API URL 解析
- `modules/gui/base/universal_data_loader_base.py` - 數據載入基類

### 測試檔案（建議創建）
- `tests/gui/accident_analysis/test_safety_periods_widget.py`
- `tests/cli/analyzer/test_safety_periods_generation.py`

---

**報告結束**

調查完成時間: 2025年10月24日  
調查人員: GitHub Copilot AI Assistant  
報告版本: 1.0
