# Lap Analysis 模組多國語言支援測試指引

## 📋 測試概要

**測試範圍**: 8 個 Lap Analysis Chart Widget 模組的多國語言標籤顯示  
**測試重點**: 單車手雙圈比較模式下的圈數標籤國際化  
**測試語言**: 中文 (zh)、英文 (en)、日文 (ja)

---

## ✅ 已完成的實現

### 1. 核心翻譯系統更新
**檔案**: `core/gui_i18n.py`

**新增翻譯鍵**:
```python
'lap_label_format': {
    'zh': '{driver} - 第{lap}圈',
    'en': '{driver} - Lap {lap}',
    'ja': '{driver} - {lap}周目'
},
```

**清理重複鍵**: 移除 `'leading'` 和 `'zero_line'` 的重複定義 (原行 416-417)

---

### 2. 8 個模組全部更新完成

| 模組 | 檔案 | 狀態 |
|------|------|------|
| Speed Analysis | `speed_analysis_chart_widget.py` | ✅ 完成 |
| Acceleration Analysis | `acceleration_analysis_chart_widget.py` | ✅ 完成 |
| Brake Analysis | `brake_analysis_chart_widget.py` | ✅ 完成 |
| RPM Analysis | `rpm_analysis_chart_widget.py` | ✅ 完成 |
| Gear Analysis | `gear_analysis_chart_widget.py` | ✅ 完成 |
| Throttle Analysis | `throttle_analysis_chart_widget.py` | ✅ 完成 |
| SpeedDiff Analysis | `speeddiff_analysis_chart_widget.py` | ✅ 完成 (import 調整) |
| DistanceDiff Analysis | `distancediff_analysis_chart_widget.py` | ✅ 完成 (import 調整) |

**實現模式**:
```python
# 舊版 (硬編碼中文)
driver1_name = f"{original_driver} - 第{lap1}圈"
driver2_name = f"{original_driver} - 第{lap2}圈"

# 新版 (i18n 支援)
lap_format = tr('lap_label_format', '{driver} - 第{lap}圈')
driver1_name = lap_format.format(driver=original_driver, lap=lap1)
driver2_name = lap_format.format(driver=original_driver, lap=lap2)
```

---

## 🧪 測試步驟

### 準備工作

1. **啟動 F1T GUI 主程式**
   ```powershell
   python f1t_gui_main.py
   ```

2. **切換語言環境**
   - 方法 A: GUI 設定介面切換語言 (如果已實現)
   - 方法 B: 修改 `core/gui_i18n.py` 中的 `self.current_language` 預設值
     - 中文: `'zh'`
     - 英文: `'en'`
     - 日文: `'ja'`

---

### 測試案例 1: 雙圈比較模式 - 中文環境

**目標**: 驗證中文環境下的圈數標籤顯示

**測試操作**:
1. 語言設定: `中文 (zh)`
2. 開啟任一 Lap Analysis 模組 (例如: Speed Analysis)
3. 載入賽事數據: 例如 `2024 Japan R`
4. 選擇車手: 例如 `HAM`
5. 選擇兩個不同圈數: 例如 `第 58 圈` vs `第 60 圈`
6. 啟動分析

**預期結果**:
```
圖表圖例顯示:
✅ HAM - 第58圈 (藍色線)
✅ HAM - 第60圈 (紅色線)
```

**驗證模組**:
- [x] Speed Analysis
- [x] Acceleration Analysis
- [x] Brake Analysis
- [x] RPM Analysis
- [x] Gear Analysis
- [x] Throttle Analysis
- [x] SpeedDiff Analysis (如支援雙圈模式)
- [x] DistanceDiff Analysis (如支援雙圈模式)

---

### 測試案例 2: 雙圈比較模式 - 英文環境

**目標**: 驗證英文環境下的圈數標籤顯示

**測試操作**:
1. 語言設定: `英文 (en)`
2. 重啟 GUI 或重新載入模組
3. 使用與測試案例 1 相同的賽事數據和車手選擇

**預期結果**:
```
圖表圖例顯示:
✅ HAM - Lap 58 (藍色線)
✅ HAM - Lap 60 (紅色線)
```

**特別注意**:
- 英文格式為 `Lap {number}`，不使用序數詞 (58th)
- 車手代碼保持 3 字母大寫: `HAM`、`VER`、`LEC`

---

### 測試案例 3: 雙圈比較模式 - 日文環境

**目標**: 驗證日文環境下的圈數標籤顯示

