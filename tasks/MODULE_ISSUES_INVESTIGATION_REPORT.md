# F1T 模組問題調查報告
**Module Issues Investigation Report**

**調查日期**: 2025-10-02  
**調查人員**: GitHub Copilot AI Assistant  
**版本**: 1.0.0

---

## 📋 問題摘要 (Issue Summary)

本次調查針對使用者報告的兩個關鍵問題：

1. ❌ **Track Analysis 模組找不到問題**
2. ⚠️ **Lap Time Box Plot 模組的最小化限制與其他模組不一致問題**

---

## 🔍 問題 1: Track Analysis 模組找不到

### 問題描述

使用者回報無法找到 Track Analysis（賽道分析）模組。

### 調查結果

**✅ 模組實際存在且可正常導入**

#### 檔案結構驗證

```
modules/gui/track_analysis/
├── __init__.py                      ✅ 存在
├── track_analysis_module.py         ✅ 存在
├── track_data_loader.py             ✅ 存在  
├── track_data_processor.py          ✅ 存在
├── track_map_widget.py              ✅ 存在
└── __pycache__/                     ✅ 已編譯
```

#### 導入測試結果

```powershell
PS> python -c "from modules.gui.track_analysis import TrackAnalysisModule; print('TrackAnalysisModule 可用')"
TrackAnalysisModule 可用  ✅ 成功
```

#### GUI 主程式中的整合狀態

**檔案**: `f1t_gui_main.py`

**導入位置** (Line 7495-7500):
```python
try:
    from modules.gui.track_analysis import TrackAnalysisModule
    TRACK_ANALYSIS_AVAILABLE = True
    print("[OK] [MODULE_IMPORT] TrackAnalysisModule 載入完成")
except ImportError as e:
    TRACK_ANALYSIS_AVAILABLE = False
    print(f"警告: TrackAnalysisModule 不可用: {e}")
```
✅ **狀態**: 正常導入，`TRACK_ANALYSIS_AVAILABLE = True`

**使用位置** (Line 7949-7980):
```python
elif "賽道" in function_name:
    # 使用新的 TrackAnalysisModule 而不是舊的 TrackMapWidget
    try:
        from modules.gui.track_analysis import TrackAnalysisModule
        
        # 創建賽道分析模組實例
        params = self.get_current_parameters()
        track_module = TrackAnalysisModule(
            year=params['year'], 
            race=params['race'], 
            session=params['session']
        )
        
        print(f"[OK] [NEW] 使用新版 TrackAnalysisModule: {params['year']} {params['race']} {params['session']}")
        return track_module
            
    except ImportError as e:
        print(f"[ERROR] [ERROR] TrackAnalysisModule 導入失敗: {e}")
```
✅ **狀態**: 正常使用

**菜單註冊** (Line 4941, 5897):
```python
# 分析菜單中
analysis_menu.addAction(tr('track_analysis', '[FINISH] Track Analysis'), self.open_track_analysis_window)

# 功能樹視圖中
QTreeWidgetItem(basic_group, [tr("track_analysis", "Track Analysis")])
```
✅ **狀態**: 已註冊至菜單

#### 國際化支援狀態

**檔案**: `core/gui_i18n.py`

```python
'track_analysis': {
    'zh': '賽道分析', 
    'en': 'Track Analysis', 
    'ja': 'トラック分析'
}
```
✅ **狀態**: 完整支援中英日三語

### 問題根因分析

經過完整調查，**Track Analysis 模組並無技術性問題**。可能的原因包括：

#### A. 使用者介面訪問問題

**可能情況 1**: 使用者從錯誤的入口尋找模組
- ❌ 錯誤: 在「分析模組」標籤中尋找
- ✅ 正確: 在主菜單「分析」→「[FINISH] Track Analysis」中點擊

**可能情況 2**: 模組名稱混淆
- 舊名稱: "Track Map" / "賽道軌跡"
- 新名稱: "Track Analysis" / "賽道分析"

**可能情況 3**: 未出現在快速啟動區
- Track Analysis 可能未加入「分析模組」標籤的快速功能卡片
- 但可從主菜單正常訪問

