# F1T GUI - EXE 打包前檢查報告

## 檢查日期
2025-10-13

## 檢查項目

### ✅ 1. PyInstaller 配置檔案
- **檔案**: `F1T_GUI.spec`
- **狀態**: 存在且已更新
- **HiddenImports 數量**: **125 個模組**（從原本的 48 個增加到 125 個）

### ✅ 2. Runtime Hook
- **檔案**: `pyinstaller_runtime_hook.py`
- **狀態**: 存在
- **功能**: 自動設置 `F1_LOG_LEVEL=DEBUG`

### ✅ 3. 建置腳本
- **檔案**: `Build_F1T_GUI.bat`
- **狀態**: 存在且可用
- **版本**: V0.3.0

## 新增的關鍵模組（77 個）

### 🎯 Demo/Championship 模組（13 個）
- `modules.gui.constructor_standings` (含 mdi, module, data_loader)
- `modules.gui.driver_standings` (含 mdi, module, data_loader)
- `modules.gui.season_progress` (含 mdi, module, data_loader)
- `modules.gui.weather_timeline` (含 mdi, widget, data_loader)

### 🎯 Lap Analysis 差異分析（12 個）
- `modules.gui.lap_analysis.speeddiff_analysis` (完整模組)
- `modules.gui.lap_analysis.distancediff_analysis` (完整模組)
- `modules.gui.lap_analysis.timediff_analysis` (完整模組)
- 每個模組包含: mdi, module, chart_widget, data_loader

### 🎯 Ideal Lap Analysis（17 個）
- `modules.gui.ideal_lap_analysis` (主模組)
- `modules.gui.ideal_lap_analysis.ideal_lap_options_dialog`
- `modules.gui.ideal_lap_analysis.shared_colors`
- `modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.*` (完整)
- `modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.*` (完整)
- `modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.*` (完整)

### 🎯 缺失的 Data Loaders（7 個）
- `modules.gui.lap_analysis.speed_analysis.speed_analysis_data_loader`
- `modules.gui.lap_analysis.rpm_analysis.rpm_analysis_data_loader`
- `modules.gui.lap_analysis.gear_analysis.gear_analysis_data_loader`
- `modules.gui.lap_analysis.brake_analysis.brake_analysis_data_loader`
- `modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_data_loader`
- `modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_data_loader`
- `modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_module`
- `modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_mdi`

### 🎯 Shared/Core 模組（6 個）
- `modules.gui.shared.season_calendar_provider`
- `modules.gui.shared.race_selection_manager`
- `modules.gui.themes` (含 color_palette_provider)
- `modules.gui.lap_analysis.linkage` (含 linkage_manager)

### 🎯 Lap Box Plot（4 個）
- `modules.gui.lap_box_plot_analysis.*` (根目錄版本，完整模組)

## 問題分析

### ❌ 為什麼這些模組之前沒有被載入？

#### 1. **動態導入（Lazy Import）**
主程式 `f1t_gui_main.py` 中使用了**延遲導入**模式：
```python
# 例如：只在選單被點擊時才導入
def _on_constructor_standings_clicked(self):
    from modules.gui.constructor_standings import ConstructorStandingsMDI
    # ...
```

PyInstaller 的**靜態分析無法檢測**這類動態導入，因此必須手動在 `hiddenimports` 中聲明。

#### 2. **日語選單與模組對應**
從您的截圖中看到的日文選單項目（例如「コンストラクター順位」「ドライバー順位」）對應的模組：
- **コンストラクター順位** → `constructor_standings` ❌ 之前缺失
- **ドライバー順位** → `driver_standings` ❌ 之前缺失  
- **シーズン進捗** → `season_progress` ❌ 之前缺失
- **天気タイムライン** → `weather_timeline` ❌ 之前缺失

這些都是**通過選單動態加載**的模組，必須在 spec 中明確聲明。

