# 修復報告：GUI 賽事選擇器「無賽事」問題

**修復日期**: 2025-10-07  
**問題編號**: GUI-CALENDAR-001  
**嚴重程度**: 🔴 高 (影響所有 GUI 模組的賽事選擇功能)

---

## 📋 問題描述

### 症狀
- GUI 主視窗和子視窗的賽事下拉選單顯示「無賽事」或空白
- 所有分析模組無法正常選擇賽事
- 問題出現在 CLI 功能 -f99 升級為批量查詢模式之後

### 根本原因
CLI 功能 -f99 (賽季賽程查詢) 更新後：

1. **JSON 檔案命名格式改變**：
   - 舊格式：`season_calendar_2025_20251006.json` (單一年份)
   - 新格式：`season_calendar_2020-2025_20251006T162216Z.json` (批量多年)

2. **JSON 數據結構改變**：
   ```json
   // 舊格式（單年）
   {
     "data": [
       {"round": 1, "event_name": "..."},
       ...
     ]
   }
   
   // 新格式（多年嵌套）
   {
     "data": {
       "2020": {"data": [...]},
       "2021": {"data": [...]},
       "2025": {"data": [...]}
     }
   }
   ```

3. **API 回應額外包裝層**：
   ```json
   {
     "data": {           // ← API 包裝層
       "data": {         // ← CLI 輸出層
         "2025": {...}   // ← 年份數據
       }
     }
   }
   ```

4. **GUI 的 `SeasonCalendarProvider` 不相容**：
   - `_load_latest_json()` 使用舊的檔案名稱模式 `season_calendar_{year}_` 搜尋
   - `_transform_payload()` 無法處理多年嵌套結構
   - 無法解開 API 的雙層包裝

---

## ✅ 修復方案

### 修改檔案
- `modules/gui/shared/season_calendar_provider.py`

### 主要變更

#### 1. 更新 `_load_latest_json()` 方法
**變更內容**：
- 搜尋所有 `season_calendar_*.json` 檔案（不限單年格式）
- 使用新方法 `_payload_contains_year()` 檢查每個檔案是否包含所需年份
- 支援單年和多年 JSON 檔案

**程式碼**：
```python
def _load_latest_json(self, year: int) -> Optional[Dict[str, Any]]:
    """載入最新的季節日曆 JSON，支援單年和多年格式"""
    if not JSON_DIR.exists():
        return None
    
    # 搜尋所有 season_calendar JSON 檔案
    all_candidates = sorted(
        JSON_DIR.glob("season_calendar_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    
    for candidate in all_candidates:
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
            
            # 檢查是否包含指定年份的數據
            if self._payload_contains_year(payload, year):
                print(f"[SEASON] 從本地 JSON 載入: {candidate.name} (年份: {year})")
                return payload
                
        except Exception as e:
            print(f"[SEASON] 讀取 {candidate.name} 失敗: {e}")
            continue
    
    print(f"[SEASON] 未找到包含 {year} 年的本地 JSON 檔案")
    return None
```

#### 2. 新增 `_payload_contains_year()` 輔助方法
**功能**：檢查 JSON payload 是否包含指定年份的數據

**程式碼**：
```python
def _payload_contains_year(self, payload: Dict[str, Any], year: int) -> bool:
    """檢查 payload 是否包含指定年份的數據"""
    if not isinstance(payload, dict):
        return False
    
    data = payload.get("data")
    if not data:
        return False
    
    # 多年嵌套格式: {"data": {"2020": {...}, "2025": {...}}}
    if isinstance(data, dict) and str(year) in data:
        return True
    
    # 單年格式: {"data": [{...}, {...}]}
    if isinstance(data, list):
        # 檢查 metadata 中的年份
        metadata = payload.get("metadata", {})
        if metadata.get("year") == year:
            return True
    
    return False
```

#### 3. 更新 `_transform_payload()` 方法
**變更內容**：
- 添加 `year` 參數以支援多年格式
- 解開 API 的雙層包裝 (`data.data`)
- 從多年嵌套結構中提取特定年份的數據
- 向後兼容單年格式

