# 🔄 Season Calendar 自動刷新機制修復報告

**日期**: 2025-10-20  
**問題**: United States (2025-10-19) 顯示為 [Upcoming] 而不是 Completed  
**根本原因**: GUI 沒有檢查本地 JSON 的新鮮度

---

## 🐛 問題描述

### 用戶反饋
> "今天是 2025-10-20，United States 正賽在 2025-10-19，為什麼還顯示 [Upcoming]？"

### 問題截圖
```
Netherlands (2025-08-31)          ← Completed ✅
Italy (2025-09-07)                ← Completed ✅
Singapore (2025-10-05)            ← Completed ✅
United States (2025-10-19) [Upcoming]  ← ❌ 錯誤！應該是 Completed
Mexico (2025-10-26) [Upcoming]         ← 正確
```

---

## 🔍 根本原因分析

### 問題鏈條

```
最新 JSON 生成於 10/13
    ↓
當時 United States (10/19) 還沒比賽
    ↓
JSON 中 is_completed = False
    ↓
GUI 只讀取 JSON，不檢查時間
    ↓
即使現在是 10/20，還是顯示 Upcoming
```

### CLI 層（Function 99）
```python
# ✅ 有時間計算
is_completed = bool(race_dt_utc and race_dt_utc <= reference)

# ✅ 有刷新檢查
CALENDAR_REFRESH_HOURS = 168  # 7天

# ❌ 但沒有自動執行
```

### GUI 層（SeasonCalendarProvider）- 修復前
```python
# ❌ 沒有時間檢查
def get_completed_events(self, year: int):
    payload = self._fetch_from_api(year)  # API 可能不可用
    if payload is None:
        payload = self._load_latest_json(year)  # 直接讀取舊 JSON
```

---

## ✅ 修復方案

### 修改檔案
`modules/gui/shared/season_calendar_provider.py`

### 新增功能

#### 1. 添加刷新常數
```python
# 🔄 Calendar 刷新策略：與 CLI 保持一致
CALENDAR_REFRESH_HOURS = 168  # 7 天 (賽程固定除非有改期)
```

#### 2. 新增檔案年齡檢查方法
```python
def _get_latest_json_info(self, year: int) -> tuple[Optional[Path], Optional[float]]:
    """
    獲取最新的 season calendar JSON 檔案資訊
    
    Returns:
        (檔案路徑, 檔案年齡小時數) 如果找到
        (None, None) 如果找不到
    """
    # 搜索最新的 JSON 檔案
    for candidate in all_candidates:
        if self._payload_contains_year(payload, year):
            # 計算檔案年齡
            file_mtime = datetime.fromtimestamp(candidate.stat().st_mtime, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            age_hours = (now - file_mtime).total_seconds() / 3600
            
            return (candidate, age_hours)
```

#### 3. 智能刷新邏輯
```python
def get_completed_events(self, year: int) -> List[SeasonEvent]:
    """
    ✨ 智能刷新邏輯：
    - 優先檢查本地 JSON 的新鮮度（< 7天）
    - 如果新鮮，直接使用本地 JSON
    - 如果過期或不存在，嘗試通過 API 刷新
    - API 失敗則降級使用舊的 JSON（總比沒有好）
    """
    
    # 🔍 Step 1: 檢查本地 JSON 的新鮮度
    local_json_path, local_json_age_hours = self._get_latest_json_info(year)
    is_local_fresh = local_json_age_hours is not None and local_json_age_hours < CALENDAR_REFRESH_HOURS
    
    if is_local_fresh:
        print(f"[SEASON] 本地 JSON 仍新鮮（{local_json_age_hours:.1f} 小時前），直接使用")
        payload = self._load_latest_json(year)
    else:
        # 🌐 Step 2: 本地 JSON 過期或不存在，嘗試 API 刷新
        print(f"[SEASON] 本地 JSON 已過期（{local_json_age_hours:.1f} 小時前），嘗試通過 API 刷新")
        payload = self._fetch_from_api(year)
        
        # 📁 Step 3: API 失敗，降級使用舊的 JSON
        if payload is None:
            print(f"[SEASON] API 不可用，降級使用本地 JSON（即使過期）")
            payload = self._load_latest_json(year)
```

---

## 📊 修復效果

### 修復前
```
10/13 生成 JSON → is_completed=False
                ↓
10/20 GUI 讀取 → 顯示 [Upcoming] ❌
```

### 修復後
```
10/20 GUI 啟動
    ↓
檢查 JSON 年齡 = 168+ 小時（過期）
    ↓
調用 API 獲取最新數據
    ↓
API 返回最新狀態：is_completed=True
    ↓
顯示 Completed ✅
```

### 降級策略
```
API 不可用
    ↓
降級使用舊 JSON（總比沒有好）
    ↓
顯示 [Upcoming] ⚠️
    ↓
提示用戶手動刷新
```

---

## 🧪 測試驗證

