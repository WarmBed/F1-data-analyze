# SpeedDiff Analysis Worker GC Fix Report
**日期**: 2025-11-15  
**模組**: `speeddiff_analysis_mdi.py`  
**問題**: 缺少停止舊 Worker 和異常處理邏輯  
**狀態**: 🔧 修復中

---

## 階段 1: 問題定位

### 搜索結果
```bash
# 搜索 Worker 創建位置
grep "self.api_worker = CrossEventComparisonWorker" speeddiff_analysis_mdi.py
→ Line 1644: self.api_worker = CrossEventComparisonWorker(...)

# 搜索跨賽事對比方法
grep "def update_cross_event_comparison" speeddiff_analysis_mdi.py
→ Line 1604: def update_cross_event_comparison(...)
```

### 代碼位置
- **檔案**: `modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_mdi.py`
- **方法**: `update_cross_event_comparison()` (Line 1604)
- **Worker 創建**: Line 1644
- **問題**: 缺少停止舊 Worker 和完整異常處理

---

## 階段 2: 修復前代碼分析

### 修復前代碼 (Lines 1640-1660)
```python
            # 更新資訊標籤
            self._update_info_label()
            
            # 創建 API Worker
            print(f"[SPEEDDIFF-CROSS-EVENT] 🚀 創建跨賽事比較 Worker...")
            self.api_worker = CrossEventComparisonWorker(
                driver1=driver1, year1=year1, race1=race1, session1=session1, lap1=lap1,
                driver2=driver2, year2=year2, race2=race2, session2=session2, lap2=lap2
            )
            
            # 連接信號
            self.api_worker.success.connect(self._on_cross_event_data_loaded)
            self.api_worker.failure.connect(self._on_cross_event_load_error)
            self.api_worker.progress.connect(lambda value: print(f"[SPEEDDIFF-CROSS-EVENT] 進度: {value}%"))
            
            # 啟動 Worker
            print(f"[SPEEDDIFF-CROSS-EVENT] 🔄 啟動 API 請求...")
            self.api_worker.start()
            
            return True
```

### 問題分析
| 項目 | 修復前狀態 | 預期狀態 |
|------|-----------|---------|
| **停止舊 Worker** | ❌ 無 | ✅ 需要 `if hasattr(self, 'api_worker')` |
| **Worker 創建** | ⚠️ 無 try/except | ✅ 需要異常處理 + 日誌 |
| **信號連接** | ⚠️ 無 try/except | ✅ 需要異常處理 + 日誌 |
| **Worker 引用保存** | ✅ **已有** `self.api_worker` | ✅ 正確 |
| **Worker 啟動** | ⚠️ 無 try/except | ✅ 需要異常處理 + 日誌 |

### 與 Brake 模組對比
| 差異點 | SpeedDiff (修復前) | Brake (修復後) |
|--------|------------------|---------------|
| 停止舊 Worker | ❌ 無 | ✅ Lines 762-769 |
| Worker 創建異常處理 | ❌ 無 | ✅ Lines 772-783 (try/except) |
| 信號連接異常處理 | ❌ 無 | ✅ Lines 786-797 (try/except) |
| **Worker 引用保存** | ✅ **有** `self.api_worker` | ✅ `self._cross_event_worker` |
| Worker 啟動異常處理 | ❌ 無 | ✅ Lines 803-813 (try/except) |

**注意**: SpeedDiff 使用 `self.api_worker` 而非 `self._cross_event_worker`，這是合理的命名差異。

---

## 階段 3: 修復實施

