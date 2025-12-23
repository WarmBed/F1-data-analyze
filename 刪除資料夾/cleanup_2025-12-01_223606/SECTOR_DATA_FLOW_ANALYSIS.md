# Sector 標註數據流分析與重新載入方案

**日期**: 2025-11-12  
**問題**: 切換賽道時 Sector 標註位置錯誤（舊賽道座標殘留）

---

## 📊 當前數據流分析

### 1. 切換賽道的完整流程

```
[用戶操作: 選擇新 Race]
         ↓
[主視窗 F1T GUI]
         ↓
    調用 module.update_parameters(year, race, session)
         ↓
[HistoricalTrackMapMDI]
    ├─ 更新內部參數 (self.race = new_race)
    ├─ 調用 API 獲取新數據
    └─ 等待 API 響應
         ↓
[API 返回新數據]
         ↓
    _on_data_loaded(data) 被觸發
         ↓
    ┌─────────────────────────────────┐
    │ 🔴 問題區域：複雜的數據處理邏輯   │
    ├─────────────────────────────────┤
    │ 1. 保存舊的 sector_boundaries   │
    │ 2. 檢測賽道是否變更             │
    │ 3. 決定是否保留舊數據           │
    │ 4. 補充 track_data               │
    │ 5. 調用 load_track_data()       │
    │ 6. 調用 set_sector_boundaries() │
    └─────────────────────────────────┘
         ↓
[TrackMapWidget 更新]
    ├─ 載入新的賽道地圖
    ├─ 載入/保留 sector_boundaries
    └─ 重繪 paintEvent()
         ↓
[顯示結果]
    ✅ 理想：新賽道 + 新座標
    ❌ 實際：新賽道 + 舊座標（座標錯誤）
```

### 2. Sector 標註顯示流程

```
[sector_boundaries 數據]
    ↓
    包含：
    - sector: int (1, 2, 3)
    - name: str ("S1 End", "S2 End", "S3 End")
    - distance_m: float (1233.1, 3130.3, 0.0)
    - position_x: float (2126.9, -4.0, -3674.2)  ← 賽道特定座標
    - position_y: float (-2616.1, 660.0, -5269.4) ← 賽道特定座標
    ↓
[TrackMapWidget.paintEvent()]
    ↓
    調用 _draw_sector_boundaries()
    ↓
    對每個 boundary:
        1. 取得世界座標 (position_x, position_y)
        2. 計算賽道切線方向 _get_track_tangent_at_position()
        3. 計算垂直方向（normal vector）
        4. 繪製垂直線（300m，黑色實線）
        5. 繪製標籤（S1/S2/S3）
    ↓
[繪製到螢幕]
```

### 3. 問題根源

**核心問題**：`position_x` 和 `position_y` 是**賽道特定的絕對座標**

| 賽道 | S1 End X | S1 End Y | 特徵 |
|------|----------|----------|------|
| Brazil | 2126.9 | -2616.1 | 負 Y 座標 |
| Bahrain | 5806.0 | 4839.0 | 正 X/Y 座標 |

**問題場景**：
1. 用戶在 Bahrain 賽道（座標：X=5806, Y=4839）
2. 切換到 Brazil 賽道
3. 保護性邏輯保留了 Bahrain 的座標
4. Brazil 地圖繪製 Bahrain 的座標 → **位置完全錯誤**

---

## 🔄 當前解決方案的問題

### 嘗試 1: 持久化邏輯（失敗）
```python
# 問題：_current_flags_data 被新數據覆蓋後無法恢復
old_sector_boundaries = self._current_flags_data.get("sector_boundaries")
self._current_flags_data = data  # ← 覆蓋
# 嘗試恢復：但已經是新數據了
```

### 嘗試 2: 保護性清空（部分成功）
```python
# 問題：保護過度，清空了也保留
if not new_data:
    if self.sector_boundaries:  # 保留舊數據
        pass  # ← 可能是錯誤賽道的座標
```

