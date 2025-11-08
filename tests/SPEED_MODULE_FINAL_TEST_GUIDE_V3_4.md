# 速度模組最終修復測試指南 v3.4

## 🎯 修復內容總結

### 已實施的修復

#### 1. SpeedChartWidget 強化清理（speed_analysis_chart_widget.py）

新增了 3 個清理步驟：

**步驟 0**：從連動管理器解除註冊
```python
linkage_manager.unregister_module(self)
```

**步驟 7**：徹底斷開所有 Qt 連接
```python
self.disconnect()
```

**步驟 8**：徹底清理 __dict__
```python
for attr in all_attrs:
    if not attr.startswith('__'):
        delattr(self, attr)
```

#### 2. SpeedAnalysisModule 強化清理（speed_analysis_mdi.py）

新增了階段 7：

**徹底清理模組 __dict__**
```python
essential_attrs = {'_module_id', '_module_name', '_version'}
for attr in all_attrs:
    if attr not in essential_attrs and not attr.startswith('__'):
        delattr(self, attr)
```

---

## 🧪 測試步驟

### 步驟 1：確保 GUI 已關閉

```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
```

### 步驟 2：啟動 GUI

```powershell
python f1t_gui_main.py
```

### 步驟 3：執行測試操作

1. ✅ 開啟速度分析模組
2. ⏳ 等待 5 秒（確保完全載入）
3. ❌ 關閉速度分析模組
4. ⏳ 等待 5 秒（確保完全清理）
5. 🔍 執行 objgraph 快照

### 步驟 4：檢查日誌

```powershell
# 搜尋新版清理輸出
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "階段 7|已清理.*個屬性|Qt 連接已斷開|已從連動管理器解除註冊" | Select-Object -Last 20

# 檢查 GC 回收結果
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "已執行垃圾回收" | Select-Object -Last 5

# 檢查最終 __dict__ 狀態
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "剩餘.*個屬性" | Select-Object -Last 5
```

---

## 🔍 預期輸出

### ✅ 成功的輸出

#### SpeedChartWidget 清理
```
[SPEED_CHART] 🧹 開始清理資源...
[SPEED_CHART]   ✅ 已從連動管理器解除註冊
[SPEED_CHART]   ✅ Matplotlib 圖表已清理
[SPEED_CHART]   ✅ Canvas 已清理
[SPEED_CHART]   ✅ QTableWidget 已完全清理（包含所有 Items）
[SPEED_CHART]   ✅ Signal Receiver 已清理
[SPEED_CHART]   ✅ 數據引用已清空
[SPEED_CHART]   ✅ SpeedChartWidget 已清理
[SPEED_CHART]   ✅ 資料載入器引用已清空
[SPEED_CHART]   ✅ Qt 連接已斷開
[SPEED_CHART]   ✅ __dict__ 已清理（50+ 個屬性）  ← 新增！
[SPEED_CHART] ✅ 資源清理完成
```

#### SpeedAnalysisModule 清理
```
[SPEED_MDI] 🧹 階段 7: 清理模組 __dict__...  ← 新增！
[SPEED_MDI] 🔍 __dict__ 共有 20+ 個屬性
[SPEED_MDI] ✅ 已清理 15+ 個屬性
[SPEED_MDI] 🔍 剩餘 3 個屬性: ['_module_id', '_module_name', '_version']
[SPEED_MDI] ✅ 速度分析模組資源清理完成
```

#### GC 回收
```
[SPEED_MDI] ✅ 已執行垃圾回收（回收 5+ 個物件）  ← 不再是 0！
```

---

## 📊 成功標準

### Objgraph 報告檢查

在最新的 objgraph 報告中：

❌ **修復前**：
```
SpeedAnalysisModule    +1  ← 洩漏
SpeedChartWidget       +1  ← 洩漏
```

✅ **修復後**：
```
（這兩個類型應該完全消失）
```

### 記憶體變化

| 項目 | 修復前 | 修復後（預期） |
|------|--------|---------------|
| 開啟增加物件 | +888 | +600~ |
| 關閉減少物件 | -306 | -600~ |
| 洩漏物件 | +582 | 0 ✅ |
| GC 回收 | 0 | 5+ ✅ |

---

## 🎯 三種可能結果

### 場景 A：完全成功 🎉

```
✅ objgraph 不再顯示 SpeedAnalysisModule
✅ objgraph 不再顯示 SpeedChartWidget
✅ GC 回收 > 0 個物件
✅ 開啟/關閉物件數平衡
```

**結論**：問題完全解決！可以應用到其他 8 個 Lap Analysis 模組。

---

### 場景 B：部分改善 ⚠️

```
✅ SpeedChartWidget 消失
❌ SpeedAnalysisModule 仍然 +1
🔄 GC 回收 1-2 個物件（部分改善）
```

**下一步診斷**：
1. 檢查 MDI 子視窗管理器是否持有模組引用
2. 檢查是否有全域字典持有模組
3. 使用 `gc.get_referrers()` 追蹤 SpeedAnalysisModule 的剩餘引用

---

### 場景 C：沒有改善 ❌

```
❌ 兩個組件仍然洩漏
❌ GC 仍回收 0 個物件
```

**可能原因**：
1. Python 緩存沒有清理乾淨 → 重新清理並重啟
2. 有其他強引用未發現 → 需要更深入的 gc.get_referrers() 追蹤
3. Qt 內部機制持有引用 → 可能需要調整 deleteLater() 的時機

---

## 📝 測試檢查清單

測試後請確認：

- [ ] 新增的清理步驟是否執行？
  - [ ] 「已從連動管理器解除註冊」
  - [ ] 「Qt 連接已斷開」
  - [ ] 「__dict__ 已清理」
  - [ ] 「階段 7: 清理模組 __dict__」

- [ ] GC 回收物件數是否 > 0？

- [ ] objgraph 報告中是否還有這兩個組件？

- [ ] 開啟/關閉後物件總數是否平衡？

---

## 🔧 故障排除

### 如果看不到新輸出

```powershell
# 1. 檢查是否使用了舊的 pyc 檔案
Get-ChildItem -Path "modules\gui\lap_analysis\speed_analysis\__pycache__" -Filter "*.pyc" | Select-Object Name, LastWriteTime

# 2. 強制刪除緩存
Remove-Item -Path "modules\gui\lap_analysis\speed_analysis\__pycache__" -Recurse -Force

# 3. 確認程式碼是否正確修改
Select-String -Path "modules\gui\lap_analysis\speed_analysis\speed_analysis_chart_widget.py" -Pattern "階段 7|Qt 連接已斷開"

# 4. 確認 GUI 已完全關閉
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 📞 測試後提供資訊

請提供以下資訊：

1. **新版清理輸出**
   ```powershell
   Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "階段 7|__dict__ 已清理|Qt 連接已斷開" | Select-Object -Last 10
   ```

2. **GC 回收結果**
   ```powershell
   Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "已執行垃圾回收" | Select-Object -Last 3
   ```

3. **Objgraph 報告檔名**
   ```powershell
   Get-ChildItem -Path "." -Filter "objgraph_report_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Select-Object Name, LastWriteTime
   ```

4. **是否看到這兩個組件**
   ```powershell
   Select-String -Path "objgraph_report_*.txt" -Pattern "SpeedAnalysisModule|SpeedChartWidget" | Select-Object -Last 5
   ```

---

**文檔版本**：v3.4
**創建時間**：2025-10-15 20:20
**狀態**：等待測試結果
**預期**：完全解決記憶體洩漏問題