### 修復後代碼 (Lines 1640-1708)
```python
            # 更新資訊標籤
            self._update_info_label()
            
            # 停止舊的 Worker（如果存在）
            if hasattr(self, 'api_worker') and self.api_worker:
                try:
                    if self.api_worker.isRunning():
                        print(f"[SPEEDDIFF-CROSS-EVENT] 停止舊的 Worker...")
                        self.api_worker.requestInterruption()
                        self.api_worker.wait(500)
                except:
                    pass
            
            # 創建 API Worker
            try:
                print(f"[SPEEDDIFF-CROSS-EVENT] 🚀 創建跨賽事比較 Worker...")
                self.api_worker = CrossEventComparisonWorker(
                    driver1=driver1, year1=year1, race1=race1, session1=session1, lap1=lap1,
                    driver2=driver2, year2=year2, race2=race2, session2=session2, lap2=lap2
                )
                print(f"[SPEEDDIFF-CROSS-EVENT] ✅ Worker 創建成功")
            except Exception as e:
                error_msg = f"創建 API Worker 失敗: {e}"
                print(f"[ERROR] [SPEEDDIFF-CROSS-EVENT] {error_msg}")
                import traceback
                traceback.print_exc()
                return False
            
            # 連接信號
            try:
                self.api_worker.success.connect(self._on_cross_event_data_loaded)
                self.api_worker.failure.connect(self._on_cross_event_load_error)
                self.api_worker.progress.connect(lambda value: print(f"[SPEEDDIFF-CROSS-EVENT] 進度: {value}%"))
                print(f"[SPEEDDIFF-CROSS-EVENT] ✅ 信號連接成功")
            except Exception as e:
                error_msg = f"連接 Worker 信號失敗: {e}"
                print(f"[ERROR] [SPEEDDIFF-CROSS-EVENT] {error_msg}")
                import traceback
                traceback.print_exc()
                return False
            
            # 啟動 Worker
            try:
                print(f"[SPEEDDIFF-CROSS-EVENT] 🔄 啟動 API 請求...")
                self.api_worker.start()
                print(f"[SPEEDDIFF-CROSS-EVENT] ✅ API Worker 已啟動")
            except Exception as e:
                error_msg = f"啟動 API Worker 失敗: {e}"
                print(f"[ERROR] [SPEEDDIFF-CROSS-EVENT] {error_msg}")
                import traceback
                traceback.print_exc()
                return False
            
            return True
```

### 修復要點
1. ✅ **停止舊 Worker**: Lines 1643-1651 (9 lines)
2. ✅ **Worker 創建**: Lines 1653-1667 (15 lines, try/except)
3. ✅ **信號連接**: Lines 1669-1682 (14 lines, try/except)
4. ✅ **Worker 引用**: Line 1658 - 已有 `self.api_worker` ⭐
5. ✅ **Worker 啟動**: Lines 1684-1695 (12 lines, try/except)

---

## 階段 4: 測試驗證

### 測試清單
- [x] **Import 測試**: `python -c "from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi import SpeeddiffAnalysisModule; print('✅ SpeedDiff Import 測試通過')"`
  - ✅ 結果: 測試通過，無 Import 錯誤
  - 輸出: `[GUI_I18N] 已載入語言設定: en`
- [ ] **GUI 啟動測試**: 啟動 GUI，檢查 SpeedDiff 模組是否正常載入
- [ ] **跨賽事對比測試**: 選擇兩場比賽進行速度差對比，確認無崩潰
- [ ] **EXE 測試**: 在 EXE 環境下測試跨賽事對比功能

### 測試結果
```powershell
PS> python -c "from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi import SpeeddiffAnalysisModule; print('✅ SpeedDiff 模組 Import 測試通過')"
[GUI_I18N] 已載入語言設定: en (檔案: core\gui_language_config.json)
[OK] [MODULE_FACTORY] Speed analysis module registered
✅ SpeedDiff 模組 Import 測試通過
```

### 驗證結果
- ✅ Import 無錯誤
- ⏳ GUI 正常顯示 SpeedDiff 分析 (待用戶測試)
- ⏳ 跨賽事對比功能正常運作 (待用戶測試)
- ⏳ EXE 環境下無崩潰 (待 EXE 建置後測試)

---

## 修復總結

### 代碼變更統計
- **修改行數**: ~50 行新增/修改代碼（包含異常處理和日誌）
- **已有優勢**: 已使用 `self.api_worker` 保存引用
- **主要改進**: 添加停止舊 Worker 邏輯和完整異常處理

### 技術細節
- **既有優勢**: SpeedDiff 已經正確使用 `self.api_worker` 保存引用
- **改進點**: 添加防禦性編程（停止舊 Worker、異常處理）
- **命名差異**: 使用 `self.api_worker` 而非 `self._cross_event_worker` (都有效)

---

**修復狀態**: ✅ 修復完成，Import 測試通過  
**下一步**: 更新總體進度文檔 `ALL_MODULES_WORKER_FIX_SUMMARY_20251115.md`