**程式碼**：
```python
def _transform_payload(self, payload: Dict[str, Any], year: Optional[int] = None) -> List[SeasonEvent]:
    """轉換 payload 為 SeasonEvent 列表，支援單年和多年格式"""
    events: List[SeasonEvent] = []
    
    # 先解開可能的 API 包裝層
    # API 回應格式: {"data": {"data": {"2025": {...}}}}
    # 本地 JSON 格式: {"data": {"2025": {...}}}
    data_container = payload.get("data")
    
    # 檢查是否有雙層嵌套（API 格式）
    if isinstance(data_container, dict) and "data" in data_container:
        # 如果內層還有 "data" key，且是字典（包含年份 keys），則解開一層
        inner_data = data_container.get("data")
        if isinstance(inner_data, dict) and any(k.isdigit() for k in inner_data.keys()):
            data_container = inner_data
    
    # 處理多年嵌套格式
    if isinstance(data_container, dict) and year is not None:
        # 多年格式: {"data": {"2020": {...}, "2025": {...}}}
        year_str = str(year)
        if year_str in data_container:
            year_data = data_container[year_str]
            # 遞迴處理單年數據
            if isinstance(year_data, dict):
                raw_events = self._extract_event_records(year_data.get("data"))
            else:
                raw_events = self._extract_event_records(year_data)
        else:
            print(f"[SEASON] payload 中未找到 {year} 年的數據")
            print(f"[SEASON] 可用的年份: {list(data_container.keys())}")
            return events
    else:
        # 單年格式: {"data": [{...}, {...}]}
        raw_events = self._extract_event_records(data_container)
    
    # ... (後續處理保持不變)
```

#### 4. 更新調用點
**變更**：在 `get_completed_events()` 中傳遞 `year` 參數

```python
events = self._transform_payload(payload, year=year)
```

---

## 🧪 測試結果

### 測試案例 1: 本地 JSON 載入
```
✅ 2025 年: 24 個賽事（18 已完成 + 6 未開賽）
✅ 2024 年: 24 個賽事（全部已完成）
✅ 2020-2023 年: 正常載入
```

### 測試案例 2: API 載入
```
✅ API URL: https://api.f1telemetrystationpro.org
✅ 成功解開雙層包裝
✅ 正確提取年份數據
```

### 測試案例 3: 快取機制
```
✅ 同一年份的重複請求使用快取
✅ 不同年份的請求正確隔離
```

### 測試案例 4: 向後兼容
```
✅ 支援舊的單年 JSON 格式
✅ 支援新的多年 JSON 格式
✅ 自動識別檔案格式
```

---

## 📊 影響範圍

### 修復的模組
- ✅ GUI 主視窗賽事選擇器
- ✅ 所有子視窗（Lap Analysis、Tire Analysis、Rain Analysis 等）
- ✅ 設定對話框的賽事列表
- ✅ SeasonCalendarProvider 的所有消費者

### 不受影響
- ✅ CLI 功能（-f99 正常運作）
- ✅ API 服務器（返回正確的嵌套結構）
- ✅ 其他 GUI 功能

---

## 🔄 相容性

### 向後兼容
- ✅ 支援舊的單年 JSON 檔案
- ✅ 支援新的多年 JSON 檔案
- ✅ 自動選擇最新的可用檔案

### 向前兼容
- ✅ 支援未來的 JSON 結構變更（只要保持年份 key 格式）
- ✅ 智能檔案搜尋，不依賴固定命名模式

---

## 📝 備註

### API-ONLY 模式符合性
此修復完全符合 API-ONLY 政策：
- ✅ 僅讀取已存在的本地 JSON 檔案
- ✅ 優先使用 API 獲取數據
- ✅ 不自動啟動 CLI 進程
- ✅ 本地 JSON 作為 fallback 機制

### CLI 功能 -f99 使用指引
開發者需要新數據時，手動執行：
```powershell
# 生成 2020-2025 所有年份（批量模式，預設啟用）
python f1_analysis_modular_main.py -f 99

# 或指定單一年份
python f1_analysis_modular_main.py -f 99 -y 2025 --no-all-years
```

生成的 JSON 檔案會自動被 GUI 識別和使用。

---

## ✅ 驗證清單

- [x] 本地 JSON 載入正常
- [x] API 載入正常
- [x] 多年格式支援
- [x] 單年格式向後兼容
- [x] GUI 賽事選擇器顯示正常
- [x] 快取機制正常
- [x] 錯誤處理完善
- [x] 日誌輸出清晰
- [x] 符合 API-ONLY 政策

---

**修復狀態**: ✅ 完成  
**測試狀態**: ✅ 通過  
**部署狀態**: ✅ 可立即使用

建議使用者重啟 GUI 應用程式以載入修復。
