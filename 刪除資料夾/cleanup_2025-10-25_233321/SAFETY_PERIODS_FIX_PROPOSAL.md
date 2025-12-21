# Safety Periods 修復方案 - 使用 Detailed Records + Sector 資訊

**日期**：2025-10-24  
**狀態**：設計階段 → 準備實施  
**優先級**：高（功能完全無法運作）

---

## 🎯 用戶提出的解決方案

**核心想法**：利用 `all_incidents` 詳細記錄中的 **sector 資訊** 和 **Safety Car 事件訊息** 來生成 safety_periods 資料。

### ✅ 可用的數據來源（已驗證）

從 2021 Bahrain GP 測試結果確認：

#### 1. **Safety Car 配對訊息**
```
SAFETY CAR DEPLOYED (Lap 1) → SAFETY CAR IN THIS LAP (Lap 3)
VIRTUAL SAFETY CAR DEPLOYED (Lap 4) → VIRTUAL SAFETY CAR ENDING (Lap 5)
```

#### 2. **Yellow Flag Sector 資訊**
```
YELLOW IN TRACK SECTOR 12 (Lap 1)
YELLOW IN TRACK SECTOR 3 (Lap 1)
YELLOW IN TRACK SECTOR 4 (Lap 4)
```

#### 3. **FastF1 提供的完整 Status 欄位**
```python
{
    "Category": "SafetyCar",
    "Status": "DEPLOYED" | "IN THIS LAP" | "ENDING"
}
```

---

## 🔧 實施方案：兩階段生成

### **階段 1：基礎配對邏輯**（最小可行方案）

在 `all_incidents_summary.py` 的 `analyze_all_incidents()` 函數末尾添加：

```python
def _generate_safety_periods(incidents_data):
    """
    從 all_incidents 詳細記錄中生成 safety_periods 配對資料
    
    邏輯：
    1. 找到所有 "DEPLOYED" 訊息 → 記錄為 start_lap
    2. 找到對應的 "IN THIS LAP" / "ENDING" 訊息 → 記錄為 end_lap
    3. 配對成 safety_period 物件
    """
    safety_periods = []
    
    # 篩選出所有 Safety Car 相關記錄
    sc_records = [
        r for r in incidents_data['all_incidents']
        if r.get('category') == 'SAFETY_CAR'
    ]
    
    # 狀態機：追蹤當前活動的 Safety Car
    active_sc = None  # {type, start_lap, reason, sector}
    active_vsc = None
    
    for record in sc_records:
        msg_upper = record['message'].upper()
        lap = record['lap']
        sector = record.get('sector')
        
        # 檢測 Safety Car Deployed
        if 'SAFETY CAR DEPLOYED' in msg_upper and 'VIRTUAL' not in msg_upper:
            if active_sc is None:  # 防止重複部署
                active_sc = {
                    'type': 'SC',
                    'start_lap': lap,
                    'reason': _extract_sc_reason(record),
                    'sector': sector
                }
        
        # 檢測 Safety Car In This Lap (結束)
        elif 'SAFETY CAR IN THIS LAP' in msg_upper:
            if active_sc is not None:
                safety_periods.append({
                    'type': 'SC',
                    'start_lap': active_sc['start_lap'],
                    'end_lap': lap,
                    'reason': active_sc['reason'],
                    'sector': active_sc['sector']
                })
                active_sc = None  # 重置
        
        # 檢測 Virtual Safety Car Deployed
        elif 'VIRTUAL SAFETY CAR DEPLOYED' in msg_upper:
            if active_vsc is None:
                active_vsc = {
                    'type': 'VSC',
                    'start_lap': lap,
                    'reason': _extract_sc_reason(record),
                    'sector': sector
                }
        
        # 檢測 Virtual Safety Car Ending
        elif 'VIRTUAL SAFETY CAR ENDING' in msg_upper:
            if active_vsc is not None:
                safety_periods.append({
                    'type': 'VSC',
                    'start_lap': active_vsc['start_lap'],
                    'end_lap': lap,
                    'reason': active_vsc['reason'],
                    'sector': active_vsc['sector']
                })
                active_vsc = None
    
    return safety_periods


def _extract_sc_reason(record):
    """
    從 Safety Car 記錄中提取部署原因
    
    優先順序：
    1. 同一圈的事故/黃旗事件
    2. Message 中的關鍵字（ACCIDENT, DEBRIS, etc.）
    3. 預設為 "Unknown"
    """
    lap = record['lap']
    
    # 搜索同一圈的其他事件作為原因
    # 這裡需要訪問完整的 incidents_data，所以需要重構
    msg_upper = record['message'].upper()
    
    if any(kw in msg_upper for kw in ['ACCIDENT', 'CRASH', 'COLLISION']):
        return "Accident"
    elif 'DEBRIS' in msg_upper:
        return "Debris on track"
    elif 'SPIN' in msg_upper or 'STOPPED' in msg_upper:
        return "Vehicle incident"
    elif 'TRACK' in msg_upper and 'UNSAFE' in msg_upper:
        return "Unsafe track conditions"
    else:
        return "Unspecified"
```

