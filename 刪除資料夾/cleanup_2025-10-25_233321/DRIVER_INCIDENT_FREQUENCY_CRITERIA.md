# Driver Incident Frequency 計數標準說明

## 🎯 核心問題：什麼狀況下會被列入 Driver Incident Frequency？

---

## 📋 簡短答案

**任何出現在 FIA Race Control Messages 中，並且訊息內容包含車手資訊的事件，都會被計入該車手的事故頻率。**

---

## 🔍 詳細流程分析

### 第一步：數據來源

**來源**: FastF1 的 `session.race_control_messages`

這是 FIA 在比賽中發布的所有官方訊息，包括：
- 旗標（黃旗、紅旗、綠旗等）
- 事故通知
- 賽道狀況（Track Clear、DRS Enabled）
- 調查通知
- 處罰決定
- 賽道邊界違規
- 安全車進出

**範例訊息**:
```
"TRACK LIMITS - CAR 1 (VER)"
"YELLOW FLAG - SECTOR 2 - CAR 44 (HAM) INCIDENT"
"INCIDENT INVOLVING CAR 16 (LEC) AND CAR 55 (SAI) UNDER INVESTIGATION"
"PENALTY - 5 SEC TIME PENALTY - CAR 11 (PER) - CAUSING A COLLISION"
"RED FLAG - CARS 4 (NOR) AND 81 (PIA) ACCIDENT AT TURN 3"
```

### 第二步：車手資訊提取

**位置**: `CLI_modules/cli/analyzer/all_incidents_summary.py:73-88`

**提取邏輯**:
```python
def extract_driver_info(message):
    """從訊息中提取車手資訊"""
    import re
    
    # 模式 1: 提取車號和車手代碼
    # 範例: "CAR 1 (VER)" 或 "CARS 16 (LEC) AND 55 (SAI)"
    car_pattern = r'CAR[S]?\s+(\d+)\s*\(([A-Z]{3})\)'
    cars = re.findall(car_pattern, message.upper())
    
    if cars:
        # ✅ 成功提取車號和車手代碼
        # 例如: [('1', 'VER')] 或 [('16', 'LEC'), ('55', 'SAI')]
        return [{'car_number': car[0], 'driver_code': car[1]} for car in cars]
    
    # 模式 2: 僅提取車號（沒有車手代碼）
    # 範例: "CAR 1" 或 "CARS 16 AND 55"
    car_number_pattern = r'CAR[S]?\s+(\d+)'
    car_numbers = re.findall(car_number_pattern, message.upper())
    
    if car_numbers:
        # ⚠️ 只有車號，車手代碼標記為 'UNK' (Unknown)
        # 例如: [{'car_number': '1', 'driver_code': 'UNK'}]
        return [{'car_number': num, 'driver_code': 'UNK'} for num in car_numbers]
    
    # ❌ 無法提取車手資訊
    return []
```

**提取規則**:

| 訊息格式 | 提取結果 | 是否計入 Driver Incident Frequency |
|---------|---------|----------------------------------|
| `"CAR 1 (VER)"` | `driver_code='VER'` | ✅ **是** - VER +1 |
| `"CARS 16 (LEC) AND 55 (SAI)"` | `driver_code='LEC'`, `driver_code='SAI'` | ✅ **是** - LEC +1, SAI +1 |
| `"CAR 44"` (無車手代碼) | `driver_code='UNK'` | ⚠️ **可能** - 取決於 GUI 是否過濾 UNK |
| `"TRACK CLEAR"` (無車號) | (空列表) | ❌ **否** - 不涉及特定車手 |
| `"DRS ENABLED"` (無車號) | (空列表) | ❌ **否** - 不涉及特定車手 |

### 第三步：事故記錄創建

**位置**: `CLI_modules/cli/analyzer/all_incidents_summary.py:310-344`

每條 Race Control Message 都會被處理並創建一條事故記錄：

```python
for idx, (_, message) in enumerate(race_control.iterrows()):
    msg_text = str(message.get('Message', ''))
    
    # 提取車手資訊
    involved_drivers = extract_driver_info(msg_text)
    
    # 創建事故詳情
    incident_detail = {
        'sequence_number': incident_sequence,
        'lap': lap,
        'time': format_time(time),
        'message': msg_text,
        'category': category,  # 例如: TRACK_LIMITS, YELLOW_FLAG, ACCIDENT
        'severity': severity,   # 例如: LOW, MEDIUM, HIGH, CRITICAL
        'impact': impact,
        'involved_drivers': involved_drivers,
        'driver_codes': [d['driver_code'] for d in involved_drivers],  # ⬅️ 關鍵欄位
        'car_numbers': [d['car_number'] for d in involved_drivers],
        # ... 其他欄位
    }
    
    # 加入到 all_incidents 列表
    incidents_data['all_incidents'].append(incident_detail)
```

