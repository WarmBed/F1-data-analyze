# F48 直線速度分析改進任務 - 整合賽道位置數據

## 任務概述
改進 -f48 全部車手直線速度分析，整合 -f2 賽道位置功能，解決多直線段賽道（如新加坡）的測量一致性問題。

## 問題分析

### 當前問題（新加坡賽道案例）
```
問題描述：
1. 新加坡賽道有兩條主要直線段
2. 某些直線段的起始速度已經 > 100 km/h
3. 當前算法從最高速度點向前回推找 100 km/h
4. 如果直線段起始速度 > 100 km/h，則無法完成加速性能計算
5. 不同車手可能在不同直線段達到最高速度，導致比較不公平

當前邏輯流程：
[車手A] → 找最速圈 → 找整圈最高速度點 → 向前回推找100km/h → 計算加速時間
[車手B] → 找最速圈 → 找整圈最高速度點 → 向前回推找100km/h → ❌ 起始速度>100，失敗

問題根源：
- 各車手可能在不同位置/不同直線段達到最高速度
- 缺乏統一的測量基準點
- 沒有利用賽道位置信息來標準化測量位置
```

### 改進目標
```
目標：統一所有車手的測量位置，確保公平比較

改進策略：
1. 先找出最速車手的最速圈（性能基準）
2. 從基準圈中識別主直線段的位置範圍（Distance）
3. 所有車手統一在該位置範圍內找最高速度點
4. 從統一位置的最高速度點回推 100 km/h
5. 計算該直線段的加速性能

優點：
✅ 所有車手在同一直線段比較（位置標準化）
✅ 避免起始速度過高的問題（選擇最佳直線段）
✅ 基於最速表現確定測量點（代表性更強）
✅ 保證數據的可比性和一致性
```

## 實現計劃

### 階段 1：整合賽道位置數據功能
- [ ] 在 `AllDriversStraightLineSpeedAnalysis` 類中添加賽道位置分析方法
- [ ] 實現 `_get_track_position_data()` 方法（參考 -f2 實現）
- [ ] 從最速車手的最速圈獲取完整的位置-速度映射
- [ ] 驗證位置數據的完整性和準確性

**參考實現位置：**
- `CLI_modules/cli/analyzer/track_position_analysis.py` - 位置數據獲取
- 特別注意 `analyze_track_position_data()` 函數的實現邏輯

### 階段 2：識別主直線段位置範圍
- [ ] 實現 `_identify_main_straight_position()` 方法
- [ ] 基於最速車手的數據識別主直線段
- [ ] 返回主直線段的位置範圍（distance_start, distance_end）
- [ ] 記錄主直線段的特徵（起始速度、最高速度、加速度）

**算法邏輯：**
```python
def _identify_main_straight_position(self, reference_car_data, reference_driver):
    """
    從最速車手的最速圈中識別主直線段位置
    
    步驟：
    1. 找到整圈速度最高的點（尾速最高點）
    2. 從該點向前回推，找到速度持續上升的起點
    3. 確保該直線段：
       - 速度增益 >= 100 km/h（從起點到尾速）
       - 起始速度 <= 100 km/h（確保能計算加速性能）
       - 包含足夠的距離（至少 200m）
    4. 記錄該直線段的 Distance 範圍
    
    返回：
    {
        "driver": "VER",
        "lap_number": 58,
        "segment_distance_start": 1234.5,  # 主直線段起點距離
        "segment_distance_end": 1789.2,    # 主直線段終點距離
        "segment_start_speed": 85.3,       # 起始速度
        "segment_max_speed": 312.7,        # 尾速
        "segment_length": 554.7            # 直線段長度
    }
    """
```

### 階段 3：標準化所有車手的測量位置
- [ ] 修改 `_compute_driver_record()` 方法
- [ ] 添加 `reference_segment` 參數傳遞主直線段位置
- [ ] 實現 `_find_speed_in_position_range()` 方法
- [ ] 在指定位置範圍內找每個車手的最高速度點

