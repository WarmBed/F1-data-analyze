# 🛞 車手進站詳細記錄 GUI 模組設計文件

**功能編號**: 功能5  
**開發日期**: 2025年8月31日  
**負責開發**: F1T GUI開發團隊  
**優先級**: 高  
**狀態**: 📋 **設計階段**  
**最後更新**: 2025年8月31日  
**基於**: F1_Analysis_Main_Menu-f5 5. 🛞 車手進站詳細記錄 (Driver Detailed Pitstop Records)  

## 📋 開發狀態總覽

### 🎯 開發目標
- [ ] **車手進站詳細記錄GUI** - `DriverDetailedPitstopWidget` 類實現
- [ ] **集成到進站分析模組** - 作為分頁3功能整合到現有 `PitstopAnalysisModule`
- [ ] **JSON數據管理** - 擴展 `PitstopDataManager` 支援車手詳細進站數據
- [ ] **車手詳細記錄表格** - 顯示每位車手的完整進站歷程
- [ ] **參數同步** - 與主視窗的年份、賽事、賽段同步
- [ ] **JSON 檔案讀取** - `driver_detailed_pitstop_records_{year}_{race}.json`
- [ ] **CLI自動生成** - 找不到JSON時自動呼叫CLI生成車手詳細數據
- [ ] **GUI自動更新** - CLI執行完成後自動刷新顯示新數據
- [ ] **多車手視圖** - 支援所有車手或特定車手的詳細記錄顯示
- [ ] **錯誤處理** - 完整的異常處理和使用者回饋

### ✅ 已有基礎架構
- [x] **進站分析模組** - `PitstopAnalysisModule` 已完成
- [x] **MDI 子視窗** - 完整的 GUI 模組工廠支援
- [x] **數據管理器** - `PitstopDataManager` 基礎實現
- [x] **參數同步** - 與主視窗同步機制已建立
- [x] **分頁架構** - 標籤頁設計已預留分頁3
- [x] **CLI功能** - 功能5已完整實現並可正常運作
- [x] **JSON格式** - 數據結構已確定且穩定

## 📋 開發核心原則遵循

### ✅ 核心原則檢查清單
- [x] **模組化設計** - 基於現有進站分析模組架構擴展
- [x] **數據優先** - 優先使用JSON緩存，與車手/車隊進站分析一致
- [x] **用戶體驗** - MDI子視窗分頁設計，無縫整合現有UI
- [x] **錯誤處理** - 複用現有異常處理和狀態反饋機制
- [x] **性能考量** - 背景執行CLI分析，避免GUI凍結
- [x] **代碼複用** - 最大化重用現有PitstopAnalysisModule架構
- [x] **一致性** - 遵循車手/車隊進站分析的GUI風格和命名規範
- [x] **智能化** - 自動檢測和生成缺失數據，提升用戶體驗
- [x] **響應性** - CLI執行完成後自動更新GUI，無需手動操作

### 🎯 具體開發目標
1. 在進站分析MDI子視窗的分頁3中顯示車手進站詳細記錄
2. 支援車手詳細JSON數據讀取和CLI後端分析調用（功能5）
3. 與現有參數同步機制完全整合（年份、賽事、賽段）
4. 提供每位車手的完整進站歷程（進站次數、圈數、時間、車隊）
5. 支援智能數據生成、自動GUI更新等進階功能

## 🏗️ 技術架構設計

