# 🚨 Accident Analysis GUI - 方案B改進版 (無賽道地圖 + Safety/Penalties)

## 🎨 **方案B改進版：統計視角 (Statistics View)** - 適合中等視窗

```
┌──────────────────────────────────────────────────────────────────────────┐
│  🚨 Accident Analysis - 2025 Japan Grand Prix                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  📊 Quick Stats       ⚠️ 12  🟡🟡 3  🟡 8  🔴 1  🚩 2  ⚖️ 4           │
│                                                                          │
│  🏎️ Driver Incident Frequency                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ VER ████████████████░░░░  (12 Track Limits, 1 Yellow)             │ │
│  │ HAM █████████░░░░░░░░░░░  (7 Track Limits, 1 Collision)           │ │
│  │ LEC ██████░░░░░░░░░░░░░░  (5 Track Limits)                        │ │
│  │ SAI ████░░░░░░░░░░░░░░░░  (3 Track Limits, 1 Yellow)              │ │
│  │ ALO ███░░░░░░░░░░░░░░░░░  (2 Track Limits, 🔴 RED FLAG)           │ │
│  │ RUS ██░░░░░░░░░░░░░░░░░░  (2 Track Limits)                        │ │
│  │ ... (Click to expand all 20 drivers)                              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  🏁 Safety Periods (2 total)     ⚖️ Penalties (4 total)                 │
│  ┌─────────────────────────────┐ ┌──────────────────────────────────────┐│
│  │ Lap 24-29  🔴 Red Flag      │ │ Lap 12  VER  5s Time  Track Limits  ││
│  │ └─ Heavy crash T13 (ALO)    │ │ Lap 24  HAM  10s Time Collision     ││
│  │    Race suspended 5 laps    │ │ Lap 35  LEC  Drive Th Pit Exit Line ││
│  │                             │ │ Lap 42  RUS  5s Time  Track Limits  ││
│  │ Lap 48-53  🚩 Safety Car    │ │                                      ││
│  │ └─ Oil spill T9             │ │ Total Time Penalties: 20s            ││
│  │    6 laps neutralized       │ │ Drive Through Penalties: 1           ││
│  └─────────────────────────────┘ └──────────────────────────────────────┘│
│                                                                          │
│  🏆 Severity Classification                                              │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐              │
│  │ 🟢 Low (15) │ 🟡 Med (8)  │ 🟠 High (3) │ 🔴 Crit (1) │              │
│  │ Track Lmts  │ Yellow Flgs │ Double Ylw  │ Red Flag    │              │
│  │ 62.5%       │ 33.3%       │ 12.5%       │ 4.2%        │              │
│  └─────────────┴─────────────┴─────────────┴─────────────┘              │
│                                                                          │
│  📈 Race Impact Analysis                                                 │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 🕐 Race Duration: 1h 42m 15s (+14m 32s due to interruptions)      │ │
│  │ 🏁 Green Flag Time: 1h 27m 43s (85.8% of total race time)         │ │
│  │ 🚩 Safety Periods: 14m 32s (14.2% of total race time)             │ │
│  │ 📊 Incident Rate: 0.45 per lap (24 incidents / 53 laps)           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  [🔍 Filter: All | 🔄 Last updated: 19:45:23 | 💾 Export JSON]          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 **替代佈局：上下分區版本** (如果視窗較窄)

```
┌─────────────────────────────────────────────────────────────┐
│  🚨 Accident Analysis - 2025 Japan GP                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 Quick Stats   ⚠️ 12  🟡🟡 3  🟡 8  🔴 1  🚩 2  ⚖️ 4     │
│                                                             │
│  🏎️ Driver Incident Frequency                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ VER ████████████████░░░░  (13x incidents)          │   │
│  │ HAM █████████░░░░░░░░░░░  (8x incidents)           │   │
│  │ LEC ██████░░░░░░░░░░░░░░  (5x incidents)           │   │
│  │ SAI ████░░░░░░░░░░░░░░░░  (4x incidents)           │   │
│  │ ALO ███░░░░░░░░░░░░░░░░░  (3x incidents) 🔴        │   │
│  │ ... (Show top 5, click to expand)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🏁 Safety Periods (2)        ⚖️ Penalties (4)             │
│  ┌───────────────────────┐   ┌─────────────────────────┐   │
│  │ L24-29 🔴 Red Flag    │   │ VER  5s   Track Limits │   │
│  │ L48-53 🚩 Safety Car  │   │ HAM  10s  Collision    │   │
│  │ Total: 11 laps (20.8%)│   │ LEC  DT   Pit Exit     │   │
│  └───────────────────────┘   │ RUS  5s   Track Limits │   │
│                               └─────────────────────────┘   │
│  🏆 Severity Distribution                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🟢 Low: 15 (62.5%) ████████████████████████         │   │
│  │ 🟡 Med: 8 (33.3%)  ████████████                     │   │
│  │ 🟠 High: 3 (12.5%) ████                             │   │
│  │ 🔴 Crit: 1 (4.2%)  █                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📈 Race Impact: +14m 32s | Incident Rate: 0.45/lap       │
│                                                             │
│  [🔍 Filter] [💾 Export] [🔄 Refresh: 19:45:23]            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 **設計重點說明**

