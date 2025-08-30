# 🏁 車隊進站時間排行榜 GUI 模組設計文件

**功能編號**: 功能4  
**開發日期**: 2025年8月31日  
**負責開發**: F1T GUI開發團隊  
**優先級**: 高  
**狀態**: ✅ **開發完成，已部署，功能正常**  
**最後更新**: 2025年8月31日 - 修復CLI自動生成與GUI更新機制  
**基於**: F1_Analysis_Main_Menu-f4 4. 🏁 車隊進站時間排行榜 (Team Pitstop Ranking)  

## 📋 開發狀態總覽

### 🎯 開發目標 - 全部完成 ✅
- [x] **車隊進站排行榜** - `TeamPitstopRankingWidget` 類實現 ✅
- [x] **集成到進站分析模組** - 作為分頁2功能整合到現有 `PitstopAnalysisModule` ✅
- [x] **JSON數據管理** - 擴展 `PitstopDataManager` 支援車隊數據 ✅
- [x] **車隊排行榜表格** - 顯示車隊進站統計與排行 ✅
- [x] **參數同步** - 與主視窗的年份、賽事、賽段同步 ✅
- [x] **JSON 檔案讀取** - `team_pitstop_ranking_{year}_{race}_Grand_Prix.json` ✅
- [x] **CLI自動生成** - 找不到JSON時自動呼叫CLI生成車隊數據 ✅
- [x] **GUI自動更新** - CLI執行完成後自動刷新顯示新數據 ✅
- [x] **工具列隱藏** - 簡化UI，隱藏刷新和匯出按鈕 ✅
- [x] **表格優化** - 添加最慢時間欄位，時間格式為SS.0 ✅
- [x] **錯誤處理** - 完整的異常處理和使用者回饋 ✅

### 🚀 新增功能亮點
- [x] **智能CLI觸發** - 自動檢測缺失的車隊JSON檔案並生成
- [x] **無縫GUI更新** - 背景生成完成後自動更新排行榜
- [x] **線程安全處理** - 修復QTimer線程衝突問題
- [x] **統一刷新機制** - 與車手進站採用一致的更新邏輯
- [x] **優化UI設計** - 簡潔的6欄表格，隱藏工具列

### ✅ 已有基礎架構
- [x] **進站分析模組** - `PitstopAnalysisModule` 已完成
- [x] **MDI 子視窗** - 完整的 GUI 模組工廠支援
- [x] **數據管理器** - `PitstopDataManager` 基礎實現
- [x] **參數同步** - 與主視窗同步機制已建立
- [x] **分頁架構** - 標籤頁設計已完成
- [x] **信號機制** - 完整的信號槽連接和處理

## 🎯 實際部署狀態

### ✅ 功能驗證完成
1. **JSON檔案載入** - 能正確讀取車隊進站數據 ✅
2. **CLI自動生成** - 缺失檔案時自動呼叫CLI (功能4) ✅
3. **GUI即時更新** - CLI完成後2秒自動刷新顯示 ✅
4. **數據排序** - 按最快時間正確排序 ✅
5. **表格顯示** - 6欄表格完整顯示車隊統計 ✅
6. **參數同步** - 賽事切換時正確同步更新 ✅

### 🔧 解決的技術問題
1. **排名第1行數據顯示問題** - 修復數據填充和表格清理邏輯 ✅
2. **QTimer線程衝突** - 改用信號機制，確保主線程安全 ✅
3. **CLI執行後GUI不更新** - 實現自動刷新機制 ✅
4. **表格欄位優化** - 移除不必要欄位，添加最慢時間 ✅
5. **時間格式統一** - 調整為SS.0格式，提升可讀性 ✅

## 📋 開發核心原則遵循

### ✅ 核心原則檢查清單
- [x] **模組化設計** - 基於現有進站分析模組架構擴展
- [x] **數據優先** - 優先使用JSON緩存，與車手進站分析一致
- [x] **用戶體驗** - MDI子視窗分頁設計，無縫整合現有UI
- [x] **錯誤處理** - 複用現有異常處理和狀態反饋機制
- [x] **性能考量** - 背景執行CLI分析，避免GUI凍結
- [x] **代碼複用** - 最大化重用現有PitstopAnalysisModule架構
- [x] **一致性** - 遵循車手進站分析的GUI風格和命名規範
- [x] **智能化** - 自動檢測和生成缺失數據，提升用戶體驗
- [x] **響應性** - CLI執行完成後自動更新GUI，無需手動操作

### 🎯 具體開發目標 - 全部達成
1. ✅ 在進站分析MDI子視窗的分頁2中顯示車隊進站時間排行榜
2. ✅ 支援車隊JSON數據讀取和CLI後端分析調用（功能4）
3. ✅ 與現有參數同步機制完全整合（年份、賽事、賽段）
4. ✅ 提供車隊進站統計數據（最快時間、最慢時間、進站次數、一致性分數）
5. ✅ 支援智能數據生成、自動GUI更新等進階功能

## 🏗️ 技術架構設計 - 實際實現