### 嘗試 3: 賽道變更檢測（當前方案）
```python
# 問題：需要正確的 metadata，增加複雜度
old_race = old_metadata.get("race")
new_race = new_metadata.get("race")
if old_race != new_race:
    old_sector_boundaries = []  # 清空
```

**複雜度累積**：
- 需要保存舊數據
- 需要檢測賽道變更
- 需要判斷是否保留
- 需要處理多個數據源
- 需要處理雙重載入
- 需要大量調試輸出

---

## ✨ 建議方案：切換賽道時重新載入 MDI

### 為什麼這是更好的選擇？

#### 1. **符合語義**
```
切換賽道 = 查看不同的賽道分析
         = 應該是完全獨立的視圖
         ≠ 在同一視圖中更新數據
```

每個賽道是獨立的分析對象，不應共享狀態。

#### 2. **簡化邏輯**
```python
# ❌ 當前方案（複雜）
def update_parameters():
    old_data = save_old_data()
    new_data = fetch_new_data()
    if track_changed(old_data, new_data):
        clear_old_data()
    merge_data(old_data, new_data)
    update_widgets()

# ✅ 重新載入方案（簡單）
def update_parameters():
    if track_changed():
        close_current_mdi()
        create_new_mdi(new_params)
```

#### 3. **無狀態污染**
```
重新載入 = 全新狀態
         = 無舊數據殘留
         = 無座標錯誤
         = 無需複雜檢測
```

#### 4. **更少的 Bug**
```
當前方案遇到的 Bug：
❌ SECTOR-RACE-SWITCH-001: 持久化邏輯失效
❌ SECTOR-RACE-SWITCH-002: 雙重載入覆蓋
❌ SECTOR-RACE-SWITCH-003: 座標錯誤（當前）

重新載入方案：
✅ 無需持久化 → 無法失效
✅ 無雙重載入 → 無法覆蓋
✅ 無座標混淆 → 無法錯誤
```

---

## 🛠️ 實施方案

### 方案 A: 在 MDI 層檢測並重建

```python
# historical_track_map_mdi.py
class HistoricalTrackMapMDI(UniversalAnalysisMDI):
    def update_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
        """更新參數 - 如果賽道變更則重建"""
        
        # 檢測賽道變更
        old_race = getattr(self, 'current_race', None)
        new_race = race
        
        if old_race and old_race != new_race:
            print(f"[MDI] 🔄 檢測到賽道變更: {old_race} → {new_race}")
            print(f"[MDI] 🔨 請求重建 MDI 視窗")
            
            # 發送信號請求主視窗重建此 MDI
            self.request_rebuild.emit({
                'year': year,
                'race': race,
                'session': session
            })
            return True
        
        # 同一賽道，正常更新
        return super().update_parameters(year, race, session, **kwargs)
```

### 方案 B: 在主視窗層管理重建

```python
# f1t_gui_main.py
class MainWindow:
    def sync_module_parameters(self, module, param_type, value):
        """同步參數到模組 - 處理賽道變更"""
        
        if param_type == 'race':
            old_race = getattr(module, 'current_race', None)
            new_race = value
            
            # 檢測賽道變更
            if old_race and old_race != new_race:
                # 對於需要重建的模組類型
                if self._should_rebuild_on_track_change(module):
                    print(f"[MAIN] 🔄 重建模組: {old_race} → {new_race}")
                    self._rebuild_module(module, new_race)
                    return
        
        # 正常更新參數
        module.update_parameters(...)
    
    def _should_rebuild_on_track_change(self, module) -> bool:
        """判斷模組是否需要在賽道變更時重建"""
        rebuild_types = [
            'historical_track_map',  # 歷年賽道分析
            # 其他賽道特定模組...
        ]
        return getattr(module, '_module_factory_type', None) in rebuild_types
    
    def _rebuild_module(self, old_module, new_race):
        """重建模組"""
        # 1. 獲取當前 MDI 子視窗
        sub_window = self._find_subwindow_for_module(old_module)
        
        # 2. 關閉舊視窗
        if sub_window:
            sub_window.close()
        
        # 3. 創建新模組實例
        new_module = self._create_module_with_params(
            module_type='historical_track_map',
            year=self.current_year,
            race=new_race,
            session=self.current_session
        )
        
        # 4. 添加到 MDI 區域
        new_sub_window = QMdiSubWindow()
        new_sub_window.setWidget(new_module.get_main_widget())
        self.mdi_area.addSubWindow(new_sub_window)
        new_sub_window.show()
```