**新增方法：**
```python
def _find_speed_in_position_range(
    self, 
    car_data: pd.DataFrame, 
    distance_start: float, 
    distance_end: float
) -> Optional[Dict]:
    """
    在指定的位置範圍內找到最高速度點
    
    Args:
        car_data: 車手的遙測數據
        distance_start: 目標直線段起始距離
        distance_end: 目標直線段終點距離
    
    Returns:
        {
            "max_speed_idx": idx,
            "max_speed": 310.5,
            "distance": 1678.9,
            "can_calculate_acceleration": True  # 能否回推到100km/h
        }
    """
```

### 階段 4：重構加速性能計算
- [ ] 修改 `_calculate_acceleration_in_segment()` 方法
- [ ] 確保在統一的位置範圍內計算加速性能
- [ ] 從最高速度點向前回推到 100 km/h（在同一位置範圍內）
- [ ] 處理無法回推到 100 km/h 的情況（記錄實際起始速度）

**改進邏輯：**
```python
def _calculate_acceleration_in_position_range(
    self,
    car_data: pd.DataFrame,
    max_speed_idx: int,
    distance_start: float,
    distance_end: float
) -> Optional[Dict[str, float]]:
    """
    在指定位置範圍內計算加速性能
    
    改進點：
    1. 只在 [distance_start, distance_end] 範圍內搜索
    2. 從 max_speed_idx 向前回推找 100 km/h
    3. 如果找不到 100 km/h，記錄實際最低速度
    4. 計算實際速度區間的加速時間（如 120→250 km/h）
    
    返回：
    {
        "time_seconds": 4.23,
        "distance_meters": 456.7,
        "speed_start_kmh": 120.0,      # 實際起始速度（可能>100）
        "speed_end_kmh": 250.0,        # 實際終止速度
        "avg_acceleration_ms2": 8.5,
        "measurement_position_start": 1234.5,  # 測量位置範圍
        "measurement_position_end": 1789.2
    }
    """
```

### 階段 5：更新數據結構和輸出
- [ ] 擴展 `DriverSpeedRecord` 數據類
- [ ] 添加位置信息字段
- [ ] 添加主直線段信息到 JSON 輸出
- [ ] 更新排行榜顯示格式

**數據結構擴展：**
```python
@dataclass
class DriverSpeedRecord:
    # 現有字段...
    
    # 新增字段
    measurement_segment: Optional[Dict[str, float]] = None  # 測量位置信息
    reference_segment: Optional[Dict[str, float]] = None    # 參考直線段信息
    
    def as_dict(self) -> Dict[str, Any]:
        result = {
            # 現有字段...
            
            # 新增：測量位置信息
            "measurement_segment": {
                "distance_start": self.measurement_segment.get("distance_start"),
                "distance_end": self.measurement_segment.get("distance_end"),
                "position_standardized": True  # 標記已使用位置標準化
            } if self.measurement_segment else None,
            
            # 新增：參考基準信息
            "reference_info": {
                "reference_driver": self.reference_segment.get("driver"),
                "reference_lap": self.reference_segment.get("lap_number"),
                "segment_length": self.reference_segment.get("segment_length")
            } if self.reference_segment else None
        }
        return result
```

### 階段 6：向後兼容性處理
- [ ] 保留原有的全圈掃描邏輯作為回退方案
- [ ] 如果位置數據不可用，自動回退到舊算法
- [ ] 添加算法版本標記到輸出

**回退邏輯：**
```python
def run(self, top_n=None, include_chart=True):
    """執行分析（帶位置標準化）"""
    
    # 嘗試獲取位置數據
    position_data_available = self._check_position_data_availability()
    
    if position_data_available:
        print("[INFO] 使用位置標準化算法（基於賽道位置的統一測量）")
        return self._run_with_position_standardization(top_n, include_chart)
    else:
        print("[WARNING] 位置數據不可用，回退到傳統算法（全圈掃描）")
        return self._run_legacy_algorithm(top_n, include_chart)
```

## 測試計劃

### 測試案例 1：新加坡賽道（多直線段）
```powershell
# 測試新加坡 2024 正賽
python f1_analysis_modular_main.py -f 48 -y 2024 -r Singapore -s R

預期結果：
✅ 所有車手在同一主直線段測量
✅ 加速性能數據完整（100→250 km/h）
✅ JSON 包含位置標準化信息
✅ 排行榜顯示統一的測量位置
```