### 📂 整合到現有模組結構 ✅
```
modules/
├── pitstop_analysis_mdi.py          # 現有進站分析模組 (已擴展)
│   ├── PitstopAnalysisModule        # 主模組類 (已實現) ✅
│   │   ├── 分頁1: 車手排行榜         # 分頁索引0 ✅
│   │   └── 分頁2: 車隊排行榜         # 分頁索引1 ✅
│   ├── PitstopDataManager          # 數據管理器 (已擴展支援車隊數據) ✅
│   │   ├── loadTeamPitstopData()   # 車隊JSON載入 ✅
│   │   ├── _find_team_pitstop_file() # 車隊檔案搜尋 ✅
│   │   ├── _generate_team_data_via_cli() # CLI自動生成 ✅
│   │   └── team_data_loaded信號     # 車隊數據載入完成信號 ✅
│   ├── PitstopRankingWidget        # 車手排行榜控件 (已實現) ✅
│   └── TeamPitstopRankingWidget    # 車隊排行榜控件 (已實現) ✅
│       ├── setup_table()           # 6欄表格設置 ✅
│       ├── update_ranking_data()   # 數據更新邏輯 ✅
│       ├── populate_table()        # 表格填充 ✅
│       └── format_time_display()   # 時間格式化(SS.0) ✅
└── interfaces.py                   # 模組介面定義 (已存在) ✅

f1t_gui_main.py                     # 主 GUI 程式 (無需修改) ✅
├── ModuleFactory                   # 模組工廠 (已註冊進站分析) ✅
├── CustomMdiArea                   # 自定義 MDI 區域 ✅
├── MainWindowParameterProvider     # 參數提供者 ✅
└── GlobalSignalManager            # 全域信號管理 ✅
```

### 🔄 實際數據流架構圖 ✅
```
┌─────────────────┐    參數同步     ┌─────────────────────┐
│   MainWindow    │ ──────────────► │ PitstopAnalysisModule│
│ - year_combo    │  (已實現的      │ - current_year      │
│ - race_combo    │   ParameterProvider) - current_race  │
│ - session_combo │                 │ - current_session   │
└─────────────────┘                 └─────────────────────┘
                                              │
                              ┌───────────────┴───────────────┐
                              │                               │
                        車手數據載入 ✅                    🆕 車隊數據載入 ✅
                              ▼                               ▼
                    ┌─────────────────────┐           ┌─────────────────────┐
                    │ PitstopDataManager  │           │ PitstopDataManager  │
                    │ (已實現)            │           │ (已擴展車隊支援)     │
                    │ - _find_pitstop_    │           │ - _find_team_       │
                    │   data_file()       │           │   pitstop_file()    │
                    └─────────────────────┘           └─────────────────────┘
                              │                               │
                     data_loaded信號 ✅                team_data_loaded信號 ✅
                              ▼                               ▼
                    ┌─────────────────────┐           ┌─────────────────────┐
                    │ PitstopRankingWidget│           │🆕TeamPitstopRanking │
                    │ (已實現)            │           │   Widget (已實現)    │
                    │ - 分頁1: 車手排行榜  │           │ - 分頁2: 車隊排行榜  │
                    └─────────────────────┘           └─────────────────────┘
```

### 🚀 智能CLI觸發與GUI自動更新流程 ✅
```
用戶切換參數 → 檢查車隊JSON → 檔案不存在
                    ↓
               觸發CLI功能4 → f1_analysis_modular_main.py -f 4
                    ↓
               背景執行生成 → team_pitstop_ranking_{year}_{race}_Grand_Prix.json
                    ↓
               CLI執行完成 → 發送team_data_reload_requested信號
                    ↓
               主線程處理 → QTimer.singleShot(2000) 延遲刷新
                    ↓
              自動載入JSON → 車隊排行榜表格更新 ✅
```

### 🎯 實際核心類別實現詳情

#### 1. `TeamPitstopRankingWidget` 類 ✅
**檔案位置**: `modules/pitstop_analysis_mdi.py` (行 1452-1705)

**關鍵實現功能**：
- ✅ **隱藏工具列**: 移除刷新和匯出按鈕，簡化UI
- ✅ **6欄表格**: 排名、車隊名稱、最快時間、最慢時間、進站次數、一致性分數
- ✅ **時間格式SS.0**: format_time_display() 方法統一時間顯示
- ✅ **智能排序**: 按最快時間自動排序車隊
- ✅ **數據驗證**: validate_team_data() 確保數據完整性

```python
class TeamPitstopRankingWidget(QWidget):
    """車隊進站排行榜 Widget - 顯示車隊進站統計與排行"""
    
    def setup_table(self):
        # 🔧 修正：設置6欄表格
        headers = ["排名", "車隊名稱", "最快時間", "最慢時間", "進站次數", "一致性分數"]
        
    def update_ranking_data(self, data):
        # 🔧 修正：按最快時間排序
        self.ranking_data = sorted(self.ranking_data, 
                                 key=lambda x: x.get("fastest_time", float('inf')))
        
    def format_time_display(self, seconds):
        # 🔧 修正：時間格式為SS.0
        return f"{seconds:.1f}"
```

#### 2. `PitstopDataManager` 車隊功能擴展 ✅  
**檔案位置**: `modules/pitstop_analysis_mdi.py` (行 449-670)

**關鍵新增方法**：
- ✅ `loadTeamPitstopData()`: 統一車隊數據載入邏輯
- ✅ `_find_team_pitstop_file()`: 智能車隊檔案搜尋（多目錄、多格式）
- ✅ `_generate_team_data_via_cli()`: 自動CLI呼叫機制（功能4）
- ✅ `_load_team_json_file()`: 車隊JSON檔案解析
- ✅ `_validate_team_pitstop_data()`: 車隊數據完整性驗證

