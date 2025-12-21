# 🔧 Gear Analysis - Worker 生命週期修復報告

**日期**: 2025-11-15  
**任務**: 將 Brake Analysis 的 Worker GC 修復應用到 Gear Analysis  
**參考模組**: Brake Analysis (已修復)  
**目標模組**: Gear Analysis (待修復)

---

## 📋 階段 1: 完整搜索結果

### 1.1 核心類別搜索

**搜索目標**: Worker 類別定義

| 項目 | Brake 模組 | Gear 模組 | 狀態 |
|------|-----------|-----------|------|
| Worker 類別 | `CrossEventBrakeComparisonWorker` | `CrossEventComparisonWorker` | ✅ 存在 |
| 檔案路徑 | `brake_analysis_mdi.py` | `gear_analysis_mdi.py` | ✅ 存在 |
| 行號 | Line 36 | Line 31 | ✅ 存在 |

### 1.2 關鍵方法搜索

**搜索目標**: `update_cross_event_comparison` 方法

| 項目 | Brake 模組 | Gear 模組 | 狀態 |
|------|-----------|-----------|------|
| 方法定義 | ✅ 找到 | ✅ 找到 Line 880 | 存在 |
| Worker 創建位置 | Line ~771 | Line ~918 | ✅ 存在 |
| Worker 保存 | ✅ `self._cross_event_worker = api_worker` | ❌ **缺少** | 🔴 需修復 |

---

## 🔍 階段 2: 逐行代碼對比

### 2.1 Brake 模組 (已修復) - Lines 762-821

**檔案**: `modules/gui/lap_analysis/brake_analysis/brake_analysis_mdi.py`

```python
# 停止舊的 Worker（如果存在）
if hasattr(self, '_cross_event_worker') and self._cross_event_worker:
    try:
        if self._cross_event_worker.isRunning():
            print(f"[BRAKE-CROSS-EVENT] 停止舊的 Worker...")
            self._cross_event_worker.requestInterruption()
            self._cross_event_worker.wait(500)
    except:
        pass

# 創建 API Worker
try:
    api_worker = CrossEventBrakeComparisonWorker(
        driver1=driver1, year1=year1, race1=race1, session1=session1, lap1=lap1,
        driver2=driver2, year2=year2, race2=race2, session2=session2, lap2=lap2,
        force_refresh=False,
        timeout=120
    )
    print(f"[BRAKE-CROSS-EVENT] ✅ Worker 創建成功")
except Exception as e:
    error_msg = f"創建 API Worker 失敗: {e}"
    print(f"[ERROR] [BRAKE-CROSS-EVENT] {error_msg}")
    import traceback
    traceback.print_exc()
    return False

# 連接信號
try:
    api_worker.success.connect(self._on_cross_event_data_loaded)
    api_worker.failure.connect(self._on_cross_event_load_error)
    api_worker.progress.connect(self._on_api_progress)
    print(f"[BRAKE-CROSS-EVENT] ✅ 信號連接成功")
except Exception as e:
    error_msg = f"連接 Worker 信號失敗: {e}"
    print(f"[ERROR] [BRAKE-CROSS-EVENT] {error_msg}")
    import traceback
    traceback.print_exc()
    return False

# 🔴 關鍵修復：保存 Worker 引用（防止被垃圾回收導致 EXE 崩潰）
self._cross_event_worker = api_worker

# 啟動 Worker
try:
    api_worker.start()
    print(f"[BRAKE-CROSS-EVENT] ✅ API Worker 已啟動")
except Exception as e:
    error_msg = f"啟動 API Worker 失敗: {e}"
    print(f"[ERROR] [BRAKE-CROSS-EVENT] {error_msg}")
    import traceback
    traceback.print_exc()
    return False

print(f"[BRAKE-CROSS-EVENT] API 請求已啟動")
return True
```

### 2.2 Gear 模組 (修復前) - Lines 910-935

**檔案**: `modules/gui/lap_analysis/gear_analysis/gear_analysis_mdi.py`

```python
# 創建 API Worker
api_worker = CrossEventComparisonWorker(
    driver1=driver1, year1=year1, race1=race1, session1=session1, lap1=lap1,
    driver2=driver2, year2=year2, race2=race2, session2=session2, lap2=lap2,
    force_refresh=False,
    timeout=120
)

# 連接信號
api_worker.success.connect(self._on_cross_event_data_loaded)
api_worker.failure.connect(self._on_cross_event_load_error)
api_worker.progress.connect(self._on_api_progress)

# ❌ 缺少：保存 Worker 引用
# ❌ 缺少：停止舊 Worker 邏輯
# ❌ 缺少：try/except 保護
# ❌ 缺少：詳細日誌

# 啟動 Worker
api_worker.start()

print(f"[CROSS-EVENT] API 請求已啟動")
return True
```

### 2.3 Gear 模組 (修復後) - Lines 915-977