### 測試案例 2：摩納哥賽道（無長直線段）
```powershell
# 測試摩納哥 2024 正賽（極端案例）
python f1_analysis_modular_main.py -f 48 -y 2024 -r Monaco -s R

預期結果：
✅ 算法能識別最佳加速區間（即使沒有長直線）
✅ 或正確回退到舊算法
✅ 不會因為缺少典型直線段而崩潰
```

### 測試案例 3：蒙扎賽道（典型長直線）
```powershell
# 測試蒙扎 2024 正賽（基準測試）
python f1_analysis_modular_main.py -f 48 -y 2024 -r Italy -s R

預期結果：
✅ 與舊算法結果一致（長直線段，兩種算法應趨同）
✅ 位置標準化提供額外的位置信息
✅ 加速性能計算準確
```

### 測試案例 4：回退測試（無位置數據）
```powershell
# 人為禁用位置數據，測試回退邏輯
# （修改代碼暫時返回 None）

預期結果：
✅ 自動檢測到位置數據不可用
✅ 回退到舊算法
✅ 輸出中標記使用的算法版本
✅ 功能完全正常，無錯誤
```

## 關鍵代碼修改點

### 1. 主入口方法修改
```python
# 文件：all_drivers_straight_line_speed.py
# 位置：run() 方法

def run(self, top_n=None, include_chart=True):
    """執行全部車手直線速度分析（位置標準化版）"""
    
    # 步驟 1：檢查位置數據可用性
    position_available = self._check_position_data_availability()
    
    if position_available:
        # 步驟 2：獲取最速車手和最速圈
        fastest_driver, fastest_lap = self._find_overall_fastest_lap()
        
        # 步驟 3：從最速圈識別主直線段位置
        reference_segment = self._identify_main_straight_position(
            fastest_driver, 
            fastest_lap
        )
        
        if reference_segment:
            print(f"[INFO] 主直線段位置已確定：")
            print(f"   參考車手: {reference_segment['driver']}")
            print(f"   位置範圍: {reference_segment['segment_distance_start']:.1f}m - "
                  f"{reference_segment['segment_distance_end']:.1f}m")
            print(f"   直線長度: {reference_segment['segment_length']:.1f}m")
            
            # 步驟 4：使用位置標準化算法
            return self._run_with_position_standardization(
                reference_segment, 
                top_n, 
                include_chart
            )
    
    # 步驟 5：回退到舊算法
    print("[WARNING] 位置標準化不可用，使用傳統全圈掃描算法")
    return self._run_legacy_algorithm(top_n, include_chart)
```

### 2. 核心位置識別方法
```python
def _identify_main_straight_position(self, driver_code: str, lap_obj) -> Optional[Dict]:
    """從最速車手的最速圈中識別主直線段位置"""
    
    # 獲取遙測數據
    car_data = self._extract_car_data(lap_obj)
    if car_data is None or "Speed" not in car_data.columns or "Distance" not in car_data.columns:
        return None
    
    speeds = pd.to_numeric(car_data["Speed"], errors="coerce").dropna()
    distances = pd.to_numeric(car_data["Distance"], errors="coerce")
    
    # 找到最高速度點
    max_speed_idx = speeds.idxmax()
    max_speed = speeds[max_speed_idx]
    max_speed_distance = distances[max_speed_idx]
    
    # 向前回推找直線段起點（速度持續上升的起點）
    segment_start_idx = None
    for idx in reversed(speeds.index[:speeds.index.get_loc(max_speed_idx)]):
        current_speed = speeds[idx]
        
        # 條件：速度 <= 100 km/h 或速度開始明顯下降
        if current_speed <= 100:
            segment_start_idx = idx
            break
        
        # 檢查速度是否開始明顯下降（非直線段）
        if idx > speeds.index[0]:
            prev_idx = speeds.index[speeds.index.get_loc(idx) - 1]
            if speeds[prev_idx] > current_speed + 10:  # 速度下降超過10 km/h
                segment_start_idx = idx
                break
    
    if segment_start_idx is None:
        # 無法找到合適的起點
        return None
    
    segment_start_distance = distances[segment_start_idx]
    segment_start_speed = speeds[segment_start_idx]
    segment_length = max_speed_distance - segment_start_distance
    
    # 驗證直線段有效性
    speed_gain = max_speed - segment_start_speed
    if speed_gain < 100 or segment_length < 200:
        # 速度增益不足或距離太短
        return None
    
    return {
        "driver": driver_code,
        "lap_number": self._extract_lap_number(lap_obj),
        "segment_distance_start": float(segment_start_distance),
        "segment_distance_end": float(max_speed_distance),
        "segment_start_speed": float(segment_start_speed),
        "segment_max_speed": float(max_speed),
        "segment_length": float(segment_length),
        "speed_gain": float(speed_gain)
    }
```

