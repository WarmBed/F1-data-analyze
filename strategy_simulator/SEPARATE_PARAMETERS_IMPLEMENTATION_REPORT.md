# 比賽策略模擬器 - 分離參數系統實現報告

## 📅 更新日期：2026-01-05

---

## 🎯 實現內容總結

### ✅ 1. **分離參數系統**

為解決「單車手策略比較」和「20車手競爭模擬」使用相同迭代次數的問題，實現了雙參數系統：

#### **UI 變更（input_panel.py）**

##### **新增兩個獨立滑桿：**
```python
# 策略比較迭代次數（單車手模式）
self.strategy_iterations_spin = QSpinBox()
├─ 範圍: 50 - 5000
├─ 預設值: 100
├─ 步進: 50
└─ 提示: "單車手模式：比較不同策略的時間差異（建議 100-500 次）"

# 競爭模擬迭代次數（20車手模式）
self.competitive_iterations_spin = QSpinBox()
├─ 範圍: 100 - 10000
├─ 預設值: 1000
├─ 步進: 100
└─ 提示: "競爭模式：20車手位置統計（建議 1000+ 次以獲得準確的位置機率）"
```

##### **向後兼容性：**
```python
# 保留舊參數指向策略比較
self.mc_iterations_spin = self.strategy_iterations_spin
```

#### **參數傳遞（get_parameters()）**

```python
# 新增兩個獨立參數
'strategy_iterations': self.strategy_iterations_spin.value()      # 策略比較次數
'competitive_iterations': self.competitive_iterations_spin.value() # 競爭模擬次數
'mc_iterations': self.mc_iterations_spin.value()                   # 向後兼容
```

---

### ✅ 2. **智能迭代次數選擇（main_window.py）**

#### **_run_monte_carlo 方法更新**

```python
# 步驟 1: 檢查是否有足夠的 FP2 預測數據
has_competitive_data = False
if hasattr(self, 'fp2_tab'):
    test_predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=False)
    has_competitive_data = len(test_predictions) >= 10

# 步驟 2: 根據模式選擇對應的迭代次數
if has_competitive_data:
    # 競爭模式：使用競爭迭代次數（預設 1000）
    mc_iterations = input_params.get('competitive_iterations', 1000)
    mode_name = "競爭模式 (20車手)"
else:
    # 單車手策略比較：使用策略迭代次數（預設 100）
    mc_iterations = input_params.get('strategy_iterations', 100)
    mode_name = "策略比較模式 (單車手)"

print(f"[MAIN_WINDOW] Iterations: {mc_iterations} ({mode_name})")
```

**邏輯說明：**
- **≥10 位車手數據** → 自動啟用競爭模式 → 使用 1000 次迭代
- **<10 位車手數據** → 單車手模式 → 使用 100 次迭代

---

### ✅ 3. **完整賽事標籤調試增強**

#### **問題診斷**
用戶反映「完整賽事」標籤點擊「執行完整賽事」後沒有數據顯示。

#### **實現的修復**

##### **A) main_window.py - _on_full_race_requested**
添加詳細的調試輸出和錯誤檢查：

```python
def _on_full_race_requested(self, params: dict):
    print(f"[MAIN_WINDOW] ====== FULL RACE SIMULATION REQUESTED ======")
    print(f"[MAIN_WINDOW] Request params: {params}")
    print(f"[MAIN_WINDOW] Has _current_params: {hasattr(self, '_current_params')}")
    print(f"[MAIN_WINDOW] Has _current_results: {hasattr(self, '_current_results')}")
    if hasattr(self, '_current_results'):
        print(f"[MAIN_WINDOW] Current results count: {len(self._current_results)}")
    
    # 檢查必要數據
    if not hasattr(self, '_current_params') or not self._current_params:
        error_msg = "請先配置模擬參數並執行策略優化"
        self.status_bar.showMessage(error_msg)
        if hasattr(self.full_race_tab, 'status_label'):
            self.full_race_tab.status_label.setText(error_msg)
            self.full_race_tab.status_label.setStyleSheet("color: #d32f2f;")
        return
```

##### **B) main_window.py - 模擬完成後**
添加結果數據結構驗證：

```python
# 模擬完成後
print(f"[MAIN_WINDOW] Full race simulation completed, updating results...")
print(f"[MAIN_WINDOW] Single result: {single_result}")
print(f"[MAIN_WINDOW] Statistics keys: {multi_stats.keys() if isinstance(multi_stats, dict) else type(multi_stats)}")

self.full_race_tab.update_simulation_result({
    'single': single_result,
    'statistics': multi_stats
})

print(f"[MAIN_WINDOW] Results updated in full_race_tab")
self.status_bar.showMessage(f"完整賽事模擬完成 ({iterations} 次迭代)")
```