#### B. 運行時環境問題

**可能情況 4**: Python 緩存問題
```powershell
# 清理 __pycache__ 後可能需要重新導入
Remove-Item -Path "modules\gui\track_analysis\__pycache__\*" -Recurse -Force
```

**可能情況 5**: 依賴模組問題
- TrackAnalysisModule 依賴 `TrackMapWidget` 和 `TrackDataProcessor`
- 如果子模組有錯誤，可能導致初始化失敗

### 解決方案

#### 立即可用的訪問方式

1. **從主菜單訪問** (推薦):
   ```
   主菜單 → 分析 (Analysis) → [FINISH] Track Analysis
   ```

2. **從功能樹訪問**:
   ```
   功能樹視圖 → 基礎分析 (Basic Analysis) → Track Analysis
   ```

3. **檢查控制台輸出**:
   ```
   啟動 GUI 時檢查是否出現:
   [OK] [MODULE_IMPORT] TrackAnalysisModule 載入完成
   ```

#### 需要調查的點

如果使用者仍然無法找到模組，建議檢查：

1. ✅ **檢查 Python 版本**:
   ```powershell
   python --version  # 應為 Python 3.12+
   ```

2. ✅ **檢查依賴安裝**:
   ```powershell
   pip list | Select-String "PyQt5|matplotlib|numpy"
   ```

3. ✅ **查看 GUI 啟動日誌**:
   ```powershell
   python f1t_gui_main.py 2>&1 | Select-String "TrackAnalysis"
   ```

4. ✅ **測試直接導入**:
   ```powershell
   python -c "from modules.gui.track_analysis import TrackAnalysisModule; print('OK')"
   ```

### 改進建議

為了避免未來使用者遇到類似困擾，建議：

#### 1. 增強可見性

```python
# 在「分析模組」標籤中添加 Track Analysis 快速卡片
def create_analysis_modules_tab(self):
    # ... existing code ...
    
    # 添加賽道分析卡片
    track_card = self.create_function_card(
        "🗺️ Track Analysis",
        "賽道分析",
        "分析賽道位置數據與車手軌跡"
    )
    track_card.clicked.connect(self.open_track_analysis_window)
    grid_layout.addWidget(track_card, row, col)
```

#### 2. 統一命名

將所有相關命名統一為 "Track Analysis"：
- ✅ 模組名稱: `TrackAnalysisModule`
- ✅ 菜單項目: "Track Analysis"
- ✅ 視窗標題: "Track Analysis"
- ❌ 避免使用: "Track Map", "賽道軌跡" 等舊名稱

#### 3. 添加說明工具提示

```python
analysis_menu.addAction(
    tr('track_analysis', '[FINISH] Track Analysis')
).setToolTip(
    "分析賽道位置數據、車手軌跡與賽道地圖視覺化"
)
```

---

## ⚠️ 問題 2: Lap Time Box Plot 最小化限制不一致

### 問題描述

使用者發現 Lap Time Box Plot（圈速箱型圖）模組的最小化限制與其他模組不一致。

### 調查結果

**✅ 問題確認：確實存在不一致的最小尺寸設定**

#### 各模組最小尺寸對比

| 模組名稱 | 圖表組件檔案 | 最小寬度 | 最小高度 | 狀態 |
|---------|------------|---------|---------|------|
| **Rain Analysis** | `rain_analysis_chart_widget.py` | 200px | 100px | ✅ 標準 |
| **Tire Analysis** | `tire_analysis_chart_widget.py` | 200px | 100px | ✅ 標準 |
| **Driver Lap Analysis** | `driverlap_analysis_chart_widget.py` | 200px | 100px | ✅ 標準 |
| **Lap Time Box Plot** | `lap_box_plot_chart_widget.py` | **800px** | **500px** | ❌ **異常** |

#### 問題代碼位置

**檔案**: `modules/gui/lap_box_plot_analysis/lap_box_plot_chart_widget.py`  
**行號**: Line 91

```python
# 設置最小尺寸
self.setMinimumSize(800, 500)  # ❌ 不一致：應為 200x100
```

