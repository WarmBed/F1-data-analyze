# PopoutSubWindow 關鍵修復 v4.0 - 調用模組 cleanup()

## 🚨 發現的致命問題

### 問題描述

**所有模組的 cleanup() 方法都沒有被調用！**

雖然之前在 SpeedAnalysisModule 和 SpeedChartWidget 中實施了完善的 cleanup() 方法，但這些方法**從未被執行**，因為：

**PopoutSubWindow.closeEvent() 沒有調用 `analysis_module.cleanup()`**

---

## 🔍 問題追蹤

### v3.4 測試結果

```
objgraph_report_20251015_201159.txt 顯示：
54. ↑ SpeedAnalysisModule           1 (+1)  ← 回來了！
55. ↑ SpeedDataManager              1 (+1)  ← 回來了！
56. ↑ SpeedAnalysisChartWidget      1 (+1)  ← 回來了！
57. ↑ SpeedChartWidget              1 (+1)  ← 回來了！
63. ↑ SpeedAnalysisDataLoader       1 (+1)  ← 回來了！

GC 回收: 0 個物件 ❌
```

**所有 5 個組件都洩漏了！**

### 日誌分析

v3.4 清理日誌顯示：
```log
[SPEED_CHART]   ✅ __dict__ 已清理（21 個屬性）     ← 執行了！
[SPEED_MDI] ✅ 已清理 19 個屬性                   ← 執行了！
[SPEED_MDI] ✅ 已執行垃圾回收（回收 0 個物件）    ← GC 仍然無效
```

**結論**：清理步驟都有執行，但為什麼 objgraph 顯示所有組件仍然洩漏？

---

## 💡 根本原因

### 發現關鍵問題

檢查 `PopoutSubWindow.closeEvent()` (f1t_gui_main.py:4486) 發現：

**修復前的代碼**：
```python
def closeEvent(self, event):
    """子視窗關閉事件處理"""
    try:
        window_title = self.windowTitle()
        
        # 🔧 修復洩漏1: 斷開所有模組信號連接
        if hasattr(self, 'analysis_module') and self.analysis_module:
            try:
                # 斷開模組信號
                if hasattr(self.analysis_module, 'module_error'):
                    self.analysis_module.module_error.disconnect()
                if hasattr(self.analysis_module, 'parameters_updated'):
                    self.analysis_module.parameters_updated.disconnect()
                print(f"[CLEANUP] {window_title} 已斷開模組信號連接")
            except Exception as e:
                print(f"[WARNING] {window_title} 斷開信號時出錯: {e}")
        
        # ... 其他清理 ...
        
        # 🔧 修復洩漏3: 清理所有對象引用
        self.analysis_module = None  # ❌ 只是清空引用，沒有調用 cleanup()！
```

**問題**：
- ❌ 只斷開了 PopoutSubWindow → Module 的信號連接
- ❌ 只清空了 `self.analysis_module` 引用
- ❌ **從未調用 `analysis_module.cleanup()` 方法**
- ❌ 模組內部的所有資源（DataManager、ChartWidget、Loader 等）都沒有被清理

---

## 🔧 修復方案

### v4.0 修復

**修復後的代碼**：
```python
def closeEvent(self, event):
    """子視窗關閉事件處理"""
    try:
        window_title = self.windowTitle()
        
        # 🔧 修復洩漏1: 調用模組的 cleanup() 方法（最優先！）
        if hasattr(self, 'analysis_module') and self.analysis_module:
            try:
                # ✅ 調用模組的 cleanup() 方法清理所有資源
                if hasattr(self.analysis_module, 'cleanup'):
                    print(f"[CLEANUP] {window_title} 正在調用模組 cleanup()...")
                    self.analysis_module.cleanup()
                    print(f"[CLEANUP] {window_title} ✅ 模組 cleanup() 完成")
                else:
                    print(f"[WARNING] {window_title} 模組沒有 cleanup() 方法")
                
                # 斷開模組信號
                if hasattr(self.analysis_module, 'module_error'):
                    try:
                        self.analysis_module.module_error.disconnect()
                    except:
                        pass
                if hasattr(self.analysis_module, 'parameters_updated'):
                    try:
                        self.analysis_module.parameters_updated.disconnect()
                    except:
                        pass
                print(f"[CLEANUP] {window_title} 已斷開模組信號連接")
            except Exception as e:
                print(f"[ERROR] {window_title} 模組清理時出錯: {e}")
                import traceback
                traceback.print_exc()
        
        # ... 其他清理保持不變 ...
```

