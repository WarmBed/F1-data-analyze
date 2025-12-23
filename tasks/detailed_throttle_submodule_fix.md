# 🔧 Detailed Lap & Throttle Analysis 子模組修復報告

**修復日期**: 2025-10-09  
**問題**: AttributeError 和模組調用錯誤

---

## 🚨 **發現的問題**

### **問題 1: `open_detailed_lap_analysis` 方法不存在**

**錯誤訊息**:
```
AttributeError: 'StyleHMainWindow' object has no attribute 'open_detailed_lap_analysis'
```

**錯誤代碼**:
```python
# ❌ 錯誤：調用不存在的方法
elif clean_name in ["Detailed Lap Table", "詳細圈速表格"]:
    self.main_window.open_detailed_lap_analysis()  # ⚠️ 方法不存在
```

**根本原因**:
- `open_detailed_lap_analysis()` 方法從未在 `StyleHMainWindow` 中定義
- 實際存在的是 `_prompt_detailed_lap_options()` 和 `_create_detailed_lap_boxplot_window()`

---

### **問題 2: Throttle Analysis 子模組錯誤調用**

**錯誤代碼**:
```python
# ❌ 錯誤：使用 hasattr 檢查不存在的方法
if hasattr(self.main_window, 'open_throttle_analysis'):
    self.main_window.open_throttle_analysis()  # ⚠️ 方法不存在
else:
    print(f"[TREE_CLICK] ⚠️ open_throttle_analysis 方法不存在，跳過")
```

**根本原因**:
- `open_throttle_analysis()` 方法不存在
- Throttle Analysis 有兩個獨立的子模組：
  - `throttle_box_plot_analysis` - 油門箱線圖
  - `throttle_line_chart_analysis` - 油門折線圖
- 應該直接導入並使用這些模組，而不是調用父級方法

---

## ✅ **修復方案**

### **1. Detailed Lap Analysis 子模組修復**

#### **(D) Detailed Lap Table - 詳細圈速表格**

```python
elif clean_name in ["Detailed Lap Table", "詳細圈速表格"]:
    print(f"[TREE_CLICK] 開啟詳細圈速表格（直接模式）")
    try:
        from modules.gui.driver_race.detailed_lap_analysis import (
            driverLapAnalysisModule,
            create_driverLap_analysis_module
        )
        
        # 創建模組實例
        module = create_driverLap_analysis_module()
        module.current_year = str(params['year'])
        module.current_race = params['race']
        module.current_session = params['session']
        
        # 初始化模組
        if module.initialize_module():
            window_title = module.get_window_title(
                year=str(params['year']),
                race=params['race'],
                session=params['session']
            )
            
            # 創建視窗
            sub_window = PopoutSubWindow(window_title, self.main_window.get_current_mdi_area(), module)
            sub_window.setWidget(module.get_widget())
            module.set_parent_window(sub_window)
            
            width, height = module.get_default_size()
            sub_window.resize(width, height)
            
            self.main_window.get_current_mdi_area().addSubWindow(sub_window)
            sub_window.show()
            
            print(f"[DETAILED_LAP] ✅ 成功開啟詳細圈速表格")
        else:
            print(f"[DETAILED_LAP] ❌ 模組初始化失敗")
    except Exception as e:
        print(f"[DETAILED_LAP] ❌ 開啟失敗: {e}")
        import traceback
        traceback.print_exc()
```

**模組路徑**: `modules.gui.driver_race.detailed_lap_analysis`  
**CLI 功能**: `-f 28` (detailed_laptime_analysis)

---

#### **(D) Lap Time Box Plot - 圈速箱線圖**

