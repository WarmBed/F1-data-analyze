# Throttle Line Chart EXE 打包失效問題修復指南

## 🐛 問題診斷

### 症狀
- 在 Python 環境下運行正常
- 打包成 EXE 後 Throttle Line Chart 功能失效
- 可能的錯誤訊息：`ModuleNotFoundError` 或 `ImportError`

### 根本原因
**PyInstaller 無法自動偵測動態導入的模組**

在 `f1t_gui_main.py` 中，Throttle Line Chart 使用了**動態導入**：

```python
# 這種導入方式在函數內部，PyInstaller 無法自動偵測
def _on_throttle_line_chart_triggered(self):
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import (
        ThrottleLineChartModule,
    )
    # ...
```

PyInstaller 只能自動偵測**頂層導入**（在檔案最上方的 `import` 語句）。

---

## ✅ 解決方案

### 方案 1：修改 F1T_GUI.spec（推薦）

已在 `F1T_GUI.spec` 中添加所有動態導入模組到 `hiddenimports`：

```python
hiddenimports=[
    # Throttle Analysis 模組（動態導入）
    'modules.gui.Throttle_analysis.throttle_analysis_options_dialog',
    'modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module',
    'modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi',
    'modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_data_loader',
    'modules.gui.Throttle_analysis.throttle_line_chart_analysis.signal_bus',
    'modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_module',
    
    # Detailed Lap Analysis 模組（動態導入）
    'modules.gui.driver_race.detailed_lap_analysis.detailed_lap_options_dialog',
    'modules.gui.driver_race.detailed_lap_analysis.detailed_lap_analysis_module',
    'modules.gui.driver_race.detailed_lap_analysis.detailed_lap_analysis_mdi',
    'modules.gui.driver_race.detailed_lap_analysis.detailed_lap_data_loader',
    'modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_mdi',
    
    # Lap Analysis Chart Widgets（動態導入）
    'modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget',
    'modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_chart_widget',
    'modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi',
    'modules.gui.lap_analysis.rpm_analysis.rpm_analysis_chart_widget',
    'modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi',
    'modules.gui.lap_analysis.gear_analysis.gear_analysis_chart_widget',
    'modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi',
    'modules.gui.lap_analysis.brake_analysis.brake_analysis_chart_widget',
    'modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi',
    'modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_chart_widget',
    'modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi',
    
    # 其他分析模組（動態導入）
    'modules.gui.lap_analysis.lap_time_analysis_module',
    'modules.gui.speed_analysis.speed_analysis_module',
    'modules.gui.pitstop_analysis.pitstop_analysis_mdi',
    'modules.gui.accident_analysis.accident_analysis_mdi',
    'modules.gui.telemetry_analysis_mdi',
    'modules.gui.rain_analysis.rain_analysis_module',
    'modules.gui.rain_analysis.rain_analysis_mdi',
    'modules.gui.rain_analysis.rain_analysis_data_loader',
    'modules.gui.tire_analysis.tire_analysis_module',
    'modules.gui.tire_analysis.tire_analysis_mdi',
    'modules.gui.track_analysis',
    
    # Module Factory 和 Interfaces
    'modules.gui.interfaces.analysis_module',
    
    # Universal Chart Widget 和 Base 模組
    'modules.gui.universal_chart_widget',
    'modules.gui.throttle_duration_chart_widget',
    'modules.gui.lap_time_chart_widget',
    'modules.gui.base.universal_data_loader_base',
    'modules.gui.base.universal_analysis_mdi',
    
    # Core 模組
    'core.gui_i18n',
    'core.gui_settings_manager',
],
```

---

## 🔧 重新打包步驟

### 1. 清理舊檔案
```powershell
# 刪除舊的 build 和 dist 目錄
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue

# 刪除舊的 .spec 緩存
Remove-Item -Path "*.spec~" -Force -ErrorAction SilentlyContinue
```

### 2. 使用更新後的 .spec 打包
```powershell
pyinstaller F1T_GUI.spec
```