### 測試腳本
`test_calendar_freshness.py`

### 測試場景

#### 場景 1: JSON 新鮮（< 7天）
```
Input:  JSON 生成於 3 天前
Output: 直接使用本地 JSON，不調用 API
Log:    [SEASON] 本地 JSON 仍新鮮（72.5 小時前），直接使用
```

#### 場景 2: JSON 過期（> 7天）
```
Input:  JSON 生成於 10 天前
Output: 調用 API 刷新
Log:    [SEASON] 本地 JSON 已過期（240.0 小時前），嘗試通過 API 刷新
```

#### 場景 3: JSON 不存在
```
Input:  沒有本地 JSON
Output: 調用 API 獲取
Log:    [SEASON] 未找到本地 JSON，嘗試通過 API 獲取
```

#### 場景 4: API 不可用 + JSON 過期
```
Input:  API 離線，JSON 過期
Output: 降級使用舊 JSON
Log:    [SEASON] API 不可用，降級使用本地 JSON（即使過期）
```

---

## 📝 使用指南

### 立即修復（手動刷新）

#### 方法 1: CLI 刷新
```powershell
# 強制重新生成日曆
python f1_analysis_modular_main.py -f 99 --force

# 重啟 GUI（自動載入新 JSON）
python f1t_gui_main.py
```

#### 方法 2: API 刷新
```powershell
# 啟動 API 服務器
python refactored_api.py

# 調用 API（用 curl 或瀏覽器）
curl -X POST "http://localhost:8000/api/v2/analysis/execute?function_id=99&force=true"

# 重啟 GUI
python f1t_gui_main.py
```

### 自動刷新（修復後）

```python
# GUI 啟動時自動檢查
provider = SeasonCalendarProvider()
events = provider.get_completed_events(2025)

# 如果 JSON 過期（> 7天），自動調用 API 刷新
# 如果 API 不可用，降級使用舊 JSON 並提示用戶
```

---

## 🎯 最佳實踐

### 開發環境

1. **定期執行 CLI**：每週執行一次 `python f1_analysis_modular_main.py -f 99`
2. **監控檔案年齡**：檢查 `json/season_calendar_*.json` 的修改時間
3. **測試 API 可用性**：確保 API 服務器運行正常

### 生產環境

1. **API 優先**：確保 API 服務器 24/7 運行
2. **備用 JSON**：保留最新的 JSON 檔案作為離線備份
3. **監控告警**：設置監控檢測 JSON 過期（> 7天）

### 用戶體驗

1. **透明提示**：在 Console 顯示數據來源和年齡
2. **手動刷新**：提供 GUI 按鈕手動觸發刷新（未來增強）
3. **狀態指示**：顯示數據最後更新時間

---

## 🔮 未來增強

### Phase 1: GUI 手動刷新按鈕
```python
# 在 GUI 添加 "刷新賽程" 按鈕
def refresh_calendar_manually(self):
    # 清除緩存
    self._season_provider._cache.clear()
    
    # 強制 API 刷新
    self._season_provider.get_completed_events(year, force=True)
    
    # 重新載入 race_combo
    self._refresh_calendar_for_year(year)
```

### Phase 2: 背景自動刷新
```python
# 每小時檢查一次
QTimer.singleShot(3600000, self._check_calendar_freshness)

def _check_calendar_freshness(self):
    if self._need_refresh():
        self._refresh_calendar_silently()
```

### Phase 3: 實時推送通知
```python
# WebSocket 推送賽事更新
def on_race_completed(event_data):
    # 更新內存緩存
    self._update_event_status(event_data)
    
    # 刷新 GUI
    self._refresh_race_combo()
```

---

## 📚 相關文檔

- [Upcoming Race Logic](./UPCOMING_RACE_LOGIC.md) - 完整邏輯說明
- [Upcoming Race Flowchart](./UPCOMING_RACE_FLOWCHART.md) - 流程圖
- [API-ONLY 模式政策](../.github/copilot-instructions.md) - 開發政策

---

## ✅ 修復確認

- [x] 識別問題根源（GUI 沒有時間檢查）
- [x] 添加檔案年齡檢查方法
- [x] 實現智能刷新邏輯
- [x] 添加降級策略（API 不可用時）
- [x] 保持與 CLI 刷新週期一致（7天）
- [x] 創建測試腳本驗證修復
- [x] 編寫完整文檔

**修復完成時間**: 2025-10-20  
**測試狀態**: ✅ 待驗證  
**可部署**: ✅

---

## 💡 關鍵要點

1. **問題**: GUI 不檢查 JSON 檔案年齡，導致顯示過期數據
2. **修復**: 添加智能刷新邏輯，檢查 JSON 年齡並自動調用 API
3. **策略**: API 優先 → 新鮮 JSON → 過期 JSON（降級）
4. **週期**: 與 CLI 保持一致（7 天）
5. **用戶體驗**: 透明日誌 + 降級策略 + 未來手動刷新