### 📂 整合到現有模組結構
```
modules/
├── pitstop_analysis_mdi.py          # 現有進站分析模組 (擴展)
│   ├── PitstopAnalysisModule        # 主模組類 (已實現) ✅
│   │   ├── 分頁1: 車手排行榜         # 分頁索引0 ✅
│   │   ├── 分頁2: 車隊排行榜         # 分頁索引1 ✅
│   │   └── 分頁3: 車手詳細記錄       # 分頁索引2 🆕
│   ├── PitstopDataManager          # 數據管理器 (已擴展支援車隊數據) ✅
│   │   ├── loadDriverDetailedData() # 車手詳細JSON載入 🆕
│   │   ├── _find_driver_detailed_file() # 車手詳細檔案搜尋 🆕
│   │   ├── _generate_driver_detailed_via_cli() # CLI自動生成 🆕
│   │   └── driver_detailed_loaded信號 # 車手詳細數據載入完成信號 🆕
│   ├── PitstopRankingWidget        # 車手排行榜控件 (已實現) ✅
│   ├── TeamPitstopRankingWidget    # 車隊排行榜控件 (已實現) ✅
│   └── DriverDetailedPitstopWidget # 車手詳細記錄控件 (新增) 🆕
│       ├── setup_detailed_table()  # 詳細進站表格設置 🆕
│       ├── update_detailed_data()  # 詳細數據更新邏輯 🆕
│       ├── populate_detailed_table() # 詳細表格填充 🆕
│       └── format_detailed_display() # 詳細記錄格式化 🆕
└── interfaces.py                   # 模組介面定義 (已存在) ✅

f1t_gui_main.py                     # 主 GUI 程式 (無需修改) ✅
├── ModuleFactory                   # 模組工廠 (已註冊進站分析) ✅
├── CustomMdiArea                   # 自定義 MDI 區域 ✅
├── MainWindowParameterProvider     # 參數提供者 ✅
└── GlobalSignalManager            # 全域信號管理 ✅
```

### 🔄 數據流架構圖
```
┌─────────────────┐    參數同步     ┌─────────────────────┐
│   MainWindow    │ ──────────────► │ PitstopAnalysisModule│
│ - year_combo    │  (已實現的      │ - current_year      │
│ - race_combo    │   ParameterProvider) - current_race  │
│ - session_combo │                 │ - current_session   │
└─────────────────┘                 └─────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
             車手排行榜 ✅               車隊排行榜 ✅           🆕 車手詳細記錄
                    ▼                         ▼                         ▼
          ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
          │PitstopDataManager│       │PitstopDataManager│       │PitstopDataManager│
          │(已實現)          │       │(已擴展車隊支援)  │       │(新增詳細支援)    │
          │- _find_pitstop_ │       │- _find_team_    │       │- _find_driver_  │
          │  data_file()    │       │  pitstop_file() │       │  detailed_file()│
          └─────────────────┘       └─────────────────┘       └─────────────────┘
                    │                         │                         │
           data_loaded信號 ✅        team_data_loaded信號 ✅   driver_detailed_loaded信號 🆕
                    ▼                         ▼                         ▼
          ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
          │PitstopRanking   │       │TeamPitstop      │       │🆕DriverDetailed  │
          │Widget (已實現)   │       │RankingWidget    │       │PitstopWidget     │
          │- 分頁1: 車手排行 │       │(已實現)         │       │(新增)            │
          │                │       │- 分頁2: 車隊排行 │       │- 分頁3: 詳細記錄 │
          └─────────────────┘       └─────────────────┘       └─────────────────┘
```

### 🚀 智能CLI觸發與GUI自動更新流程
```
用戶切換參數 → 檢查車手詳細JSON → 檔案不存在
                    ↓
               觸發CLI功能5 → python f1_analysis_modular_main.py -f 5
                    ↓
               背景執行生成 → driver_detailed_pitstop_records_{year}_{race}.json
                    ↓
               CLI執行完成 → 發送driver_detailed_reload_requested信號
                    ↓
               主線程處理 → QTimer.singleShot(2000) 延遲刷新
                    ↓
              自動載入JSON → 車手詳細記錄表格更新 ✅
```

### 🎯 核心類別設計

#### 1. `DriverDetailedPitstopWidget` 類 🆕
**檔案位置**: `modules/pitstop_analysis_mdi.py`

```python
class DriverDetailedPitstopWidget(QWidget):
    """
    車手進站詳細記錄視窗組件
    實現每位車手完整進站歷程展示和管理功能
    """
    
    def __init__(self, data_manager):
        # 初始化UI組件
        self.data_manager = data_manager
        self.detailed_data = {}
        self.setupUI()
        
    def setupUI(self):
        # 建立車手詳細記錄表格
        # 支援多車手滾動視圖
        
    def update_detailed_records(self, year, race, session):
        # 更新車手詳細記錄數據
        # 呼叫數據管理器載入詳細JSON
        
    def display_detailed_data(self, detailed_data):
        # 顯示車手詳細記錄
        # 按車手分組，按進站次序排列
```

#### 2. `PitstopDataManager` 詳細記錄支援擴展 🆕
**檔案位置**: `modules/pitstop_analysis_mdi.py`

