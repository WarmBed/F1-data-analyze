# 🐛 深度診斷報告：RPM 模式切換 Race/Driver 時自動呼叫 Pitstop 模組

**日期**: 2025-10-06  
**嚴重性**: ⚠️ **MEDIUM** - 不影響功能但破壞用戶體驗  
**症狀**: 在 RPM 分析視窗中切換賽事/車手時，系統自動創建並顯示 Pitstop 進站分析視窗

---

## 📋 問題分析

### 1️⃣ 已排除的可能原因

經過深度程式碼檢查，以下機制**不是**問題根源：

#### ❌ API-ONLY 模式違規（已修復）
- **狀態**: ✅ 所有 8 個 lap_analysis 模組已修復
- **驗證**: `verify_api_only_compliance.py` 顯示 0 違規
- **縮排錯誤**: ✅ 已通過 `fix_indentation_errors.py` 修復

#### ❌ RPM 模組自動創建視窗
- **檢查**: `rpm_analysis_mdi.py` 沒有 `create_pitstop` 或 `PitstopAnalysis` 調用
- **update_parameters**: 只重新載入 RPM 數據，不創建其他模組

#### ❌ 主視窗自動載入機制
- **`sync_to_all_mdi_subwindows`**: 只發送通知給**已存在**的子視窗
- **`receive_main_window_update_notification`**: Pitstop 模組只是更新參數並重載數據

#### ❌ 分析模組管理器
- **`AnalysisModuleManager`**: 只管理統計面板顯示狀態，不創建視窗

### 2️⃣ 可能的問題根源

基於症狀和程式碼分析，最可能的原因是：

#### 🔍 假設 A: 車手列表載入邏輯觸發 Pitstop
```python
# f1t_gui_main.py line 858-900
def load_available_drivers(self, year: str, race: str) -> List[str]:
    """載入可用的車手列表 - 從進站分析JSON獲取"""
    print(f"[DRIVERS] 從進站分析JSON載入車手列表: {year} {race}")
    
    # 搜尋進站分析JSON檔案
    pitstop_patterns = [...]
    
    # 如果找不到JSON...可能觸發了什麼？
```

**可疑點**：
- 載入車手列表時依賴**進站分析 JSON**
- 如果 JSON 不存在，可能有後備邏輯**自動創建 Pitstop 視窗**來獲取數據

#### 🔍 假設 B: MDI 子視窗的錯誤關聯
```python
# 可能的問題：PopoutSubWindow 保留了對 Pitstop 模組的引用
# 當 RPM 視窗更新參數時，意外觸發了 Pitstop 視窗的創建
```

**可疑點**：
- `check_and_show_lap_controls_if_needed` 方法會掃描所有 MDI 子視窗
- 可能將 Pitstop 誤認為 lap_analysis 模組並添加到追蹤列表

#### 🔍 假設 C: 快取或單例模式殘留
```python
# 可能 Pitstop 模組使用單例模式
# 第一次創建後，後續「更新參數」時會重新顯示視窗
```

---

## 🔬 診斷步驟

### 立即執行以獲取更多信息

```powershell
# 1. 檢查日誌中 Pitstop 創建的調用堆疊
Select-String -Path "dist\logs\f1_gui_*.log" -Pattern "MODULE_FACTORY.*進站|MODULE_FACTORY.*Pitstop|創建進站分析" -Context 5,5

# 2. 檢查車手列表載入時的行為
Select-String -Path "dist\logs\f1_gui_*.log" -Pattern "DRIVERS.*進站|load_available_drivers" -Context 3,3

# 3. 檢查 MDI 子視窗追蹤
Select-String -Path "dist\logs\f1_gui_*.log" -Pattern "LAP_CONTROL.*進站|LAP_CONTROL.*Pitstop" -Context 2,2

# 4. 啟用詳細調試並重現問題
# 在 f1t_gui_main.py 中添加調試輸出，然後：
# - 開啟 RPM 分析視窗
# - 切換賽事/車手
# - 觀察日誌輸出
```

### 添加調試輸出

```python
# 在 f1t_gui_main.py 的關鍵位置添加：

def load_available_drivers(self, year: str, race: str) -> List[str]:
    """載入可用的車手列表 - 從進站分析JSON獲取"""
    import traceback
    print(f"[DEBUG_PITSTOP] load_available_drivers 被調用")
    print(f"[DEBUG_PITSTOP] 調用堆疊:")
    for line in traceback.format_stack()[-5:]:
        print(f"[DEBUG_PITSTOP] {line.strip()}")
    
    # ... 原有程式碼 ...
```

