# F1T Live Timing - 比賽前準備檢查清單

## 概述

本文檔列出在 F1 比賽開始前，確保 Live Timing 所有功能正常運作的檢查步驟。

---

## 🔴 Realtime 模式現況

**當前狀態：尚未完整實現**

Realtime 模式的「Connect」按鈕目前只有 placeholder：
```python
def _on_connect_clicked(self):
    """連接即時 Live Timing"""
    print("[CONTROL_DOCK] Connect clicked - realtime mode not yet implemented")
    # TODO: 實現即時連接
```

### 需要實現的功能

1. **SignalR 連接器**（`F1SignalRClient`）
   - Negotiate 獲取 ConnectionToken
   - WebSocket 連接
   - 訂閱數據流 (Position.z, TimingData, CarData.z 等)
   - 數據解碼 (Base64 + Zlib)

2. **Realtime 數據源整合**
   - 將 `demo_live_position_tracking.py` 中的 `F1SignalRClient` 整合到 GUI
   - 實現 `RealTimeLiveF1DataSource` 類

---

## ✅ Historical 模式 (當前可用)

Historical 模式完全可用，用於播放已下載的賽事數據。

### 數據來源
- **本地 PKL 快取**：`json/LiveF1/{year}/{race}_{session}/`
- **API 下載**：通過 `F1APIDownloader` 從 F1 官方獲取歷史數據

---

## 📋 比賽前檢查清單

### 1. API 服務器狀態
```powershell
# 確認 API 服務器運行中
curl https://api.f1telemetrystationpro.org/api/v2/system/health
```

**預期結果**：
```json
{"status": "healthy", "version": "2.0.0"}
```

### 2. 賽道數據 API
```powershell
# 測試 Function 2 (Track Analysis)
python -c "from modules.gui.live_timing.core.api_client import get_api_client; c = get_api_client(); c.clear_cache(); d = c.get_track_analysis(2025, 'Qatar', 'R'); print('position_records:', len(d.get('position_records', [])))"
```

**預期結果**：`position_records: > 0`

### 3. 配置數據 API
```powershell
# 測試 Config API
python -c "from modules.gui.live_timing.core.api_client import get_api_client; c = get_api_client(); d = c.get_tire_degradation(); print('circuits:', len(d.get('circuits', {})) if d else 0)"
```

**預期結果**：`circuits: > 0`

### 4. GUI 啟動測試
```powershell
# 執行 GUI
python f1t_gui_main.py
```

**檢查項目**：
- [ ] 狀態列顯示 `[API] ONLINE`
- [ ] Live Timing 選單可開啟
- [ ] Track Map 和 Circle Map 正常顯示賽道

### 5. Historical 模式功能測試
1. 開啟 Live Timing Control Panel
2. 選擇 Historical 模式
3. 選擇年份、賽事、會話
4. 點擊 Load
5. 確認：
   - [ ] 數據載入成功
   - [ ] Track Map 顯示賽道輪廓
   - [ ] Circle Map 顯示車手位置
   - [ ] Ranking Tower 顯示排名
   - [ ] Driver Strategy 顯示輪胎策略

---

## 🔧 常見問題排解

### 問題 1: Track Map / Circle Map 空白
**原因**：API 返回數據結構問題
**解決**：確認 `api_client.py` 正確解析嵌套的 `data.data` 結構

### 問題 2: Config API 404
**原因**：API 服務器未重啟
**解決**：重啟 API 服務器載入新的 config 路由

### 問題 3: 賽道數據 0 點
**原因**：賽事名稱不匹配
**解決**：確認賽事名稱正確（例如 "Qatar" 而非 "Qatari"）

---

## 📅 比賽時間表 (2025 賽季)

| 站次 | 賽事 | 日期 |
|------|------|------|
| 24 | 阿布達比 | 2025-12-07 (Sun) |

### 下一場比賽準備
1. **比賽前 1 天**：確認 API 服務器運行
2. **比賽前 2 小時**：測試 Historical 模式
3. **比賽開始時**：使用 Historical 模式播放歷史數據（Realtime 尚未實現）

---

## 🚀 未來工作：Realtime 實現計劃

### Phase 1: SignalR 客戶端
- [ ] 將 `demo_live_position_tracking.py` 的 `F1SignalRClient` 移到 `modules/gui/live_timing/core/`
- [ ] 創建 `signalr_client.py`
- [ ] 實現 QThread 包裝器

### Phase 2: 數據管理器整合
- [ ] 在 `data_manager.py` 中添加 Realtime 數據源支持
- [ ] 實現 `connect_realtime()` 和 `disconnect_realtime()` 方法

### Phase 3: UI 整合
- [ ] 實現 `_on_connect_clicked()` 方法
- [ ] 實現連接狀態更新
- [ ] 實現斷線重連機制

---

## 附錄：SignalR 連接參考代碼

```python
# 從 demo_live_position_tracking.py 提取
class F1SignalRClient:
    """F1 Live Timing SignalR 客戶端"""
    
    SIGNALR_URL = "https://livetiming.formula1.com/signalr"
    HUB_NAME = "Streaming"
    PROTOCOL_VERSION = "1.5"
    
    TOPICS = [
        "CarData.z",
        "Position.z",
        "TimingData",
        "DriverList",
        "WeatherData",
        "TrackStatus",
        "SessionInfo",
        "LapCount",
        "RaceControlMessages"
    ]
```

---

*最後更新：2025-12-05*
