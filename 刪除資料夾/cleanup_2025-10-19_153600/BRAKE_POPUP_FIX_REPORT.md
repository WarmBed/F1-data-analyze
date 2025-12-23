# Brake Performance 彈窗問題修正報告

## 📋 問題描述

**症狀**: 打開 "All Drivers Brake Performance" 時彈出 QMessageBox 錯誤警告，顯示 "API 返回失敗"

**原因分析**:

1. **API-ONLY 模式設計**: 系統禁止 GUI 直接搜尋本地 JSON 檔案，必須透過 API 獲取數據
2. **錯誤處理過度**: `brake_performance_loader.py` 的 `_fetch_via_api_and_cache` 方法在 API 失敗時會發送 `load_error` 信號
3. **信號觸發彈窗**: `load_error` 信號連接到 MDI 的 `_on_load_error` 方法，該方法調用 `QMessageBox.critical()` 顯示彈窗

## 🔍 根本原因

在 API-ONLY 模式下：
- `_find_data_file()` 返回 `None`（因為 `_local_storage_enabled()` 返回 `False`）
- 觸發 `_fetch_via_api_and_cache()` 調用
- 如果 API 不可用或返回錯誤，方法內部發送 `load_error.emit()`
- 信號觸發 MDI 的錯誤處理器，顯示彈窗

**問題**: API 暫時不可用是**正常情況**，不應該彈出錯誤警告干擾用戶體驗。

## ✅ 修正方案

### 修正 1: 移除 API 失敗時的 `load_error.emit`

**檔案**: `modules/gui/all_drivers_brake_performance_analysis/brake_performance_loader.py`

**位置**: Line 202-203, 208-209

**修正前**:
```python
except Exception as exc:
    self._error(tr("brake_perf_api_load_failed", "API 載入失敗: {error}").format(error=str(exc)))
    self.load_error.emit(tr("brake_perf_api_load_failed", "API 載入失敗: {error}").format(error=str(exc)))
    return None

if not isinstance(payload, dict) or not payload.get("success", False):
    message = payload.get("message") if isinstance(payload, dict) else tr("brake_perf_unknown_error", "未知錯誤")
    self._error(tr("brake_perf_api_return_failed", "API 返回失敗: {message}").format(message=message))
    self.load_error.emit(tr("brake_perf_api_return_failed", "API 返回失敗: {message}").format(message=message))
    return None
```

**修正後**:
```python
except Exception as exc:
    self._error(tr("brake_perf_api_load_failed", "API 載入失敗: {error}").format(error=str(exc)))
    # ⚠️ [API-ONLY 模式修正] 不發送 load_error 信號，避免彈窗
    # API 失敗是正常情況，讓用戶通過其他方式獲取數據
    self._debug("💡 提示: API 暫時不可用，請稍後重試或檢查網絡連接")
    return None

if not isinstance(payload, dict) or not payload.get("success", False):
    message = payload.get("message") if isinstance(payload, dict) else tr("brake_perf_unknown_error", "未知錯誤")
    self._error(tr("brake_perf_api_return_failed", "API 返回失敗: {message}").format(message=message))
    # ⚠️ [API-ONLY 模式修正] 不發送 load_error 信號，避免彈窗
    self._debug("💡 提示: API 響應異常，請檢查後端服務狀態")
    return None
```

### 修正 2: 移除儲存失敗時的 `load_error.emit`

**檔案**: `modules/gui/all_drivers_brake_performance_analysis/brake_performance_loader.py`

**位置**: Line 222

**修正前**:
```python
output_path = self._write_payload_to_cache(payload, year, race, session)
if output_path:
    self.load_progress.emit(60)
    return output_path

self.load_error.emit(tr("brake_perf_save_error", "儲存 API 結果時發生錯誤"))
return None
```

**修正後**:
```python
output_path = self._write_payload_to_cache(payload, year, race, session)
if output_path:
    self.load_progress.emit(60)
    return output_path

# ⚠️ [API-ONLY 模式修正] 儲存失敗不影響數據使用，不發送 load_error
self._error(tr("brake_perf_save_error", "儲存 API 結果時發生錯誤"))
self._debug("💡 數據已成功獲取但未能寫入本地緩存，不影響使用")
return None
```