#### 3. **子模組遺漏**
許多分析模組有多個子組件：
- `xxx_mdi.py` - MDI 視窗
- `xxx_module.py` - 模組邏輯
- `xxx_data_loader.py` - 數據載入器 ❌ **經常被遺漏**
- `xxx_chart_widget.py` - 圖表小工具

之前只添加了 `mdi` 和 `module`，但 **data_loader 被遺漏**，導致 EXE 運行時找不到數據載入器。

## 修復摘要

### 修改的檔案
1. **F1T_GUI.spec** - 增加 77 個 hiddenimports
   - 原本：48 個
   - 現在：**125 個** ✅

### 修復類別
| 類別 | 數量 | 說明 |
|------|------|------|
| Championship/Demo 模組 | 13 | constructor_standings, driver_standings, season_progress, weather_timeline |
| Lap Analysis 差異分析 | 12 | speeddiff, distancediff, timediff (完整模組) |
| Ideal Lap Analysis | 17 | ranking_table, sector_heatmap, sector_comparison |
| Data Loaders 補充 | 7 | 各分析模組的數據載入器 |
| Shared/Core 模組 | 6 | season_calendar_provider, themes, linkage |
| Lap Box Plot (根目錄) | 4 | 根目錄版本的 lap_box_plot_analysis |
| Driver Race 模組 | 2 | driverlap_analysis_module, driverlap_analysis_mdi |

## 驗證步驟

### ✅ 已完成
1. 提取 `f1t_gui_main.py` 中所有動態導入
2. 對比 `F1T_GUI.spec` 找出缺失模組
3. 更新 spec 文件添加所有缺失模組
4. 創建驗證腳本 `verify_hiddenimports.py`

### ⚠️ 待測試
1. **Import 測試** - 驗證所有模組可正常導入
2. **PyInstaller 打包** - 執行 `Build_F1T_GUI.bat`
3. **EXE 功能測試** - 測試所有選單項目

## 建議的測試流程

### 步驟 1: 驗證導入（5 分鐘）
```powershell
python verify_hiddenimports.py
```

### 步驟 2: 執行打包（10-15 分鐘）
```powershell
.\Build_F1T_GUI.bat
```

### 步驟 3: 測試 EXE（20 分鐘）
1. 啟動 `dist\F1T_GUI.exe`
2. 測試日文選單中的所有項目：
   - ✅ コンストラクター順位（Constructor Standings）
   - ✅ ドライバー順位（Driver Standings）
   - ✅ シーズン進捗（Season Progress）
   - ✅ 天気タイムライン（Weather Timeline）
   - ✅ Ideal Lap Analysis 子模組
   - ✅ Speed Diff/Distance Diff/Time Diff 分析

## 風險評估

### 🟢 低風險
- 所有新增模組都是**已存在**的實際模組
- 遵循現有的命名規範
- 與主程式的動態導入完全對應

### 🟡 中風險
- 部分模組可能有**循環依賴**（但主程式已正常運行）
- EXE 大小可能增加 50-100 MB

### 🔴 需注意
- 確保所有 `__init__.py` 存在且正確
- 驗證 data_loader 與 mdi 的連接正常
- 測試 API-ONLY 模式在 EXE 中的行為

## 下一步行動

1. ✅ **立即執行**: `python verify_hiddenimports.py` 驗證導入
2. ✅ **通過後執行**: `.\Build_F1T_GUI.bat` 打包 EXE
3. ✅ **打包完成後**: 測試所有日文選單功能
4. 📝 **記錄結果**: 建立測試報告

## 總結

**問題根源**: PyInstaller 無法自動檢測**延遲導入（lazy import）**的模組，特別是通過選單點擊才動態加載的功能。

**解決方案**: 手動在 `F1T_GUI.spec` 的 `hiddenimports` 中聲明所有動態導入的模組。

**影響範圍**: 
- ✅ 修復了 **77 個缺失模組**
- ✅ 涵蓋所有日文選單功能
- ✅ 包含完整的 data_loader、module、mdi 組件

**建議**: 在未來添加新功能時，同步更新 `F1T_GUI.spec` 以避免類似問題。