#### 對比：其他模組的標準設定

**Rain Analysis** (`rain_analysis_chart_widget.py`, Line 172):
```python
self.setMinimumSize(200, 100)  # ✅ 標準設定
```

**Tire Analysis** (`tire_analysis_chart_widget.py`, Line 99):
```python
self.setMinimumSize(200, 100)  # ✅ 標準設定
```

**Driver Lap Analysis** (`driverlap_analysis_chart_widget.py`, Line 69):
```python
self.setMinimumSize(200, 100)  # 調整為與 Tire Analysis 一致的最小尺寸 ✅
```

### 問題影響分析

#### 1. **使用者體驗影響**

**異常行為**:
- ❌ Lap Time Box Plot 視窗**無法縮小到與其他模組相同的尺寸**
- ❌ 最小寬度 800px 限制導致無法在小螢幕上靈活排列
- ❌ 最小高度 500px 限制導致無法並排顯示多個分析視窗

**正常模組行為** (200x100):
- ✅ 可以自由縮小視窗以節省空間
- ✅ 可以在螢幕上並排顯示多個分析視窗
- ✅ 適應各種螢幕尺寸和解析度

#### 2. **MDI 視窗管理影響**

**視窗排列限制**:
```
┌─────────────────────────────────────────────────────┐
│ MDI Area (1920x1080)                                 │
│                                                       │
│  ┌─ Rain (可縮小到 200x100) ─┐  ✅ 靈活              │
│  │                            │                       │
│  └────────────────────────────┘                       │
│                                                       │
│  ┌─ Lap Box Plot (最小 800x500) ────────────────┐   │
│  │                                                │   │
│  │                                                │   │
│  │          ❌ 無法縮小                            │   │
│  │                                                │   │
│  │                                                │   │
│  └────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────┘
```

#### 3. **架構一致性影響**

**違反通用模組標準**:
- ❌ 所有基於 `UniversalAnalysisMDI` 的模組應遵循相同的視窗規範
- ❌ 破壞了「通用架構」的一致性原則
- ❌ 增加維護成本和使用者困惑

### 根因分析

#### 可能原因

**A. 開發階段遺留問題**:
- Lap Time Box Plot 是較新的模組
- 開發時可能尚未建立統一的最小尺寸標準
- 開發者基於圖表內容複雜度設定了較大的最小尺寸

**B. 特殊需求考量**:
- 箱型圖可能包含多個車手數據（最多 20 位）
- 開發者可能認為需要較大的空間以確保可讀性
- 但這與其他同樣複雜的模組（如 Tire Analysis）不一致

**C. QPainter 重寫時的疏忽**:
根據專案歷史文件 `LAP_BOXPLOT_QPAINTER_REWRITE_REPORT.md`，Lap Time Box Plot 曾進行 QPainter 重寫。在重寫過程中可能未考慮最小尺寸的統一性。

### 解決方案

#### 修復計劃

**目標**: 將 Lap Time Box Plot 的最小尺寸調整為與其他模組一致的 **200x100**

#### 步驟 1: 修改圖表組件最小尺寸

**檔案**: `modules/gui/lap_box_plot_analysis/lap_box_plot_chart_widget.py`  
**行號**: Line 91

**修改前**:
```python
# 設置最小尺寸
self.setMinimumSize(800, 500)
```

**修改後**:
```python
# 設置最小尺寸（與其他通用模組一致）
self.setMinimumSize(200, 100)  # 統一為 200x100，提供更高的佈局靈活性
```

#### 步驟 2: 驗證其他相關檔案

檢查是否有其他檔案設定了過大的最小尺寸：

**檔案**: `modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_chart_widget.py`  
**行號**: Line 172

```python
self.setMinimumSize(200, 100)  # ✅ 已正確設定
```

**注意**: 專案中存在兩個圖表組件檔案：
1. `lap_box_plot_chart_widget.py` - **主要使用的 QPainter 版本** ❌
2. `lap_box_plot_analysis_chart_widget.py` - 備用的 matplotlib 版本 ✅