新增車手詳細支援方法：
```python
def loadDriverDetailedData(self, year, race, session):
    """載入車手進站詳細數據 - JSON優先+CLI後備"""
    
def checkAndGenerateDriverDetailedData(self, year, race, session):
    """檢查並自動生成缺失的車手詳細JSON檔案"""
    
def executeDriverDetailedCLI(self, year, race, session):
    """執行CLI功能5生成車手進站詳細數據"""
```

### 📊 車手進站詳細記錄數據結構分析

#### 車手詳細進站 JSON 檔案格式
**檔案命名**: `driver_detailed_pitstop_records_{year}_{race}.json`  
**範例檔案**: `driver_detailed_pitstop_records_2025_Belgian_Grand_Prix.json`

```json
{
  "function_id": 5,
  "function_name": "Driver Detailed Pitstop Records",
  "analysis_type": "driver_detailed_pitstop_records",
  "session_info": {
    "event_name": "Belgian Grand Prix",
    "circuit_name": "Spa-Francorchamps",
    "session_type": "Race",
    "year": 2025
  },
  "timestamp": "2025-08-31T01:21:09.746649",
  "data": {
    "VER": [
      {
        "pitstop_number": 1,
        "lap_number": 16,
        "pit_duration": 23.1,
        "session_time": "Unknown",
        "team": "Red Bull Racing"
      },
      {
        "pitstop_number": 2,
        "lap_number": 34,
        "pit_duration": 23.2,
        "session_time": "Unknown",
        "team": "Red Bull Racing"
      }
    ],
    "LEC": [
      {
        "pitstop_number": 1,
        "lap_number": 26,
        "pit_duration": 23.2,
        "session_time": "Unknown",
        "team": "Ferrari"
      }
    ]
  }
}
```

#### 關鍵欄位說明

| JSON欄位 | 說明 | 顯示格式 |
|----------|------|----------|
| `車手代碼` | VER, LEC等車手簡稱 | 字串 |
| `pitstop_number` | 進站順序號 | 第1次、第2次... |
| `lap_number` | 進站圈數 | 整數 |
| `pit_duration` | 進站時間 | SS.0秒格式 |
| `team` | 車隊名稱 | 完整車隊名稱 |

## 📊 UI設計規格

