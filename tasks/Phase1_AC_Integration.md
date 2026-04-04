# Assetto Corsa 模擬器整合模組

## 專案狀態: Phase 1 完成

**最後更新**: 2026-01-22

---

## Phase 1 完成項目

- [x] 1. **建立專屬模組結構**: `modules/gui/simulation_adapter/`
    - [x] `__init__.py` - 模組導出
    - [x] `data_fusion.py` - 數據融合與 BoP 計算
    - [x] `config_generator.py` - AC INI/JSON 生成器

- [x] 2. **開發數據聚合核心 (`AcDataFusion`)**:
    - [x] 讀取 Function 121 (FP2 Straight Line) JSON 輸出
    - [x] 提取 Pace (Long Run 平均圈速) 數據
    - [x] 提取 Speed (最高尾速) 數據
    - [x] 2025 車手-車隊對應表 (DRIVER_TEAM_MAP_2025)
    - [x] 測試車手過濾 (TEST_DRIVERS_FILTER: DOO, DRU, SHW...)
    - [x] 隊友推算邏輯 (TEAMMATE_MAP_2025)

- [x] 3. **實作 BoP (性能平衡) 轉換邏輯**:
    - [x] `Ballast` 計算: 基於 Pace Gap (每 0.3s 差距 = 10kg)
    - [x] `Restrictor` 計算: 基於 Speed Gap (每 1km/h 差距 = 1%)
    - [x] 缺失 Long Run 數據推算: 隊友 +0.2s 或中位數 +0.3s

- [x] 4. **開發設定檔生成器 (`AcConfigGenerator`)**:
    - [x] 輸出 `sim_config_{year}_{race}_{session}.json`
    - [x] 輸出 `entry_list_{year}_{race}_{session}.ini`

- [x] 5. **測試腳本**:
    - [x] `run_ac_simulation_phase1.py` - 2025 澳洲站 FP2 案例

---

## 生成的檔案

| 檔案 | 路徑 | 說明 |
|------|------|------|
| INI 設定 | `ac_sim_output/entry_list_2025_Australia_FP2.ini` | AC Server 用 |
| JSON 摘要 | `ac_sim_output/sim_config_2025_Australia_FP2.json` | 數據預覽 |

---

## 2025 澳洲站 FP2 測試結果

| 排名 | 車手 | 車隊 | BALLAST | RESTRICTOR | Pace Source |
|------|------|------|---------|------------|-------------|
| P1 | NOR | McLaren | 0 kg | 0% | measured |
| P2 | ALB | Williams | 3 kg | 15% | measured |
| P3 | LEC | Ferrari | 7 kg | 14% | measured |
| P4 | PIA | McLaren | 8 kg | 13% | measured |
| P5 | HAM | Ferrari | 10 kg | 18% | measured |
| P6 | VER | Red Bull | 10 kg | 10% | measured |
| ... | GAS | Alpine | - | - | estimated (中位數) |
| ... | RUS | Mercedes | 19 kg | 13% | estimated (隊友 ANT) |

**過濾車手**: DOO (Alpine 測試車手)

---

## Phase 2 計畫 (待 AC 驗證後)

- [ ] 1. **AC 實際測試**: 載入 INI 觀察 AI 行為
- [ ] 2. **係數校準**: 根據模擬結果調整 SEC_PER_10KG, SPEED_KMH_PER_1PCT_RESTRICTOR
- [ ] 3. **預測準確度**: 比較 AC 模擬結果與真實 Q/R 排名
- [ ] 4. **批次生成**: 為 2025 所有賽事自動生成 INI

---

## Phase 3 計畫 (長期)

- [ ] 1. **GUI 整合**: 在 F1T GUI 新增 "AC 模擬設定" 功能模組
- [ ] 2. **F131 整合**: 引入 FP2-Race 相關性數據
- [ ] 3. **輪胎策略**: 加入輪胎選擇建議
- [ ] 4. **AI 個性化**: 根據車手風格調整 AGGRESSION

---

## 使用方式

### 前置條件
```powershell
# 先生成 FP2 直線分析數據
python f1_analysis_modular_main.py -f 121 -y 2025 -r Australia -s FP2
```

### 執行模擬設定生成
```powershell
python run_ac_simulation_phase1.py
```

### 輸出位置
```
ac_sim_output/
├── entry_list_2025_Australia_FP2.ini   # 複製到 AC Server
└── sim_config_2025_Australia_FP2.json  # 數據預覽
```

---

## 相關文件

- 可行性研究: [tasks/AC_Simulation_Feasibility_Study.md](AC_Simulation_Feasibility_Study.md)
- 數據融合: [modules/gui/simulation_adapter/data_fusion.py](../modules/gui/simulation_adapter/data_fusion.py)
- 設定生成: [modules/gui/simulation_adapter/config_generator.py](../modules/gui/simulation_adapter/config_generator.py)
