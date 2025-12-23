# PopoutSubWindow 記憶體洩漏修復 v4.1 - 添加詳細診斷

## 🔍 v4.0 測試結果分析

### objgraph_report_20251015_205725.txt 顯示

**所有 5 個組件仍然洩漏 + PopoutSubWindow 本身也洩漏！**

```
54. ↑ SpeedAnalysisModule           1 (+1) ❌
55. ↑ SpeedDataManager              1 (+1) ❌
56. ↑ SpeedAnalysisChartWidget      1 (+1) ❌
57. ↑ SpeedChartWidget              1 (+1) ❌
58. ↑ PopoutSubWindow               1 (+1) ❌ 關鍵！視窗本身洩漏！
59. ↑ DraggableTitleBar             1 (+1) ❌
63. ↑ SpeedAnalysisDataLoader       1 (+1) ❌
```

### 日誌分析

#### ✅ v4.0 改進已生效

```log
[20:57:21] [CLEANUP] Speed Analysis_2025_Singapore_R 正在調用模組 cleanup()...
[20:57:21] [SPEED_MDI] 🧹 開始清理速度分析模組資源...
[20:57:21] [SPEED_CHART]   ✅ __dict__ 已清理（21 個屬性）
[20:57:21] [SPEED_MDI] ✅ 已清理 19 個屬性
[20:57:21] [CLEANUP] ✅ 模組 cleanup() 完成
[20:57:21] [CLEANUP] ✅ DraggableTitleBar 資源清理完成
[20:57:22] [CLEANUP] Speed Analysis_2025_Singapore_R 資源已清理完成
```

**確認**：
- ✅ `analysis_module.cleanup()` 被調用
- ✅ 所有清理階段都執行
- ✅ TitleBar 清理完成

#### ❌ 但 GC 仍然無效

```log
[20:57:21] [SPEED_MDI] ✅ 已執行垃圾回收（回收 0 個物件）
```

**問題**：GC 回收 0 個物件，表示仍有強引用！

---

## 💡 根本原因

### PopoutSubWindow 本身洩漏了！

**關鍵發現**：
- 如果 PopoutSubWindow 本身沒有被釋放
- 那麼它持有的所有模組引用也無法釋放
- 即使模組的 cleanup() 執行了，引用仍然存在

### 可能的原因

#### 1. MDI 區域仍持有引用

PopoutSubWindow.closeEvent() 中有：
```python
if self.parent_mdi and hasattr(self.parent_mdi, 'removeSubWindow'):
    try:
        self.parent_mdi.removeSubWindow(self)
    except Exception:
        pass  # ← 靜默失敗，沒有日誌！
```

**問題**：
- ❌ 沒有日誌輸出，無法確認是否執行
- ❌ Exception 被靜默吞掉
- ❌ 沒有確認 removeSubWindow 是否成功

#### 2. Qt 的 deleteLater() 未調用

PopoutSubWindow 設置了 `Qt.WA_DeleteOnClose`，但：
- 可能需要明確調用 `deleteLater()`
- Qt 事件循環可能延遲處理

#### 3. 重複 cleanup() 調用

發現兩次調用 cleanup()：
```log
[20:57:21] [CLEANUP] 正在調用模組 cleanup()...        ← PopoutSubWindow.closeEvent()
[20:57:21] ✅ 模組 cleanup() 完成

[20:57:21] [LAP_CONTROL] 調用模組清理方法           ← on_lap_analysis_window_closed()
[20:57:22] 🧹 開始清理資源...
[20:57:22] ✅ 已清理 1 個屬性  ← 第二次只剩 1 個屬性
```

雖然這不是主要問題，但可能干擾清理過程。

---

## 🔧 v4.1 修復方案

### 修復 1：添加 MDI 移除診斷日誌

**修復前**：
```python
if self.parent_mdi and hasattr(self.parent_mdi, 'removeSubWindow'):
    try:
        self.parent_mdi.removeSubWindow(self)
    except Exception:
        pass  # 靜默失敗
```

**修復後**：
```python
if self.parent_mdi and hasattr(self.parent_mdi, 'removeSubWindow'):
    try:
        print(f"[CLEANUP] {window_title} 正在從 MDI 區域移除子視窗...")
        self.parent_mdi.removeSubWindow(self)
        print(f"[CLEANUP] {window_title} ✅ 已從 MDI 區域移除")
    except Exception as e:
        print(f"[ERROR] {window_title} 從 MDI 移除失敗: {e}")
else:
    print(f"[WARNING] {window_title} 無法移除（parent_mdi={self.parent_mdi}）")
```

