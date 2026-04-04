# F1T x Assetto Corsa: 真實數據驅動模擬系統 - 可行性與架構研究

**版本**: 1.0  
**日期**: 2026-01-22  
**狀態**: 規劃階段  
**目標**: 建立橋樑連接 F1T 真實數據分析與 Assetto Corsa 物理模擬引擎。

---

## 1. 核心願景 (Vision)
利用 F1 練習賽 (FP1/FP2/FP3) 的真實遙測數據，量化每位車手的「當下狀態」，並將其轉譯為賽車模擬器 (Assetto Corsa) 的性能參數。在真實排位賽 (Q) 與正賽 (R) 開始前，進行數百次電腦模擬 (Monte Carlo Simulation)，預測賽事走向、事故風險與最終排名。

---

## 2. 系統架構 (System Architecture)

### 模組 A: F1T 數據特徵提取器 (Features Extractor)
*   **位置**: `modules/gui/simulation_adapter/` (需新增)
*   **輸入**: FastF1/OpenF1 歷史數據 (2022-2025) + 當週 FP 數據
*   **核心算法**:
    1.  **基準單圈 (Base Pace)**: 以前三名平均成績為基準 (1.0)。
    2.  **實力因子 (Performance Delta)**: 計算每位車手落後基準的 % (例如 +0.5%)。
    3.  **穩定性指數 (Consistency)**: 基於 Long Run 的圈速標準差。
    4.  **侵略性指數 (Aggression)**: 基於歷史事故率與超車嘗試次數。
*   **輸出**: `race_config_{Year}_{Race}.json`

### 模組 B: 參數轉譯中間件 (Performance Translator)
*   **功能**: 將抽象的 F1 數據映射為 AC 具體的物理參數。
*   **Mapping Table**:

| F1 真實指標 | 變數 | Assetto Corsa 參數 (server/entry_list) | 影響效果 |
| :--- | :--- | :--- | :--- |
| **單圈速度** | Pace Gap | **Ballast (壓艙物)** | 每 +10kg 約慢 0.3秒 (需動態校準) |
| **最高尾速** | Top Speed | **Restrictor (進氣限制)** | 限制引擎馬力輸出，影響直線速度 |
| **駕駛失誤率** | Error Rate | **AI Consistency** | 數值越低，AI 越容易鎖死或跑開 |
| **攻擊慾望** | Overtakes | **AI Aggression** | 數值越高，AI 越敢晚煞車與切內線 |
| **起跑能力** | Launch | **Reaction Time** | (由 CSP 參數控制或隨機變數) |

### 模組 C: 模擬執行器 (Simulation Runner)
*   **工具**: Python subprocess + Content Manager CLI (或直接操作 server_cfg.ini)
*   **流程**:
    1.  生成批次處理設定檔。
    2.  啟動 AC 無介面模式 / 快速渲染模式。
    3.  監控比賽進程 (透過 Shared Memory 或 Log)。
    4.  收集結果。

---

## 3. 關鍵技術挑戰與解決方案

### Q1: AI 路線單一化問題 (Fast_lane.ai)
*   **問題**: Assetto Corsa 的傳統 AI 依賴單一最佳路徑 (`fast_lane.ai`)，導致看起來像「火車巡遊」。
*   **解決方案 (核心技術)**: **性能差異模擬 (Performance-based Simulation)**
    *   **原理**: 我們不修改 AI 的幾何路徑，而是給予不同的物理限制。
    *   **機制**: 當後車 (Pace 快/Ballast 輕) 在直線或出彎比前車快時，AC 的物理引擎會強制後車變線 (Overtake logic)，自然形成多線並行的攻防畫面。
    *   **結論**: 只要 Performance Delta (性能差) 足夠精確，AI 就不會在同一條線上排隊。

### Q2: 性能平衡 (BoP) 的轉換模型
*   **模型**: 線性回歸模型 (Linear Regression Model)
*   **公式**: `Ballast_KG = (Gap_Seconds / Sensitivity_Factor) * 10`
    *   `Gap_Seconds`: 相對於 P1 的圈速差距 (來自 FP2)。
    *   `Sensitivity_Factor`: 該賽道每 10kg 會慢幾秒 (通常約 0.3s~0.4s，需校準)。
    *   **範例**: 
        *   VER (P1): Gap 0.0s -> 0kg
        *   HAM (P5): Gap 0.3s -> (0.3 / 0.3) * 10 = **10kg**
        *   SAR (P20): Gap 2.0s -> (2.0 / 0.3) * 10 = **66kg**

### Q3: 模組 (MOD) 依賴性
*   **需求**: 必須使用高品質且物理統一的 F1 MOD (如 RSS Formula Hybrid)。
*   **統一性**: 20 台車使用同一車輛物理模型，僅透過參數調整性能，避免不同車隊 MOD 原始物理不平衡的問題。
5. 開發路線圖 (Roadmap)