### 🛞 車手進站詳細記錄子視窗 - 分頁3設計
```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│ 🏆 進站分析 - 2025 Belgian Race                                                  ❌關閉     │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ 🏆 最快進站 │🏁 車隊統計│🛞 詳細記錄│                                                     │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│                                🛞 車手進站詳細記錄                                          │
│                                                                                           │
│ 🏎️ VER (Red Bull Racing) - 共 2 次進站:                                                   │
│ ┌──────────┬──────┬──────────┬──────────────┐                                             │
│ │ 進站次數 │ 圈數 │ 進站時間 │     備註     │                                             │
│ ├──────────┼──────┼──────────┼──────────────┤                                             │
│ │  第1次   │  16  │  23.1秒  │   正常進站   │                                             │
│ │  第2次   │  34  │  23.2秒  │   正常進站   │                                             │
│ └──────────┴──────┴──────────┴──────────────┘                                             │
│                                                                                           │
│ 🏎️ LEC (Ferrari) - 共 1 次進站:                                                           │
│ ┌──────────┬──────┬──────────┬──────────────┐                                             │
│ │ 進站次數 │ 圈數 │ 進站時間 │     備註     │                                             │
│ ├──────────┼──────┼──────────┼──────────────┤                                             │
│ │  第1次   │  26  │  23.2秒  │   正常進站   │                                             │
│ └──────────┴──────┴──────────┴──────────────┘                                             │
│                                                                                           │
│ 🏎️ HAM (Mercedes) - 共 2 次進站:                                                          │
│ ┌──────────┬──────┬──────────┬──────────────┐                                             │
│ │ 進站次數 │ 圈數 │ 進站時間 │     備註     │                                             │
│ ├──────────┼──────┼──────────┼──────────────┤                                             │
│ │  第1次   │  23  │  23.3秒  │   正常進站   │                                             │
│ │  第2次   │  39  │  23.9秒  │   正常進站   │                                             │
│ └──────────┴──────┴──────────┴──────────────┘                                             │
│                                                                                           │
│ [繼續顯示其他車手...]                                                                      │
│                                                                                           │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ 📊 共 18 位車手 │ 📄 來源: JSON │ ⏱️ 更新: 2025-08-31 14:35:20 │ 🤖 智能生成: 開啟   │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

### 🔍 車手詳細記錄表格結構

#### 每車手獨立表格設計
- **車手標題列**: 🏎️ [車手代碼] ([車隊名稱]) - 共 X 次進站
- **詳細記錄表格**: 4欄標準格式
  - 進站次數 (第1次、第2次...)
  - 圈數 (整數)
  - 進站時間 (SS.0格式)
  - 備註 (正常進站/異常)

#### 表格特點
- ✅ **滾動視圖**: 支援多車手垂直滾動
- ✅ **分組顯示**: 按車手分組，每車手一個獨立表格
- ✅ **統一格式**: 時間格式統一為SS.0（秒.十分位）
- ✅ **智能排序**: 車手按字母順序，進站按時間順序
- ✅ **即時更新**: 支援CLI生成後自動刷新

## 🔧 詳細實現規格

### 1. DriverDetailedPitstopWidget 類別實現

#### 類別結構
```python
class DriverDetailedPitstopWidget(QWidget):
    """車手進站詳細記錄 Widget - 顯示每位車手完整進站歷程"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.detailed_data = {}          # 車手詳細記錄數據
        self.current_data = {}           # 儲存當前數據，用於分析功能
        self.setup_ui()
        
    def setup_ui(self):
        """設置使用者界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 隱藏工具列，保持與車隊排行榜一致的設計
        
        # 主要滾動區域
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
    def setup_driver_tables(self):
        """為每位車手設置獨立的進站記錄表格"""
        # 清理現有表格
        # 為每位車手創建標題和表格
        # 設置統一的4欄格式
        
    def update_detailed_data(self, data: Dict[str, Any]):
        """更新車手詳細記錄數據"""
        # 驗證數據格式
        # 按車手分組處理數據
        # 延遲更新UI確保數據準備完成
        
    def populate_driver_tables(self):
        """填充所有車手的詳細記錄表格"""
        # 遍歷所有車手數據
        # 為每位車手創建獨立表格
        # 填充進站詳細記錄
        
    def format_pitstop_display(self, pitstop_data):
        """格式化進站記錄顯示"""
        # 進站次數格式化
        # 時間格式化為SS.0
        # 備註信息生成
```

### 2. PitstopDataManager 車手詳細記錄支援

#### 關鍵新增方法
```python
class PitstopDataManager(QObject):
    # 新增車手詳細相關信號
    driver_detailed_loaded = pyqtSignal(dict)        # 車手詳細數據載入完成
    driver_detailed_reload_requested = pyqtSignal()  # 車手詳細數據重載請求
    
    def loadDriverDetailedData(self, year: str, race: str, session: str) -> bool:
        """載入車手進站詳細數據 - 支援JSON優先+CLI後備"""
        # 1. 檢查現有JSON檔案
        json_file = self._find_driver_detailed_file(year, race, session)
        
        if json_file:
            # 載入現有JSON
            QTimer.singleShot(10, lambda: self._load_driver_detailed_json(json_file))
            return True
        else:
            # 自動觸發CLI生成
            print(f"[AUTO_GEN] 找不到車手詳細JSON，觸發CLI自動生成")
            return self._generate_driver_detailed_via_cli(year, race, session)
    
    def _find_driver_detailed_file(self, year: str, race: str, session: str) -> Optional[str]:
        """搜尋車手進站詳細數據檔案（支援多格式匹配）"""
        search_dirs = ["json", "json_exports", "cache"]
        
        # 賽事名稱映射
        race_full_names = {
            "Japan": "Japanese_Grand_Prix",
            "China": "Chinese_Grand_Prix", 
            "Belgium": "Belgian_Grand_Prix",
            "Miami": "Miami_Grand_Prix",
            # ... 其他賽事映射
        }
        
        race_full_name = race_full_names.get(race, f"{race.replace(' ', '_')}_Grand_Prix")
        
        patterns = [
            f"driver_detailed_pitstop_records_{year}_{race_full_name}.json",
            f"driver_detailed_pitstops_{year}_{race_full_name}.json",
            f"driver_detailed_pitstop_records_{year}_{race.replace(' ', '_')}.json",
        ]
        
        # 搜尋多個目錄中的精確匹配
        for search_dir in search_dirs:
            for pattern in patterns:
                search_path = os.path.join(search_dir, pattern)
                if os.path.exists(search_path):
                    return search_path
        return None
    
    def _generate_driver_detailed_via_cli(self, year: str, race: str, session: str) -> bool:
        """透過CLI生成車手進站詳細數據（後台執行）"""
        command = [
            "python", "f1_analysis_modular_main.py",
            "-f", "5",  # 功能5: 車手進站詳細記錄
            "-y", str(year), "-r", race, "-s", session
        ]
        
        def run_driver_detailed_cli():
            process = subprocess.Popen(command, ...)
            if process.returncode == 0:
                # 使用信號機制，在主執行緒中處理
                self.driver_detailed_reload_requested.emit()
                
        # 在後台執行車手詳細 CLI
        thread = threading.Thread(target=run_driver_detailed_cli, daemon=True)
        thread.start()
        return True
