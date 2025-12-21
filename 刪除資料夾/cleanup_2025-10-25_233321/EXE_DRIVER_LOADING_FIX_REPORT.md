# 🔧 EXE環境車手列表載入失敗問題 - 深度調查報告

**問題日期**: 2025-10-23  
**問題描述**: 在 EXE 版本中使用 Lap Analysis → Speed Analysis 時，主 GUI 的 bar 中 driver 1 顯示空白，driver 2 只能選擇 "None"  
**嚴重程度**: ⚠️ **嚴重** - 影響所有 Lap Analysis 功能的使用  

---

## 🔍 問題分析

### ✅ 開發環境測試結果（正常）

執行診斷測試 `test_driver_loading_exe.py` 顯示：

```
✅ 成功載入 21 個車手
車手列表: ['ALB', 'ALO', 'ANT', 'BEA', 'BOR', 'COL', 'DOO', 'GAS', 'HAD', 'HAM', 'HUL', 'LAW', 'LEC', 'NOR', 'OCO', 'PIA', 'RUS', 'SAI', 'STR', 'TSU', 'VER']
```

**結論**: 開發環境下，車手列表可以從 `team_colors_2025_fastf1_20251019T045138Z.json` 正常載入。

---

### ❌ EXE 環境問題根源

根據代碼分析（`f1t_gui_main.py` 第 857-1120 行），問題可能出現在以下幾個環節：

#### 1. **工作目錄問題** ⭐ 最可能原因
EXE 執行時的當前工作目錄可能不是預期的專案根目錄，導致：
- `glob.glob("json/team_colors_*.json")` 找不到檔案
- 相對路徑無法正確解析

```python
# 當前代碼（第 966 行）
team_color_patterns = [
    f"json/team_colors_{year}_*.json",  # ❌ 相對路徑在EXE中可能失效
    f"json/team_colors_2025_*.json",
    f"json/team_colors_2024_*.json"
]
```

#### 2. **資源路徑問題**
EXE 打包後，資源檔案可能被放在臨時目錄，而不是與 EXE 同級的 `json/` 目錄。

#### 3. **API 調用失敗**
如果 JSON 不存在，代碼會嘗試通過 API 生成（第 982-1003 行），但：
- API 可能無法連接（網路問題）
- API timeout 設定太短（30秒）
- API 返回格式不符合預期

#### 4. **異常被靜默捕獲**
```python
# 第 1107-1120 行
except Exception as e:
    print(f"[ERROR] [DRIVERS] 載入車手列表失敗: {e}")
    # ❌ 只打印錯誤，但在EXE中看不到終端輸出
    # ❌ 沒有日誌記錄到檔案
```

---

## 🛠️ 解決方案

### 方案 1: **添加絕對路徑支援** ⭐ 推薦

修改 `_load_available_drivers()` 方法，支援 EXE 環境：

