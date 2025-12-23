# Phase 2 & 3 完整翻譯計劃

## 需要翻譯的主要區域

## ✅ Phase 2 已完成 (100%)

### ✅ 主選單欄 (create_professional_menubar) - 100% 完成
- [x] File Menu
  - Open Session... ✅
  - Save Workspace ✅
  - Export Report... ✅
  - Exit ✅
  
- [x] Analysis Menu
  - [RAIN] Rain Analysis ✅
  - [FINISH] Track Analysis ✅
  - 🏎️ Race Overview ✅
  - Telemetry Analysis ✅
  - Telemetry Comparison ✅
  - Driver Comparison ✅
  - Sector Analysis ✅
  
- [x] View Menu
  - Tile Windows ✅
  - Cascade Windows ✅
  - Minimize All Windows ✅
  - Maximize All Windows ✅
  - Restore All Windows ✅
  - Close All Windows ✅
  - Full Screen ✅
  
- [x] Tools Menu
  - Data Validation ✅
  - System Settings ✅
  - Check API Status ✅

### ✅ 自定義標題欄 (DraggableTitleBar) - 100% 完成
- [x] Sync button tooltip ✅
- [x] Linkage button tooltip ✅
- [x] Restore size button tooltip ✅
- [x] Window settings button tooltip ✅
- [x] Minimize button tooltip ✅
- [x] Maximize button tooltip ✅
- [x] Popout button tooltip ✅
- [x] Close button tooltip ✅
- [x] Context menu items ✅
- [x] Status messages ✅

### PopoutSubWindow
- [ ] Window title templates
- [ ] Status messages
- [ ] Error messages

### GUI 模組 (優先級排序)
1. [ ] modules/gui/lap_analysis/telemetry_analysis_mdi.py
2. [ ] modules/gui/lap_analysis/speed_analysis_mdi.py
3. [ ] modules/gui/track_analysis/track_analysis_module.py
4. [ ] modules/gui/rain_analysis/rain_universal_analysis_mdi.py
5. [ ] modules/gui/accident_analysis/accident_universal_analysis_mdi.py

## 實施策略
1. 先添加所有翻譯鍵值到 gui_i18n.py（包含日文）
2. 批量替換主視窗中的硬編碼字串
3. 逐個模組進行翻譯
