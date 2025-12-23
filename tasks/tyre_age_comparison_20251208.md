# 🔍 Ranking Tower vs Chase Strategy - Tyre Age 獲取邏輯完整對比

**創建日期**: 2025-12-08  
**模組 A (參考)**: Ranking Tower (`ranking_tower.py`)  
**模組 B (目標)**: Chase Strategy (`chase_strategy.py`)  
**對比目標**: 輪胎齡 (tyre age) 獲取邏輯

---

## 📊 整體流程對比

### Ranking Tower 流程圖
```
snapshot 更新
    ↓
_on_snapshot_updated()
    ↓ (建立 tyre_state 字典)
從 snapshot.drivers 提取 → tyre_state[driver_num] = {...}
    ↓                           - 'tyre_age': driver_data.get('tyre_age')
    ↓
傳遞給 _ranking_widget
    ↓
update_data(snapshot, tyre_state)
    ↓
self._current_tyre_state = tyre_state
    ↓
_set_tyre_info(row, driver_num)
    ↓
tyre_info = self._current_tyre_state.get(driver_num, {})
    ↓
tyre_age = tyre_info.get('tyre_age', ...)  ← 關鍵：使用 'tyre_age' 鍵
```

### Chase Strategy 流程圖
```
snapshot 更新
    ↓
_on_snapshot_updated()
    ↓ (建立 tyre_state 字典)
從 snapshot.drivers 提取 → tyre_state[driver_num] = {...}
    ↓                           - 'age': driver_data.get('tyre_age')  ⚠️ 注意：鍵名不同
    ↓
傳遞給 _widget
    ↓
update_snapshot(snapshot, tyre_state)
    ↓
self._tyre_state = tyre_state
    ↓
_refresh_strategies()
    ↓
p1_tyre = self._tyre_state.get(self._selected_p1, {})
    ↓
p1_age = p1_tyre.get('age', 0)  ← 關鍵：使用 'age' 鍵
```

---

## 🔑 關鍵差異分析

### ⚠️ 差異 1: tyre_state 字典的鍵名不一致

| 模組 | 存儲時的鍵名 | 讀取時的鍵名 | 是否匹配 |
|------|-------------|-------------|---------|
| **Ranking Tower** | `'tyre_age'` | `'tyre_age'` | ✅ 匹配 |
| **Chase Strategy** | `'age'` | `'age'` | ✅ 匹配 |

**說明**: 兩個模組內部一致，但彼此鍵名不同。

---

## 📝 詳細代碼對比

### 階段 1: `_on_snapshot_updated()` - 建立 tyre_state

#### Ranking Tower (行 1344-1395)
```python
def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
    # ... (略)
    
    # 優先從 snapshot 的 drivers 中提取（即時模式）
    for driver_num, driver_data in drivers.items():
        if driver_data.get('compound') or driver_data.get('tyre_age') is not None:
            tyre_state[driver_num] = {
                'compound': driver_data.get('compound', 'UNKNOWN'),
                'tyre_age': driver_data.get('tyre_age', 0),  # ← 鍵名: 'tyre_age'
                'tyre_new': driver_data.get('tyre_new', False),
                'stint_count': driver_data.get('pit_count', 0) + 1,
                'stints': driver_data.get('stints', []),
            }
    
    # 備用：從 DataManager 獲取
    if not tyre_state:
        if hasattr(self._data_manager, 'get_tyre_state'):
            tyre_state = self._data_manager.get_tyre_state()
        elif hasattr(self._data_manager, 'get_tyre_state_at_time'):
            timestamp = snapshot.get('race_time', '')
            if timestamp:
                tyre_state = self._data_manager.get_tyre_state_at_time(timestamp)
```