### ✅ **新增功能**
1. **🏁 Safety Periods 區塊**
   - 顯示紅旗、Safety Car時段
   - 包含持續時間和影響範圍
   - 計算中斷時間百分比

2. **⚖️ Penalties 區塊**
   - 列出所有處罰詳情
   - 統計總時間處罰和Drive Through數量
   - 按時間順序排列

3. **📈 Race Impact Analysis**
   - 比賽總時長vs正常時長
   - 綠旗時間百分比
   - 事故率計算（incidents per lap）

### ✅ **保留的優秀元素**
- 車手事故頻率橫條圖（直觀比較）
- 嚴重程度分類（顏色編碼）
- Quick Stats 一行概覽
- 簡潔的篩選和匯出控制

### ✅ **中等視窗優化**
- 寬度控制在70-80字符
- 重要資訊置於上半部
- 可摺疊展開的車手清單
- 左右分欄充分利用空間

---

## 🛠️ **實作重點**

### **資料結構需求**
```python
safety_periods = [
    {
        "type": "red_flag",
        "start_lap": 24,
        "end_lap": 29,
        "duration_laps": 5,
        "reason": "Heavy crash T13 (ALO)",
        "description": "Race suspended"
    },
    {
        "type": "safety_car", 
        "start_lap": 48,
        "end_lap": 53,
        "duration_laps": 6,
        "reason": "Oil spill T9",
        "description": "6 laps neutralized"
    }
]

penalties = [
    {
        "lap": 12,
        "driver": "VER",
        "penalty_type": "5s_time",
        "reason": "Track Limits"
    },
    # ... more penalties
]
```

### **新增 Widget 組件**
1. **SafetyPeriodsWidget** - 安全期間展示
2. **PenaltiesSummaryWidget** - 處罰摘要
3. **RaceImpactWidget** - 比賽影響分析
4. **DriverIncidentBarChart** - 車手事故橫條圖

### **佈局結構**
```python
# 主佈局：垂直排列
main_layout = QVBoxLayout()
main_layout.addWidget(quick_stats_widget)
main_layout.addWidget(driver_frequency_widget)

# 中間區域：左右分欄
middle_layout = QHBoxLayout()
middle_layout.addWidget(safety_periods_widget)
middle_layout.addWidget(penalties_widget)
main_layout.addLayout(middle_layout)

# 底部區域
main_layout.addWidget(severity_classification_widget)
main_layout.addWidget(race_impact_widget)
main_layout.addWidget(controls_widget)
```

---

## 🎨 **視覺化強化建議**

### **顏色主題**
- 🟢 **低風險事件**: `#4CAF50` (綠色)
- 🟡 **中等風險**: `#FF9800` (橙色)  
- 🟠 **高風險**: `#FF5722` (深橙)
- 🔴 **危急事件**: `#F44336` (紅色)
- 🚩 **Safety Car**: `#FFC107` (黃色)

### **圖示使用**
- `⚠️` Track Limits
- `🟡🟡` Double Yellow
- `🟡` Yellow Flag  
- `🔴` Red Flag
- `🚩` Safety Car
- `⚖️` Penalties
- `🏁` Safety Periods

### **互動功能**
1. 車手清單可展開/收合
2. 點擊車手名稱顯示詳細事故
3. 懸停顯示完整事故描述
4. 處罰項目點擊顯示詳細規則

---

## 💡 **這個設計的優勢**

1. **✅ 移除複雜地圖**：減少視覺干擾，專注數據分析
2. **✅ 加強統計面向**：Safety Periods和Penalties提供關鍵資訊  
3. **✅ 中等視窗友善**：佈局適合常見的MDI子視窗大小
4. **✅ 保持B方案精神**：車手頻率橫條圖和分類統計仍為核心
5. **✅ 實用性強**：Race Impact Analysis提供實際賽事影響評估

**這個改進版本如何？需要再調整任何部分嗎？** 🎯