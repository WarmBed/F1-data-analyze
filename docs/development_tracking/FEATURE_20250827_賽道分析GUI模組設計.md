# 賽道分析GUI模組設計文件

## 📋 文檔資訊
- **文檔類型**: 功能開發設計
- **創建日期**: 2025-08-27
- **最後更新**: 2025-08-27
- **作者**: F1T開發團隊
- **版本**: 1.0.0
- **相關項目**: GUI賽道地圖視覺化功能

## 🎯 模組目的
基於CLI功能2的賽道位置分析數據，開發GUI版本的賽道分析模組，核心功能為**繪製互動式賽道地圖 (Track Map)**，提供視覺化的賽道布局、位置座標和距離資訊。

## 📊 數據來源分析

### 🔍 CLI JSON數據格式
基於 `raw_data_track_position_2025_Unknown_20250827_084745.json` 的資料結構：

#### 核心數據結構
```json
{
  "analysis_type": "track_position_analysis",
  "function": "2",
  "session_info": {
    "year": 2025,
    "race": "Unknown", 
    "track_name": "Japanese Grand Prix",
    "session_type": "R"
  },
  "position_analysis": {
    "track_bounds": {
      "x_min": -13796.0, "x_max": 5962.0,
      "y_min": -7004.0, "y_max": 3135.0
    },
    "distance_covered_m": 57619.88,
    "total_position_records": 50
  },
  "detailed_position_records": [
    {
      "point_index": 1,
      "distance_m": 0.0,
      "position_x": 1674.0,
      "position_y": -619.0
    }
    // ... 50個位置點
  ]
}
```

### 🎯 賽道地圖繪製關鍵數據
1. **位置座標**: `position_x`, `position_y` - 賽道路線的實際座標點
2. **距離數據**: `distance_m` - 每個點距離起點的累積距離
3. **賽道邊界**: `track_bounds` - 確定地圖顯示範圍
4. **總距離**: `distance_covered_m` - 一圈的總長度

## 🏗️ GUI模組架構設計

### 📂 模組檔案結構
```
modules/gui/
├── track_analysis_module.py          # 主要模組檔案
├── track_map_widget.py              # 賽道地圖繪製元件
├── track_data_processor.py          # 賽道數據處理器
└── track_analysis_cache.py          # 賽道分析緩存管理
```

### 🧩 核心類別設計

#### 1. **TrackAnalysisModule** (主模組)
```python
class TrackAnalysisModule(QWidget):
    """賽道分析主模組 - 整合賽道地圖和數據顯示"""
    
    def __init__(self, year=2025, race="Japan", session="R"):
        # 初始化UI布局
        # 整合賽道地圖元件和控制面板
        
    def start_analysis_workflow(self):
        # 開始賽道分析工作流程
        # 載入CLI JSON數據 → 處理座標 → 繪製地圖
        
    def set_analysis_parameters(self, parameters):
        # 設定分析參數 (年份、賽事、賽段)
```

#### 2. **TrackMapWidget** (地圖繪製核心)
```python
class TrackMapWidget(QWidget):
    """賽道地圖繪製元件 - 核心視覺化功能"""
    
    def __init__(self):
        # 初始化繪圖環境 (matplotlib + PyQt5)
        
    def load_track_data(self, json_data):
        # 載入賽道位置數據
        # 解析座標點、距離、邊界資訊
        
    def draw_track_map(self):
        # 繪製賽道地圖主功能
        # 1. 繪製賽道路線 (連接所有座標點)
        # 2. 標示距離標記
        # 3. 顯示起終點線
        # 4. 添加互動功能
        
    def add_distance_markers(self):
        # 添加距離標記 (每1000m一個標記)
        
    def add_sector_indicators(self):
        # 添加賽段指示器 (S1, S2, S3)
        
    def enable_interactive_features(self):
        # 啟用互動功能
        # - 滑鼠懸停顯示座標和距離
        # - 縮放和平移功能
        # - 點擊座標點顯示詳細資訊
```

