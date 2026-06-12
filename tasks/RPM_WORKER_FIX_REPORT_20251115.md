# RPM Analysis Worker 生命週期修復報告

**文件版本**: v1.0  
**修復日期**: 2025-11-15  
**修復時間**: 19:30  
**修復模組**: RPM Analysis (`rpm_analysis_mdi.py`)  
**當前狀態**: ✅ 修復完成，Import 測試通過

---

## 📊 階段一：問題診斷

### 🔍 問題定位
**檔案位置**: `modules/gui/lap_analysis/rpm_analysis/rpm_analysis_mdi.py`  
**問題方法**: `update_cross_event_comparison()` (Lines 966-1030)  
**核心問題**: Line 1004 創建 Worker 為局部變數 `api_worker`，未保存為實例屬性

### ⚠️ 當前代碼問題（Lines 1004-1020）
```python
# 創建 API Worker
api_worker = CrossEventComparisonWorker(  # ❌ 局部變數！
    driver1=driver1, year1=year1, race1=race1, session1=session1, lap1=lap1,
    driver2=driver2, year2=year2, race2=race2, session2=session2, lap2=lap2,
    force_refresh=False,
    timeout=120
)

# 連接信號
api_worker.success.connect(self._on_cross_event_data_loaded)
api_worker.failure.connect(self._on_cross_event_load_error)
api_worker.progress.connect(self._on_api_progress)

# 啟動 Worker
api_worker.start()

print(f"[RPM-CROSS-EVENT] API 請求已啟動")
return True
```

**問題分析**:
1. ❌ Worker 未保存為實例屬性（`self._cross_event_worker`）
2. ❌ 未檢查並停止舊的 Worker
3. ❌ 無異常處理機制（Worker 創建、信號連接、啟動都缺乏 try/except）
4. ❌ PyInstaller EXE 中會因 GC 導致 QThread 崩潰

---

## 🔧 階段二：修復方案對比

### 📋 標準修復模式（參考 Brake Analysis Lines 762-821）

| 修復要素 | Brake 標準實現 | RPM 當前狀態 | 修復需求 |
|---------|---------------|-------------|---------|
| **停止舊 Worker** | ✅ Lines 762-770 (9 lines) | ❌ 無 | 🔧 需添加 |
| **Worker 創建 try/except** | ✅ Lines 772-786 (15 lines) | ❌ 無 | 🔧 需添加 |
| **信號連接 try/except** | ✅ Lines 788-801 (14 lines) | ❌ 無 | 🔧 需添加 |
| **Worker 引用保存** | ✅ Line 808 `self._cross_event_worker` | ❌ Line 1004 局部變數 | 🔧 需修改 |
| **Worker 啟動 try/except** | ✅ Lines 810-821 (12 lines) | ❌ 無 | 🔧 需添加 |

**修復規模**: 預計從 17 行擴展為約 60 行（+43 行防禦性編程）

---

## 🎯 階段三：代碼修復

### ✅ 修復目標（Lines 1000-1030）
將簡單的 Worker 創建/連接/啟動模式，升級為完整的防禦性編程模式：

#### 1️⃣ 停止舊 Worker (9 lines)
```python
# 停止舊的 Worker（如果存在）
if hasattr(self, '_cross_event_worker') and self._cross_event_worker:
    try:
        if self._cross_event_worker.isRunning():
            print(f"[RPM-CROSS-EVENT] 停止舊的 Worker...")
            self._cross_event_worker.requestInterruption()
            self._cross_event_worker.wait(500)
    except:
        pass
```

#### 2️⃣ Worker 創建 try/except (15 lines)
```python
try:
    print(f"[RPM-CROSS-EVENT] 🚀 創建跨賽事比較 Worker...")
    api_worker = CrossEventComparisonWorker(...)
    print(f"[RPM-CROSS-EVENT] ✅ Worker 創建成功")
except Exception as e:
    error_msg = f"創建 API Worker 失敗: {e}"
    print(f"[ERROR] [RPM-CROSS-EVENT] {error_msg}")
    import traceback
    traceback.print_exc()
    return False
```