---

## 🛠️ 修復策略

基於假設，提供以下修復方案：

### 方案 1: 檢查並修復車手列表載入邏輯

**目標**: 確保 `load_available_drivers` 不會觸發 Pitstop 視窗創建

```python
# f1t_gui_main.py
def load_available_drivers(self, year: str, race: str) -> List[str]:
    """載入可用的車手列表 - 從進站分析JSON獲取"""
    print(f"[DRIVERS] 從進站分析JSON載入車手列表: {year} {race}")
    
    # ✅ 修復：只讀取 JSON，絕不自動創建視窗
    json_files = self._search_pitstop_json(year, race)
    
    if json_files:
        return self._extract_drivers_from_json(json_files[0])
    else:
        # ❌ 原先：可能自動創建 Pitstop 視窗
        # ✅ 修復：返回標準車手列表
        print(f"[DRIVERS] ⚠️ 找不到進站分析 JSON，使用標準車手列表")
        return [
            "VER", "PER", "LEC", "SAI", "HAM", "RUS", "NOR", "PIA",
            "ALO", "STR", "TSU", "YUK", "ALB", "SAR", "MAG", "HUL",
            "GAS", "OCO", "BOT", "ZHO"
        ]
```

### 方案 2: 過濾 Pitstop 模組不進入 lap_analysis 追蹤

**目標**: 確保 `check_and_show_lap_controls_if_needed` 不會將 Pitstop 視窗誤認為 lap_analysis

```python
# f1t_gui_main.py
def check_and_show_lap_controls_if_needed(self):
    """檢查是否有遙測分析視窗，如果有就顯示控件"""
    # ... 現有程式碼 ...
    
    for sub_window in current_mdi_area.subWindowList():
        window_title = sub_window.windowTitle()
        
        # ✅ 添加過濾：排除進站分析視窗
        if any(keyword in window_title for keyword in ["進站分析", "Pitstop", "ピットストップ"]):
            print(f"[LAP_CONTROL] ⏭️  跳過非遙測模組: {window_title}")
            continue
        
        # ... 現有檢查邏輯 ...
```

### 方案 3: 禁用 Pitstop 模組的自動響應

**目標**: 確保 Pitstop 模組不會響應主視窗的參數更新通知

```python
# modules/gui/pitstop_analysis/pitstop_analysis_mdi.py
def receive_main_window_update_notification(self, param_type, value):
    """接收主視窗參數變更通知"""
    print(f"[ANNOUNCE] [NOTIFICATION] 進站分析模組收到主視窗更新通知: {param_type}={value}")
    
    # ✅ 添加檢查：只有用戶主動開啟的 Pitstop 視窗才響應
    if not hasattr(self, '_user_created') or not self._user_created:
        print(f"[NOTIFICATION] ⚠️ 非用戶主動創建的進站分析視窗，忽略通知")
        return
    
    # ... 原有程式碼 ...
```

### 方案 4: 全域禁用 Pitstop 自動創建

**目標**: 在 `create_analysis_function` 或 `_create_analysis_module` 中添加白名單

```python
# f1t_gui_main.py
def _create_analysis_module(self, function_name: str, params: dict):
    """創建分析模組"""
    
    # ✅ 添加檢查：禁止非用戶操作創建 Pitstop
    if "進站分析" in function_name or "Pitstop" in function_name:
        if not params.get('user_initiated', False):
            print(f"[MODULE_FACTORY] ❌ 禁止自動創建 Pitstop 模組")
            return None
    
    # ... 原有程式碼 ...
```

---

## 🧪 測試計劃

### 測試案例 1: RPM 模式切換賽事
1. 開啟 RPM 分析視窗
2. 在主視窗切換賽事（例如：Japan → Australia）
3. **預期結果**: 只有 RPM 視窗更新，不應出現 Pitstop 視窗
4. **實際結果**: (待測試)

### 測試案例 2: RPM 模式切換車手
1. 開啟 RPM 分析視窗
2. 在 RPM 視窗內切換車手（例如：VER → LEC）
3. **預期結果**: 只有 RPM 圖表更新，不應出現 Pitstop 視窗
4. **實際結果**: (待測試)