### 3. 位置範圍內速度計算
```python
def _find_speed_in_position_range(
    self,
    car_data: pd.DataFrame,
    distance_start: float,
    distance_end: float
) -> Optional[Dict]:
    """在指定位置範圍內找到最高速度點"""
    
    if "Distance" not in car_data.columns or "Speed" not in car_data.columns:
        return None
    
    distances = pd.to_numeric(car_data["Distance"], errors="coerce")
    speeds = pd.to_numeric(car_data["Speed"], errors="coerce")
    
    # 過濾出目標位置範圍內的數據
    mask = (distances >= distance_start) & (distances <= distance_end)
    range_data = car_data[mask]
    
    if range_data.empty:
        return None
    
    range_speeds = speeds[mask]
    max_speed_idx = range_speeds.idxmax()
    max_speed = range_speeds[max_speed_idx]
    max_speed_distance = distances[max_speed_idx]
    
    # 檢查是否能回推到 100 km/h
    can_calculate_acceleration = False
    for idx in reversed(range_speeds.index[:range_speeds.index.get_loc(max_speed_idx)]):
        if range_speeds[idx] <= 100:
            can_calculate_acceleration = True
            break
    
    return {
        "max_speed_idx": max_speed_idx,
        "max_speed": float(max_speed),
        "distance": float(max_speed_distance),
        "can_calculate_acceleration": can_calculate_acceleration
    }
```

## 預期輸出格式

### JSON 輸出結構（新增字段）
```json
{
  "success": true,
  "analysis_type": "all_drivers_straight_line_speed",
  "algorithm_version": "2.0_position_standardized",
  "reference_segment": {
    "driver": "VER",
    "lap_number": 58,
    "segment_distance_start": 1234.5,
    "segment_distance_end": 1789.2,
    "segment_length": 554.7,
    "segment_start_speed": 85.3,
    "segment_max_speed": 312.7
  },
  "drivers": [
    {
      "driver": "VER",
      "max_speed_kmh": 312.7,
      "lap_number": 58,
      "measurement_segment": {
        "distance_start": 1234.5,
        "distance_end": 1789.2,
        "position_standardized": true
      },
      "acceleration_100_300": {
        "time_seconds": 4.23,
        "speed_start_kmh": 100.0,
        "speed_end_kmh": 250.0,
        "measurement_position_start": 1234.5,
        "measurement_position_end": 1567.8
      }
    }
  ]
}
```

## 完成標準
- [ ] 所有車手在統一位置範圍內測量（位置標準化）
- [ ] 新加坡賽道測試通過（多直線段場景）
- [ ] 摩納哥賽道測試通過（極端案例）
- [ ] 蒙扎賽道結果與舊算法一致（基準測試）
- [ ] 回退邏輯正常工作（無位置數據時）
- [ ] JSON 輸出包含完整的位置信息
- [ ] 代碼符合反幻覺編碼原則（所有方法經驗證）
- [ ] 文檔更新（copilot-instructions.md）

## 注意事項
1. **反幻覺編碼原則**：所有新方法必須基於現有 -f2 的驗證實現
2. **向後兼容**：必須保留舊算法作為回退方案
3. **位置數據依賴**：FastF1 的 `get_pos_data()` 可能不是所有賽道都可用
4. **性能考慮**：位置數據可能很大，考慮緩存策略
5. **錯誤處理**：任何步驟失敗都應優雅回退，不影響基本功能

## 參考文件
- `CLI_modules/cli/analyzer/track_position_analysis.py` - 賽道位置分析實現
- `CLI_modules/cli/analyzer/all_drivers_straight_line_speed.py` - 當前速度分析實現
- `CLI_modules/cli/core/function_mapper.py` - 功能映射和調用邏輯
