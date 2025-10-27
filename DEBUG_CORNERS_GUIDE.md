# 調試增強測試指南

## 目的
通過詳細的調試輸出，追蹤 official_corners 從 API 到 GUI 顯示的完整數據流。

## 增強的調試點

### 1. track_analysis_mdi.py - process_loaded_data (line 665-679)
```
✅ process_loaded_data: 提取到 N 個彎道
   - available: True/False
   - count: N
   - corners 陣列長度: N
```

### 2. track_analysis_mdi.py - processed_data 構建 (line 707-713)
```
✅ processed_data 包含 official_corners: N 個彎道
```

### 3. track_analysis_mdi.py - on_data_loaded (line 1055-1066)
```
==================== on_data_loaded 開始 ====================
data keys: [...]
✅ 輸入 data 包含 official_corners: N 個彎道
```

### 4. track_analysis_mdi.py - track_data 構建 (line 1080-1094)
```
==================== 構建 track_data ====================
track_data keys: [...]
✅ track_data 包含 official_corners:
   - available: True
   - count: N
   - corners 陣列長度: N
   - 第一個彎道: 1, X=..., Y=...
```

### 5. track_map_widget.py - load_track_data (line 109-140)
```
==================== load_track_data 開始 ====================
track_data keys: [...]
==================== 載入 official_corners ====================
official_corners_data 類型: <class 'dict'>
✅ 成功載入 N 個官方彎道
   第一個彎道: number=1, x=..., y=...
self.official_corners 最終狀態: 長度=N
self.show_official_corners 狀態: True/False
```

### 6. track_map_widget.py - paintEvent (line 318-326)
```
paintEvent: 準備繪製 N 個彎道
或
paintEvent: show_official_corners=False (未啟用)
或
paintEvent: official_corners 為空 (長度=0)
```

### 7. track_map_widget.py - _draw_official_corners (line 409-418)
```
_draw_official_corners: 開始繪製
   self.official_corners 長度: N
_draw_official_corners: 準備繪製 N 個彎道
```

## 測試步驟

### 1. 清理舊的 Python 進程
```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

### 2. 啟動 GUI 並觀察 console 輸出
```powershell
python f1t_gui_main.py
```

### 3. 載入測試賽事
- Year: 2025
- Race: United States (2025-10-19)  # 從截圖看到
- Session: R

或

- Year: 2024
- Race: Japan (2024-04-07)  # 從截圖看到
- Session: R

### 4. 檢查 console 輸出

**期望看到的完整流程**：

```
[TRACK_ANALYSIS_MDI] ✅ process_loaded_data: 提取到 18 個彎道
[TRACK_ANALYSIS_MDI] ✅ processed_data 包含 official_corners: 18 個彎道
[TRACK_ANALYSIS_MDI] ==================== on_data_loaded 開始 ====================
[TRACK_ANALYSIS_MDI] ✅ 輸入 data 包含 official_corners: 18 個彎道
[TRACK_ANALYSIS_MDI] ==================== 構建 track_data ====================
[TRACK_ANALYSIS_MDI] ✅ track_data 包含 official_corners:
[TRACK_ANALYSIS_MDI]    - available: True
[TRACK_ANALYSIS_MDI]    - count: 18
[TRACK_ANALYSIS_MDI] ==================== 調用 load_track_data ====================
[TRACK_MAP] ==================== load_track_data 開始 ====================
[TRACK_MAP] ==================== 載入 official_corners ====================
[TRACK_MAP] ✅ 成功載入 18 個官方彎道
[TRACK_MAP] self.official_corners 最終狀態: 長度=18
[TRACK_MAP] self.show_official_corners 狀態: True
[TRACK_MAP] paintEvent: 準備繪製 18 個彎道
[TRACK_MAP] _draw_official_corners: 開始繪製
[TRACK_MAP] _draw_official_corners: 準備繪製 18 個彎道
```

### 5. 檢查可能的問題點

#### 問題 A: process_loaded_data 階段就沒有彎道
```
❌ process_loaded_data: 未找到 official_corners
   payload keys: [...]
```
**原因**: `_extract_analysis_payload` 沒有正確解析雙層 data 結構
**檢查**: API 響應是否正確

#### 問題 B: track_data 沒有彎道
```
❌ track_data 的 official_corners 為空
```
**原因**: `on_data_loaded` 沒有從 data 中提取 official_corners
**檢查**: 上一步 processed_data 是否包含

#### 問題 C: load_track_data 沒有接收到彎道
```
❌ 未載入官方彎道
   available: False
   corners 存在: False
```
**原因**: track_data 傳遞時遺失了 official_corners
**檢查**: MDI 構建的 track_data 結構

#### 問題 D: paintEvent 沒有繪製
```
paintEvent: show_official_corners=False (未啟用)
```
**原因**: checkbox 沒有勾選
**解決**: 在控制面板勾選「顯示官方彎道」

#### 問題 E: official_corners 為空
```
paintEvent: official_corners 為空 (長度=0)
```
**原因**: load_track_data 沒有成功載入
**檢查**: 回到問題 C

## 下一步

根據 console 輸出，找到哪個環節斷掉了，然後針對性修復。

## 快速測試腳本

如果不想啟動完整 GUI，可以用 standalone 測試：

```powershell
python test_track_map_standalone.py --year 2024 --race Japan
```

這個會直接讀取本地 JSON，跳過 API，更容易隔離問題。