```python
def loadTeamPitstopData(self, year: str, race: str, session: str) -> bool:
    """載入車隊進站數據 - 支援JSON優先+CLI後備"""
    # 1. 檢查現有JSON檔案
    # 2. 如不存在則自動觸發CLI功能4
    # 3. CLI完成後發送重載信號

def _find_team_pitstop_file(self, year: str, race: str, session: str):
    """搜尋車隊進站數據檔案（支援多格式匹配）"""
    # 支援多種檔案命名格式
    # 搜尋 json、json_exports、cache 多個目錄
    
def _generate_team_data_via_cli(self, year: str, race: str, session: str):
    """透過CLI生成車隊進站數據（後台執行）"""
    # 非阻塞執行 subprocess
    # 完成後發送 team_data_reload_requested 信號
```

#### 3. 線程安全和信號機制 ✅

**解決的關鍵問題**：
- ✅ **QTimer線程衝突**: 改用信號槽機制確保主線程安全
- ✅ **GUI自動更新**: CLI完成後2秒自動刷新顯示
- ✅ **非阻塞執行**: 背景執行CLI，避免GUI凍結

```python
# 信號定義
team_data_loaded = pyqtSignal(dict)          # 車隊數據載入完成
team_data_reload_requested = pyqtSignal()    # 車隊數據重載請求
error_occurred = pyqtSignal(str)             # 錯誤發生信號

# CLI執行完成後的處理邏輯
def run_team_cli():
    if process.returncode == 0:
        # 🔧 修正：使用信號機制，在主執行緒中處理
        self.team_data_reload_requested.emit()
```

### 📊 車隊排行榜表格結構 - 最終實現 ✅

| 欄位索引 | 欄位名稱 | 顯示內容 | 格式 | 說明 |
|---------|----------|----------|------|------|
| 0 | 排名 | 1, 2, 3... | 整數 | 按最快時間排序 |
| 1 | 車隊名稱 | McLaren, Red Bull... | 字串 | 車隊名稱 |
| 2 | 最快時間 | 23.5 | SS.0 | 該車隊最快進站時間 |
| 3 | 最慢時間 | 45.2 | SS.0 | 該車隊最慢進站時間 ✨新增 |
| 4 | 進站次數 | 5 | 整數 | 該車隊總進站次數 |
| 5 | 一致性分數 | 85.3 | 小數點1位 | 進站穩定性評分 |

**實際顯示特點**：
- ✅ **隱藏工具列**: 移除刷新和匯出按鈕，簡化介面
- ✅ **智能排序**: 自動按最快時間升序排列
- ✅ **統一時間格式**: 時間格式統一為SS.0（秒.十分位）
- ✅ **即時更新**: 支援CLI生成後自動刷新和重新排序
- ✅ **固定列寬**: 最佳化列寬配置提升閱讀體驗
### 🎯 實際JSON數據結構分析 ✅

#### 車隊進站 JSON 檔案格式（最終實現）
**檔案命名**: `team_pitstop_ranking_{year}_{race}_Grand_Prix.json`  
**範例檔案**: `team_pitstop_ranking_2025_Japanese_Grand_Prix.json`

```json
{
  "function_id": 4,
  "function_name": "Team Pitstop Ranking",
  "analysis_type": "team_pitstop_ranking",
  "session_info": {
    "event_name": "Japanese Grand Prix",
    "circuit_name": "Suzuka",
    "session_type": "Race",
    "year": 2025
  },
  "timestamp": "2025-08-31T00:04:55.373420",
  "data": [
    {
      "team": "Ferrari",
      "fastest_time": 22.9,
      "average_time": 23.1,
      "median_time": 23.1,
      "pitstop_count": 2,
      "std_deviation": 0.2828427124746205,
      "consistency_score": 94.34314575050759
    },
    {
      "team": "McLaren",
      "fastest_time": 23.0,
      "average_time": 23.1,
      "median_time": 23.1,
      "pitstop_count": 2,
      "std_deviation": 0.141421356237309,
      "consistency_score": 97.17157287525382
    }
  ]
}
```

#### 關鍵欄位對應表格顯示

| JSON欄位 | 表格欄位 | 顯示格式 | 說明 |
|----------|----------|----------|------|
| `team` | 車隊名稱 | 字串 | 直接顯示車隊名稱 |
| `fastest_time` | 最快時間 | SS.0 | 格式化為秒.十分位 ✨ |
| `slowest_time` | 最慢時間 | SS.0 | 計算或映射顯示 ✨ |
| `pitstop_count` | 進站次數 | 整數 | 直接顯示次數 |
| `consistency_score` | 一致性分數 | 小數點1位 | 百分比數值 |

**注意**: `slowest_time` 可能從其他數據計算得出，如果JSON中沒有直接提供。

## 📋 實際UI設計規格 - 最終實現 ✅