```python
# 停止舊的 Worker（如果存在）
if hasattr(self, '_cross_event_worker') and self._cross_event_worker:
    try:
        if self._cross_event_worker.isRunning():
            print(f"[CROSS-EVENT] 停止舊的 Worker...")
            self._cross_event_worker.requestInterruption()
            self._cross_event_worker.wait(500)
    except:
        pass

# 創建 API Worker
try:
    api_worker = CrossEventComparisonWorker(
        driver1=driver1, year1=year1, race1=race1, session1=session1, lap1=lap1,
        driver2=driver2, year2=year2, race2=race2, session2=session2, lap2=lap2,
        force_refresh=False,
        timeout=120
    )
    print(f"[CROSS-EVENT] ✅ Worker 創建成功")
except Exception as e:
    error_msg = f"創建 API Worker 失敗: {e}"
    print(f"[ERROR] [CROSS-EVENT] {error_msg}")
    import traceback
    traceback.print_exc()
    return False

# 連接信號
try:
    api_worker.success.connect(self._on_cross_event_data_loaded)
    api_worker.failure.connect(self._on_cross_event_load_error)
    api_worker.progress.connect(self._on_api_progress)
    print(f"[CROSS-EVENT] ✅ 信號連接成功")
except Exception as e:
    error_msg = f"連接 Worker 信號失敗: {e}"
    print(f"[ERROR] [CROSS-EVENT] {error_msg}")
    import traceback
    traceback.print_exc()
    return False

# 🔴 關鍵修復：保存 Worker 引用（防止被垃圾回收導致 EXE 崩潰）
self._cross_event_worker = api_worker

# 啟動 Worker
try:
    api_worker.start()
    print(f"[CROSS-EVENT] ✅ API Worker 已啟動")
except Exception as e:
    error_msg = f"啟動 API Worker 失敗: {e}"
    print(f"[ERROR] [CROSS-EVENT] {error_msg}")
    import traceback
    traceback.print_exc()
    return False

print(f"[CROSS-EVENT] API 請求已啟動")
return True
```

---

## ⚠️ 階段 3: 差異分析

### 差異 #1: 缺少停止舊 Worker 的邏輯

**位置**: Gear Line ~910 之前  
**類型**: 缺少邏輯  
**優先級**: 🔴 高  

**影響**:
- 如果用戶連續多次修改跨賽事參數，舊的 Worker 可能仍在運行
- 可能導致多個 Worker 同時運行，浪費資源
- 舊 Worker 的回調可能覆蓋新數據

---

### 差異 #2: 缺少 Worker 引用保存 (🔴 關鍵)

**位置**: Gear Line ~925  
**類型**: 🔴 **關鍵缺失**  
**優先級**: 🔴 **最高**  

**Brake 模組**:
```python
# 🔴 關鍵修復：保存 Worker 引用（防止被垃圾回收導致 EXE 崩潰）
self._cross_event_worker = api_worker
```

**Gear 模組**:
```python
# ❌ 完全缺少此行
```

**影響**:
- **在 EXE 環境中，Worker 對象會被立即 GC**
- **QThread 被 GC 後會導致程序崩潰**
- 這是 **Brake/Throttle 模組原始崩潰的根本原因**

---

### 差異 #3: 缺少 try/except 保護

**位置**: Worker 創建、信號連接、啟動的所有步驟  
**類型**: 缺少異常處理  
**優先級**: 🔴 高  

**影響**:
- Worker 創建失敗時沒有清晰的錯誤日誌
- 異常會向上拋出，可能導致整個模組崩潰
- 無法區分是創建失敗、連接失敗還是啟動失敗

---

### 差異 #4: 缺少詳細日誌

**位置**: 各個步驟之間  
**類型**: 缺少調試輸出  
**優先級**: 🟡 中  

**影響**:
- 問題發生時難以追蹤執行流程
- 無法確認 Worker 是否成功創建/連接/啟動

---

## 🔧 階段 4-6: 修復實施

### 修復完成 ✅

**位置**: `gear_analysis_mdi.py` Lines 915-977

**修復內容**:
1. ✅ 添加停止舊 Worker 邏輯 (Lines 918-925)
2. ✅ Worker 創建包裹在 try/except (Lines 928-939)
3. ✅ 信號連接包裹在 try/except (Lines 942-952)
4. ✅ **關鍵修復**: `self._cross_event_worker = api_worker` (Line 955)
5. ✅ Worker 啟動包裹在 try/except (Lines 958-968)
6. ✅ 詳細日誌輸出

---

## ✅ 階段 7: 測試驗證

### 7.1 Import 測試
```python
from modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi import GearAnalysisModule
print("✅ Gear 模組 Import 測試通過")
```

**測試結果**: ✅ 通過 (2025-11-15 04:25)

### 7.2 代碼驗證
- ✅ 修復代碼已確認正確寫入
- ✅ 包含所有必要的 try/except 塊
- ✅ Worker 引用保存到 `self._cross_event_worker`
- ✅ 詳細日誌輸出完整

### 7.3 待執行測試
- [ ] EXE 崩潰重現測試 (待重新建置 EXE)
- [ ] 實際運行日誌驗證

---

## 📊 階段 8: 修復檢查清單

### 代碼修復完成度
- [x] 添加停止舊 Worker 邏輯 ✅
- [x] 添加 Worker 創建 try/except ✅
- [x] 添加信號連接 try/except ✅
- [x] **添加 `self._cross_event_worker = api_worker`** (🔴 最關鍵) ✅
- [x] 添加 Worker 啟動 try/except ✅
- [x] 添加所有步驟的詳細日誌 ✅

### 測試驗證完成度
- [x] Import 測試通過 ✅
- [x] 代碼語法正確 ✅
- [ ] EXE 崩潰重現測試通過 (待 EXE 重建)
- [ ] 實際運行日誌驗證 (待 EXE 重建)

### 文檔完成度
- [x] 差異分析文檔完成 ✅
- [x] 修復方案文檔完成 ✅
- [x] 修復代碼已應用 ✅
- [ ] 最終測試結果記錄 (待 EXE 測試)

---

**版本**: v1.0  
**狀態**: ✅ 修復完成，Import 測試通過，待 EXE 重建後進行完整測試  
**完成時間**: 2025-11-15 04:25  
**參考**: `BRAKE_QTHREAD_GC_FIX_REPORT.md`, `THROTTLE_WORKER_FIX_REPORT_20251115.md`