```python
elif clean_name in ["Lap Time Box Plot", "圈速箱線圖"]:
    print(f"[TREE_CLICK] 開啟圈速箱線圖（直接模式）")
    try:
        from modules.gui.driver_race.lap_box_plot_analysis import (
            LapTimeBoxPlotAnalysis,
        )
        
        # 使用現有的方法創建視窗
        self.main_window._create_detailed_lap_boxplot_window(
            self.main_window.get_current_mdi_area(),
            params["year"], params["race"], params["session"]
        )
        print(f"[LAP_BOXPLOT] ✅ 成功開啟圈速箱線圖")
    except Exception as e:
        print(f"[LAP_BOXPLOT] ❌ 開啟失敗: {e}")
        import traceback
        traceback.print_exc()
```

**模組路徑**: `modules.gui.driver_race.lap_box_plot_analysis`  
**CLI 功能**: `-f 28` (detailed_laptime_analysis)  
**現有方法**: `_create_detailed_lap_boxplot_window()` (Line 9025)

---

### **2. Throttle Analysis 子模組修復**

#### **(T) Throttle Box Plot - 油門箱線圖**

```python
elif clean_name in ["Throttle Box Plot", "油門箱線圖"]:
    print(f"[TREE_CLICK] 開啟油門箱線圖（直接模式）")
    try:
        from modules.gui.Throttle_analysis.throttle_box_plot_analysis import (
            ThrottleBoxPlotAnalysisModule,
            create_throttle_boxplot_module
        )
        
        # 創建模組實例
        module = create_throttle_boxplot_module()
        module.current_year = str(params['year'])
        module.current_race = params['race']
        module.current_session = params['session']
        
        # 初始化模組
        if module.initialize_module():
            window_title = module.get_window_title(
                year=str(params['year']),
                race=params['race'],
                session=params['session']
            )
            
            # 創建視窗
            sub_window = PopoutSubWindow(window_title, self.main_window.get_current_mdi_area(), module)
            sub_window.setWidget(module.get_widget())
            module.set_parent_window(sub_window)
            
            width, height = module.get_default_size()
            sub_window.resize(width, height)
            
            self.main_window.get_current_mdi_area().addSubWindow(sub_window)
            sub_window.show()
            
            print(f"[THROTTLE_BOXPLOT] ✅ 成功開啟油門箱線圖")
        else:
            print(f"[THROTTLE_BOXPLOT] ❌ 模組初始化失敗")
    except Exception as e:
        print(f"[THROTTLE_BOXPLOT] ❌ 開啟失敗: {e}")
        import traceback
        traceback.print_exc()
```

**模組路徑**: `modules.gui.Throttle_analysis.throttle_box_plot_analysis`  
**CLI 功能**: `-f 54` (Lap Throttle Ratio Per Driver)

---

#### **(T) Throttle Line Chart - 油門折線圖**

```python
elif clean_name in ["Throttle Line Chart", "油門折線圖"]:
    print(f"[TREE_CLICK] 開啟油門折線圖（直接模式）")
    try:
        from modules.gui.Throttle_analysis.throttle_line_chart_analysis import (
            ThrottleLineChartModule,
            create_throttle_line_chart_module
        )
        
        # 創建模組實例
        module = create_throttle_line_chart_module()
        module.current_year = str(params['year'])
        module.current_race = params['race']
        module.current_session = params['session']
        
        # 初始化模組
        if module.initialize_module():
            window_title = module.get_window_title(
                year=str(params['year']),
                race=params['race'],
                session=params['session']
            )
            
            # 創建視窗
            sub_window = PopoutSubWindow(window_title, self.main_window.get_current_mdi_area(), module)
            sub_window.setWidget(module.get_widget())
            module.set_parent_window(sub_window)
            
            width, height = module.get_default_size()
            sub_window.resize(width, height)
            
            self.main_window.get_current_mdi_area().addSubWindow(sub_window)
            sub_window.show()
            
            print(f"[THROTTLE_LINECHART] ✅ 成功開啟油門折線圖")
        else:
            print(f"[THROTTLE_LINECHART] ❌ 模組初始化失敗")
    except Exception as e:
        print(f"[THROTTLE_LINECHART] ❌ 開啟失敗: {e}")
        import traceback
        traceback.print_exc()
```