#### 3. **TrackDataProcessor** (數據處理器)
```python
class TrackDataProcessor:
    """賽道數據處理器 - 處理座標轉換和計算"""
    
    def parse_json_data(self, json_file_path):
        # 解析CLI輸出的JSON檔案
        
    def process_coordinates(self, raw_coordinates):
        # 處理座標數據
        # 1. 座標平滑化
        # 2. 座標標準化
        # 3. 計算曲率半徑
        
    def calculate_track_features(self):
        # 計算賽道特徵
        # 1. 直線段識別
        # 2. 彎道分析
        # 3. 高速/低速區域標示
        
    def generate_distance_grid(self):
        # 生成距離網格標記
```

## 🎨 UI設計規範

### 📐 布局結構
```
┌─────────────────────────────────────────────────────────────┐
│  賽道分析模組 - 2025 Japan R                                 │
├─────────────────────────────────────────────────────────────┤
│  [控制面板] [重新載入] [匯出地圖] [設定]                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    賽道地圖顯示區域                            │
│                 ┌─────────────────────┐                      │
│                 │                     │                      │
│                 │    鈴鹿賽道地圖        │                      │
│                 │  (互動式座標圖)       │                      │
│                 │                     │                      │
│                 └─────────────────────┘                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  賽道資訊顯示區                                                │
│  • 總長度: 5.807 km                                          │
│  • 位置點數: 50                                               │
│  • 座標範圍: X(-13796 ~ 5962), Y(-7004 ~ 3135)              │
└─────────────────────────────────────────────────────────────┘
```

### 🎨 視覺設計要求