**重要**: 即使一條訊息沒有提取到車手資訊（`involved_drivers = []`），該事故仍然會被記錄到 `all_incidents`，但 `driver_codes` 會是空列表 `[]`。

### 第四步：車手事故統計

**位置**: `CLI_modules/cli/analyzer/all_incidents_summary.py:428-441`

```python
# 記錄涉及的車手
for driver in involved_drivers:
    driver_code = driver['driver_code']
    incidents_data['incident_summary']['involved_drivers'].add(driver_code)
    
    # ⬅️ 關鍵：建立 driver_involvement 字典
    if driver_code not in incidents_data['driver_involvement']:
        incidents_data['driver_involvement'][driver_code] = []
    incidents_data['driver_involvement'][driver_code].append({
        'sequence': incident_sequence,
        'lap': lap,
        'category': category,
        'severity': severity
    })
```

**結果**:
```json
{
  "driver_involvement": {
    "VER": [
      {"sequence": 1, "lap": 3, "category": "TRACK_LIMITS", "severity": "LOW"},
      {"sequence": 15, "lap": 12, "category": "YELLOW_FLAG", "severity": "HIGH"},
      {"sequence": 28, "lap": 24, "category": "INVESTIGATION", "severity": "MEDIUM"}
    ],
    "HAM": [
      {"sequence": 8, "lap": 8, "category": "PENALTY", "severity": "MEDIUM"},
      {"sequence": 22, "lap": 18, "category": "ACCIDENT", "severity": "HIGH"}
    ],
    "UNK": [
      {"sequence": 45, "lap": 35, "category": "CONTACT", "severity": "MEDIUM"}
    ]
  }
}
```

### 第五步：GUI 統計顯示

**位置**: `modules/gui/accident_analysis/accident_analysis_mdi.py:590-603`

```python
def update_driver_incident_chart(self, json_data):
    """更新車手事故頻率圖表"""
    data_section = json_data.get('data', {})
    all_incidents = data_section.get('all_incidents', [])
    
    # 統計每個車手的事故數量
    driver_incidents = {}
    for incident in all_incidents:
        driver = incident.get('driver_code', '')  # ⬅️ 注意：這裡取的是單一欄位，不是列表
        if driver:  # ⬅️ 只要 driver_code 不是空字串就計入
            driver_incidents[driver] = driver_incidents.get(driver, 0) + 1
    
    self.driver_chart.update_chart_data(driver_incidents)
```

**⚠️ 重要發現**:

這裡有個**數據結構不一致**的問題：

- **CLI 輸出**: `incident['driver_codes']` 是一個**列表** `['VER', 'LEC']`
- **GUI 讀取**: `incident.get('driver_code', '')` 讀取的是單一欄位（**不存在**！）

**實際應該是**:
```python
# ❌ 錯誤：讀取不存在的欄位
driver = incident.get('driver_code', '')

# ✅ 正確：應該遍歷 driver_codes 列表
driver_codes = incident.get('driver_codes', [])
for driver in driver_codes:
    if driver:
        driver_incidents[driver] = driver_incidents.get(driver, 0) + 1
```

---

## 📊 會被計入的事故類型

根據 `categorize_incident_detailed()` 函數，以下所有類型都會被記錄：

### 1. 賽道邊界違規
- **關鍵字**: `TRACK LIMITS`
- **範例**: `"TRACK LIMITS - CAR 1 (VER)"`
- **類別**: `TRACK_LIMITS`
- **嚴重程度**: `LOW`

### 2. 黃旗事件
- **關鍵字**: `YELLOW FLAG`, `DOUBLE YELLOW`
- **範例**: `"YELLOW FLAG - SECTOR 2 - CAR 44 (HAM) INCIDENT"`
- **類別**: `YELLOW_FLAG`
- **嚴重程度**: `HIGH` (單黃) 或 `MEDIUM` (雙黃)

### 3. 紅旗事件
- **關鍵字**: `RED FLAG`
- **範例**: `"RED FLAG - CARS 4 (NOR) AND 81 (PIA) ACCIDENT AT TURN 3"`
- **類別**: `RED_FLAG`
- **嚴重程度**: `CRITICAL`