### 修正 3: 同步修正 Speed Loader

**檔案**: `modules/gui/lap_analysis/speed_analysis/straight_line_speed_loader.py`

**內容**: 與 Brake Loader 相同的修正，保持一致性

## 🎯 修正原則

1. **靜默失敗**: API 失敗時只記錄錯誤日誌，不彈出警告
2. **保留關鍵錯誤**: 參數驗證失敗等**用戶可控的錯誤**仍然彈窗提示
3. **區分錯誤類型**:
   - ✅ **保留彈窗**: 參數錯誤、用戶輸入錯誤
   - ❌ **移除彈窗**: API 不可用、網絡錯誤、後端服務錯誤

## 📊 保留的 load_error.emit 使用場景

### Brake Performance Loader

1. **Line 49**: 參數驗證失敗
   ```python
   if not self._validate_load_parameters(kwargs):
       self.load_error.emit(tr("brake_perf_load_param_invalid", "載入參數不正確"))
   ```
   ✅ **保留原因**: 用戶輸入錯誤，需要提示修正

2. **Line 176**: 缺少必要參數
   ```python
   except (KeyError, TypeError, ValueError) as exc:
       self.load_error.emit(tr("brake_perf_load_missing_params", "缺少必要參數"))
   ```
   ✅ **保留原因**: 程式邏輯錯誤，需要提示開發者

### Speed Loader

同 Brake Loader，保留參數驗證相關的錯誤彈窗。

## ✅ 預期效果

### 修正前行為:
1. 用戶打開 Brake Performance
2. 系統嘗試 API 調用
3. API 失敗（網絡問題/服務離線）
4. **彈出 QMessageBox 錯誤警告** ❌
5. 用戶關閉警告後介面空白

### 修正後行為:
1. 用戶打開 Brake Performance
2. 系統嘗試 API 調用
3. API 失敗（網絡問題/服務離線）
4. **靜默記錄錯誤日誌** ✅
5. 介面顯示空白或 loading 狀態
6. 用戶可以手動重試或等待 API 恢復

## 🧪 測試建議

### 測試場景 1: API 正常運作
```python
# 啟動 API 服務器
python refactored_api.py

# 打開 GUI，開啟 Brake Performance
# 預期: 正常載入數據，無任何警告
```

### 測試場景 2: API 不可用
```python
# 不啟動 API 服務器（或停止服務）

# 打開 GUI，開啟 Brake Performance
# 預期: 不彈出警告，終端顯示錯誤日誌，介面空白
```

### 測試場景 3: 參數錯誤
```python
# 修改 MDI 初始化參數為無效值
mdi.current_year = "invalid"

# 預期: 彈出參數錯誤警告（正確行為）
```

## 📝 補充說明

### 為什麼不使用 QMessageBox.warning?

因為在 API-ONLY 模式下，API 不可用是**預期內的正常狀況**，不是錯誤或警告，只是數據暫時不可用。類比：
- ❌ 網頁載入失敗不應該彈出警告框
- ✅ 網頁顯示 "載入中..." 或空白狀態

### 用戶如何知道載入失敗？

1. **介面狀態**: 表格保持空白或顯示 "無數據"
2. **終端日誌**: 開發者可查看詳細錯誤訊息
3. **狀態列**: MDI 底部狀態列可顯示 "API 不可用" 狀態（未來改進）

## 🔄 後續改進建議

1. **添加狀態指示器**: 在 MDI 中顯示 "正在載入..." 或 "API 不可用" 狀態
2. **重試機制**: 提供 "重新載入" 按鈕讓用戶手動重試
3. **降級提示**: 在 API 不可用時提示用戶可以使用離線數據（如果有）
4. **統一錯誤處理**: 創建 `ErrorPolicy` 類別統一管理哪些錯誤需要彈窗

---

**修正完成日期**: 2025-10-19  
**影響模組**: 
- `brake_performance_loader.py` (3 處修正)
- `straight_line_speed_loader.py` (3 處修正)

**測試狀態**: ⏳ 待測試