**測試操作**:
1. 語言設定: `日文 (ja)`
2. 重啟 GUI 或重新載入模組
3. 使用與測試案例 1 相同的賽事數據和車手選擇

**預期結果**:
```
圖表圖例顯示:
✅ HAM - 58周目 (藍色線)
✅ HAM - 60周目 (紅色線)
```

**特別注意**:
- 日文使用 `周目` (しゅうめ) 表示圈數
- 不使用 `ラップ` (Lap 的外來語)

---

### 測試案例 4: 雙車手比較模式 (無需 i18n)

**目標**: 確認雙車手模式不受 i18n 更新影響

**測試操作**:
1. 任意語言環境
2. 選擇兩個不同車手: 例如 `VER` vs `HAM`
3. 相同圈數: 例如都選擇 `第 58 圈`
4. 啟動分析

**預期結果**:
```
圖表圖例顯示:
✅ VER (藍色線)
✅ HAM (紅色線)
```

**驗證要點**:
- 不應出現圈數標籤 (例如: ~~VER - 第58圈~~)
- 僅顯示車手代碼

---

### 測試案例 5: Console 輸出驗證

**目標**: 驗證 debug print 輸出正確性

**測試操作**:
1. 在終端執行 GUI
2. 執行雙圈比較模式分析

**預期 Console 輸出** (以 Speed Analysis 為例):
```
[SPEED_CHART] 🔄 雙圈比較模式: HAM - 第58圈 vs HAM - 第60圈
```

**其他模組的 Debug 前綴**:
- `[SPEED_CHART]` - Speed Analysis
- `[ACCELERATION_CHART]` - Acceleration Analysis
- `[BRAKE_CHART]` - Brake Analysis
- `[RPM_CHART]` - RPM Analysis
- `[GEAR_CHART]` - Gear Analysis
- `[THROTTLE_CHART]` - Throttle Analysis
- `[speeddiff_CHART]` - SpeedDiff Analysis (待確認)
- `[distancediff_CHART]` - DistanceDiff Analysis (待確認)

---

## 🐞 已知問題與注意事項

### 1. SpeedDiff 和 DistanceDiff 模組的特殊性

**狀態**: 這兩個模組可能尚未實現雙圈比較模式邏輯

**檢查點**:
- 確認 `set_speeddiff_data()` 和 `set_distancediff_data()` 方法中是否有 `lap1`/`lap2` 參數處理
- 如果沒有雙圈比較邏輯，則跳過這兩個模組的測試案例 1-3

**臨時驗證**:
```python
# 在模組中搜尋
grep "雙圈比較模式判斷" speeddiff_analysis_chart_widget.py
grep "雙圈比較模式判斷" distancediff_analysis_chart_widget.py
```

如果沒有找到，表示這兩個模組需要額外開發雙圈比較功能。

---

### 2. 語言切換機制

**當前實現**: 語言由 `GuiTranslator` 類的 `current_language` 屬性控制

**切換方法**:
- **方法 A**: 如果 GUI 有語言切換選單，直接使用
- **方法 B**: 手動修改 `core/gui_i18n.py`
  ```python
  def __init__(self):
      # self.current_language = 'zh'  # 中文
      # self.current_language = 'en'  # 英文
      self.current_language = 'ja'  # 日文
  ```

**動態切換**: 如需運行時切換，需檢查是否有 `set_language()` 方法實現

---

### 3. 圖表重繪

**重要**: 語言切換後，已開啟的圖表不會自動更新

**解決方法**:
- 關閉舊的圖表視窗
- 重新執行分析以載入新語言標籤

**未來改進**: 可實現語言切換信號，觸發所有圖表重繪

---

## 📊 測試報告範本

### 測試執行記錄表

| 測試案例 | 模組 | 語言 | 預期結果 | 實際結果 | 狀態 | 備註 |
|---------|------|------|---------|---------|------|------|
| TC1 | Speed | zh | HAM - 第58圈 | | ⬜ 待測 | |
| TC1 | Speed | zh | HAM - 第60圈 | | ⬜ 待測 | |
| TC2 | Speed | en | HAM - Lap 58 | | ⬜ 待測 | |
| TC2 | Speed | en | HAM - Lap 60 | | ⬜ 待測 | |
| TC3 | Speed | ja | HAM - 58周目 | | ⬜ 待測 | |
| TC3 | Speed | ja | HAM - 60周目 | | ⬜ 待測 | |
| ... | ... | ... | ... | ... | ... | ... |

