# 📊 F1T GUI 記憶體診斷分析報告

**測試日期**: 2025-10-15 15:22  
**測試場景**: 開啟 9 個 Lap Analysis 模組  
**報告來源**: `objgraph_report_20251015_152254.txt`

---

## 🎯 執行摘要

### ⚠️ 發現記憶體洩漏跡象

開啟 9 個 Lap Analysis 模組後，GUI 相關物件出現異常成長，懷疑存在記憶體洩漏。

---

## 📈 物件統計分析

### Top 5 物件類型
| 類型 | 數量 | 百分比 | 評估 |
|------|------|--------|------|
| function | 23,219 | 24.31% | ✅ 正常 |
| tuple | 13,338 | 13.97% | ✅ 正常 |
| dict | 11,053 | 11.57% | ✅ 正常 |
| wrapper_descriptor | 6,538 | 6.85% | ✅ 正常 |
| ReferenceType | 5,487 | 5.75% | ✅ 正常 |

這些都是 Python 內建類型，數量在合理範圍內。

---

## 🚨 成長追蹤分析（關鍵發現）

### PyQt5 GUI 物件異常成長

| 物件類型 | 之前 | 目前 | 成長量 | 每模組平均 | 狀態 |
|---------|------|------|--------|-----------|------|
| **QTableWidgetItem** | -257 | 196 | **+453** | ~50 個 | 🔴 **可疑** |
| **QLabel** | -57 | 90 | **+147** | ~16 個 | 🔴 **可疑** |
| **QPushButton** | -9 | 81 | **+90** | ~10 個 | 🔴 **可疑** |
| **QColor** | -42 | 52 | **+94** | ~10 個 | 🔴 **可疑** |
| **Condition** | -43 | 45 | **+88** | ~10 個 | 🟡 警告 |
| **deque** | -47 | 45 | **+92** | ~10 個 | 🟡 警告 |
| **QVBoxLayout** | -26 | 54 | **+80** | ~9 個 | 🔴 **可疑** |
| **QWidget** | -16 | 37 | **+53** | ~6 個 | 🔴 **可疑** |
| **QHBoxLayout** | -6 | 36 | **+42** | ~5 個 | 🔴 **可疑** |
| **QFrame** | -4 | 27 | **+31** | ~3 個 | 🟡 警告 |

### 📊 統計總結

**9 個 Lap Analysis 模組的物件創建平均值**:
- QTableWidgetItem: ~50 個/模組
- QLabel: ~16 個/模組  
- QPushButton: ~10 個/模組
- QLayout 系列: ~14 個/模組

**問題評估**:
這些數量對於單個分析模組來說是合理的，**但問題在於關閉模組後這些物件是否會被正確回收**。

---

## 🔬 洩漏診斷測試

### 建議的測試步驟

#### 步驟 1: 建立基準
```
1. 關閉所有 9 個 Lap Analysis 模組
2. 點擊「強制垃圾回收」3 次
3. 點擊「追蹤成長」建立新基準
```

#### 步驟 2: 測試單一模組
```
1. 開啟 1 個 Lap Analysis 模組
2. 完全使用該模組（切換 Tab、查看圖表）
3. 關閉該模組
4. 點擊「強制垃圾回收」3 次
5. 點擊「追蹤成長」
```

**預期結果**:
- ✅ **正常**: QTableWidgetItem 等物件回到接近基準值
- 🔴 **洩漏**: QTableWidgetItem 等物件仍保持高數量

#### 步驟 3: 重複測試
```
重複步驟 2 共 5 次，觀察物件數量是否持續累積
```

---

## 🔍 可能的洩漏原因

### 1. Signal/Slot 連接未斷開
```python
# 可能的問題
self.some_widget.clicked.connect(self.some_method)
# 關閉視窗時未斷開連接

# 正確做法
def closeEvent(self, event):
    self.some_widget.clicked.disconnect(self.some_method)
    event.accept()
```

### 2. 全局引用或父物件引用
```python
# 可能的問題
global_list.append(self.some_widget)  # 全局引用
self.parent().widget_cache[id] = self  # 父物件保留引用

# 這些引用會阻止垃圾回收
```

