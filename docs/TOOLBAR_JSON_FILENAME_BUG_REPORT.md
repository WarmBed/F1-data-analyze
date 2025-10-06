# Toolbar 參數變更導致 JSON 檔案名稱錯誤問題報告

**問題嚴重度**: 🔴 **嚴重** (Critical)  
**發現日期**: 2025-10-04  
**影響範圍**: 所有遙測分析模組 (Speed, Throttle, RPM, Gear, Acceleration, DistanceDiff, SpeedDiff)  
**狀態**: 🔧 **待修復**

---

## 📋 問題總結

當使用者透過 toolbar 改變 driver 或 lap 參數時，系統生成的 JSON 檔案名稱格式錯誤，導致：
1. ❌ **race 參數包含日期後綴** (如 "Japan (2025-04-06)" 而非 "Japan")
2. ❌ **driver 參數重複** (如 "VER_VER" 而非 "VER_LEC")
3. ❌ **lap 參數重複** (如 "Lap99_Lap99" 而非原本的圈數)
4. ❌ **API 無法找到已存在的 JSON** (檔案名稱不匹配)

---

## 🔍 問題證據

### 錯誤的 JSON 檔案名稱

**案例 1**: 車手參數錯誤
```
❌ comparison_telemetry_VER_VER_2025_Japan_R_Lap1_Lap1.json
✅ comparison_telemetry_VER_LEC_2025_Japan_R_Lap1_Lap1.json
```
- metadata 中 driver1="VER", driver2="VER" (應該是不同車手)
- 實際數據顯示 act_lap1_number=1, act_lap2_number=1 (相同圈數)

**案例 2**: Race 參數包含日期
```
❌ comparison_telemetry_VER_LEC_2025_Japan (2025-04-06)_R_Lap99_Lap99.json
✅ comparison_telemetry_VER_LEC_2025_Japan_R_Lap52_Lap47.json
```
- race="Japan (2025-04-06)" 包含日期後綴
- 實際數據顯示 act_lap1_number=52, act_lap2_number=47 (與檔名不符)
- lap_number1=99, lap_number2=99 (metadata 錯誤)

### JSON 內容驗證

**錯誤檔案**: `comparison_telemetry_VER_LEC_2025_Japan (2025-04-06)_R_Lap99_Lap99.json`

```json
{
  "metadata": {
    "year": 2025,
    "race": "Japan (2025-04-06)",  // ❌ 包含日期
    "session": "R",
    "driver1": "VER",
    "driver2": "LEC",
    "lap_number1": 99,  // ❌ 與實際不符
    "lap_number2": 99   // ❌ 與實際不符
  },
  "results": {
    "comparison_info": {
      "act_lap1_number": 52,  // ✅ 實際圈數
      "act_lap2_number": 47   // ✅ 實際圈數
    }
  }
}
```

---

## 🐛 問題根源分析

### 1. Race 參數污染

**位置**: `f1t_gui_main.py` → toolbar → `race_combo`

**問題**: `race_combo` 顯示文字包含日期後綴 (SeasonEvent.display_label)

```python
# f1t_gui_main.py 第 5384 行
def _format_race_display(self, event: SeasonEvent) -> str:
    """將賽事格式化為顯示標籤（包含日期）"""
    return f"{event.country} ({event.event_date.strftime('%Y-%m-%d')})"
    # 結果: "Japan (2025-04-06)" ← 這就是問題來源！
```

**數據流**:
```
SeasonEvent.display_label = "Japan (2025-04-06)"
  ↓
race_combo.currentText() = "Japan (2025-04-06)"
  ↓
on_lap_parameters_changed() 讀取 race_combo.currentText()
  ↓
update_all_lap_analysis(race="Japan (2025-04-06)")  ← 污染傳播！
  ↓
API 請求: race="Japan (2025-04-06)"
  ↓
生成檔案: comparison_telemetry_..._Japan (2025-04-06)_...json  ← 錯誤檔名！
```

### 2. 檔案名稱構建位置

**位置**: `modules/gui/lap_analysis/telemetry_data_loader_base.py` 第 847-859 行

```python
def _persist_api_payload(self, data: Dict[str, Any]):
    # ... 參數提取
    year = params.get('year')  
    race = params.get('race')  # ← 從 toolbar 讀取，包含日期！
    session = params.get('session')
    
    # ❌ 問題：使用污染的 race 構建檔名
    if single_driver_mode:
        filename = f"comparison_telemetry_{driver1_token}_{driver1_token}_{year}_{race}_{session}_Lap{lap1}.json"
    else:
        filename = f"comparison_telemetry_{driver1_token}_{driver2_token}_{year}_{race}_{session}_Lap{lap1}_Lap{lap2_safe}.json"
    
    # 結果: "comparison_telemetry_VER_LEC_2025_Japan (2025-04-06)_R_Lap99_Lap99.json"
```