#### Chase Strategy (行 1137-1163)
```python
def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
    # 獲取輪胎狀態 - 與 Ranking Tower 一致的邏輯
    tyre_state = {}
    drivers = snapshot.get('drivers', {})
    
    # 優先從 snapshot 的 drivers 中提取
    for driver_num, driver_data in drivers.items():
        if driver_data.get('compound') or driver_data.get('tyre_age') is not None:
            tyre_state[driver_num] = {
                'compound': driver_data.get('compound', 'UNKNOWN'),
                'age': driver_data.get('tyre_age', 0),  # ← 鍵名: 'age' ⚠️
                'tyre_new': driver_data.get('tyre_new', False),
                'stint_count': driver_data.get('pit_count', 0) + 1,
                'stints': driver_data.get('stints', []),
            }
    
    # 備用：從 DataManager 獲取
    if not tyre_state and self._data_manager:
        if hasattr(self._data_manager, 'get_tyre_state'):
            tyre_state = self._data_manager.get_tyre_state()
```

**差異總結 - 階段 1:**
| 項目 | Ranking Tower | Chase Strategy | 差異 |
|------|--------------|----------------|------|
| 鍵名 | `'tyre_age'` | `'age'` | ⚠️ 不一致 |
| 數據來源 | `driver_data.get('tyre_age', 0)` | `driver_data.get('tyre_age', 0)` | ✅ 一致 |
| 備用邏輯 | 有 `get_tyre_state_at_time` | 沒有 | ⚠️ 功能少 |

---

### 階段 2: 傳遞 tyre_state

#### Ranking Tower
```python
# _on_snapshot_updated() 內
self._ranking_widget.set_car_data(car_data)

# 在 update_data() 內
def update_data(self, snapshot: Dict, tyre_state: Dict = None):
    self._current_tyre_state = tyre_state or {}  # ← 存儲為實例變數
```

#### Chase Strategy
```python
# _on_snapshot_updated() 內
self._widget.update_snapshot(snapshot, tyre_state)

# 在 update_snapshot() 內
def update_snapshot(self, snapshot: Dict[str, Any], tyre_state: Dict[str, Dict] = None):
    self._tyre_state = tyre_state or {}  # ← 存儲為實例變數
```

**差異總結 - 階段 2:**
| 項目 | Ranking Tower | Chase Strategy | 差異 |
|------|--------------|----------------|------|
| 存儲變數名 | `_current_tyre_state` | `_tyre_state` | ✅ 命名不同但功能一致 |

---

### 階段 3: 讀取 tyre age

#### Ranking Tower (行 700-725)
```python
def _set_tyre_info(self, row: int, driver_num: str):
    tyre_info = self._current_tyre_state.get(driver_num, {})
    compound = tyre_info.get('compound', 'UNKNOWN')
    
    # 齡 (欄位 5)
    tyre_age = tyre_info.get('tyre_age', tyre_info.get('stint_length', ''))  # ← 鍵名: 'tyre_age'
    age_item = QTableWidgetItem(str(tyre_age) if tyre_age else '')
    age_item.setTextAlignment(Qt.AlignCenter)
    self._set_age_color(age_item, tyre_age, compound)
    self.table.setItem(row, 5, age_item)
```

#### Chase Strategy (行 855-885)
```python
def _refresh_strategies(self):
    # 方法 1: 從 tyre_state 獲取
    if self._tyre_state:
        p1_tyre = self._tyre_state.get(self._selected_p1, {})
        p2_tyre = self._tyre_state.get(self._selected_p2, {})
    
    # 方法 2: 直接從 driver data 獲取 (備用)
    if not p1_tyre or not p1_tyre.get('compound'):
        p1_tyre = {
            'compound': p1_data.get('compound', 'MEDIUM'),
            'age': p1_data.get('tyre_age', 0)  # ← 備用來源
        }
    
    p1_age = p1_tyre.get('age', 0)  # ← 鍵名: 'age'
    p2_age = p2_tyre.get('age', 0)
    p1_compound = p1_tyre.get('compound', 'MEDIUM')
    p2_compound = p2_tyre.get('compound', 'MEDIUM')
```