需要修改的是 **QPainter 版本**。

#### 步驟 3: 確保預設視窗大小合理

**檔案**: `f1t_gui_main.py`  
**行號**: Line 8660

```python
# 設置視窗大小（初始大小，可縮放）
sub_window.resize(1400, 800)  # ✅ 預設大小保持不變
```

**說明**:
- **預設大小 (1400x800)**: 確保初次打開時有足夠空間顯示完整圖表 ✅
- **最小尺寸 (200x100)**: 允許使用者根據需求縮小視窗 ✅
- 兩者互不衝突，可以並存

#### 步驟 4: 測試縮放行為

修改後需要測試：

1. ✅ **視窗可以縮小到 200x100**
   - 縮小後圖表應自動調整縮放比例
   - 文字標籤可能重疊，但不應導致崩潰

2. ✅ **視窗可以自由放大**
   - 放大時圖表應正確重繪
   - 所有元素應保持可見且清晰

3. ✅ **與其他模組並排顯示**
   - 可以同時顯示多個分析視窗
   - 視窗可以靈活排列組合

### 預期效果

#### 修復前

```
❌ Lap Time Box Plot 最小尺寸: 800x500
   - 無法與其他模組靈活排列
   - 佔用過多 MDI 空間
   - 架構不一致
```

#### 修復後

```
✅ Lap Time Box Plot 最小尺寸: 200x100
   - 與所有其他模組保持一致
   - 可靈活調整視窗大小
   - 符合通用架構標準
```

### 架構改進建議

為了避免未來出現類似問題，建議：

#### 1. 在基礎類別中定義標準常數

**檔案**: `modules/gui/base/universal_analysis_mdi_base.py`

```python
class UniversalAnalysisMDI(QObject):
    """通用分析 MDI 基礎類別"""
    
    # 🎯 統一的視窗尺寸標準
    DEFAULT_WINDOW_SIZE = (1400, 800)      # 預設視窗大小
    MINIMUM_WINDOW_SIZE = (200, 100)       # 最小視窗大小（統一標準）
    CHART_MINIMUM_SIZE = (200, 100)        # 圖表組件最小尺寸
    
    def __init__(self, main_window=None):
        super().__init__()
        # ... existing code ...
```

#### 2. 在圖表基礎類別中強制執行

```python
class UniversalChartWidget(QWidget):
    """通用圖表組件基礎類別"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 🎯 強制設定統一的最小尺寸
        self.setMinimumSize(*UniversalAnalysisMDI.CHART_MINIMUM_SIZE)
```

#### 3. 添加尺寸標準檢查工具

```python
def validate_module_window_sizes():
    """
    驗證所有分析模組的視窗尺寸設定是否符合標準
    
    檢查項目:
    1. 圖表組件最小尺寸是否為 200x100
    2. MDI 視窗預設尺寸是否合理
    3. 尺寸設定是否一致
    """
    import inspect
    from modules.gui.base import UniversalAnalysisMDI
    
    # 查找所有繼承 UniversalAnalysisMDI 的模組
    # 檢查每個模組的圖表組件最小尺寸
    # 報告不符合標準的模組
    pass
```

#### 4. 更新開發文檔

在 `.github/copilot-instructions.md` 中添加：

```markdown
### 視窗尺寸標準

所有基於 `UniversalAnalysisMDI` 的分析模組必須遵循以下尺寸規範：

**圖表組件最小尺寸** (`ChartWidget`):
- 寬度: **200px**
- 高度: **100px**
- 設定方法: `self.setMinimumSize(200, 100)`

**MDI 視窗預設尺寸**:
- 寬度: **1400px**
- 高度: **800px**
- 設定方法: `sub_window.resize(1400, 800)`

**範例**:
```python
class YourChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ✅ 正確：統一的最小尺寸
        self.setMinimumSize(200, 100)
        
        # ❌ 錯誤：不要使用自訂的過大尺寸
        # self.setMinimumSize(800, 500)
```
```

---

## 📊 修復優先級評估

