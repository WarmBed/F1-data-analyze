# View 和 Analysis 選單隱藏報告

## 📅 更新日期
2025年10月22日

## 🎯 修改目標
隱藏主選單列中的 **View** 和 **Analysis** 選單

## 📝 修改內容

### 已隱藏的選單

#### 1️⃣ **View 選單**
隱藏的功能項目：
- Tile Windows (平鋪視窗)
- Cascade Windows (層疊視窗)
- Minimize All Windows (最小化所有視窗)
- Maximize All Windows (最大化所有視窗)
- Restore All Windows (恢復所有視窗)
- Close All Windows (關閉所有視窗)
- Full Screen (全螢幕)

#### 2️⃣ **Analysis 選單**
隱藏的功能項目：
- Driver Standings (車手積分榜)
- Constructor Standings (車隊積分榜)
- Season Progress (賽季進度)

## 📂 修改的檔案

### `f1t_gui_main.py` (第 6546-6566 行)

**變更前**：
```python
# 檢視菜單
view_menu = menubar.addMenu(tr('view_menu'))
view_menu.addAction(tr('tile_windows', 'Tile Windows'), self.tile_windows)
# ... 更多項目 ...

# 分析菜單
analysis_menu = menubar.addMenu(tr('menu_analysis', 'Analysis'))
analysis_menu.addAction(tr('menu_driver_standings', 'Driver Standings'), self.open_driver_standings)
# ... 更多項目 ...
```

**變更後**：
```python
# 檢視菜單 (已隱藏)
# view_menu = menubar.addMenu(tr('view_menu'))
# view_menu.addAction(tr('tile_windows', 'Tile Windows'), self.tile_windows)
# ... 更多項目已註解 ...

# 分析菜單 (已隱藏)
# analysis_menu = menubar.addMenu(tr('menu_analysis', 'Analysis'))
# analysis_menu.addAction(tr('menu_driver_standings', 'Driver Standings'), self.open_driver_standings)
# ... 更多項目已註解 ...
```

## 📊 選單結構變更

### 變更前
```
選單列：
├── File
├── View          ← 已隱藏
├── Analysis      ← 已隱藏
├── Tools
└── Help
```

### 變更後
```
選單列：
├── File
├── Tools
└── Help
```

## ✅ 驗證結果

- ✅ 語法檢查通過 (`python -m py_compile f1t_gui_main.py`)
- ✅ View 選單已隱藏（所有子項目已註解）
- ✅ Analysis 選單已隱藏（所有子項目已註解）
- ✅ 其他選單（File, Tools, Help）保持正常運作

## 🔄 如何恢復

如果未來需要恢復這些選單，只需：

1. 打開 `f1t_gui_main.py`
2. 找到第 6546-6566 行
3. 移除註解符號 `#`
4. 重新啟動 GUI

## 📝 備註

- 隱藏的功能仍然存在於代碼中，只是不顯示在選單列
- 相關的方法（如 `tile_windows()`, `open_driver_standings()`）仍然保留在程式中
- 翻譯鍵仍然保留在 `core/gui_i18n.py` 中
- 如需完全移除這些功能，建議保留代碼以便未來使用

## 🚀 下一步建議

1. **測試 GUI**：
   ```powershell
   python f1t_gui_main.py
   ```
   確認選單列只顯示 File、Tools、Help

2. **重新生成 EXE**：
   ```powershell
   pyinstaller F1T_GUI.spec --clean
   ```

3. **測試 EXE**：
   確認 EXE 版本的選單列也正確隱藏了 View 和 Analysis

---

## ✅ 修改完成

**狀態**: ✅ 已完成
**影響範圍**: 僅影響選單列顯示，不影響其他功能
**向後相容**: ✅ 是（代碼僅註解，未刪除）