#### 賽道地圖視覺元素
1. **賽道路線**: 
   - 粗線條 (寬度3-4px)
   - 顏色: 深灰色 (#2C3E50)
   - 平滑曲線連接所有座標點

2. **起終點線**:
   - 垂直線條，黑白格子圖案
   - 位置: point_index=1 和 point_index=50 之間

3. **距離標記**:
   - 每1000m設置一個標記點
   - 顯示累積距離 (如: "1.0km", "2.0km")
   - 標記樣式: 小圓點 + 文字標籤

4. **座標網格**:
   - 淺灰色虛線網格
   - X軸和Y軸刻度標示

5. **互動元素**:
   - 滑鼠懸停: 顯示座標 (X, Y) 和距離
   - 縮放: 滾輪縮放功能
   - 平移: 滑鼠拖拽移動地圖

## 🔧 技術實現細節

### 📊 座標處理算法
```python
def smooth_track_coordinates(coordinates):
    """座標平滑化算法"""
    # 使用三次樣條插值平滑賽道路線
    # 避免尖銳角度，呈現真實賽道曲線
    
def normalize_coordinates(coordinates, canvas_size):
    """座標標準化"""
    # 將賽道座標映射到畫布尺寸
    # 保持長寬比例，居中顯示
    
def calculate_curve_radius(point1, point2, point3):
    """計算彎道曲率半徑"""
    # 用於識別彎道程度和高速/低速區域
```

### 🎯 地圖繪製流程
1. **數據載入階段**
   ```python
   json_data = load_track_analysis_json(file_path)
   coordinates = extract_coordinates(json_data)
   ```

2. **座標處理階段**
   ```python
   smoothed_coords = smooth_track_coordinates(coordinates)
   normalized_coords = normalize_coordinates(smoothed_coords, canvas_size)
   ```

3. **地圖繪製階段**
   ```python
   draw_track_outline(normalized_coords)
   add_start_finish_line()
   add_distance_markers()
   add_coordinate_grid()
   ```

4. **互動功能階段**
   ```python
   enable_mouse_hover_info()
   enable_zoom_pan_controls()
   ```

## 📋 功能需求清單

### ✅ 核心功能 (MVP)
- [x] JSON數據載入和解析
- [ ] 賽道路線繪製 (連接座標點)
- [ ] 起終點線標示
- [ ] 距離標記顯示
- [ ] 基本互動功能 (縮放、平移)

### 🚀 進階功能
- [ ] 賽道分段顯示 (S1, S2, S3)
- [ ] 彎道曲率分析和標示
- [ ] 高速/低速區域顏色編碼
- [ ] 3D地形顯示 (如有高度數據)
- [ ] 車手路線疊加 (不同車手的racing line)
- [ ] 超車熱點區域標示

### 🎨 UI/UX增強
- [ ] 地圖樣式切換 (衛星圖、輪廓圖、技術圖)
- [ ] 座標信息面板
- [ ] 地圖匯出功能 (PNG, SVG)
- [ ] 全螢幕地圖模式
- [ ] 賽道數據統計面板

## 🔗 系統整合

### 📡 與CLI模組的整合
```python
def call_cli_track_analysis(year, race, session):
    """呼叫CLI功能2進行賽道分析"""
    command = f"python f1_analysis_modular_main.py -f 2 -y {year} -r {race} -s {session}"
    # 執行CLI命令並獲取JSON輸出
    
def load_cli_output_json():
    """載入CLI輸出的JSON檔案"""
    # 從json/目錄載入最新的track_position分析結果
```

### 🔄 與主GUI的整合
```python
# 在 f1t_gui_main.py 中添加賽道分析選項
def add_track_analysis_option():
    """在左側選單添加賽道分析選項"""
    track_item = QTreeWidgetItem(["賽道分析", "Track Analysis"])
    # 整合到現有的分析選單中
```

## 📈 開發里程碑

### 🗓️ 開發階段規劃

#### Phase 1: 基礎功能 (1-2天)
- 創建基本GUI模組結構
- 實現JSON數據載入
- 完成基本賽道路線繪製

#### Phase 2: 地圖增強 (2-3天)  
- 添加距離標記和起終點線
- 實現縮放和平移功能
- 完善座標顯示和互動

#### Phase 3: 視覺優化 (1-2天)
- 優化地圖視覺效果
- 添加賽道資訊面板
- 實現地圖匯出功能

#### Phase 4: 系統整合 (1天)
- 整合到主GUI系統
- 完成緩存機制
- 進行全面測試

## ⚠️ 技術挑戰和解決方案

### 🎯 座標系統轉換
**挑戰**: FastF1的座標系統與GUI畫布座標系統不同
**解決方案**: 實現座標標準化和映射算法

### 🖼️ 大數據點渲染性能
**挑戰**: 50+個座標點的平滑渲染可能影響性能
**解決方案**: 使用座標抽樣和LOD (Level of Detail) 技術

### 🔄 即時更新機制
**挑戰**: 賽事參數變更時需要重新載入地圖
**解決方案**: 實現智能緩存和差異更新機制

## 🧪 測試策略

### 🎯 測試用例
1. **數據載入測試**: 測試各種JSON格式的正確解析
2. **座標渲染測試**: 驗證座標點正確顯示在地圖上
3. **互動功能測試**: 驗證縮放、平移、懸停功能
4. **性能測試**: 測試大量座標點的渲染性能
5. **多賽道測試**: 測試不同賽道的地圖顯示

### 📊 測試數據
- 使用2025 Japan R的現有數據作為基準
- 準備其他賽道的測試數據 (如 Monaco, Silverstone)
- 測試邊界情況 (極小/極大座標範圍)

## 📚 相關資源

### 🔗 技術參考
- **FastF1 文檔**: 座標系統說明
- **Matplotlib 文檔**: 2D圖形繪製
- **PyQt5 文檔**: GUI元件整合

### 📋 相關檔案
- `modules/track_position_analysis.py` - CLI版本參考
- `json/raw_data_track_position_*.json` - 數據格式參考
- `modules/gui/universal_chart_widget.py` - 圖表元件參考

---

## 📈 更新歷史
| 日期 | 版本 | 變更內容 | 作者 |
|------|------|----------|------|
| 2025-08-27 | 1.0.0 | 初始版本 - 完整設計文件 | F1T開發團隊 |

---
*本文檔由 F1T-LOCAL-V13 賽道分析GUI模組開發計畫生成*