### 修復 2：明確調用 deleteLater()

**添加**：
```python
# 🔧 修復洩漏5: 明確調用 deleteLater() 確保 Qt 釋放資源
print(f"[CLEANUP] {window_title} 正在調用 deleteLater()...")
self.deleteLater()
print(f"[CLEANUP] {window_title} ✅ deleteLater() 已調用")
```

**原理**：
- 雖然設置了 `Qt.WA_DeleteOnClose`，但明確調用更保險
- 確保 Qt 事件循環會在下一次迭代時刪除物件
- 添加日誌確認調用

---

## 🧪 v4.1 測試計畫

### 預期日誌輸出

```log
[CLEANUP] Speed Analysis_2025_Singapore_R 正在調用模組 cleanup()...
[SPEED_MDI] 🧹 開始清理速度分析模組資源...
[SPEED_CHART]   ✅ __dict__ 已清理（21 個屬性）
[SPEED_MDI] ✅ 已清理 19 個屬性
[SPEED_MDI] ✅ 已執行垃圾回收（回收 5+ 個物件）  ← 期待不再是 0
[CLEANUP] ✅ 模組 cleanup() 完成
[CLEANUP] ✅ DraggableTitleBar 資源清理完成
[CLEANUP] 正在從 MDI 區域移除子視窗...           ← 新增！
[CLEANUP] ✅ 已從 MDI 區域移除                   ← 新增！
[CLEANUP] 正在調用 deleteLater()...              ← 新增！
[CLEANUP] ✅ deleteLater() 已調用                 ← 新增！
[CLEANUP] 資源已清理完成
```

### 檢查命令

```powershell
# 1. 確認 MDI 移除操作
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "從 MDI 區域移除|已從 MDI 區域移除" | Select-Object -Last 5

# 2. 確認 deleteLater 調用
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "deleteLater" | Select-Object -Last 5

# 3. 檢查 GC 回收
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "已執行垃圾回收" | Select-Object -Last 3

# 4. 檢查 objgraph
Get-ChildItem -Path "." -Filter "objgraph_report_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object { Write-Host $_.Name; Select-String -Path $_.FullName -Pattern "PopoutSubWindow|SpeedAnalysisModule" }
```

---

## 📊 可能的結果

### 場景 A：部分改善

```
✅ PopoutSubWindow 消失（不再洩漏）
❌ 模組組件仍然洩漏（1-2 個）
```

**結論**：MDI 引用問題解決，但模組內部還有循環引用

### 場景 B：完全解決

```
✅ PopoutSubWindow 消失
✅ 所有 5 個模組組件消失
✅ GC 回收 > 0 個物件
```

**結論**：問題完全解決！

### 場景 C：仍然洩漏

```
❌ PopoutSubWindow 仍然 +1
❌ 所有組件仍然洩漏
```

**下一步**：
- 檢查是否有其他全域列表持有引用
- 使用 `gc.get_referrers()` 追蹤引用鏈
- 檢查 Qt 父子關係（可能需要 `setParent(None)`）

---

## 🎓 關鍵經驗

### v4.0 → v4.1 進展

**v4.0 成就**：
- ✅ 確認了 cleanup() 調用鏈正確
- ✅ 所有清理步驟都執行
- ✅ 發現了根本問題：PopoutSubWindow 本身洩漏

**v4.1 改進**：
- ✅ 添加 MDI 移除診斷日誌
- ✅ 明確調用 deleteLater()
- ✅ 詳細的異常處理

### 調試方法論

1. **從外到內**：
   - 先確認最外層（PopoutSubWindow）是否釋放
   - 再檢查內層（模組組件）

2. **完整日誌**：
   - 每個關鍵步驟都要有日誌
   - Exception 絕不靜默吞掉

3. **驗證假設**：
   - 不能假設代碼執行了
   - 必須用日誌確認

---

**文檔版本**：v4.1
**創建時間**：2025-10-15 21:05
**狀態**：等待測試
**關鍵改進**：添加 MDI 移除和 deleteLater 診斷