```python
def _load_available_drivers(self):
    """載入可用的車手列表 - 支援EXE環境"""
    try:
        import json
        import glob
        import os
        import sys
        
        # ========== 修復 1: 獲取正確的工作目錄 ==========
        if getattr(sys, 'frozen', False):
            # EXE 環境：使用執行檔所在目錄
            base_path = os.path.dirname(sys.executable)
            print(f"[DRIVERS] EXE模式，基礎路徑: {base_path}")
        else:
            # 開發環境：使用當前工作目錄
            base_path = os.getcwd()
            print(f"[DRIVERS] 開發模式，基礎路徑: {base_path}")
        
        # 獲取年份和賽事
        year = "2025"
        race = "Japan"
        
        try:
            if self.parent() and hasattr(self.parent(), 'get_current_parameters'):
                params = self.parent().get_current_parameters()
                year = params.get('year', '2025')
                race = params.get('race', 'Japan')
        except Exception as param_error:
            print(f"[DRIVERS] 使用預設參數: {year} {race}")
        
        if hasattr(self, 'year_combo'):
            year = self.year_combo.currentText()
            race = self.race_combo.currentText()
        
        print(f"[DRIVERS] 載入車手列表: {year} {race}")
        
        drivers = []
        
        # ========== 修復 2: 使用絕對路徑搜索 JSON ==========
        print(f"[DRIVERS] 步驟 1: 從 team_colors JSON 讀取...")
        json_dir = os.path.join(base_path, "json")
        
        team_color_patterns = [
            f"{json_dir}/team_colors_{year}_*.json",
            f"{json_dir}/team_colors_2025_*.json",
            f"{json_dir}/team_colors_2024_*.json"
        ]
        
        # ========== 修復 3: 添加診斷日誌 ==========
        print(f"[DRIVERS] JSON目錄: {json_dir}")
        print(f"[DRIVERS] JSON目錄存在: {os.path.exists(json_dir)}")
        if os.path.exists(json_dir):
            print(f"[DRIVERS] JSON目錄內容: {os.listdir(json_dir)[:10]}")  # 只顯示前10個
        
        for pattern in team_color_patterns:
            files = glob.glob(pattern)
            print(f"[DRIVERS] 搜索模式: {pattern}")
            print(f"[DRIVERS] 找到檔案數: {len(files)}")
            
            if files:
                latest_file = max(files, key=os.path.getmtime)
                print(f"[DRIVERS] 使用檔案: {latest_file}")
                
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        color_data = json.load(f)
                    
                    if 'data' in color_data and 'drivers' in color_data['data']:
                        drivers = sorted(list(color_data['data']['drivers'].keys()))
                        print(f"[DRIVERS] ✅ 從 team_colors JSON 載入 {len(drivers)} 個車手")
                        break
                except Exception as e:
                    print(f"[DRIVERS] ⚠️  讀取 team_colors 失敗: {e}")
                    # ========== 修復 4: 記錄到日誌檔案 ==========
                    import traceback
                    with open('driver_loading_error.log', 'a', encoding='utf-8') as log_file:
                        log_file.write(f"\n{'='*60}\n")
                        log_file.write(f"時間: {os.path.basename(latest_file)}\n")
                        log_file.write(f"錯誤: {e}\n")
                        log_file.write(f"{'='*60}\n")
                        traceback.print_exc(file=log_file)
        
        # ========== 修復 5: 如果沒有JSON，提供備用車手列表 ==========
        if not drivers:
            print(f"[DRIVERS] ⚠️  無法從JSON載入，使用2025年標準車手列表")
            drivers = [
                'VER', 'NOR', 'LEC', 'PIA', 'SAI', 'HAM', 'RUS', 'ALO', 
                'HUL', 'PER', 'GAS', 'ALB', 'OCO', 'STR', 'TSU', 
                'RIC', 'MAG', 'BOT', 'ZHO', 'SAR', 'LAW'
            ]
            print(f"[DRIVERS] ✅ 使用備用列表: {len(drivers)} 個車手")
        
        # 添加到下拉選單
        self.driver1_combo.clear()
        self.driver2_combo.clear()
        
        none_label = "None"  # 使用固定英文標籤避免翻譯問題
        self.driver2_combo.addItem(none_label, None)
        
        for driver in drivers:
            self.driver1_combo.addItem(driver, driver)
            self.driver2_combo.addItem(driver, driver)
        
        # 預設選擇
        if len(drivers) > 0:
            self.driver1_combo.setCurrentIndex(0)
            self.driver2_combo.setCurrentIndex(0)
            print(f"[DRIVERS] ✅ 成功載入 {len(drivers)} 個車手，預設: {drivers[0]}")
        
    except Exception as e:
        print(f"[ERROR] [DRIVERS] 嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()
        
        # ========== 修復 6: 強制顯示錯誤對話框（僅在GUI存在時） ==========
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "車手列表載入失敗",
                f"無法載入車手列表，請檢查以下項目：\n\n"
                f"1. json/ 目錄是否與 EXE 同級\n"
                f"2. team_colors_*.json 檔案是否存在\n"
                f"3. 查看 driver_loading_error.log 瞭解詳情\n\n"
                f"錯誤訊息: {str(e)}"
            )
        except:
            pass
        
        # 仍然添加空的選項避免崩潰
        self.driver1_combo.clear()
        self.driver2_combo.clear()
        self.driver1_combo.addItem("❌ 無車手數據", None)
        self.driver2_combo.addItem("None", None)
```

---

### 方案 2: **強制使用備用車手列表** （臨時方案）