```

### 3. 主模組整合邏輯

#### PitstopAnalysisModule 車手詳細記錄整合
```python
class PitstopAnalysisModule(QWidget):
    def __init__(self, ...):
        # 添加車手詳細記錄分頁
        self.detailed_widget = DriverDetailedPitstopWidget()
        self.tab_widget.addTab(self.detailed_widget, "🛞 詳細記錄")
        
        # 連接車手詳細數據信號
        self.data_manager.driver_detailed_loaded.connect(self.detailed_widget.update_detailed_data)
        self.data_manager.driver_detailed_reload_requested.connect(self.reload_detailed_data)
        
    def onParametersChanged(self, year, race, session):
        """參數變更時的處理邏輯"""
        # 更新車手排行榜
        if self.tab_widget.currentIndex() == 0:
            self.data_manager.loadPitstopData(year, race, session)
        
        # 更新車隊排行榜
        elif self.tab_widget.currentIndex() == 1:
            self.data_manager.loadTeamPitstopData(year, race, session)
        
        # 🆕 更新車手詳細記錄
        elif self.tab_widget.currentIndex() == 2:
            self.data_manager.loadDriverDetailedData(year, race, session)
    
    def reload_detailed_data(self):
        """重新載入車手詳細數據（CLI完成後調用）"""
        # 延遲2秒後重新載入，確保檔案生成完成
        QTimer.singleShot(2000, lambda: self.data_manager.loadDriverDetailedData(
            self.current_year, self.current_race, self.current_session))
```

## 🧪 開發驗收標準

### ✅ 功能驗收
- [ ] 車手詳細記錄JSON檔案正確載入和解析
- [ ] CLI自動生成功能5正常工作（年份修正後）
- [ ] GUI自動更新機制運作正常
- [ ] 多車手滾動視圖顯示正確
- [ ] 每車手獨立表格格式正確
- [ ] 時間格式化為SS.0正確顯示
- [ ] 參數同步機制正常工作

### ✅ 技術實施驗收
- [ ] 代碼符合現有模組架構模式
- [ ] 信號槽機制正確實現
- [ ] 數據載入邏輯高效穩定
- [ ] UI 組件正確整合到 MDI 架構
- [ ] 無記憶體洩漏和性能問題
- [ ] 完整的錯誤處理和日誌記錄
- [ ] 符合 F1T GUI 編碼標準

### ✅ 使用者體驗驗收
- [ ] UI 風格與現有模組一致
- [ ] 滾動和查看操作流暢
- [ ] 載入時間合理 (< 5秒)
- [ ] 錯誤訊息清晰明確
- [ ] 支援完整的參數同步

---

**🚀 開發準備就緒**: 此設計完全基於現有的進站分析模組架構和已成功實現的車隊排行榜模組，可直接開始實施開發。所有核心組件都複用現有的設計模式和實現標準，確保與現有系統的無縫整合。

**CLI驗證**: 功能5已完整實現並正常運作，JSON數據格式穩定，為GUI開發提供了可靠的數據基礎。

**最終確認**: ✅ 車手進站詳細記錄GUI模組設計已完全對齊現有進站分析模組架構，具備智能數據管理和自動更新機制，可以開始實施開發。