**差異總結 - 階段 3:**
| 項目 | Ranking Tower | Chase Strategy | 差異 |
|------|--------------|----------------|------|
| 讀取鍵名 | `'tyre_age'` | `'age'` | ⚠️ 不一致 |
| 備用鍵 | `'stint_length'` | 直接從 driver_data | ⚠️ 邏輯不同 |
| 備用來源 | 無 | 從 `p1_data.get('tyre_age')` | ✅ Chase Strategy 更完善 |

---

## 🔴 問題診斷

### 為什麼 Chase Strategy 顯示 (0)?

**問題根因分析:**

1. **鍵名不匹配問題 (已修復)**  
   - ✅ Chase Strategy 現在使用 `'age'` 作為鍵名，存儲和讀取一致

2. **可能的數據來源問題**  
   - ❓ `driver_data.get('tyre_age')` 可能返回 `None` 或 `0`
   - ❓ snapshot 中的 drivers 可能沒有 `tyre_age` 欄位

3. **DataManager 備用邏輯缺失**  
   - ⚠️ Chase Strategy 沒有 `get_tyre_state_at_time` 備用方案

---

## ✅ 修復建議

### 建議 1: 統一鍵名 (可選)
如果要完全統一，可以改為：
```python
# Chase Strategy _on_snapshot_updated()
tyre_state[driver_num] = {
    'compound': driver_data.get('compound', 'UNKNOWN'),
    'tyre_age': driver_data.get('tyre_age', 0),  # 改用 'tyre_age'
    # ...
}

# Chase Strategy _refresh_strategies()
p1_age = p1_tyre.get('tyre_age', 0)  # 改用 'tyre_age'
```

### 建議 2: 增強備用邏輯
```python
# Chase Strategy _on_snapshot_updated()
if not tyre_state and self._data_manager:
    if hasattr(self._data_manager, 'get_tyre_state'):
        tyre_state = self._data_manager.get_tyre_state()
    elif hasattr(self._data_manager, 'get_tyre_state_at_time'):  # ← 新增
        timestamp = snapshot.get('race_time', '')
        if timestamp:
            tyre_state = self._data_manager.get_tyre_state_at_time(timestamp)
```

### 建議 3: 增加調試輸出 (已實現)
```python
# Chase Strategy 已添加詳細調試
print(f"[CHASE_STRATEGY] Tyre from tyre_state - P1: {p1_tyre}, P2: {p2_tyre}")
print(f"[CHASE_STRATEGY] P1 tyre: {p1_compound}({p1_age})")
```

---

## 🧪 測試驗證清單

- [ ] 重啟 GUI，檢查終端調試輸出
- [ ] 確認 `[CHASE_STRATEGY] Tyre from tyre_state` 是否有數據
- [ ] 確認 `[CHASE_STRATEGY] P1 tyre: HARD(24)` 是否顯示正確齡期
- [ ] 比對 Ranking Tower 顯示的齡期是否一致
- [ ] 檢查 snapshot 中 `driver_data` 是否包含 `tyre_age` 欄位

---

## 📌 結論

### 主要差異
1. **鍵名不同**: Ranking Tower 使用 `'tyre_age'`，Chase Strategy 使用 `'age'`
2. **備用邏輯**: Ranking Tower 有 `get_tyre_state_at_time`，Chase Strategy 沒有
3. **備用來源**: Chase Strategy 有從 driver_data 直接讀取的備用方案

### 當前狀態
- ✅ Chase Strategy 已實現與 Ranking Tower 相同的數據提取邏輯
- ✅ Chase Strategy 有更完善的備用機制（直接從 driver_data 讀取）
- ⚠️ 需要確認 snapshot.drivers 中是否真的有 `tyre_age` 資料

### 下一步
查看終端日誌，確認：
```
[CHASE_STRATEGY] Tyre from tyre_state - P1: {'compound': 'HARD', 'age': 24, ...}
```
如果 `age: 0`，則說明 snapshot 來源問題，而非代碼邏輯問題。