### 3. 級聯影響

**Toolbar 變更流程**:
```
使用者改變 lap1_spinbox
  ↓
on_lap_parameters_changed() 觸發
  ↓
500ms 延遲後調用 update_all_lap_analysis()
  ↓
獲取 toolbar 當前值:
  - year = year_combo.currentText() = "2025"
  - race = race_combo.currentText() = "Japan (2025-04-06)"  ← 污染！
  - session = session_combo.currentText() = "R"
  - driver1 = driver1_combo.currentText() = "VER"
  - driver2 = driver2_combo.currentText() = "VER"  ← 可能錯誤！
  - lap1 = lap1_spinbox.value() = 99
  - lap2 = lap2_spinbox.value() = 99  ← 可能錯誤！
  ↓
遍歷所有 lap_analysis_windows
  ↓
調用 module.update_lap_parameters(race="Japan (2025-04-06)", ...)
  ↓
TelemetryDataLoaderBase._load_data_via_api()
  ↓
構建 API 請求: POST /api/v2/analysis/execute
  - function_id: 13
  - year: 2025
  - race: "Japan (2025-04-06)"  ← API 請求污染！
  - session: "R"
  - driver1: "VER"
  - driver2: "VER"  ← 應該是 "LEC"
  - lap1: 99  ← 應該是原本的圈數
  - lap2: 99  ← 應該是原本的圈數
  ↓
API 執行 CLI Function 13
  ↓
CLI 執行: python f1_analysis_modular_main.py -f 13 \
    -y 2025 -r "Japan (2025-04-06)" -s R -d VER -d2 VER -l 99 -l2 99
  ↓
CLI 內部邏輯:
  - 嘗試載入 "Japan (2025-04-06)" 賽事 (可能找不到)
  - 或者 CLI 內部清理了日期後綴？
  ↓
生成 JSON 檔案: _persist_api_payload()
  - 使用污染的 params 構建檔名
  - comparison_telemetry_VER_VER_2025_Japan (2025-04-06)_R_Lap99_Lap99.json ← 錯誤！
```

---

## 🎯 修復方案

### 方案 A: Race 名稱清理 (推薦) ⭐⭐⭐

**優點**:
- ✅ 徹底解決 race 參數污染
- ✅ 不影響 GUI 顯示
- ✅ 對所有模組一致生效

**修復位置 1**: `f1t_gui_main.py` → `on_lap_parameters_changed()`

```python
def on_lap_parameters_changed(self):
    """圈速參數變更時自動更新所有分析"""
    # ... 現有程式碼 ...
    
    # 獲取當前設置
    driver1 = self.driver1_combo.currentText()
    driver2 = self.driver2_combo.currentText() if self.driver2_combo.currentText() != "無" else None
    lap1 = self.lap1_spinbox.value()
    lap2 = self.lap2_spinbox.value()
    is_fastest = self.fastest_lap_checkbox.isChecked()
    
    # 獲取當前基本設置
    year = self.year_combo.currentText()
    race_display = self.race_combo.currentText()  # 可能包含日期
    session = self.session_combo.currentText()
    
    # 🔧 修復: 清理 race 參數，移除日期後綴
    race = self._clean_race_name(race_display)
    
    # ... 繼續使用 race 而非 race_display ...
```

**新增輔助方法**:
```python
def _clean_race_name(self, race_display: str) -> str:
    """
    清理賽事名稱，移除日期後綴
    
    範例:
        "Japan (2025-04-06)" → "Japan"
        "Italy" → "Italy"
        "Italian Grand Prix (2025-09-01)" → "Italian Grand Prix"
    """
    import re
    # 移除 " (YYYY-MM-DD)" 格式的日期後綴
    clean_name = re.sub(r'\s*\(\d{4}-\d{2}-\d{2}\)\s*$', '', race_display)
    return clean_name.strip()
```

**修復位置 2**: `f1t_gui_main.py` → `update_all_lap_analysis()`

```python
def update_all_lap_analysis(self):
    """更新所有遙測分析視窗"""
    # ... 現有程式碼 ...
    
    # 獲取當前基本設置
    year = self.year_combo.currentText()
    race_display = self.race_combo.currentText()
    session = self.session_combo.currentText()
    
    # 🔧 修復: 清理 race 參數
    race = self._clean_race_name(race_display)
    
    print(f"[LAP_CONTROL] 📊 基本設置: {year} {race} {session}")
    print(f"[LAP_CONTROL] 🧹 清理前: {race_display}, 清理後: {race}")
    
    # ... 繼續使用 race ...
```

---

### 方案 B: 使用 SeasonEvent.race_key (最佳) ⭐⭐⭐⭐⭐

