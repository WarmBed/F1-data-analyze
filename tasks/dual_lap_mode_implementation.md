# 🔄 雙圈比較模式 - 實施任務

**創建日期**: 2025-10-07  
**目標**: 將雙圈比較模式應用到所有遙測分析模組

---

## 📋 任務清單

### Phase 1: 核心模組 (優先級: 🔴 高)

- [x] **Speed Analysis** ✅
  - [x] 修改 `set_speed_data()` 方法簽名
  - [x] 修改判斷邏輯
  - [x] 修改 `update_speed_data()` 方法
  - [x] 單元測試通過
  - [x] 創建實施文檔
  - **完成時間**: 2025-10-07

- [ ] **Throttle Analysis** ⏳
  - [ ] 修改 `set_throttle_data()` 方法簽名
  - [ ] 修改判斷邏輯
  - [ ] 修改 `update_throttle_data()` 方法
  - [ ] 測試驗證
  - **預計時間**: 30 分鐘

- [ ] **RPM Analysis** ⏳
  - [ ] 修改 `set_rpm_data()` 方法簽名
  - [ ] 修改判斷邏輯
  - [ ] 修改 `update_rpm_data()` 方法
  - [ ] 測試驗證
  - **預計時間**: 30 分鐘

---

### Phase 2: 擴展模組 (優先級: 🟡 中)

- [ ] **Brake Analysis** ⏳
  - [ ] 修改 `set_brake_data()` 方法
  - [ ] 修改判斷邏輯
  - [ ] 測試驗證
  - **預計時間**: 25 分鐘

- [ ] **Gear Analysis** ⏳
  - [ ] 修改 `set_gear_data()` 方法
  - [ ] 修改判斷邏輯
  - [ ] 測試驗證
  - **預計時間**: 25 分鐘

---

### Phase 3: 進階模組 (優先級: 🟢 低)

- [ ] **Acceleration Analysis** ⏳
  - [ ] 確認模組結構
  - [ ] 應用雙圈比較邏輯
  - [ ] 測試驗證
  - **預計時間**: 35 分鐘

- [ ] **Speed Diff Analysis** ⏳
  - [ ] 確認模組結構
  - [ ] 應用雙圈比較邏輯
  - [ ] 測試驗證
  - **預計時間**: 35 分鐘

- [ ] **Distance Diff Analysis** ⏳
  - [ ] 確認模組結構
  - [ ] 應用雙圈比較邏輯
  - [ ] 測試驗證
  - **預計時間**: 35 分鐘

---

## 🔧 標準化修改步驟

### 每個模組的修改清單

#### 步驟 1: 修改 set_*_data() 方法
```python
# 在方法簽名中添加 lap1 和 lap2 參數
def set_*_data(self, ..., 
               lap1: int = None,  # 🆕 新增
               lap2: int = None   # 🆕 新增
              ):
```

#### 步驟 2: 修改判斷邏輯
```python
# 在設置數據後，添加雙圈比較判斷
if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
    is_dual_lap_mode = True
    self.driver1_name = f"{driver1_name} - 第{lap1}圈"
    self.driver2_name = f"{driver2_name} - 第{lap2}圈"
else:
    self.driver1_name = driver1_name
    self.driver2_name = driver2_name

# 修改 is_single_driver 判斷
if not driver2_data or driver2_name == "":
    self.is_single_driver = True
elif driver1_name == driver2_name:
    if lap1 is not None and lap2 is not None and lap1 != lap2:
        self.is_single_driver = False  # 雙圈比較模式
    else:
        self.is_single_driver = True   # 單車手模式
else:
    self.is_single_driver = False
```

#### 步驟 3: 修改 update_*_data() 方法
```python
# 提取圈數信息
lap1 = None
lap2 = None
if len(drivers) >= 2:
    lap1 = drivers[0].get('lap_number')
    lap2 = drivers[1].get('lap_number')

# 在判斷邏輯中加入雙圈比較
if driver1_name == driver2_name:
    if lap1 is not None and lap2 is not None and lap1 != lap2:
        is_dual_lap_mode = True
        is_single_driver_mode = False
    else:
        is_single_driver_mode = True

# 調用 set_*_data() 時傳遞圈數
self.chart_widget.set_*_data(
    ...,
    lap1=lap1,  # 🆕 新增
    lap2=lap2   # 🆕 新增
)
```

#### 步驟 4: 測試驗證
```python
# 測試案例
1. 同車手不同圈：LEC L10 vs LEC L50 → 雙圈比較模式
2. 同車手相同圈：LEC L10 vs LEC L10 → 單車手模式
3. 不同車手：VER L10 vs LEC L15 → 雙車手模式
```

---

## 📊 進度追蹤

### 總體進度
- **已完成**: 1/8 模組 (12.5%)
- **進行中**: 0/8 模組
- **待開始**: 7/8 模組

### 時間預估
- **Phase 1**: ~60 分鐘 (Throttle + RPM)
- **Phase 2**: ~50 分鐘 (Brake + Gear)
- **Phase 3**: ~105 分鐘 (Acceleration + Speed Diff + Distance Diff)
- **總計**: ~215 分鐘 (~3.5 小時)

---

## 🎯 下一步行動

### 立即執行
```powershell
# 1. 查看 Throttle Analysis 修改指南
python apply_dual_lap_mode.py --module throttle

# 2. 手動修改檔案
# modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py

# 3. 測試 Throttle Analysis
# (在 GUI 中測試 LEC L10 vs LEC L50)
```

### 建議順序
1. **Throttle Analysis** (最常用，優先實施)
2. **RPM Analysis** (常用，次優先)
3. **Brake Analysis** (中等使用頻率)
4. **Gear Analysis** (中等使用頻率)
5. 其他模組（根據使用需求決定）

---

## 📝 注意事項

### 常見陷阱
1. ⚠️ 確保 `lap1` 和 `lap2` 參數設為 `None` (而非 `1`)
2. ⚠️ 修改判斷邏輯時注意優先級順序
3. ⚠️ 記得在兩個地方都修改（`set_*_data` 和 `update_*_data`）
4. ⚠️ 調試輸出中的模組名稱要對應（如 `[THROTTLE_CHART]`）

### 測試重點
1. ✅ 同車手不同圈：應顯示兩條線
2. ✅ 同車手相同圈：應只顯示一條線
3. ✅ 圖例標籤正確：顯示 "車手 - 第X圈"
4. ✅ 統計表格正確：顯示兩個圈速的比較

---

## 🔗 相關資源

- **完整實施報告**: `IMPLEMENTATION_Dual_Lap_Comparison_Mode.md`
- **快速參考**: `QUICKREF_Dual_Lap_Mode.md`
- **測試腳本**: `test_dual_lap_mode.py`
- **應用工具**: `apply_dual_lap_mode.py`

---

**最後更新**: 2025-10-07  
**維護者**: F1T Team

