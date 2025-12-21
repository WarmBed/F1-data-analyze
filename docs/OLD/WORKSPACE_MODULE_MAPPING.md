# Workspace 模組映射表

本文檔記錄所有需要支援的 GUI 分析模組，用於 Workspace 序列化/反序列化。

---

## ✅ 已支援模組

| 模組名稱 | analysis_type | 類別名稱 | 導入路徑 | 參數 |
|---------|--------------|---------|---------|-----|
| Rain Analysis | `rain_weather`, `rain_analysis` | `RainAnalysisModuleAdapter` | `modules.gui.rain_analysis.rain_analysis_module` | year, race, session |
| Tire Analysis | `tire`, `tire_strategy` | `TireAnalysisModuleAdapter` | `modules.gui.tire_analysis.tire_analysis_module` | year, race, session |
| Track Analysis | `track_analysis` | `TrackAnalysisUniversal` | `modules.gui.track_analysis` | year, race, session |

---

## 🔄 待添加模組

### 📊 賽事分析模組

| 模組名稱 | analysis_type | 類別名稱 | 導入路徑 | 參數 | 優先級 |
|---------|--------------|---------|---------|-----|-------|
| Pitstop Analysis | `pitstop` | `PitstopAnalysisModule` | `modules.gui.pitstop_analysis.pitstop_analysis_mdi` | year, race, session | 🔥 高 |
| Accident Analysis | `accident` | `AccidentAnalysisModule` | `modules.gui.accident_analysis.accident_analysis_mdi` | year, race, session | 🔥 高 |
| Lap Box Plot | `lap_boxplot` | `LapBoxPlotAnalysisMDI` | `modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi` | year, race, session | 🔥 高 |

### 🏎️ 車手分析模組

| 模組名稱 | analysis_type | 類別名稱 | 導入路徑 | 參數 | 優先級 |
|---------|--------------|---------|---------|-----|-------|
| Telemetry Analysis | `telemetry` | `TelemetryAnalysisModule` | `modules.gui.telemetry_analysis_mdi` | year, race, session, driver1, driver2 | 🔥 高 |
| Driver Lap Analysis | `driver_lap` | `driverLapAnalysisMDI` | `modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_mdi` | year, race, session, driver | ⚡ 中 |
| Brake Analysis | `brake` | `BrakeAnalysisModule` | `modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi` | year, race, session, driver | ⚡ 中 |
| Throttle Analysis | `throttle` | `ThrottleAnalysisModule` | `modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi` | year, race, session, driver | ⚡ 中 |
| Gear Analysis | `gear` | `GearAnalysisModule` | `modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi` | year, race, session, driver | ⚡ 中 |

### 🎯 理想圈速分析模組

| 模組名稱 | analysis_type | 類別名稱 | 導入路徑 | 參數 | 優先級 |
|---------|--------------|---------|---------|-----|-------|
| Ideal Lap Ranking | `ideal_lap_ranking` | `IdealLapRankingTableMDI` | `modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_mdi` | year, race, session | ⚡ 中 |
| Ideal Lap Heatmap | `ideal_lap` | `IdealLapSectorHeatmapMDI` | `modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_mdi` | year, race, session | ⚡ 中 |
| Ideal Lap Comparison | `ideal_lap` | `IdealLapSectorComparisonMDI` | `modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_mdi` | year, race, session | ⚡ 中 |

### 📈 性能分析模組

| 模組名稱 | analysis_type | 類別名稱 | 導入路徑 | 參數 | 優先級 |
|---------|--------------|---------|---------|-----|-------|
| Straight Line Speed | `straight_line_speed` | `AllDriversStraightLineSpeedMDI` | `modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_mdi` | year, race, session | ⚡ 中 |
| Brake Performance | `brake_performance` | `AllDriversBrakePerformanceMDI` | `modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_mdi` | year, race, session | ⚡ 中 |
| Throttle Box Plot | `throttle_boxplot` | `ThrottleBoxPlotAnalysisModule` | `modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_module` | year, race, session | 🔵 低 |