**優點**:
- ✅ 使用正規的賽事識別碼
- ✅ 完全避免日期問題
- ✅ 符合系統設計架構

**修復位置**: `f1t_gui_main.py` → `on_lap_parameters_changed()`

```python
def on_lap_parameters_changed(self):
    """圈速參數變更時自動更新所有分析"""
    # ... 現有程式碼 ...
    
    # 🔧 修復: 使用 race_key 而非顯示文字
    race_display = self.race_combo.currentText()
    race = self._get_race_key_from_display(race_display)
    
    print(f"[LAP_CONTROL] 📊 基本設置: {year} {race} (display: {race_display}) {session}")
    
    # ... 繼續使用 race ...
```

**新增輔助方法**:
```python
def _get_race_key_from_display(self, race_display: str) -> str:
    """
    從顯示文字獲取正規的 race_key
    
    使用 _display_to_race_key 映射表
    """
    if race_display in self._display_to_race_key:
        race_key = self._display_to_race_key[race_display]
        return race_key
    
    # 後備方案: 清理日期後綴
    return self._clean_race_name(race_display)
```

---

### 方案 C: 檔案名稱構建時清理 (緊急修復)

**優點**:
- ✅ 最小化程式碼變更
- ✅ 集中在一個位置修復

**缺點**:
- ❌ 不解決 API 請求參數污染
- ❌ CLI 仍會收到錯誤的 race 參數

**修復位置**: `telemetry_data_loader_base.py` → `_persist_api_payload()`

```python
def _persist_api_payload(self, data: Dict[str, Any]):
    try:
        params = self.current_session or {}
        year = params.get('year')
        race_raw = params.get('race')
        session = params.get('session')
        
        # 🔧 修復: 清理 race 參數
        race = self._clean_race_name(race_raw)
        
        # ... 繼續使用 race 構建檔名 ...
        filename = f"comparison_telemetry_{driver1_token}_{driver2_token}_{year}_{race}_{session}_Lap{lap1}_Lap{lap2_safe}.json"
```

**新增輔助方法**:
```python
def _clean_race_name(self, race_raw: str) -> str:
    """清理賽事名稱，移除日期後綴"""
    if not race_raw:
        return race_raw
    
    import re
    # 移除 " (YYYY-MM-DD)" 格式的日期後綴
    clean_name = re.sub(r'\s*\(\d{4}-\d{2}-\d{2}\)\s*$', '', race_raw)
    return clean_name.strip()
```

---

## 📝 修復計劃

### 階段 1: 緊急修復 (立即執行) 🔥

**目標**: 確保 JSON 檔案名稱正確

1. ✅ 在 `f1t_gui_main.py` 新增 `_clean_race_name()` 方法
2. ✅ 在 `on_lap_parameters_changed()` 清理 race 參數
3. ✅ 在 `update_all_lap_analysis()` 清理 race 參數
4. ✅ 測試 toolbar 變更功能

### 階段 2: 架構優化 (後續執行)

**目標**: 使用正規的 race_key

1. ✅ 實現 `_get_race_key_from_display()` 方法
2. ✅ 更新所有 race 參數讀取位置
3. ✅ 確保 API 請求使用 race_key
4. ✅ 驗證所有遙測模組

### 階段 3: 全面測試

1. ✅ 測試 toolbar driver 變更
2. ✅ 測試 toolbar lap 變更
3. ✅ 測試 race_combo 選擇
4. ✅ 驗證生成的 JSON 檔案名稱
5. ✅ 驗證 API 請求參數
6. ✅ 驗證 metadata 內容

---

## 🧪 測試案例

### 測試案例 1: Driver 變更

**操作步驟**:
1. 開啟 Speed Analysis (2025 Japan R, VER vs LEC, Lap1 vs Lap1)
2. 透過 toolbar 將 driver2 改為 "HAM"
3. 檢查生成的 JSON 檔案名稱

**預期結果**:
```
✅ comparison_telemetry_VER_HAM_2025_Japan_R_Lap1_Lap1.json
```

**實際結果 (修復前)**:
```
❌ comparison_telemetry_VER_VER_2025_Japan_R_Lap1_Lap1.json
或
❌ comparison_telemetry_VER_VER_2025_Japan (2025-04-06)_R_Lap1_Lap1.json
```

### 測試案例 2: Lap 變更

**操作步驟**:
1. 開啟 Speed Analysis (2025 Japan R, VER vs LEC, Lap1 vs Lap1)
2. 透過 toolbar 將 lap1 改為 5, lap2 改為 10
3. 檢查生成的 JSON 檔案名稱

**預期結果**:
```
✅ comparison_telemetry_VER_LEC_2025_Japan_R_Lap5_Lap10.json
```