##### **C) full_race_tab.py - update_simulation_result**
增強結果接收的調試輸出：

```python
def update_simulation_result(self, result: Dict[str, Any]):
    print(f"[FULL_RACE_TAB] ====== UPDATE_SIMULATION_RESULT CALLED ======")
    print(f"[FULL_RACE_TAB] Result keys: {result.keys() if result else 'None'}")
    print(f"[FULL_RACE_TAB] Has 'single': {'single' in result if result else False}")
    print(f"[FULL_RACE_TAB] Has 'statistics': {'statistics' in result if result else False}")
    
    self._simulation_result = result.get('single')
    self._statistics = result.get('statistics')
    
    print(f"[FULL_RACE_TAB] _simulation_result type: {type(self._simulation_result)}")
    print(f"[FULL_RACE_TAB] _statistics type: {type(self._statistics)}")
    
    if self._simulation_result:
        print(f"[FULL_RACE_TAB] Updating standings table...")
        self._update_standings_table()
        self._update_position_chart()
    else:
        print(f"[FULL_RACE_TAB] ⚠️ No simulation result to display!")
    
    if self._statistics:
        print(f"[FULL_RACE_TAB] Updating MC statistics...")
        self._update_mc_statistics()
    else:
        print(f"[FULL_RACE_TAB] ⚠️ No statistics to display!")
    
    self.status_label.setText("Simulation complete. Select a driver to highlight.")
    self.status_label.setStyleSheet("color: #2e7d32;")  # Green for success
```

---

## 🔍 問題診斷工作流

### **如何診斷「完整賽事」無數據問題：**

#### **步驟 1: 檢查主畫面是否執行了策略優化**
```
✅ 確認點擊了「執行模擬」按鈕
✅ 確認左側面板顯示了策略結果
✅ 確認 _current_params 和 _current_results 存在
```

#### **步驟 2: 查看終端調試輸出**
運行 GUI 後，切換到「完整賽事」標籤，點擊「執行完整賽事」，觀察輸出：

```
[MAIN_WINDOW] ====== FULL RACE SIMULATION REQUESTED ======
[MAIN_WINDOW] Request params: {'iterations': 100, ...}
[MAIN_WINDOW] Has _current_params: True/False  ← 檢查點 1
[MAIN_WINDOW] Has _current_results: True/False ← 檢查點 2
```

**如果輸出 False:**
- **原因**: 沒有執行主畫面的策略優化
- **解決**: 先執行主畫面的「執行模擬」

#### **步驟 3: 檢查 FP2 數據**
```
[MAIN_WINDOW] FP2 predictions: []  ← 如果是空列表
```

**如果沒有 FP2 數據:**
- **原因**: 沒有載入 FP2→Q 預測數據
- **解決**: 切換到「FP2→Q 預測」標籤，選擇賽事並載入數據

#### **步驟 4: 檢查結果傳遞**
```
[MAIN_WINDOW] Single result: <FullRaceSimulation object>  ← 應該有物件
[MAIN_WINDOW] Statistics keys: dict_keys([...])           ← 應該有字典鍵

[FULL_RACE_TAB] ====== UPDATE_SIMULATION_RESULT CALLED ======
[FULL_RACE_TAB] Has 'single': True   ← 應該是 True
[FULL_RACE_TAB] Has 'statistics': True ← 應該是 True
```

**如果 'single' 是 None:**
- **原因**: `simulator.simulate_race()` 返回 None
- **可能**: FullRaceSimulator 初始化失敗

**如果 'statistics' 是 None:**
- **原因**: `simulator.run_multiple_simulations()` 返回 None
- **可能**: 迭代次數過低或模擬崩潰

---

## 📊 UI 變更總結

### **左側面板（輸入參數）**

#### **蒙地卡羅設定區塊：**
```
┌─────────────────────────────────────┐
│  ☑ 啟用蒙地卡羅                      │
│                                     │
│  策略比較次數:  [  100  ] (50-5000) │
│  提示: 單車手模式比較不同策略       │
│                                     │
│  競爭模擬次數:  [ 1000  ] (100-10000)│
│  提示: 20車手位置統計（建議1000+）   │
│                                     │
│  SC 機率:       [ 1.5   ] %/圈      │
│  VSC 機率:      [ 2.0   ] %/圈      │
└─────────────────────────────────────┘
```

### **完整賽事標籤（右側）**