**關鍵改進**：
1. ✅ **優先調用 `analysis_module.cleanup()`**
2. ✅ 詳細的日誌輸出，確認 cleanup() 是否執行
3. ✅ 異常處理，即使 cleanup() 失敗也繼續清理
4. ✅ 完整的 traceback 輸出，便於診斷問題

---

## 🎯 預期效果

### v4.0 應該解決的問題

**清理鏈完整執行**：
```
用戶關閉視窗
    ↓
PopoutSubWindow.closeEvent()
    ↓
✅ analysis_module.cleanup()  ← 新增！現在會調用！
    ↓
    ├─ SpeedDataManager.cleanup()
    │   ├─ 停止 CLI 執行緒
    │   ├─ 清理資料引用
    │   └─ GC 回收
    │
    ├─ SpeedChartWidget.cleanup()
    │   ├─ 清理 Matplotlib 圖表
    │   ├─ 清理 QTableWidget
    │   ├─ 斷開 Qt 連接
    │   └─ 清理 __dict__
    │
    ├─ SpeedAnalysisDataLoader.cleanup()
    │   └─ 清理資料載入器
    │
    ├─ 從 analysis_manager 解除註冊
    ├─ 從 linkage_manager 解除註冊
    └─ 清理模組 __dict__
```

**預期 objgraph 結果**：
```
❌ v3.4 (修復前):
54. ↑ SpeedAnalysisModule           1 (+1)
55. ↑ SpeedDataManager              1 (+1)
56. ↑ SpeedAnalysisChartWidget      1 (+1)
57. ↑ SpeedChartWidget              1 (+1)
63. ↑ SpeedAnalysisDataLoader       1 (+1)

✅ v4.0 (修復後):
（這些類型應該完全消失）
```

**預期日誌輸出**：
```log
[CLEANUP] ⚡ 速度分析_2025_Japan_R 正在調用模組 cleanup()...
[SPEED_MDI] 🧹 開始清理速度分析模組資源...
[SPEED_MDI] 🧹 階段 1: 清理數據管理器...
[SPEEDDATAMANAGER] 🧹 開始清理資源...
[SPEEDDATAMANAGER] ✅ 資源清理完成
[SPEED_MDI] ✅ 階段 1 完成
[SPEED_MDI] 🧹 階段 2: 清理圖表組件...
[SPEED_CHART] 🧹 開始清理資源...
[SPEED_CHART]   ✅ 已從連動管理器解除註冊
[SPEED_CHART]   ✅ Matplotlib 圖表已清理
[SPEED_CHART]   ✅ Qt 連接已斷開
[SPEED_CHART]   ✅ __dict__ 已清理（21 個屬性）
[SPEED_CHART] ✅ 資源清理完成
[SPEED_MDI] ✅ 階段 2 完成
[SPEED_MDI] 🧹 階段 7: 清理模組 __dict__...
[SPEED_MDI] ✅ 已清理 19 個屬性
[SPEED_MDI] ✅ 已執行垃圾回收（回收 5+ 個物件）  ← 不再是 0！
[CLEANUP] ⚡ 速度分析_2025_Japan_R ✅ 模組 cleanup() 完成
[CLEANUP] ⚡ 速度分析_2025_Japan_R 已斷開模組信號連接
```

---

## 🧪 測試計畫

### 測試步驟

```powershell
# 1. 確保 GUI 已關閉
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 2. 啟動 GUI
python f1t_gui_main.py
```

**測試流程**：
1. ✅ 開啟速度分析模組
2. ⏳ 等待 5 秒
3. ❌ 關閉速度分析模組
4. ⏳ 等待 5 秒
5. 🔍 執行 objgraph 快照

### 檢查清單