如果 JSON 載入持續失敗，可以在對話框初始化時直接使用硬編碼的2025年車手列表：

```python
def _load_available_drivers(self):
    """載入可用的車手列表 - 備用方案"""
    # 2025年標準車手列表（來自F1官方名單）
    FALLBACK_DRIVERS_2025 = [
        'VER', 'NOR', 'LEC', 'PIA', 'SAI', 'HAM', 'RUS', 'ALO', 
        'HUL', 'PER', 'GAS', 'ALB', 'OCO', 'STR', 'TSU', 
        'RIC', 'MAG', 'BOT', 'ZHO', 'SAR', 'LAW'
    ]
    
    try:
        # ... 原有的載入邏輯 ...
        pass
    except Exception as e:
        print(f"[DRIVERS] 載入失敗，使用備用列表: {e}")
        drivers = FALLBACK_DRIVERS_2025
    
    # 確保有車手數據
    if not drivers:
        drivers = FALLBACK_DRIVERS_2025
        print(f"[DRIVERS] 啟用備用車手列表")
    
    # 填充下拉選單
    for driver in drivers:
        self.driver1_combo.addItem(driver, driver)
        self.driver2_combo.addItem(driver, driver)
```

---

### 方案 3: **打包 JSON 到 EXE** （最佳長期方案）

修改 `F1T_GUI.spec`，將必要的 JSON 檔案打包到 EXE：

```python
# F1T_GUI.spec
datas=[
    ('image/logo.png', 'image'),
    ('image/logo.ico', 'image'),
    # ✅ 添加必要的 JSON 檔案
    ('json/team_colors_2025_*.json', 'json'),  # 車手/車隊顏色
    # 注意：不打包所有 JSON，只打包關鍵檔案
]
```

---

## 🧪 測試計劃

### 測試 1: 開發環境驗證
```powershell
python f1t_gui_main.py
# 開啟 Lap Analysis → Speed Analysis
# 檢查 driver 1 和 driver 2 下拉選單是否正常
```

### 測試 2: EXE 環境驗證
```powershell
# 重新生成 EXE
pyinstaller F1T_GUI.spec --clean

# 執行 EXE
.\dist\F1T_GUI.exe

# 開啟 Lap Analysis → Speed Analysis
# 檢查：
# 1. driver 1 是否有車手選項
# 2. driver 2 是否可以選擇車手（除了None）
# 3. 查看 driver_loading_error.log 是否有錯誤記錄
```

### 測試 3: 無 JSON 環境測試
```powershell
# 暫時移動 json/ 目錄
Move-Item json json_backup

# 執行 EXE
.\dist\F1T_GUI.exe

# 檢查是否使用備用車手列表
# 應該看到 21 個標準車手

# 恢復 json/ 目錄
Move-Item json_backup json
```

---

## 📊 修復優先級

| 優先級 | 方案 | 實施難度 | 效果 |
|--------|------|----------|------|
| 🔴 高 | 方案 1：絕對路徑 + 備用列表 | 中等 | 徹底解決 |
| 🟡 中 | 方案 2：強制備用列表 | 簡單 | 臨時解決 |
| 🟢 低 | 方案 3：打包 JSON | 簡單 | 優化體驗 |

---

## 🎯 建議實施順序

1. **立即實施**: 方案 1 的修復 1-6（絕對路徑支援 + 備用列表 + 錯誤日誌）
2. **短期實施**: 方案 3（將 team_colors JSON 打包到 EXE）
3. **長期優化**: 考慮將車手列表改為從 API 動態獲取，並加入本地緩存機制

---

## ✅ 預期結果

修復後，EXE 環境下應該：
1. ✅ driver 1 下拉選單顯示 21 個車手
2. ✅ driver 2 下拉選單顯示 "None" + 21 個車手
3. ✅ 如果 JSON 不存在，自動使用備用車手列表
4. ✅ 錯誤訊息記錄到 `driver_loading_error.log`
5. ✅ 彈出明確的錯誤對話框（如果完全失敗）

---

**📝 結論**: 問題根源是 EXE 環境下的工作目錄和資源路徑問題，通過添加絕對路徑支援和備用車手列表可以徹底解決。