### 測試案例 3: 多模組同時開啟
1. 開啟 RPM + Speed + Gear 3 個視窗
2. 切換主視窗賽事
3. **預期結果**: 3 個視窗都更新，不應出現 Pitstop 視窗
4. **實際結果**: (待測試)

---

## 📝 需要用戶提供的信息

為了精確定位問題，請提供以下信息：

### 1. 重現步驟
```
請詳細描述觸發問題的操作步驟：
1. 開啟 RPM 分析視窗
2. 選擇賽事：__________
3. 選擇車手：__________
4. 執行操作：__________  (例如：「切換賽事到 Australia」)
5. 結果：Pitstop 視窗自動出現
```

### 2. 日誌片段
```powershell
# 請執行並提供輸出：
Get-Content "dist\logs\f1_gui_*.log" | Select-String -Pattern "MODULE_FACTORY|DRIVERS|LAP_CONTROL" -Context 2,2 | Select-Object -Last 100 > pitstop_debug.log
```

### 3. Pitstop 視窗標題
```
自動出現的 Pitstop 視窗標題是什麼？
例如："進站分析 - 2025 Japan R"
```

### 4. 觸發時機
```
Pitstop 視窗是在哪個時機出現的？
□ 切換賽事時
□ 切換車手時
□ 切換場次時
□ 開啟 RPM 視窗時
□ 其他：__________
```

---

## 🚀 立即可執行的臨時解決方案

### 方案 A: 手動關閉 Pitstop 視窗
```
簡單但治標不治本：
1. 當 Pitstop 視窗自動出現時
2. 直接關閉該視窗
3. 繼續使用 RPM 分析
```

### 方案 B: 停用參數同步（如果 RPM 視窗有此選項）
```
在 RPM 視窗中：
1. 尋找「同步設定」或「參數連動」選項
2. 取消勾選「與主視窗同步」
3. 這樣切換主視窗參數時不會影響 RPM
```

### 方案 C: 修改 EXE (需要重新打包)
```powershell
# 1. 應用方案 2 (過濾 Pitstop)
# 修改 f1t_gui_main.py line ~5870

# 2. 重新打包
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
pyinstaller F1T_GUI.spec --clean

# 3. 測試新 EXE
.\dist\F1T_GUI\F1T_GUI.exe
```

---

## 🎯 下一步行動

### 優先級 1 (立即執行)
- [ ] 用戶提供重現步驟和日誌
- [ ] 執行診斷步驟獲取調用堆疊
- [ ] 確認問題觸發的精確位置

### 優先級 2 (確認後修復)
- [ ] 應用對應的修復方案 (1-4)
- [ ] 執行測試計劃驗證修復
- [ ] 重新打包 EXE

### 優先級 3 (長期改進)
- [ ] 添加模組創建白名單機制
- [ ] 重構車手列表載入邏輯（不依賴 Pitstop JSON）
- [ ] 添加單元測試防止回歸

---

**診斷工程師**: GitHub Copilot  
**報告日期**: 2025-10-06  
**狀態**: 待用戶提供更多信息以精確定位問題

---

## 📎 附錄：快速檢查清單

```powershell
# 複製貼上執行以獲取完整診斷信息
Write-Host "=== Pitstop 自動創建診斷 ===" -ForegroundColor Cyan
Write-Host "`n1. 檢查 Pitstop 模組工廠調用:" -ForegroundColor Yellow
Select-String -Path "dist\logs\f1_gui_*.log" -Pattern "MODULE_FACTORY.*進站" -Context 3,3 | Select-Object -Last 10

Write-Host "`n2. 檢查車手列表載入:" -ForegroundColor Yellow
Select-String -Path "dist\logs\f1_gui_*.log" -Pattern "DRIVERS.*進站" -Context 2,2 | Select-Object -Last 10

Write-Host "`n3. 檢查 LAP_CONTROL 追蹤:" -ForegroundColor Yellow
Select-String -Path "dist\logs\f1_gui_*.log" -Pattern "LAP_CONTROL.*進站" -Context 1,1 | Select-Object -Last 10

Write-Host "`n4. 檢查參數同步通知:" -ForegroundColor Yellow
Select-String -Path "dist\logs\f1_gui_*.log" -Pattern "SYNC.*進站|NOTIFICATION.*進站" -Context 1,1 | Select-Object -Last 10

Write-Host "`n=== 診斷完成 ===" -ForegroundColor Green
```