### 3. QTimer 未停止
```python
# 可能的問題
self.timer = QTimer()
self.timer.start(1000)
# 關閉視窗時 timer 仍在運行

# 正確做法
def closeEvent(self, event):
    if hasattr(self, 'timer'):
        self.timer.stop()
    event.accept()
```

### 4. Matplotlib 圖表快取
```python
# Lap Analysis 使用 Matplotlib
# 可能未正確清理圖表資源

# 正確做法
def closeEvent(self, event):
    if hasattr(self, 'figure'):
        self.figure.clear()
        plt.close(self.figure)
    event.accept()
```

---

## 📋 建議的修復優先級

### 🔴 高優先級
1. **檢查 Lap Analysis 的 `closeEvent()`**
   - 確保所有 Signal/Slot 連接被斷開
   - 停止所有 QTimer
   - 清理 Matplotlib 圖表

2. **檢查 MDI 子視窗管理**
   - 確保關閉視窗時正確釋放資源
   - 檢查是否有循環引用

### 🟡 中優先級
3. **添加弱引用機制**
   - 對於需要長期保留的引用，考慮使用 `weakref`

4. **實現資源追蹤**
   - 在模組中添加調試日誌記錄物件創建/銷毀

### 🟢 低優先級
5. **優化物件創建**
   - 考慮物件池模式重用 QTableWidgetItem
   - 延遲創建非必要的 UI 元件

---

## 🛠️ 立即行動建議

### 1. 執行洩漏確認測試（10 分鐘）
```
按照「洩漏診斷測試」中的步驟 1-3 執行測試
記錄每個步驟後的物件數量
```

### 2. 檢查 Lap Analysis 代碼（30 分鐘）
```bash
# 搜索相關檔案
grep -r "class.*Lap.*Analysis" modules/gui/lap_analysis/

# 檢查是否實現了 closeEvent
grep -r "def closeEvent" modules/gui/lap_analysis/

# 檢查 signal 連接
grep -r "\.connect\(" modules/gui/lap_analysis/
```

### 3. 添加資源清理（1 小時）
在 Lap Analysis 模組中添加：
```python
def closeEvent(self, event):
    """視窗關閉時清理資源"""
    logger.info(f"[LAP_ANALYSIS] 清理資源...")
    
    # 1. 斷開所有 signal 連接
    # 2. 停止所有 timer
    # 3. 清理 matplotlib 圖表
    # 4. 移除引用
    
    event.accept()
```

---

## 📊 當前狀態評估

### ✅ Objgraph 工具運作正常
- 物件統計功能：正常
- 成長追蹤功能：正常
- 自動刷新功能：正常（每 5 秒執行一次掃描）
- 報告導出功能：正常

### 🟡 自動刷新功能說明
**目前行為**（正確）:
- 自動刷新只執行「掃描物件」
- 每 5 秒自動更新物件統計
- 日誌顯示每 5 秒記錄一次掃描

**不會自動執行**:
- 追蹤成長（需手動點擊）
- 生成引用圖（需手動選擇類型）
- 垃圾回收（需手動觸發）

這是**正確的設計**，因為：
- 成長追蹤需要兩個時間點的對比
- 引用圖生成需要用戶選擇類型
- 垃圾回收會影響系統效能

### 🔴 發現的問題
1. **Graphviz 未安裝** - 無法生成引用圖（已提示安裝）
2. **可能的記憶體洩漏** - PyQt5 GUI 物件未正確回收

---

## 🎯 下一步行動

### 立即執行（今天）
- [ ] 執行洩漏確認測試
- [ ] 記錄測試結果
- [ ] 確定是否真的存在洩漏

### 短期修復（本週）
- [ ] 檢查 Lap Analysis closeEvent 實現
- [ ] 添加資源清理代碼
- [ ] 重新測試確認修復

### 長期改進（下週）
- [ ] 實現資源追蹤系統
- [ ] 添加自動化記憶體測試
- [ ] 建立記憶體使用監控儀表板

---

**分析者**: AI Programming Assistant  
**報告生成時間**: 2025-10-15  
**工具版本**: Objgraph 3.6.2