### 📊 積分榜模組

| 模組名稱 | analysis_type | 類別名稱 | 導入路徑 | 參數 | 優先級 |
|---------|--------------|---------|---------|-----|-------|
| Driver Standings | `driver_standings` | `DriverStandingsMDI` | `modules.gui.driver_standings` | year | ⚡ 中 |
| Constructor Standings | `constructor_standings` | `ConstructorStandingsMDI` | `modules.gui.constructor_standings` | year | ⚡ 中 |
| Season Progress | `season_progress` | `SeasonProgressMDI` | `modules.gui.season_progress` | year | ⚡ 中 |
| Weather Timeline | `weather_timeline` | `WeatherTimelineMDI` | `modules.gui.weather_timeline` | year, race | 🔵 低 |

### 🔬 進階遙測模組

| 模組名稱 | analysis_type | 類別名稱 | 導入路徑 | 參數 | 優先級 |
|---------|--------------|---------|---------|-----|-------|
| Speed Analysis | `speed` | `SpeedAnalysisModule` | `modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi` | year, race, session, driver | 🔵 低 |
| RPM Analysis | `rpm` | `RPMAnalysisModule` | `modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi` | year, race, session, driver | 🔵 低 |
| Speed Diff | `speeddiff` | `SpeeddiffAnalysisModule` | `modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi` | year, race, session, driver1, driver2 | 🔵 低 |
| Distance Diff | `distancediff` | `distancediffAnalysisModule` | `modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi` | year, race, session, driver1, driver2 | 🔵 低 |
| Acceleration | `acceleration` | `accelerationAnalysisModule` | `modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi` | year, race, session, driver | 🔵 低 |
| Time Diff | `timediff` | `timediffAnalysisModule` | `modules.gui.lap_analysis.timediff_analysis.timediff_analysis_mdi` | year, race, session, driver1, driver2 | 🔵 低 |
| Throttle Line Chart | `throttle_line` | `ThrottleLineChartMDI` | `modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi` | year, race, session, driver | 🔵 低 |

---

## 🔧 實現策略

### 階段 1：核心模組（必須）✅
- [x] Rain Analysis
- [x] Tire Analysis
- [x] Track Analysis

### 階段 2：高優先級模組（優先實現）🔥
- [ ] Pitstop Analysis
- [ ] Accident Analysis
- [ ] Lap Box Plot
- [ ] Telemetry Analysis

### 階段 3：中優先級模組（按需實現）⚡
- [ ] Driver Lap Analysis
- [ ] Brake/Throttle/Gear Analysis
- [ ] Ideal Lap 系列
- [ ] Performance 系列
- [ ] Standings 系列

### 階段 4：低優先級模組（可選）🔵
- [ ] 進階遙測分析模組

---

## 📝 實現模板

```python
# 在 _create_module_instance 中添加：

# [模組名稱]
elif window_type == "[analysis_type]":
    from [導入路徑] import [類別名稱]
    module = [類別名稱](
        year=year,
        race=race,
        session=session,
        # 額外參數（如有）
    )
    print(f"[WORKSPACE] ✅ [模組名稱] 模組已創建 (type={window_type})")
    return module
```

---

## 🔍 參數類型說明

- **基礎參數**：`year`, `race`, `session`（所有模組共通）
- **車手參數**：`driver`, `driver1`, `driver2`（車手比較模組）
- **特殊參數**：部分模組可能需要額外參數（lap_number, sector 等）

---

## ⚠️ 注意事項

1. **analysis_type 重複**：部分模組共享相同的 `analysis_type`（例如 `ideal_lap`），需要額外識別方式
2. **參數差異**：不同模組需要不同參數組合
3. **向後兼容**：使用 `in ()` 支援多個別名（例如 `rain_weather` 和 `rain_analysis`）
4. **錯誤處理**：模組實例化失敗時返回 None

---

## 📊 進度追蹤

- **已支援**: 3 個模組
- **待添加**: 30+ 個模組
- **覆蓋率**: ~10%