### **階段 2：Sector 資訊增強**（進階功能）

利用 Yellow Flag 的 sector 資訊來補充 Safety Car 原因：

```python
def _enrich_sc_reason_with_sector(safety_periods, all_incidents):
    """
    使用 sector 資訊增強 Safety Car 原因
    
    邏輯：
    1. 找到 SC 部署前後的 YELLOW FLAG 事件
    2. 提取 sector 資訊
    3. 關聯為部署原因
    """
    for period in safety_periods:
        start_lap = period['start_lap']
        
        # 搜索 start_lap 前後 1-2 圈的黃旗事件
        related_yellows = [
            r for r in all_incidents
            if abs(r['lap'] - start_lap) <= 2
            and 'YELLOW' in r['message'].upper()
            and r.get('sector') is not None
        ]
        
        if related_yellows:
            # 取最接近的黃旗事件
            closest = min(related_yellows, key=lambda x: abs(x['lap'] - start_lap))
            sector = closest.get('sector')
            
            if sector and period['reason'] == "Unspecified":
                period['reason'] = f"Incident in Sector {sector}"
                period['sector'] = sector
    
    return safety_periods
```

---

## 📋 實施步驟

### **步驟 1：修改 CLI 後端**
- [ ] 在 `all_incidents_summary.py` 添加 `_generate_safety_periods()` 函數
- [ ] 在 `analyze_all_incidents()` 末尾調用生成邏輯
- [ ] 將結果存入 `incidents_data['safety_periods']`

### **步驟 2：測試數據生成**
- [ ] 使用 2021 Bahrain GP 測試（已知有 SC + VSC）
- [ ] 驗證生成的 safety_periods 結構正確
- [ ] 檢查 JSON 輸出格式符合 GUI 期望

### **步驟 3：GUI 驗證**
- [ ] 啟動 GUI 載入測試數據
- [ ] 確認 Safety Periods 表格正確顯示
- [ ] 驗證 Type, Start Lap, End Lap, Reason 欄位正確

### **步驟 4：邊界案例處理**
- [ ] 處理 SC 部署但未結束的情況（比賽以 SC 結束）
- [ ] 處理多次 SC 部署的情況
- [ ] 處理 SC 和 VSC 交錯的情況

---

## 🎯 預期輸出格式

```json
{
  "safety_periods": [
    {
      "type": "SC",
      "start_lap": 1,
      "end_lap": 3,
      "reason": "Incident in Sector 12",
      "sector": "12"
    },
    {
      "type": "VSC",
      "start_lap": 4,
      "end_lap": 5,
      "reason": "Incident in Sector 4",
      "sector": "4"
    }
  ]
}
```

---

## ✅ 優勢

1. **完全使用現有數據**：不需要額外 API 調用或外部數據
2. **Sector 資訊豐富上下文**：提供事故位置，提升分析價值
3. **配對邏輯簡單可靠**：狀態機模式易於理解和維護
4. **向後兼容**：不影響現有 detailed_records 功能

---

## ⚠️ 已知限制

1. **依賴訊息格式一致性**：FastF1 的訊息格式若變更可能導致配對失敗
2. **無法處理異常訊息順序**：如果 FIA 訊息順序錯誤可能誤配
3. **原因推斷可能不準確**：某些情況下無法精確確定部署原因

---

## 🚀 下一步行動

**用戶確認後立即實施**：
1. 實現 `_generate_safety_periods()` 函數
2. 測試 2021 Bahrain GP 數據生成
3. 驗證 GUI 顯示正常

**預估時間**：2-3 小時（比原方案快 40%）

---

**提案者**：GitHub Copilot  
**基於**：用戶建議 - 使用 detailed records 中的 sector 資訊