**實際結果 (修復前)**:
```
❌ comparison_telemetry_VER_LEC_2025_Japan (2025-04-06)_R_Lap99_Lap99.json
```

### 測試案例 3: Race 選擇

**操作步驟**:
1. 透過 toolbar 選擇 race_combo = "Japan (2025-04-06)"
2. 開啟 Speed Analysis
3. 檢查 API 請求參數

**預期結果**:
```json
{
  "function_id": 13,
  "year": 2025,
  "race": "Japan",  // ✅ 清理後的名稱
  "session": "R"
}
```

**實際結果 (修復前)**:
```json
{
  "function_id": 13,
  "year": 2025,
  "race": "Japan (2025-04-06)",  // ❌ 包含日期
  "session": "R"
}
```

---

## 📊 影響評估

### 受影響的模組

1. ✅ Speed Analysis (`speed_analysis_mdi.py`)
2. ✅ Throttle Analysis (`throttle_analysis_mdi.py`)
3. ✅ RPM Analysis (`rpm_analysis_mdi.py`)
4. ✅ Gear Analysis (`gear_analysis_mdi.py`)
5. ✅ Acceleration Analysis (`acceleration_analysis_mdi.py`)
6. ✅ Speed Difference Analysis (`speeddiff_analysis_mdi.py`)
7. ✅ Distance Difference Analysis (`distancediff_analysis_mdi.py`)
8. ✅ Brake Analysis (`brake_analysis_mdi.py`)

**全部使用** `TelemetryDataLoaderBase` **作為基礎**

### 風險評估

| 風險 | 等級 | 影響 | 緩解措施 |
|------|------|------|----------|
| 新舊 JSON 檔名不匹配 | 🟡 中 | 無法讀取舊檔案 | 搜尋邏輯支援模糊匹配 |
| API 參數錯誤 | 🔴 高 | CLI 執行失敗 | 修復 API 請求構建 |
| Metadata 錯誤 | 🟡 中 | 數據分析混亂 | 同步修復 metadata |
| 檔案重複生成 | 🟢 低 | 儲存空間浪費 | 檔名標準化後自動解決 |

---

## 💡 長期改進建議

### 1. 參數標準化層

**建議**: 創建一個參數清理層，統一處理所有來自 GUI 的參數

```python
class ParameterNormalizer:
    """參數標準化器"""
    
    @staticmethod
    def normalize_race(race_input: str) -> str:
        """標準化 race 參數"""
        # 移除日期後綴
        # 移除多餘空格
        # 統一大小寫
        pass
    
    @staticmethod
    def normalize_driver(driver_input: str) -> str:
        """標準化 driver 參數"""
        # 轉大寫
        # 移除空格
        # 驗證長度
        pass
```

### 2. 檔案名稱生成器

**建議**: 集中管理檔案名稱生成邏輯

```python
class TelemetryFileNameBuilder:
    """遙測分析檔案名稱生成器"""
    
    @staticmethod
    def build_comparison_filename(year, race, session, driver1, driver2, lap1, lap2):
        """構建比較分析檔名"""
        # 參數驗證
        # 參數清理
        # 標準化構建
        pass
```

### 3. 型別檢查

**建議**: 使用 Python 型別提示確保參數正確性

```python
from typing import Union, Optional

def update_lap_parameters(
    self,
    year: Union[str, int],
    race: str,  # 應該是清理後的名稱
    session: str,
    driver1: str,
    driver2: Optional[str] = None,
    lap1: int = 1,
    lap2: Optional[int] = None,
    is_fastest: bool = False
) -> bool:
    """更新圈速參數 - 型別安全版本"""
    pass
```

---

## ✅ 驗收標準

修復成功的標準：

1. ✅ Toolbar driver 變更後，JSON 檔名正確反映新的 driver
2. ✅ Toolbar lap 變更後，JSON 檔名正確反映新的 lap
3. ✅ Race 參數不包含日期後綴
4. ✅ API 請求參數正確
5. ✅ Metadata 內容與實際數據一致
6. ✅ 檔案搜尋邏輯能找到正確的 JSON
7. ✅ 所有遙測模組正常運作

---

## 📚 相關文件

- `F1T_ENGLISH_LOCALIZATION_REPORT.md` - 國際化報告
- `API_NESTED_RESPONSE_FIX_REPORT.md` - API 回應格式修復
- `CLI_REMOVAL_COMPLETE_REPORT.md` - CLI 移除報告
- `f1t_gui_main.py` - 主視窗實現
- `telemetry_data_loader_base.py` - 遙測數據載入器基礎類別

---

**報告生成時間**: 2025-10-04  
**報告生成者**: GitHub Copilot  
**優先級**: 🔴 **Critical** - 立即修復
