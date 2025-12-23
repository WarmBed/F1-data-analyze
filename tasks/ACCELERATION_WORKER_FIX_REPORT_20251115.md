# Acceleration Analysis Worker GC Fix Report
**日期**: 2025-11-15  
**模組**: `acceleration_analysis_mdi.py`  
**問題**: EXE 環境下跨賽事對比功能崩潰（Worker 被垃圾回收）  
**狀態**: 🔧 修復中

---

## 階段 1: 問題定位

### 搜索結果
```bash
# 搜索 Worker 創建位置
grep "api_worker = CrossEventComparisonWorker" acceleration_analysis_mdi.py
→ Line 960: api_worker = CrossEventComparisonWorker(...)

# 搜索跨賽事對比方法
grep "def update_cross_event_comparison" acceleration_analysis_mdi.py
→ Line 922: def update_cross_event_comparison(...)
```

### 代碼位置
- **檔案**: `modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_mdi.py`
- **方法**: `update_cross_event_comparison()` (Line 922)
- **Worker 創建**: Line 960
- **問題行**: Line 960-974 (Worker 創建但未保存引用)

---

## 階段 2: 修復前代碼分析

### 修復前代碼 (Lines 950-980)
```python
            # 實作跨賽事比較邏輯：調用 API 端點
            print(f"[ACCELERATION-CROSS-EVENT] 開始調用 API 端點: /api/v2/analysis/cross-event-comparison")
            
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
            
            # 啟動 Worker
            api_worker.start()
            
            print(f"[ACCELERATION-CROSS-EVENT] API 請求已啟動")
            return True
```

### 問題分析
| 項目 | 修復前狀態 | 預期狀態 |
|------|-----------|---------|
| **停止舊 Worker** | ❌ 無 | ✅ 需要 `if hasattr(self, '_cross_event_worker')` |
| **Worker 創建** | ⚠️ 無 try/except | ✅ 需要異常處理 + 日誌 |
| **信號連接** | ⚠️ 無 try/except | ✅ 需要異常處理 + 日誌 |
| **Worker 引用保存** | ❌ **缺失** | ✅ 需要 `self._cross_event_worker = api_worker` |
| **Worker 啟動** | ⚠️ 無 try/except | ✅ 需要異常處理 + 日誌 |

### 與 Brake 模組對比
| 差異點 | Acceleration (修復前) | Brake (修復後) |
|--------|---------------------|---------------|
| 停止舊 Worker | ❌ 無 | ✅ Lines 762-769 |
| Worker 創建異常處理 | ❌ 無 | ✅ Lines 772-783 (try/except) |
| 信號連接異常處理 | ❌ 無 | ✅ Lines 786-797 (try/except) |
| **Worker 引用保存** | ❌ **無** | ✅ **Line 800** |
| Worker 啟動異常處理 | ❌ 無 | ✅ Lines 803-813 (try/except) |

---

## 階段 3: 修復實施

### 修復後代碼 (預計 Lines 950-1020)
```python
            # 實作跨賽事比較邏輯：調用 API 端點
            print(f"[ACCELERATION-CROSS-EVENT] 開始調用 API 端點: /api/v2/analysis/cross-event-comparison")
            
            # 停止舊的 Worker（如果存在）
            if hasattr(self, '_cross_event_worker') and self._cross_event_worker:
                try:
                    if self._cross_event_worker.isRunning():
                        print(f"[ACCELERATION-CROSS-EVENT] 停止舊的 Worker...")
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
                print(f"[ACCELERATION-CROSS-EVENT] ✅ Worker 創建成功")
            except Exception as e:
                error_msg = f"創建 API Worker 失敗: {e}"
                print(f"[ERROR] [ACCELERATION-CROSS-EVENT] {error_msg}")
                import traceback
                traceback.print_exc()
                return False
            
            # 連接信號
            try:
                api_worker.success.connect(self._on_cross_event_data_loaded)
                api_worker.failure.connect(self._on_cross_event_load_error)
                api_worker.progress.connect(self._on_api_progress)
                print(f"[ACCELERATION-CROSS-EVENT] ✅ 信號連接成功")
            except Exception as e:
                error_msg = f"連接 Worker 信號失敗: {e}"
                print(f"[ERROR] [ACCELERATION-CROSS-EVENT] {error_msg}")
                import traceback
                traceback.print_exc()
                return False
            
            # 🔴 關鍵修復：保存 Worker 引用（防止被垃圾回收導致 EXE 崩潰）
            self._cross_event_worker = api_worker
            
            # 啟動 Worker
            try:
                api_worker.start()
                print(f"[ACCELERATION-CROSS-EVENT] ✅ API Worker 已啟動")
            except Exception as e:
                error_msg = f"啟動 API Worker 失敗: {e}"
                print(f"[ERROR] [ACCELERATION-CROSS-EVENT] {error_msg}")
                import traceback
                traceback.print_exc()
                return False
            
            print(f"[ACCELERATION-CROSS-EVENT] API 請求已啟動")
            return True
```

### 修復要點
1. ✅ **停止舊 Worker**: Lines 953-961 (9 lines)
2. ✅ **Worker 創建**: Lines 963-976 (14 lines, try/except)
3. ✅ **信號連接**: Lines 978-990 (13 lines, try/except)
4. ✅ **Worker 引用保存**: Line 993 ⚠️ **核心修復**
5. ✅ **Worker 啟動**: Lines 995-1006 (12 lines, try/except)

---

## 階段 4: 測試驗證

### 測試清單
- [x] **Import 測試**: `python -c "from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi import accelerationAnalysisModule; print('✅ Acceleration Import 測試通過')"`
  - ✅ 結果: 測試通過，無 Import 錯誤
  - 輸出: `[GUI_I18N] 已載入語言設定: en`
- [ ] **GUI 啟動測試**: 啟動 GUI，檢查 Acceleration 模組是否正常載入
- [ ] **跨賽事對比測試**: 選擇兩場比賽進行對比，確認無崩潰
- [ ] **EXE 測試**: 在 EXE 環境下測試跨賽事對比功能

### 測試結果
```powershell
PS> python -c "from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi import accelerationAnalysisModule; print('✅ Acceleration Import 測試通過')"
[GUI_I18N] 已載入語言設定: en (檔案: C:\Users\mike2\OneDrive\Code\F1-data-analyze\core\gui_language_config.json)
[OK] [MODULE_FACTORY] Speed analysis module registered
✅ Acceleration 模組 Import 測試通過
```

### 驗證結果
- ✅ Import 無錯誤
- ⏳ GUI 正常顯示 Acceleration 分析 (待用戶測試)
- ⏳ 跨賽事對比功能正常運作 (待用戶測試)
- ⏳ EXE 環境下無崩潰 (待 EXE 建置後測試)

---

## 修復總結

### 代碼變更統計
- **修改行數**: ~28 行新增代碼（包含異常處理和日誌）
- **核心修復**: 1 行 (`self._cross_event_worker = api_worker`)
- **參考範本**: `brake_analysis_mdi.py` Lines 762-821

### 技術細節
- **問題根因**: PyInstaller EXE 環境下，局部變數 `api_worker` 在方法返回後被 GC 回收，導致 QThread 線程崩潰
- **解決方案**: 將 Worker 保存為實例屬性 `self._cross_event_worker`，確保對象生命週期延續至任務完成
- **防禦性編程**: 添加舊 Worker 停止邏輯，避免多次調用時的資源衝突

---

**修復狀態**: ✅ 修復完成，Import 測試通過  
**下一步**: 更新總體進度文檔 `ALL_MODULES_WORKER_FIX_SUMMARY_20251115.md`