### 4. 事故/碰撞
- **關鍵字**: `ACCIDENT`, `COLLISION`, `CRASH`, `CONTACT`
- **範例**: `"INCIDENT INVOLVING CAR 16 (LEC) AND CAR 55 (SAI) - COLLISION"`
- **類別**: `ACCIDENT` 或 `CONTACT`
- **嚴重程度**: `HIGH` 或 `MEDIUM`

### 5. 調查
- **關鍵字**: `INVESTIGATION`, `UNDER INVESTIGATION`
- **範例**: `"CAR 11 (PER) UNDER INVESTIGATION - CAUSING A COLLISION"`
- **類別**: `INVESTIGATION`
- **嚴重程度**: `MEDIUM`

### 6. 處罰
- **關鍵字**: `PENALTY`
- **範例**: `"PENALTY - 5 SEC TIME PENALTY - CAR 11 (PER)"`
- **類別**: `PENALTY`
- **嚴重程度**: `MEDIUM`

### 7. 安全車
- **關鍵字**: `SAFETY CAR`
- **範例**: `"SAFETY CAR DEPLOYED - CAR 20 (MAG) STOPPED ON TRACK"`
- **類別**: `SAFETY_CAR`
- **嚴重程度**: `HIGH`

### 8. 賽道狀況
- **關鍵字**: `TRACK CLEAR`, `DRS ENABLED`, `TRACK SURFACE SLIPPERY`
- **範例**: `"TRACK CLEAR IN SECTOR 3"`
- **類別**: `GREEN_FLAG`, `DRS`, `OTHER`
- **嚴重程度**: `LOW` 或 `MEDIUM`
- **注意**: 這些訊息通常**不涉及特定車手**，所以不會計入 Driver Incident Frequency

### 9. 進站相關
- **關鍵字**: `PIT EXIT`, `PIT`
- **範例**: `"CAR 63 (RUS) - UNSAFE RELEASE FROM PIT"`
- **類別**: `PIT_EXIT` 或 `PIT_RELATED`
- **嚴重程度**: `MEDIUM`

### 10. 賽道優勢
- **關鍵字**: `LEAVING THE TRACK AND GAINING AN ADVANTAGE`
- **範例**: `"CAR 14 (ALO) - GAINING AN ADVANTAGE"`
- **類別**: `ADVANTAGE`
- **嚴重程度**: `MEDIUM`

### 11. 其他
- **關鍵字**: 無法分類的訊息
- **類別**: `OTHER`
- **嚴重程度**: `LOW`

---

## ⚠️ 特殊情況

### 情況 1: 多車手涉及同一事故

**範例訊息**:
```
"INCIDENT INVOLVING CAR 16 (LEC) AND CAR 55 (SAI) UNDER INVESTIGATION - COLLISION"
```

**處理方式**:
- **CLI 記錄**: 創建**一條**事故記錄，`driver_codes = ['LEC', 'SAI']`
- **GUI 統計** (正確實現):
  - LEC 的事故計數 +1
  - SAI 的事故計數 +1
- **結果**: 兩位車手都會被計入

**這是否算重複計數？**
- ❌ **不算**：因為兩位車手都確實參與了這起事故
- ✅ **合理**：Driver Incident Frequency 統計的是「車手參與事故的次數」，而非「事故總數」

### 情況 2: 無車手代碼的訊息

**範例訊息**:
```
"CAR 99 - STOPPED ON TRACK"  # 假設 99 號車沒有提供車手代碼
```

**處理方式**:
- **CLI 記錄**: `driver_code = 'UNK'`
- **GUI 統計** (當前實現): `UNK` 會被計入統計
- **問題**: 圖表會顯示 "UNK" 這個無意義的條目

**建議修復**:
```python
for driver in driver_codes:
    if driver and driver != 'UNK':  # ✅ 過濾 UNK
        driver_incidents[driver] = driver_incidents.get(driver, 0) + 1
```

### 情況 3: 完全不涉及車手的訊息

**範例訊息**:
```
"TRACK CLEAR"
"DRS ENABLED"
"SAFETY CAR WILL RETURN TO PITS AT END OF LAP"
```

**處理方式**:
- **CLI 記錄**: 創建事故記錄，但 `driver_codes = []` (空列表)
- **GUI 統計**: 不會計入任何車手（因為沒有 driver_code）
- **結果**: ✅ 正確，這些訊息不應該影響 Driver Incident Frequency

### 情況 4: 比賽開始前/結束後的訊息

**範例訊息**:
```
"FORMATION LAP WILL START"  # 比賽開始前
"CHEQUERED FLAG"            # 比賽結束（最後一圈）
```