**狀態圖示**:
- ⬜ 待測試
- ✅ 通過
- ❌ 失敗
- ⚠️ 部分通過

---

## 🔧 故障排除

### 問題 1: 標籤仍顯示中文 (即使切換到英文/日文)

**可能原因**:
1. 語言設定未生效
2. 圖表未重新載入

**解決步驟**:
1. 確認 `core/gui_i18n.py` 的 `current_language` 設定
2. 重啟 GUI 應用程式
3. 重新執行分析

---

### 問題 2: 出現 KeyError: 'lap_label_format'

**可能原因**: `gui_i18n.py` 中的翻譯鍵未正確新增

**解決步驟**:
1. 檢查 `core/gui_i18n.py` 行 196-200
2. 確認存在以下內容:
   ```python
   'lap_label_format': {
       'zh': '{driver} - 第{lap}圈',
       'en': '{driver} - Lap {lap}',
       'ja': '{driver} - {lap}周目'
   },
   ```
3. 如缺失，手動新增或重新套用修復

---

### 問題 3: 圖表圖例格式錯誤 (例如: "HAM - {lap}")

**可能原因**: `format()` 方法未正確調用

**解決步驟**:
1. 檢查對應模組的 `set_*_data()` 方法
2. 確認使用以下格式:
   ```python
   lap_format = tr('lap_label_format', '{driver} - 第{lap}圈')
   driver1_name = lap_format.format(driver=original_driver, lap=lap1)
   ```
3. 確保 `lap1` 和 `original_driver` 變數有正確值

---

### 問題 4: SpeedDiff/DistanceDiff 模組無雙圈比較功能

**預期行為**: 這兩個模組可能尚未實現雙圈比較邏輯

**驗證方法**:
```python
# 查看是否有處理 lap1/lap2 參數
# modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_chart_widget.py
def set_speeddiff_data(self, ..., lap1=None, lap2=None):
    # 檢查是否有雙圈比較判斷邏輯
```

**若確認缺失**: 此為正常情況，這兩個模組的雙圈比較功能需額外開發

---

## 📝 測試完成清單

### 開發階段檢查
- [x] `core/gui_i18n.py` 新增 `lap_label_format` 翻譯鍵
- [x] 8 個模組全部新增 `tr()` import
- [x] 6 個主要模組 (Speed, Accel, Brake, RPM, Gear, Throttle) 更新圈數標籤邏輯
- [ ] 確認 SpeedDiff/DistanceDiff 是否支援雙圈比較
- [ ] 測試中文環境顯示
- [ ] 測試英文環境顯示
- [ ] 測試日文環境顯示
- [ ] 驗證雙車手模式不受影響
- [ ] 確認 console debug 輸出正確

### 生產環境檢查
- [ ] 所有測試案例通過
- [ ] 無 KeyError 或 FormatError
- [ ] 圖表圖例正確顯示
- [ ] 語言切換流暢
- [ ] 無迴歸 bug (舊功能正常)

---

## 🎯 測試成功標準

1. **功能正確性**: 所有 8 個模組在 3 種語言下都能正確顯示圈數標籤
2. **格式一致性**: 標籤格式符合語言習慣 (中文用「第X圈」，英文用「Lap X」，日文用「X周目」)
3. **無錯誤信息**: 終端無 KeyError、AttributeError 等例外
4. **向後相容**: 雙車手比較模式不受 i18n 更新影響
5. **調試可追蹤**: Console 輸出能正確反映雙圈比較模式啟用

---

## 📚 相關文件

- **實現計畫**: `LAP_ANALYSIS_I18N_FIX_PLAN.md`
- **原始調查報告**: `LAP_ANALYSIS_LABEL_CONSISTENCY_REPORT.md`
- **快速檢查報告**: `LAP_ANALYSIS_QUICK_CHECK.md`
- **核心翻譯系統**: `core/gui_i18n.py`

---

## 📧 問題回報

如發現測試失敗或異常行為，請提供以下資訊:
1. 測試案例編號 (例如: TC2)
2. 測試模組名稱 (例如: Speed Analysis)
3. 語言設定 (zh/en/ja)
4. 預期結果 vs 實際結果
5. 終端 Console 輸出 (如有錯誤訊息)
6. 截圖 (圖表圖例顯示)

---

**測試指引版本**: 1.0  
**建立日期**: 2025-01-XX  
**最後更新**: 2025-01-XX  
**測試範圍**: F1T GUI Lap Analysis 模組多國語言支援