#### **狀態顯示改善：**
```
┌─────────────────────────────────────┐
│  🏁 完整賽事模擬                     │
│                                     │
│  選擇策略: [Plan A: S-S-M (45%)]   │
│  SC 場景:  [Random ▼]               │
│  迭代次數: [100]                    │
│                                     │
│  [執行完整賽事]                     │
│                                     │
│  狀態: ✅ 模擬完成 (100 次迭代)     │ ← 成功時綠色
│  狀態: ❌ 請先執行策略優化          │ ← 錯誤時紅色
└─────────────────────────────────────┘
```

---

## 🧪 測試建議

### **測試案例 1: 單車手策略比較**
```
1. 不載入 FP2→Q 數據（或只有 <10 位車手）
2. 執行主畫面策略優化
3. 觀察終端輸出：
   ✅ "Iterations: 100 (策略比較模式 (單車手))"
4. 檢查結果顯示正常
```

### **測試案例 2: 20車手競爭**
```
1. 載入完整 FP2→Q 數據（≥10 位車手）
2. 執行主畫面策略優化
3. 觀察終端輸出：
   ✅ "Iterations: 1000 (競爭模式 (20車手))"
4. 檢查位置統計精確度
```

### **測試案例 3: 完整賽事診斷**
```
1. 啟動 GUI
2. 直接切換到「完整賽事」標籤
3. 點擊「執行完整賽事」
4. 觀察終端輸出：
   ❌ "Has _current_params: False"
   ✅ 狀態標籤顯示: "請先配置模擬參數並執行策略優化"
5. 執行主畫面策略優化後再試
6. 觀察終端輸出：
   ✅ "Has _current_params: True"
   ✅ "FULL_RACE_TAB] Updating standings table..."
```

---

## 🔧 開發者注意事項

### **1. 參數向後兼容**
- `mc_iterations` 仍然存在，預設指向 `strategy_iterations`
- 舊代碼調用 `mc_iterations` 不會報錯

### **2. 迭代次數選擇邏輯**
- 自動判斷基於 FP2 數據量（≥10 位 = 競爭模式）
- 可通過參數字典明確指定：
  ```python
  params = {
      'strategy_iterations': 200,     # 策略比較用
      'competitive_iterations': 2000  # 競爭模擬用
  }
  ```

### **3. 調試輸出規範**
所有關鍵步驟都有 print 輸出：
- `[MAIN_WINDOW]` - 主窗口邏輯
- `[FULL_RACE_TAB]` - 完整賽事標籤
- `[INPUT_PANEL]` - 輸入參數面板

---

## 📝 未來改進建議

### **1. UI 改進**
- [ ] 添加「預估運算時間」顯示（基於迭代次數）
- [ ] 添加「暫停/繼續」功能（長時間模擬）
- [ ] 添加「進度百分比」顯示（替代簡單進度條）

### **2. 性能優化**
- [ ] 多執行緒並行模擬（減少 1000 次迭代的等待時間）
- [ ] 緩存中間結果（相同參數不重複計算）
- [ ] GPU 加速（對於超大規模模擬）

### **3. 數據分析**
- [ ] 導出 CSV 報告（包含所有迭代的詳細結果）
- [ ] 統計圖表（位置分佈直方圖、勝率趨勢圖）
- [ ] 敏感度分析（迭代次數 vs 結果穩定性）

---

## ✅ 檢查清單

- [x] ✅ 實現雙參數系統（strategy_iterations + competitive_iterations）
- [x] ✅ UI 添加兩個獨立滑桿
- [x] ✅ 智能選擇迭代次數（基於 FP2 數據量）
- [x] ✅ 完整賽事標籤添加詳細調試輸出
- [x] ✅ 錯誤處理改善（紅色/綠色狀態顯示）
- [x] ✅ 向後兼容舊代碼
- [ ] ⏳ 測試所有場景（等待用戶反饋）
- [ ] ⏳ 確認完整賽事數據顯示正常

---

## 📞 如何使用

### **啟動 GUI 並測試：**
```powershell
# 啟動 GUI
python f1t_gui_main.py

# 觀察終端輸出以診斷問題
```

### **查看日誌輸出：**
所有 `print()` 輸出會自動導出到 `log` 目錄（如果配置了 logger）。

---

## 🎉 完成狀態

**主要目標：**
1. ✅ **分離參數系統** - 完成實現
2. ✅ **智能迭代次數選擇** - 完成實現
3. ✅ **完整賽事調試增強** - 完成實現

**待驗證：**
- 用戶測試確認「完整賽事」數據顯示正常
- 確認 1000 次迭代的競爭模擬結果精確度符合預期

---

**報告生成時間**: 2026-01-05  
**實現者**: GitHub Copilot  
**使用者**: F1T 開發團隊