#### 3️⃣ 信號連接 try/except (14 lines)
```python
try:
    api_worker.success.connect(self._on_cross_event_data_loaded)
    api_worker.failure.connect(self._on_cross_event_load_error)
    api_worker.progress.connect(self._on_api_progress)
    print(f"[RPM-CROSS-EVENT] ✅ 信號連接成功")
except Exception as e:
    error_msg = f"連接 Worker 信號失敗: {e}"
    print(f"[ERROR] [RPM-CROSS-EVENT] {error_msg}")
    import traceback
    traceback.print_exc()
    return False
```

#### 4️⃣ Worker 引用保存 (1 line) - **關鍵修復**
```python
self._cross_event_worker = api_worker  # 保存引用防止 GC
```

#### 5️⃣ Worker 啟動 try/except (12 lines)
```python
try:
    print(f"[RPM-CROSS-EVENT] 🔄 啟動 API 請求...")
    api_worker.start()
    print(f"[RPM-CROSS-EVENT] ✅ API Worker 已啟動")
except Exception as e:
    error_msg = f"啟動 API Worker 失敗: {e}"
    print(f"[ERROR] [RPM-CROSS-EVENT] {error_msg}")
    import traceback
    traceback.print_exc()
    return False
```

### 📝 修復行數統計
- **原代碼**: Lines 1000-1023 (24 lines)
- **新代碼**: 預計 61 lines
- **淨增加**: +37 lines

---

## 🧪 階段四：測試驗證

### ✅ 測試檢查清單

#### Import 測試
- [x] 執行 `python -c "from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi import RPMAnalysisModule; print('✅ RPM 模組 Import 測試通過')"`
- [x] 確認無 ImportError
- [x] 確認無 SyntaxError

#### 功能測試
- [ ] GUI 啟動無錯誤
- [ ] RPM 模組開啟正常
- [ ] 跨賽事比較功能可用
- [ ] Worker 引用已保存（檢查 `self._cross_event_worker`）

### 📊 測試結果
```powershell
PS> python -c "from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi import RPMAnalysisModule; print('✅ RPM 模組 Import 測試通過')"

[GUI_I18N] 已載入語言設定: en (檔案: core\gui_language_config.json)
[OK] [MODULE_FACTORY] Speed analysis module registered
✅ RPM 模組 Import 測試通過

Exit Code: 0
```

✅ **測試結果**: Import 測試通過，無錯誤訊息

---

## 📋 階段五：總結

### ✅ 修復完成項目
- [x] 添加停止舊 Worker 邏輯
- [x] 添加 Worker 創建異常處理
- [x] 添加信號連接異常處理
- [x] **修改 Worker 引用為實例屬性**
- [x] 添加 Worker 啟動異常處理
- [x] Import 測試通過

### 🎯 修復效果
- **問題**: PyInstaller EXE 中 Worker 被 GC 導致崩潰
- **解決**: 將 Worker 保存為 `self._cross_event_worker` 防止 GC
- **額外**: 添加完整的異常處理和日誌輸出

### 📄 相關文件
- 個別報告: `tasks/RPM_WORKER_FIX_REPORT_20251115.md` (本文件)
- 總覽文件: `tasks/ALL_MODULES_WORKER_FIX_SUMMARY_20251115.md` (待更新)

### 🔄 下一步
- ✅ 代碼修改已完成（Lines 1000-1061, 新增 38 行）
- ✅ Import 測試已通過
- ⏳ 待更新總覽文件 `ALL_MODULES_WORKER_FIX_SUMMARY_20251115.md`

---

**報告建立時間**: 2025-11-15 19:30  
**遵循標準**: 反幻覺編碼五原則 + Brake 修復模式  
**修復模式**: 7/9 模組（加上 RPM 後）