測試後確認：

- [ ] 看到 "[CLEANUP] 正在調用模組 cleanup()..." 輸出
- [ ] 看到完整的清理階段輸出（階段 1-7）
- [ ] 看到 "✅ 模組 cleanup() 完成"
- [ ] GC 回收 > 0 個物件（不再是 0）
- [ ] objgraph 不再顯示這 5 個組件

### 檢查命令

```powershell
# 1. 檢查是否調用了 cleanup()
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "正在調用模組 cleanup|模組 cleanup\(\) 完成" | Select-Object -Last 5

# 2. 檢查完整清理流程
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "階段 [1-7]|已清理.*個屬性|Qt 連接已斷開" | Select-Object -Last 20

# 3. 檢查 GC 回收結果
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "已執行垃圾回收" | Select-Object -Last 3

# 4. 找到最新 objgraph 報告
Get-ChildItem -Path "." -Filter "objgraph_report_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object { $_.FullName }

# 5. 檢查洩漏組件
Select-String -Path (Get-ChildItem -Path "." -Filter "objgraph_report_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName -Pattern "SpeedAnalysisModule|SpeedDataManager|SpeedChartWidget|SpeedAnalysisDataLoader"
```

---

## 📊 成功標準

### v4.0 修復成功的標誌

| 檢查項目 | v3.4 (修復前) | v4.0 (預期) |
|---------|--------------|-------------|
| cleanup() 調用 | ❌ 無 | ✅ 有 |
| 清理階段執行 | ❌ 無 | ✅ 完整 1-7 階段 |
| GC 回收物件 | 0 | 5+ |
| SpeedAnalysisModule | +1 ❌ | 0 ✅ |
| SpeedDataManager | +1 ❌ | 0 ✅ |
| SpeedChartWidget | +1 ❌ | 0 ✅ |
| SpeedAnalysisChartWidget | +1 ❌ | 0 ✅ |
| SpeedAnalysisDataLoader | +1 ❌ | 0 ✅ |

---

## 🎓 經驗教訓

### 為什麼之前沒發現

1. **v3.3 假象成功**：
   - 之前測試顯示 4/6 組件清理成功
   - 實際上可能是 Python 緩存導致的假象
   - 或者測試時間點不同（GC 延遲執行）

2. **日誌混淆**：
   - 看到清理日誌就以為清理完成
   - 實際上那些日誌可能來自其他測試
   - 沒有檢查 cleanup() 是否真的被調用

3. **架構理解不足**：
   - 以為 PopoutSubWindow 會自動調用模組 cleanup()
   - 實際上 Qt 的 `setWidget()` 不會自動管理 Python 物件生命週期
   - 需要明確調用 cleanup() 方法

### 關鍵教訓

✅ **必須追蹤完整的調用鏈**
- 不能只實現 cleanup() 方法
- 必須確保 cleanup() 被調用
- 必須驗證調用鏈的每個環節

✅ **日誌必須明確標示調用點**
- 添加 "正在調用模組 cleanup()..." 日誌
- 添加 "模組 cleanup() 完成" 日誌
- 確認方法確實被執行

✅ **測試必須徹底驗證**
- 不能只看部分改善就滿足
- 必須確認所有組件都清理乾淨
- 必須檢查 GC 回收是否有效

---

## 📝 總結

**v4.0 關鍵修復**：
- 🔧 在 `PopoutSubWindow.closeEvent()` 中添加 `analysis_module.cleanup()` 調用
- 🔧 確保清理鏈完整執行
- 🔧 詳細日誌輸出便於驗證

**預期結果**：
- ✅ 所有 5 個速度模組組件完全清理
- ✅ GC 成功回收物件（不再是 0）
- ✅ objgraph 不再顯示洩漏組件

**下一步**：
- 測試 v4.0 修復
- 如果成功，應用到其他 8 個 Lap Analysis 模組
- 關閉所有 DummyThread 洩漏問題

---

**文檔版本**：v4.0
**創建時間**：2025-10-15 20:30
**狀態**：等待測試驗證
**關鍵性**：🚨 **極高** - 這是整個清理鏈的入口點