### 方案 C: 簡化版 - 只清空舊數據

如果不想重建整個 MDI，至少在賽道變更時清空所有舊數據：

```python
def _on_data_loaded(self, data: Dict[str, Any]):
    """數據載入 - 賽道變更時清空一切"""
    
    # 取得賽道資訊
    new_race = data.get("metadata", {}).get("race")
    old_race = getattr(self, '_last_loaded_race', None)
    
    # 賽道變更：清空所有組件
    if old_race and new_race and old_race != new_race:
        print(f"[MDI] 🗑️  賽道變更，清空所有組件")
        
        # 清空地圖
        if self.track_map:
            self.track_map.sector_boundaries = []
            self.track_map.official_corners = []
            self.track_map.position_data = []
            self.track_map.corner_flags = {}
        
        # 清空圖表
        if self.elevation_chart:
            self.elevation_chart.plot_elevation([], [])
        
        # 清空表格
        # ...
    
    # 記錄當前賽道
    self._last_loaded_race = new_race
    
    # 正常載入新數據
    # ...
```

---

## 📋 建議實施步驟

### 短期方案（立即修復）：
1. ✅ 實施賽道變更檢測（已完成）
2. ✅ 清空舊座標（已完成）
3. ⏳ 測試並確認

### 中期方案（優化）：
1. 實施方案 C：清空所有組件
2. 確保每次賽道變更都是全新狀態
3. 移除複雜的持久化邏輯

### 長期方案（重構）：
1. 實施方案 B：主視窗管理重建
2. 統一所有賽道特定模組的行為
3. 建立重建機制作為標準模式

---

## 🎯 推薦方案

**我強烈推薦實施「方案 B：主視窗層管理重建」**

### 理由：

1. **最乾淨的解決方案**
   - 完全避免狀態污染
   - 無需複雜的數據管理
   - 代碼更簡潔易維護

2. **最符合語義**
   - 切換賽道 = 查看新賽道
   - 應該是全新的視圖
   - 不應該共享任何狀態

3. **最少的 Bug**
   - 無持久化問題
   - 無座標錯誤
   - 無狀態混淆

4. **可擴展性**
   - 其他賽道特定模組也能使用
   - 建立標準化的重建機制
   - 未來功能更容易實現

### 性能考量：

```
重建成本：
- Widget 創建: ~50ms
- MDI 初始化: ~20ms
- API 調用: ~500ms（主要開銷）
- 總計: ~570ms

用戶體驗：
- 切換賽道頻率: 低（幾分鐘一次）
- 閃爍時間: ~50ms（不明顯）
- 載入提示: 可顯示 "載入中..."

結論：性能開銷完全可接受
```

---

## 💡 總結

### 當前方案的問題：
```
複雜度 ↑↑↑ → Bug ↑↑↑ → 維護成本 ↑↑↑
```

### 重建方案的優勢：
```
簡單 ✅ → 無 Bug ✅ → 易維護 ✅
```

### 下一步行動：

1. **立即**：測試當前的賽道變更檢測是否工作
2. **本週**：實施方案 B（主視窗管理重建）
3. **下週**：移除複雜的持久化邏輯，簡化代碼

**結論：切換賽道時重新載入 MDI 是正確且更好的設計選擇。**