**模組路徑**: `modules.gui.Throttle_analysis.throttle_line_chart_analysis`  
**CLI 功能**: `-f 54` (Lap Throttle Ratio Per Driver)

---

## 📊 **模組架構總結**

### **Detailed Lap Analysis 架構**

```
modules/gui/driver_race/
├─ detailed_lap_analysis/           # (D) Detailed Lap Table
│  ├─ __init__.py
│  ├─ driverlap_analysis_module.py  # 主模組
│  ├─ driverlap_analysis_mdi.py     # MDI 管理
│  └─ driverlap_analysis_chart_widget.py
│
└─ lap_box_plot_analysis/          # (D) Lap Time Box Plot
   ├─ __init__.py
   ├─ lap_box_plot_analysis_mdi.py
   └─ lap_box_plot_chart_widget.py
```

### **Throttle Analysis 架構**

```
modules/gui/Throttle_analysis/
├─ throttle_analysis_options_dialog.py  # 父項目對話框（已禁用）
│
├─ throttle_box_plot_analysis/          # (T) Throttle Box Plot
│  ├─ __init__.py
│  ├─ throttle_box_plot_analysis_module.py
│  ├─ throttle_box_plot_analysis_mdi.py
│  └─ throttle_box_plot_chart_widget.py
│
└─ throttle_line_chart_analysis/        # (T) Throttle Line Chart
   ├─ __init__.py
   ├─ throttle_line_chart_module.py
   ├─ throttle_line_chart_mdi.py
   ├─ throttle_line_chart_data_loader.py
   └─ [其他圖表組件]
```

---

## 🧪 **測試驗證**

### **測試步驟**

1. **啟動 GUI**:
   ```powershell
   python f1t_gui_main.py
   ```

2. **展開樹狀圖**:
   - Driver Performance Analysis
   - Detailed Lap Analysis
   - Throttle Analysis

3. **點擊子項目測試**:
   - [ ] **(D) Detailed Lap Table** → 應開啟詳細圈速表格
   - [ ] **(D) Lap Time Box Plot** → 應開啟圈速箱線圖
   - [ ] **(T) Throttle Box Plot** → 應開啟油門箱線圖
   - [ ] **(T) Throttle Line Chart** → 應開啟油門折線圖

### **預期結果**

每個子項目都應該：
- ✅ 不拋出 AttributeError
- ✅ 正確導入對應模組
- ✅ 創建並顯示分析視窗
- ✅ 終端顯示成功訊息

### **錯誤處理**

所有子項目現在都有完整的錯誤處理：
```python
except Exception as e:
    print(f"[MODULE_NAME] ❌ 開啟失敗: {e}")
    import traceback
    traceback.print_exc()
```

---

## 📝 **修復統計**

| 模組 | 狀態 | 修復內容 |
|------|------|---------|
| Detailed Lap Table | ✅ 完成 | 改用 `create_driverLap_analysis_module()` |
| Lap Time Box Plot | ✅ 完成 | 使用現有 `_create_detailed_lap_boxplot_window()` |
| Throttle Box Plot | ✅ 完成 | 導入 `create_throttle_boxplot_module()` |
| Throttle Line Chart | ✅ 完成 | 導入 `create_throttle_line_chart_module()` |

---

## 🎯 **關鍵改進**

1. **統一模組創建模式**: 所有子模組使用一致的 `create_xxx_module()` 模式
2. **完整錯誤處理**: 每個子項目都有 try-except 保護
3. **清晰的調試輸出**: 使用 `[MODULE_NAME]` 前綴標識
4. **模組架構清晰**: 明確區分 Detailed Lap 和 Throttle 的兩個子模組架構

---

## ✅ **完成確認**

- [x] 識別所有不存在的方法
- [x] 找到正確的模組入口
- [x] 實現統一的創建模式
- [x] 添加完整錯誤處理
- [x] 語法檢查通過
- [ ] GUI 功能測試（待用戶驗證）

**狀態**: 代碼修復完成，等待功能測試 ✅