### 🏁 車隊進站排行榜子視窗 - 簡化版（隱藏工具列）
```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│ 🏆 進站分析 - 2025 Japan Race                                                    ❌關閉     │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ 🏆 最快進站 │🏁 車隊統計│🔍 詳細記錄│                                                     │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│                                🏁 車隊進站時間排行榜                                        │
│                                                                                           │
│ ┌─────┬──────────┬──────────┬──────────┬──────────┬─────────────┐                         │
│ │排名 │ 車隊名稱 │ 最快時間 │ 最慢時間 │ 進站次數 │ 一致性分數  │                         │
│ ├─────┼──────────┼──────────┼──────────┼──────────┼─────────────┤                         │
│ │ 🥇1 │ Ferrari  │  22.9    │  23.3    │    2     │    94.3     │                         │
│ ├─────┼──────────┼──────────┼──────────┼──────────┼─────────────┤                         │
│ │ 🥈2 │ McLaren  │  23.0    │  23.2    │    2     │    97.2     │                         │
│ ├─────┼──────────┼──────────┼──────────┼──────────┼─────────────┤                         │
│ │ 🥉3 │ Red Bull │  23.2    │  23.7    │    2     │    92.5     │                         │
│ ├─────┼──────────┼──────────┼──────────┼──────────┼─────────────┤                         │
│ │  4  │Mercedes  │  23.5    │  24.0    │    2     │    90.9     │                         │
│ ├─────┼──────────┼──────────┼──────────┼──────────┼─────────────┤                         │
│ │  5  │ Aston M. │  24.1    │  24.5    │    2     │    88.3     │                         │
│ ├─────┼──────────┼──────────┼──────────┼──────────┼─────────────┤                         │
│ │ ... │   ...    │   ...    │   ...    │   ...    │    ...      │                         │
│ └─────┴──────────┴──────────┴──────────┴──────────┴─────────────┘                         │
│                                                                                           │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ 📊 共 10 支車隊 │ 📄 來源: JSON │ ⏱️ 更新: 2025-08-31 14:35:20 │ 🤖 智能生成: 開啟   │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

**UI 特點（實際實現）**：
- ✅ **隱藏工具列**: 不顯示刷新和匯出按鈕
- ✅ **6欄表格**: 精簡為關鍵數據欄位
- ✅ **時間格式SS.0**: 統一時間顯示格式
- ✅ **自動排序**: 按最快時間升序排列
- ✅ **智能指示**: 狀態列顯示數據來源和智能生成狀態

## 🔧 詳細實現規格 - 實際代碼

### 1. TeamPitstopRankingWidget 類別實現詳情 ✅

#### 實際類別結構
```python
class TeamPitstopRankingWidget(QWidget):
    """車隊進站排行榜 Widget - 顯示車隊進站統計與排行"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ranking_data = []           # 車隊排行榜數據
        self.current_data = {}           # 儲存當前數據，用於導出功能
        self.setup_ui()
        
    def setup_ui(self):
        """設置使用者界面"""
        # 🔧 修正：隱藏工具列（保留代碼但不添加到佈局）
        self.refresh_button = QPushButton("🔄 刷新數據")
        self.refresh_button.setVisible(False)  # 隱藏按鈕
        
        self.export_button = QPushButton("📤 匯出CSV")
        self.export_button.setVisible(False)  # 隱藏按鈕
        
        # 主要表格
        self.table_widget = QTableWidget()
        self.setup_table()
        
    def setup_table(self):
        """設置表格結構"""
        # 🔧 修正：設置6欄表格
        headers = ["排名", "車隊名稱", "最快時間", "最慢時間", "進站次數", "一致性分數"]
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # 設置固定列寬
        self.table_widget.setColumnWidth(0, 60)   # 排名
        self.table_widget.setColumnWidth(2, 80)   # 最快時間
        self.table_widget.setColumnWidth(3, 80)   # 最慢時間
        self.table_widget.setColumnWidth(4, 80)   # 進站次數
        self.table_widget.setColumnWidth(5, 100)  # 一致性分數
        
    def update_ranking_data(self, data: Dict[str, Any]):
        """更新車隊排行榜數據"""
        # 🔧 修正：按最快時間排序數據
        self.ranking_data = sorted(self.ranking_data, 
                                 key=lambda x: x.get("fastest_time", float('inf')))
        
        # 🔧 修正：延遲更新表格，確保UI準備完成
        QTimer.singleShot(100, self.populate_table)
        
    def populate_table(self):
        """填充表格數據"""
        # 🔧 修正：處理最慢時間欄位
        slowest_time = record.get("slowest_time", 
                                record.get("average_time", 0) + record.get("std_deviation", 0))
        
        # 🔧 修正：時間格式為SS.0
        item_fastest = QTableWidgetItem(self.format_time_display(fastest_time))
        item_slowest = QTableWidgetItem(self.format_time_display(slowest_time))
        
    def format_time_display(self, seconds):
        """格式化時間顯示為SS.0格式"""
        if isinstance(seconds, (int, float)) and seconds > 0:
            return f"{seconds:.1f}"
        return "0.0"
```

### 2. PitstopDataManager 車隊支援實現 ✅

#### 關鍵新增方法詳情
```python
class PitstopDataManager(QObject):
    # 新增車隊相關信號
    team_data_loaded = pyqtSignal(dict)          # 車隊數據載入完成
    team_data_reload_requested = pyqtSignal()    # 車隊數據重載請求
    
    def loadTeamPitstopData(self, year: str, race: str, session: str) -> bool:
        """載入車隊進站數據 - 支援JSON優先+CLI後備"""
        # 1. 檢查現有JSON檔案
        json_file = self._find_team_pitstop_file(year, race, session)
        
        if json_file:
            # 載入現有JSON
            QTimer.singleShot(10, lambda: self._load_team_json_file(json_file))
            return True
        else:
            # 自動觸發CLI生成
            print(f"[AUTO_GEN] 找不到車隊JSON，觸發CLI自動生成")
            return self._generate_team_data_via_cli(year, race, session)
    
    def _find_team_pitstop_file(self, year: str, race: str, session: str) -> Optional[str]:
        """搜尋車隊進站數據檔案（支援多格式匹配）"""
        search_dirs = ["json", "json_exports", "cache"]
        
        # 🔧 修正：支援多種檔案命名格式
        race_full_names = {
            "Japan": "Japanese_Grand_Prix",
            "China": "Chinese_Grand_Prix", 
            "Belgium": "Belgian_Grand_Prix",
            # ... 其他賽事映射
        }
        
        race_full_name = race_full_names.get(race, f"{race.replace(' ', '_')}_Grand_Prix")
        
        patterns = [
            f"team_pitstop_ranking_{year}_{race_full_name}.json",
            f"team_pitstop_{year}_{race_full_name}.json",
            f"team_pitstop_ranking_{year}_{race.replace(' ', '_')}.json",
        ]
        
        # 搜尋多個目錄中的精確匹配
        for search_dir in search_dirs:
            for pattern in patterns:
                search_path = os.path.join(search_dir, pattern)
                if os.path.exists(search_path):
                    return search_path
        return None
    
    def _generate_team_data_via_cli(self, year: str, race: str, session: str) -> bool:
        """透過CLI生成車隊進站數據（後台執行）"""
        command = [
            "python", "f1_analysis_modular_main.py",
            "-f", "4",  # 功能4: 車隊進站時間排行榜
            "-y", str(year), "-r", race, "-s", session
        ]
        
        def run_team_cli():
            process = subprocess.Popen(command, ...)
            if process.returncode == 0:
                # 🔧 修正：使用信號機制，在主執行緒中處理
                self.team_data_reload_requested.emit()
                
        # 在後台執行車隊 CLI
        thread = threading.Thread(target=run_team_cli, daemon=True)
        thread.start()
        return True
```

### 3. 主模組整合邏輯 ✅

#### PitstopAnalysisModule 車隊支援整合
```python
class PitstopAnalysisModule(QWidget):
    def __init__(self, ...):
        # 🔧 修正：添加車隊排行榜分頁
        self.team_widget = TeamPitstopRankingWidget()
        self.tab_widget.addTab(self.team_widget, "🏁 車隊統計")
        
        # 🔧 修正：連接車隊數據信號
        self.data_manager.team_data_loaded.connect(self.team_widget.update_ranking_data)
        self.data_manager.team_data_reload_requested.connect(self.reload_team_data)
        
    def onParametersChanged(self, year, race, session):
        """參數變更時的處理邏輯"""
        # 更新車手排行榜
        if self.tab_widget.currentIndex() == 0:
            self.data_manager.loadPitstopData(year, race, session)
        
        # 🔧 修正：更新車隊排行榜
        elif self.tab_widget.currentIndex() == 1:
            self.data_manager.loadTeamPitstopData(year, race, session)
    
    def reload_team_data(self):
        """重新載入車隊數據（CLI完成後調用）"""
        # 🔧 修正：延遲2秒後重新載入，確保檔案生成完成
        QTimer.singleShot(2000, lambda: self.data_manager.loadTeamPitstopData(
            self.current_year, self.current_race, self.current_session))
```

### 4. 線程安全和性能優化 ✅

#### 解決的關鍵技術問題
```python
# 問題1: QTimer線程衝突
# 解決方案: 使用信號槽機制
def run_team_cli():
    if process.returncode == 0:
        # ❌ 錯誤做法: 直接呼叫GUI方法
        # self.team_widget.refresh_display()
        
        # ✅ 正確做法: 發送信號給主線程處理
        self.team_data_reload_requested.emit()

# 問題2: GUI更新時機不當
# 解決方案: 延遲更新確保數據準備完成
def reload_team_data(self):
    # ✅ 延遲2秒，確保CLI生成檔案完成
    QTimer.singleShot(2000, self.actual_reload_method)

# 問題3: 表格數據顯示問題
# 解決方案: 數據排序和格式化分離
def update_ranking_data(self, data):
    # ✅ 先排序數據
    self.ranking_data = sorted(data, key=lambda x: x.get("fastest_time", float('inf')))
    
    # ✅ 延遲更新UI，確保數據準備完成
    QTimer.singleShot(100, self.populate_table)
```
        toolbar_layout.addWidget(self.export_button)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # 主要表格
        self.table_widget = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table_widget)
        
    def setup_table(self):
        """設置表格結構"""
        # 設置列數和標題
        headers = ["排名", "車隊名稱", "最快時間", "平均時間", "中位時間", 
                  "進站次數", "標準差", "一致性分數"]
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # 設置表格屬性
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSortingEnabled(True)
        
        # 設置列寬
        header = self.table_widget.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Fixed)      # 排名
        header.setSectionResizeMode(1, QHeaderView.Interactive) # 車隊名稱
        header.setSectionResizeMode(2, QHeaderView.Fixed)      # 最快時間
        header.setSectionResizeMode(3, QHeaderView.Fixed)      # 平均時間
        header.setSectionResizeMode(4, QHeaderView.Fixed)      # 中位時間
        header.setSectionResizeMode(5, QHeaderView.Fixed)      # 進站次數
        header.setSectionResizeMode(6, QHeaderView.Fixed)      # 標準差
        
        # 設置固定列寬
        self.table_widget.setColumnWidth(0, 60)   # 排名
        self.table_widget.setColumnWidth(2, 80)   # 最快時間
        self.table_widget.setColumnWidth(3, 80)   # 平均時間
        self.table_widget.setColumnWidth(4, 80)   # 中位時間
        self.table_widget.setColumnWidth(5, 80)   # 進站次數
        self.table_widget.setColumnWidth(6, 80)   # 標準差
        
    def update_ranking_data(self, data: Dict[str, Any]):
        """更新車隊排行榜數據"""
        try:
            # 驗證數據格式
            if not self.validate_team_data(data):
                self.show_error_message("無效的車隊進站數據格式")
                return
            
            # 儲存完整數據
            self.current_data = data
            
            # 提取排行榜數據
            if "data" in data:
                self.ranking_data = data["data"]
            else:
                self.ranking_data = data if isinstance(data, list) else []
            
            # 更新表格
            self.populate_table()
            
            print(f"[OK] [TEAM_RANKING] 車隊排行榜數據更新完成，{len(self.ranking_data)} 支車隊")
            
        except Exception as e:
            self.show_error_message(f"更新車隊排行榜數據失敗: {str(e)}")
            print(f"[ERROR] [TEAM_RANKING] 數據更新失敗: {e}")
    
    def populate_table(self):
        """填充表格數據"""
        self.table_widget.setRowCount(len(self.ranking_data))
        
        for row, team_data in enumerate(self.ranking_data):
            # 排名
            rank_item = QTableWidgetItem()
            if row == 0:
                rank_item.setText("🥇1")
            elif row == 1:
                rank_item.setText("🥈2")
            elif row == 2:
                rank_item.setText("🥉3")
            else:
                rank_item.setText(str(row + 1))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 0, rank_item)
            
            # 車隊名稱
            team_item = QTableWidgetItem(team_data.get("team", "Unknown"))
            team_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 1, team_item)
            
            # 最快時間
            fastest_time = team_data.get("fastest_time", 0)
            fastest_item = QTableWidgetItem(f"{fastest_time:.3f}s")
            fastest_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 2, fastest_item)
            
            # 平均時間
            avg_time = team_data.get("average_time", 0)
            avg_item = QTableWidgetItem(f"{avg_time:.3f}s")
            avg_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 3, avg_item)
            
            # 中位時間
            median_time = team_data.get("median_time", 0)
            median_item = QTableWidgetItem(f"{median_time:.3f}s")
            median_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 4, median_item)
            
            # 進站次數
            pitstop_count = team_data.get("pitstop_count", 0)
            count_item = QTableWidgetItem(str(pitstop_count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 5, count_item)
            
            # 標準差
            std_dev = team_data.get("std_deviation", 0)
            std_item = QTableWidgetItem(f"{std_dev:.3f}")
            std_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 6, std_item)
            
            # 一致性分數
            consistency = team_data.get("consistency_score", 0)
            consistency_item = QTableWidgetItem(f"{consistency:.2f}%")
            consistency_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 7, consistency_item)
    
    def validate_team_data(self, data: Dict[str, Any]) -> bool:
        """驗證車隊進站數據格式"""
        try:
            # 檢查基本結構
            if not isinstance(data, dict):
                return False
            
            # 提取記錄
            records = None
            if "data" in data:
                records = data["data"]
            elif isinstance(data, list):
                records = data
            else:
                return False
                
            if not records or not isinstance(records, list):
                return False
                
            # 驗證第一筆記錄的欄位
            first_record = records[0]
            required_fields = ["team", "fastest_time", "average_time", "pitstop_count"]
            
            for field in required_fields:
                if field not in first_record:
                    print(f"[ERROR] [VALIDATE] 缺少必要欄位: {field}")
                    return False
                    
            print(f"[OK] [VALIDATE] 車隊數據驗證通過，記錄數量：{len(records)}")
            return True
            
        except Exception as e:
            print(f"[ERROR] [VALIDATE] 車隊數據驗證異常: {e}")
            return False
    
    def show_error_message(self, message: str):
        """顯示錯誤訊息"""
        self.table_widget.setRowCount(1)
        error_item = QTableWidgetItem(f"❌ 錯誤: {message}")
        error_item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, error_item)
        self.table_widget.setSpan(0, 0, 1, self.table_widget.columnCount())
    
    def show_loading_state(self):
        """顯示載入中狀態"""
        self.table_widget.setRowCount(1)
        loading_item = QTableWidgetItem("⏳ 正在載入車隊數據...")
        loading_item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, loading_item)
        self.table_widget.setSpan(0, 0, 1, self.table_widget.columnCount())
    
    def hide_loading_state(self):
        """隱藏載入中狀態"""
        pass
    
    def clear_table(self):
        """清空表格數據"""
        self.table_widget.setRowCount(0)
        self.ranking_data = []
        self.current_data = {}
        print(f"[CLEAR] [TEAM_RANKING] 車隊表格數據已清空")
    
    def refresh_data(self):
        """刷新數據 - 委託給父模組"""
        if hasattr(self.parent(), 'refresh_team_data'):
            self.parent().refresh_team_data()
    
    def export_to_csv(self):
        """匯出CSV功能 (預留實現)"""
        print(f"[EXPORT] 車隊進站排行榜匯出功能 (開發中)")
        # TODO: 實現CSV匯出功能
```

### 2. PitstopDataManager 擴展設計

#### 新增車隊數據支援方法
```python
class PitstopDataManager(QObject):
    """進站數據管理器 - 擴展支援車隊數據載入"""
    
    # 新增車隊數據信號
    team_data_loaded = pyqtSignal(dict)  # 車隊數據載入完成信號
    
    def _find_team_pitstop_file(self, year: str, race: str, session: str) -> Optional[str]:
        """搜尋車隊進站數據檔案"""
        try:
            print(f"[FOLDER] [TEAM_PITSTOP] 搜尋車隊進站數據檔案: {year} {race} {session}")
            
            # 搜尋目錄
            search_dirs = ["json", "json_exports", "cache"]
            
            # 構建賽事的完整名稱
            race_full_names = {
                "Japan": "Japanese_Grand_Prix",
                "China": "Chinese_Grand_Prix", 
                "Belgium": "Belgian_Grand_Prix",
                # ... 完整的賽事映射
            }
            
            # 獲取完整賽事名稱
            race_full_name = race_full_names.get(race, f"{race.replace(' ', '_')}_Grand_Prix")
            
            # 精確匹配模式
            patterns = [
                f"team_pitstop_ranking_{year}_{race_full_name}.json",
                f"team_pitstop_{year}_{race_full_name}.json",
                f"team_pitstop_ranking_{year}_{race.replace(' ', '_')}.json",
            ]
            
            # 搜尋多個目錄中的精確匹配
            for search_dir in search_dirs:
                for pattern in patterns:
                    search_path = os.path.join(search_dir, pattern)
                    if os.path.exists(search_path):
                        print(f"[FOLDER] [TEAM_PITSTOP] 找到車隊檔案: {search_path}")
                        return search_path
            
            print(f"[FOLDER] [TEAM_PITSTOP] 找不到車隊檔案: {year} {race} {session}")
            return None
                
        except Exception as e:
            print(f"[ERROR] [TEAM_PITSTOP] 搜尋車隊檔案時發生錯誤: {str(e)}")
            return None
    
    def load_team_data(self, year: str, race: str, session: str):
        """載入車隊數據"""
        try:
            print(f"[FOLDER] [TEAM_DATA_MANAGER] 開始載入車隊進站數據: {year} {race} {session}")
            
            # 尋找車隊 JSON 檔案
            json_file = self._find_team_pitstop_file(year, race, session)
            print(f"[FOLDER] [TEAM_DATA_MANAGER] 搜尋到的車隊檔案: {json_file}")
            
            if json_file:
                # 載入現有 JSON
                QTimer.singleShot(10, lambda: self._load_team_json_file(json_file))
            else:
                # 如果找不到車隊檔案，發出錯誤信號
                self.error_occurred.emit("找不到車隊進站數據檔案，請先生成車手進站分析")
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"車隊數據載入失敗: {str(e)}")
            return False
    
    def _load_team_json_file(self, file_path: str):
        """載入車隊 JSON 檔案"""
        try:
            print(f"[LOAD] [TEAM_JSON] 載入車隊 JSON 檔案: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 驗證車隊數據
            if self._validate_team_pitstop_data(data):
                print(f"[OK] [TEAM_JSON] 車隊 JSON 載入成功")
                self.team_data_loaded.emit(data)
            else:
                self.error_occurred.emit("車隊進站數據格式無效")
                
        except Exception as e:
            print(f"[ERROR] [TEAM_JSON] 車隊 JSON 載入失敗: {e}")
            self.error_occurred.emit(f"車隊 JSON 載入失敗: {str(e)}")
    
    def _validate_team_pitstop_data(self, data: Dict[str, Any]) -> bool:
        """驗證車隊進站數據格式"""
        try:
            # 檢查基本結構
            if not isinstance(data, dict):
                return False
            
            # 檢查 function_id 是否為 4 (車隊進站分析)
            if data.get("function_id") != 4:
                print(f"[ERROR] [VALIDATE] 車隊數據 function_id 不匹配: {data.get('function_id')}")
                return False
            
            # 提取記錄
            records = data.get("data", [])
            if not records or not isinstance(records, list):
                return False
                
            # 驗證第一筆記錄的欄位
            first_record = records[0]
            required_fields = ["team", "fastest_time", "average_time", "pitstop_count"]
            
            for field in required_fields:
                if field not in first_record:
                    print(f"[ERROR] [VALIDATE] 車隊數據缺少必要欄位: {field}")
                    return False
                    
            print(f"[OK] [VALIDATE] 車隊數據驗證通過，記錄數量：{len(records)}")
            return True
            
        except Exception as e:
            print(f"[ERROR] [VALIDATE] 車隊數據驗證異常: {e}")
            return False
```

### 3. PitstopAnalysisModule 集成擴展

#### 修改現有模組以支援車隊分頁
```python
class PitstopAnalysisModule(IAnalysisModule):
    """進站分析模組 - 擴展支援車隊進站排行榜"""
    
    def __init__(self, parent=None):
        # ... 現有初始化代碼 ...
        
        # 新增車隊排行榜控件
        self.team_ranking_widget = None
    
    def setup_ui(self):
        """設置UI介面 - 修改以支援車隊分頁"""
        layout = QVBoxLayout(self._main_widget)
        
        # 創建標籤頁控件
        self.tab_widget = QTabWidget()
        
        # 分頁1: 車手排行榜 (已實現)
        self.ranking_widget = PitstopRankingWidget(self)
        self.tab_widget.addTab(self.ranking_widget, "🏆 最快進站")
        
        # 🆕 分頁2: 車隊排行榜 (新實現)
        self.team_ranking_widget = TeamPitstopRankingWidget(self)
        self.tab_widget.addTab(self.team_ranking_widget, "🏁 車隊統計")
        
        # 分頁3: 詳細記錄 (預留)
        placeholder_widget3 = QLabel("🔍 進站詳細記錄\n(功能開發中)")
        placeholder_widget3.setAlignment(Qt.AlignCenter)
        placeholder_widget3.setStyleSheet("color: #666; font-size: 14px;")
        self.tab_widget.addTab(placeholder_widget3, "🔍 詳細記錄")
        
        layout.addWidget(self.tab_widget)
    
    def setup_connections(self):
        """設置信號連接 - 擴展車隊數據信號"""
        # 現有數據管理器信號連接
        self.data_manager.data_loaded.connect(self.on_data_loaded)
        self.data_manager.error_occurred.connect(self.on_error_occurred)
        self.data_manager.loading_progress.connect(self.on_loading_progress)
        self.data_manager.status_changed.connect(self.on_status_changed)
        
        # 🆕 新增車隊數據信號連接
        self.data_manager.team_data_loaded.connect(self.on_team_data_loaded)
    
    def load_data(self):
        """載入數據 - 擴展支援車隊數據同時載入"""
        print(f"[LOAD] 載入進站分析數據: {self.current_year} {self.current_race} {self.current_session}")
        
        # 顯示載入狀態
        if self.ranking_widget:
            self.ranking_widget.show_loading_state()
        if self.team_ranking_widget:
            self.team_ranking_widget.show_loading_state()
        
        # 同時啟動車手和車隊數據載入
        self.data_manager.load_data(self.current_year, self.current_race, self.current_session)
        self.data_manager.load_team_data(self.current_year, self.current_race, self.current_session)
    
    def on_team_data_loaded(self, data: Dict[str, Any]):
        """處理車隊數據載入完成"""
        print(f"[OK] 車隊數據載入完成")
        
        # 隱藏載入狀態
        if self.team_ranking_widget:
            self.team_ranking_widget.hide_loading_state()
            # 更新車隊排行榜數據
            self.team_ranking_widget.update_ranking_data(data)
    
    def refresh_team_data(self):
        """刷新車隊數據 - 供車隊排行榜控件調用"""
        print(f"[REFRESH] 手動刷新車隊數據")
        if self.team_ranking_widget:
            self.team_ranking_widget.show_loading_state()
        self.data_manager.load_team_data(self.current_year, self.current_race, self.current_session)
```

## 🚀 實施步驟

### 第一階段: 基礎實現 (1-2天)
1. **創建 TeamPitstopRankingWidget 類別**
   - 實現基本 UI 結構
   - 設置表格和工具列
   - 實現數據顯示方法

2. **擴展 PitstopDataManager**
   - 新增車隊數據搜尋方法
   - 新增車隊數據載入方法
   - 新增車隊數據驗證方法

### 第二階段: 模組集成 (1天)
3. **修改 PitstopAnalysisModule**
   - 整合車隊排行榜控件到分頁2
   - 設置車隊數據信號連接
   - 修改載入流程支援車隊數據

4. **測試與調試**
   - 測試車隊數據載入
   - 測試參數同步
   - 測試錯誤處理

### 第三階段: 功能完善 (1天)
5. **進階功能實現**
   - CSV 匯出功能
   - 數據刷新功能
   - 錯誤處理優化

6. **文檔與測試**
   - 更新使用文檔
   - 完成單元測試
   - 使用者驗收測試

## 📋 驗收標準

### ✅ 功能驗收
- [ ] 車隊進站排行榜正確顯示在分頁2
- [ ] JSON 數據正確載入和解析
- [ ] 參數同步功能正常運作
- [ ] 錯誤處理和使用者回饋完整
- [ ] 載入狀態視覺化回饋
- [ ] 數據刷新功能正常

### ✅ 技術驗收
- [ ] 代碼遵循現有架構模式
- [ ] 與車手進站分析模組完全整合
- [ ] 無記憶體洩漏和性能問題
- [ ] 完整的錯誤處理和日誌記錄
- [ ] 符合 F1T GUI 編碼標準

### ✅ 使用者體驗驗收
- [ ] UI 風格與現有模組一致
- [ ] 操作流程直觀易用
- [ ] 載入時間合理 (< 5秒)
- [ ] 錯誤訊息清晰明確
- [ ] 支援完整的參數同步

---

**🚀 開發準備就緒**: 此設計完全基於現有的車手進站分析模組架構，可直接開始實施開發。所有核心組件都複用現有的設計模式和實現標準，確保與現有系統的無縫整合。

**最終確認**: ✅ 車隊進站時間排行榜GUI模組設計已完全對齊現有進站分析模組架構，可以開始實施開發。