### 3. 驗證打包結果
```powershell
# 執行 EXE
.\dist\F1T_GUI.exe

# 測試步驟：
# 1. 開啟主程式
# 2. 點擊選單：Throttle Analysis > Throttle Line Chart
# 3. 選擇 Year/Race/Session
# 4. 選擇 Driver 1
# 5. 確認圖表顯示正常
```

---

## 🧪 測試檢查清單

### 在 Python 環境測試
- [ ] `python f1t_gui_main.py` 可正常執行
- [ ] Throttle Line Chart 功能正常
- [ ] Throttle Box Plot 功能正常
- [ ] Detailed Lap Analysis 功能正常

### 在 EXE 環境測試
- [ ] EXE 可正常啟動
- [ ] Throttle Line Chart 選單項目可見
- [ ] 點擊 Throttle Line Chart 不會報錯
- [ ] Throttle Line Chart 視窗可正常開啟
- [ ] 可正常選擇 Driver 1 和 Driver 2
- [ ] 圖表可正常顯示和互動
- [ ] Tooltip 拖動功能正常

---

## 🚨 常見問題排查

### 問題 1：EXE 啟動時黑視窗一閃而過
**原因**：Python 程式錯誤導致 EXE 立即退出

**解決方案**：
1. 使用 CMD 執行 EXE 查看錯誤訊息：
   ```cmd
   cd dist
   F1T_GUI.exe
   ```
2. 或暫時將 `.spec` 中的 `console=False` 改為 `console=True` 重新打包

### 問題 2：點擊 Throttle Line Chart 後無反應
**原因**：模組未被打包或導入失敗

**檢查方法**：
1. 查看 `dist/F1T_GUI/` 目錄是否包含 Throttle 相關模組
2. 使用 console 模式查看是否有 `ImportError`

**解決方案**：
- 確認 `F1T_GUI.spec` 的 `hiddenimports` 包含所有必要模組
- 重新執行 `pyinstaller F1T_GUI.spec`

### 問題 3：圖表顯示異常或缺少元件
**原因**：圖表組件或資源檔案未被打包

**解決方案**：
1. 檢查 `matplotlib` 是否正確打包
2. 確認 `gui_i18n.py` 翻譯檔案已包含在 hiddenimports

---

## 📝 技術細節

### PyInstaller 模組偵測機制

**可自動偵測**：
```python
# 頂層導入 - PyInstaller 可自動偵測
import sys
from PyQt5.QtWidgets import QMainWindow
```

**無法自動偵測**：
```python
# 函數內動態導入 - PyInstaller 無法自動偵測
def some_function():
    from modules.gui.some_module import SomeClass  # ❌ 需要手動加入 hiddenimports
```

### 為什麼使用動態導入？

1. **減少啟動時間**：只在需要時才載入模組
2. **降低記憶體使用**：未使用的功能不佔用記憶體
3. **模組化設計**：各分析模組獨立，便於維護

### 打包後的目錄結構

```
dist/
└── F1T_GUI/
    ├── F1T_GUI.exe
    ├── _internal/
    │   ├── modules/
    │   │   └── gui/
    │   │       ├── Throttle_analysis/
    │   │       │   ├── throttle_line_chart_analysis/
    │   │       │   │   ├── throttle_line_chart_module.pyc
    │   │       │   │   ├── throttle_line_chart_mdi.pyc
    │   │       │   │   └── throttle_line_chart_data_loader.pyc
    │   │       │   └── ...
    │   │       └── ...
    │   └── ...
    └── ...
```

---

## ✅ 修復確認

修復後的 `F1T_GUI.spec` 已包含所有動態導入模組，Throttle Line Chart 應可在 EXE 中正常運作。

**版本**：V0.2.0  
**修復日期**：2025年10月8日  
**修復內容**：添加 48 個 hiddenimports 模組路徑

---

## 📞 問題回報

如果打包後仍有問題，請提供：
1. 執行環境（Python 版本、PyInstaller 版本）
2. 錯誤訊息（使用 console 模式獲取）
3. 打包命令和 .spec 檔案內容