### 階段 I: 數據轉譯核心 (Data Translation Core) - **目前焦點**
- [ ] **任務 1.1**: 定義 BoP 轉換數學模型 (初步設定每 10kg = 0.3s)。
- [ ] **任務 1.2**: 建立 `AcDataConverter` 類別，負責提取 FP2 數據並標準化。
- [ ] **任務 1.3**: 實現 JSON 與 INI 雙格式輸出，確保能對接 AC。
- [ ] **驗證**: 檢查生成的權重分佈是否合理 (例如 P20 不應該重達 300kg，需設定上限)。

### 階段 II: 模擬環境搭建與校準 (Environment & Calibration)
- [ ] **任務 2.1**: 選定標準測試賽道 (例如 Monza 或 Spa，變數較少)。
- [ ] **任務 2.2**: 進行實際 AC 測試，驗證 10kg 帶來的實際圈速影響。
- [ ] **任務 2.3**: 根據測試結果修正 BoP 係數 (`Sensitivity_Factor`)。

### 階段 III: 自動化流程整合 (Automation)
- [ ] **任務 3.1**: 開發 Python 啟動器調用 Content Manager。
- [ ] **任務 3.2**: 實現蒙地卡羅模擬 (批次跑 100 場)。
- [ ] **任務 3.3**: 統計分析模組 (輸出勝率、頒獎台機率) 供 F1T GUI 讀取預覽。
    *   **INI (AC 格式)**: 直接貼上至 `entry_list.ini` 或透過 CM API 注入。

### 4.2 檔案介面定義

**輸出檔案: `ac_sim_config.json`**
```json
{
  "session_info": { "year": 2025, "track": "Suzuka", "base_pace": 88.114 },
  "physics_model": { "sec_per_10kg": 0.3, "model_name": "RSS_FH_2025" },
  "grid": [
    {
      "driver": "VER",
      "team": "Red Bull Racing",
      "real_pace_gap": 0.000,
      "tyre_compound": "C3",
      "sim_parameters": {
        "ballast_kg": 0,
        "restrictor": 0,
        "ai_level": 100,
        "aggression": 90
      }
    },
    {
      "driver": "HAM",
      "real_pace_gap": 0.430,
      "tyre_compound": "C3",
      "sim_parameters": {
        "ballast_kg": 14,
        "restrictor": 2,
        "ai_level": 100,
        "aggression": 85
      }
    }
  ]
}
```

### 4.3 核心參數映射邏輯 (Mapping Logic) - 階段 I 定案

| 模擬目標 | AC 參數 (Entry List) | F1T 數據來源 | 轉換邏輯 |
| :--- | :--- | :--- | :--- |
| **彎道/整體圈速** | `BALLAST` (kg) | FP2 Pace Gap | `Gap / 0.3s * 10kg` (線性回歸) |
| **直線極速** | `RESTRICTOR` (%) | Speed Trap | 若低於基準 3km/h，每 1km/h 增加 1% |
| **駕駛風格/失誤** | `AI_LEVEL` (0-100) | 穩定度 (Consistency) | 標準差越小 -> AI_LEVEL 越高 (MAX=100) |
| **攻防侵略性** | `AGGRESSION` (%) | 歷史風格 (History) | 激進型 (VER/MAG)=90%+; 穩重型 (BOT)=60% |
| **初始輪胎抓地** | `SKIN` / `TYRES` | 預測起跑輪胎 | 對應 MOD 車輛的 Soft/Med/Hard 係數 |
| **輪胎磨耗** | (物理副作用) | (自然模擬) | AC 物理引擎特性：車重(Ballast)增加自然加速磨耗 |

---

## 5. 開發路線圖 (Roadmap)

### 階段 I: 數據轉譯原型 (可行性驗證)
- [ ] 腳本: 讀取 FP2 數據，計算 20 位車手 Pace 排名。
- [ ] 腳本: 輸出簡單的 `ac_entry_list.ini` 片段，包含 Ballast 設定。
- [ ] 測試: 手動將參數填入 AC，觀察 VER 是否真的比 SAR 快。

### 階段 II: 自動化執行 (MVP)
- [ ] 開發 Python `AcServerManager` 類別。
- [ ] 實現自動校準 (Auto-Calibration) 功能。
- [ ] 實現「一鍵模擬排位賽」。

### 階段 III: 完整模擬系統
- [ ] 整合至 F1T GUI (新增分頁 "Simulation")。
- [ ] 視覺化：模擬結果與真實結果的對比圖表。

---

## 5. 所需資源
*   Assetto Corsa (Ultimate Edition)
*   Content Manager
*   CSP (Custom Shaders Patch)
*   RSS Formula Hybrid 2025 (或其他高品質 F1 MOD)
*   目標賽道的 AI Line 優化版