| 問題 | 嚴重程度 | 影響範圍 | 修復難度 | 優先級 |
|-----|---------|---------|---------|-------|
| **Track Analysis 找不到** | 🟡 中 | 使用者體驗 | 🟢 易 | **P1** |
| **Box Plot 最小尺寸不一致** | 🟠 中高 | 架構一致性 + UX | 🟢 易 | **P0** |

### 優先級說明

**P0 - 立即修復** (Lap Time Box Plot 最小尺寸):
- 影響架構一致性
- 修復簡單（一行代碼）
- 影響使用者體驗
- 違反通用模組標準

**P1 - 短期改進** (Track Analysis 可見性):
- 模組功能正常，僅需改進可見性
- 可通過菜單正常訪問
- 建議添加快速卡片提升可見性

---

## 🔧 實施步驟

### 步驟 1: 修復 Lap Time Box Plot 最小尺寸 (P0)

**時間**: 5 分鐘  
**風險**: 極低

```python
# 檔案: modules/gui/lap_box_plot_analysis/lap_box_plot_chart_widget.py
# 行號: Line 91

# 修改前
self.setMinimumSize(800, 500)

# 修改後
self.setMinimumSize(200, 100)  # 統一為與其他模組一致的最小尺寸
```

**測試**:
```powershell
# 1. 啟動 GUI
python f1t_gui_main.py

# 2. 打開 Lap Time Box Plot
# 3. 嘗試縮小視窗到最小尺寸
# 4. 確認可以縮小到 200x100
# 5. 確認圖表正常顯示且無崩潰
```

### 步驟 2: 改進 Track Analysis 可見性 (P1)

**時間**: 30 分鐘  
**風險**: 低

#### A. 添加快速功能卡片

在「分析模組」標籤中添加 Track Analysis 快速訪問卡片。

#### B. 統一命名

確保所有介面元素使用一致的名稱 "Track Analysis"。

#### C. 添加工具提示

為菜單項目添加詳細的工具提示說明。

---

## 📝 總結

### 調查結論

1. ✅ **Track Analysis 模組完全正常**
   - 檔案結構完整
   - 導入功能正常
   - 已整合至 GUI
   - 可從菜單訪問
   - 建議：改進可見性

2. ❌ **Lap Time Box Plot 最小尺寸確實不一致**
   - 當前: 800x500 (異常)
   - 標準: 200x100 (其他模組)
   - 影響: 使用者體驗 + 架構一致性
   - 修復: 簡單（一行代碼）

### 建議行動

**立即執行** (今日):
- 🔧 修復 Lap Time Box Plot 最小尺寸為 200x100
- ✅ 測試視窗縮放行為
- 📝 更新開發文檔

**短期規劃** (本週):
- 🎯 改進 Track Analysis 可見性
- 📚 統一所有模組命名
- 🔍 添加尺寸標準驗證工具

**長期規劃** (下個版本):
- 🏗️ 在基礎類別中定義尺寸標準常數
- 📖 完善通用模組開發指南
- 🧪 添加自動化尺寸規範測試

---

## 📎 相關檔案清單

### 需要修改的檔案

1. **modules/gui/lap_box_plot_analysis/lap_box_plot_chart_widget.py**
   - Line 91: 修改最小尺寸為 200x100

### 需要參考的檔案

1. **modules/gui/rain_analysis/rain_analysis_chart_widget.py**
   - Line 172: 標準最小尺寸範例

2. **modules/gui/tire_analysis/tire_analysis_chart_widget.py**
   - Line 99: 標準最小尺寸範例

3. **modules/gui/driverLap_analysis/driverlap_analysis_chart_widget.py**
   - Line 69: 標準最小尺寸範例

### 相關文檔

1. **LAP_BOXPLOT_QPAINTER_REWRITE_REPORT.md**
   - QPainter 重寫歷史記錄

2. **.github/copilot-instructions.md**
   - 開發指導文件（需更新）

---

**報告結束**

**下一步**: 等待使用者確認是否立即進行修復

**預計修復時間**: 10 分鐘（包含測試）

**風險評估**: 極低（單行代碼修改，無架構變更）