**處理方式**:
- **比賽開始前**: ~~曾經被過濾~~ → 現在**全部處理**（代碼已移除過濾邏輯）
- **比賽結束**: 最後一圈的 `CHEQUERED FLAG` 會被過濾掉（正常結束標誌）
- **結果**: Formation Lap 期間的事故也會被計入

---

## 🐛 已發現的 Bug

### Bug 1: GUI 讀取錯誤的欄位

**位置**: `accident_analysis_mdi.py:596`

**問題**:
```python
# ❌ 錯誤：讀取不存在的 'driver_code' 欄位（單數）
driver = incident.get('driver_code', '')
```

**正確做法**:
```python
# ✅ 正確：讀取 'driver_codes' 列表（複數）
driver_codes = incident.get('driver_codes', [])
for driver in driver_codes:
    if driver and driver != 'UNK':
        driver_incidents[driver] = driver_incidents.get(driver, 0) + 1
```

**影響**:
- 🔴 **嚴重**: 所有事故可能都**無法被統計**到 Driver Incident Frequency
- 當前圖表可能顯示為空或不完整

**測試驗證**:
需要實際執行 GUI 並檢查：
1. 是否有數據顯示在 Driver Incident Frequency 圖表
2. 數據數量是否合理

### Bug 2: 未過濾 'UNK' 車手代碼

**問題**: 如果訊息只有車號沒有車手代碼，會產生 `driver_code = 'UNK'`，這會被計入統計並顯示在圖表上。

**建議修復**: 在統計時過濾掉 `'UNK'`

---

## 📈 統計範例

假設一場比賽有以下 Race Control Messages:

```
1. "TRACK LIMITS - CAR 1 (VER)"                           → VER +1
2. "YELLOW FLAG - SECTOR 2 - CAR 44 (HAM) INCIDENT"      → HAM +1
3. "INCIDENT INVOLVING CAR 16 (LEC) AND CAR 55 (SAI)"    → LEC +1, SAI +1
4. "TRACK CLEAR"                                          → (無車手)
5. "PENALTY - 5 SEC - CAR 1 (VER) - TRACK LIMITS"        → VER +1
6. "CAR 99 - STOPPED ON TRACK"                           → UNK +1 (⚠️ Bug)
7. "DRS ENABLED"                                          → (無車手)
8. "TRACK LIMITS - CAR 1 (VER)"                           → VER +1
```

**統計結果**:
```
VER: 3 次
HAM: 1 次
LEC: 1 次
SAI: 1 次
UNK: 1 次  ⚠️ 應該被過濾
```

**Driver Incident Frequency 圖表顯示** (前 8 名):
```
Driver │             Incidents              │ Count
───────┼────────────────────────────────────┼──────
VER    │ ████████████████████████████████   │     3
HAM    │ ██████████                          │     1
LEC    │ ██████████                          │     1
SAI    │ ██████████                          │     1
UNK    │ ██████████                          │     1  ⚠️ 不應顯示
```

---

## ✅ 總結

### 列入 Driver Incident Frequency 的條件

1. ✅ **必須條件**: 訊息出現在 `session.race_control_messages` 中
2. ✅ **必須條件**: 訊息內容包含車手識別資訊（車號 + 車手代碼）
   - 格式: `"CAR 1 (VER)"` 或 `"CARS 16 (LEC) AND 55 (SAI)"`
3. ⚠️ **可選條件**: 車手代碼不是 `'UNK'`（建議過濾）
4. ⚠️ **當前 Bug**: GUI 可能無法正確讀取 `driver_codes` 欄位

### 不會列入的情況

- ❌ 訊息不包含車號（例如: `"TRACK CLEAR"`, `"DRS ENABLED"`）
- ❌ 最後一圈的正常比賽結束訊息（`"CHEQUERED FLAG"`）
- ❌ (建議) 車手代碼為 `'UNK'` 的事故

### 所有事故類型都計入

無論是嚴重的碰撞事故還是輕微的賽道邊界違規，只要符合上述條件，都會被計入該車手的事故頻率。這意味著：

- ✅ **優點**: 全面反映車手在比賽中的所有「非正常事件」
- ⚠️ **缺點**: 無法區分嚴重程度（1 次賽道邊界違規 = 1 次碰撞事故）

### 建議改進

1. **修復 Bug 1**: 正確讀取 `driver_codes` 列表
2. **修復 Bug 2**: 過濾 `'UNK'` 車手代碼
3. **功能增強**: 增加事故類型篩選（只統計特定類型）
4. **功能增強**: 根據嚴重程度加權統計

---

**文檔版本**: 1.0  
**創建時間**: 2025年10月24日  
**作者**: GitHub Copilot AI Assistant
