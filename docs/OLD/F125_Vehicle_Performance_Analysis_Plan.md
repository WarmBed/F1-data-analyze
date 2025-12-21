# F125 車輛性能綜合分析：核心算法與邏輯設計 (v2.0)

## 1. 設計目標 (Design Objective)

本模組旨在模擬 **「賽事工程師 (Race Engineer)」** 的思維邏輯。透過整合 FP2 的三個核心性能指標（彎道、直線、煞車），逆向推導車隊的 **車輛設定 (Setup Strategy)**，並結合賽道特徵（Track Profile），評估該設定的 **戰略適應性**。

### 核心輸入 (Inputs)
* **F120 (Cornering):** 彎道性能 (反映 Downforce & Mechanical Grip)
* **F121 (Straight):** 直線性能 (反映 Drag & Engine Power)
* **F122 (Braking):** 煞車性能 (反映 Stability & Confidence)
* **F100 (Track Map):** 賽道特徵 (反映 Environment Requirements)

---

## 2. 核心算法邏輯 (Core Algorithm)

### 步驟 A: 加權排名計算 (Weighted Ranking)

為了更精準判斷空氣動力學設定，我們不能單純取平均值，必須針對關鍵指標進行加權。

#### 1. 彎道綜合排名 (Cornering Rank)
**邏輯**：高速彎最能反映下壓力設定；低速彎受懸吊與機械抓地力影響較大。
* **公式**：
    $$Score_{Corner} = (Rank_{HighSpeed} \times 0.5) + (Rank_{MidSpeed} \times 0.3) + (Rank_{LowSpeed} \times 0.2)$$
* **意義**：分數越低（排名越前），代表彎道性能越強。

#### 2. 直線綜合排名 (Straight Rank)
**邏輯**：極速 (Top Speed) 容易受 DRS 或尾流影響，加入 100-300km/h 加速時間可反映純粹的阻力 (Drag) 與動力特性。
* **公式**：
    $$Score_{Straight} = (Rank_{TopSpeed} \times 0.7) + (Rank_{Accel} \times 0.3)$$

---

### 步驟 B: 設定逆向推導 (Setup Reverse Engineering)

透過比較「彎道排名」與「直線排名」的差異 (Delta)，推斷車輛設定偏向。

* **計算優勢分數 (Advantage Score)**：
    $$Score_{Advantage} = Score_{Straight} - Score_{Corner}$$
    *(註：排名數值越小越好)*

* **判斷邏輯**：
    * **正值大 (> Threshold)**：直線排名差 (數值大)，彎道排名好 (數值小) $\rightarrow$ **高下壓力 (High Downforce / Draggy)**
    * **負值大 (< -Threshold)**：直線排名好 (數值小)，彎道排名差 (數值大) $\rightarrow$ **低下壓力 (Low Downforce / Slippery)**
    * **接近零 (~0)**：兩者排名相近 $\rightarrow$ **平衡設定 (Balanced)**

* **煞車修正 (Confidence Modifier)**：
    * 若 F122 顯示煞車穩定性極高 (CV 低)，且被判斷為「高下壓力」，則判定信心指數從「中」提升為「高」。

---

### 步驟 C: 賽道適應性評估 (Suitability Assessment)

**修正重點**：基於流體力學物理與賽道特性進行匹配。
* **高速賽道** (高 High Speed %): 需要低阻力 (Low Drag) 以最大化直道收益。
* **低速賽道** (高 Low Speed %): 需要高下壓力 (High Downforce) 以最大化過彎速度。

| 賽道類型 (Track Type) | 車輛設定 (Setup) | 評估結果 | 理由 |
| :--- | :--- | :--- | :--- |
| **High Speed** (e.g. Monza) | **Low Downforce** | ✅ **Excellent** | 符合賽道特性 (Low Drag Efficiency) |
| **High Speed** (e.g. Monza) | **High Downforce** | ❌ **Poor** | 直道將成為攻擊目標 (Sitting Duck) |
| **Low Speed** (e.g. Monaco) | **High Downforce** | ✅ **Excellent** | 符合賽道特性 (Max Grip) |
| **Low Speed** (e.g. Monaco) | **Low Downforce** | ❌ **Poor** | 缺乏抓地力，輪胎滑動嚴重 |

---

## 3. Python 核心代碼實作 (Implementation)

以下代碼可直接整合至 `F125_vehicle_performance.py`。

```python
import numpy as np

class VehiclePerformanceAnalyzer:
    def __init__(self, f120_data, f121_data, f122_data, f100_data):
        self.f120 = f120_data  # Corners
        self.f121 = f121_data  # Straights
        self.f122 = f122_data  # Braking
        self.f100 = f100_data  # Track Map
        self.drivers = self._get_driver_list()
        
        # 設定閾值 (可配置)
        self.RANK_DIFF_THRESHOLD = 4.0 

    def _get_driver_list(self):
        # 假設從 F120 獲取車手列表
        return [d['driver'] for d in self.f120['mode_a_unified']['drivers']]

    def calculate_rankings(self):
        """
        計算加權排名
        """
        metrics = {}
        
        # 1. 提取原始數據
        for driver in self.drivers:
            # F120: 提取各速域彎心速度
            d_120 = next((d for d in self.f120['mode_a_unified']['drivers'] if d['driver'] == driver), None)
            # 簡化：假設這裡已經解析出 low/mid/high 的 median_speed
            # 實際實作需根據 F120 JSON 結構遍歷 'corners'
            
            # F121: 提取極速與加速
            d_121 = next((d for d in self.f121['mode_a_unified']['drivers'] if d['driver'] == driver), None)
            top_speed = d_121['speed_stats']['median']
            accel_time = d_121['acceleration_100_300_stats']['median']
            
            metrics[driver] = {
                'corner_high': 0, # 需填入實際值
                'corner_mid': 0,
                'corner_low': 0,
                'top_speed': top_speed,
                'accel_time': accel_time # 注意：時間越短越好
            }
            
            # (此處省略從 JSON 提取具體數值的詳細 parsing 代碼，聚焦於邏輯)

        # 2. 計算分項排名 (Rank 1 is best)
        # 注意：速度越高 rank 越小；時間越短 rank 越小
        # 這裡用 helper function 生成排名字典
        
        # 3. 計算綜合加權分數
        results = {}
        for driver in self.drivers:
            # 假設已獲得該車手的各項 Rank (1-20)
            r_high = 5  # 範例值
            r_mid = 6
            r_low = 8
            r_speed = 15
            r_accel = 14
            
            # 核心算法 A: 彎道加權 (高速彎權重最大)
            corner_score = (r_high * 0.5) + (r_mid * 0.3) + (r_low * 0.2)
            
            # 核心算法 B: 直線加權 (極速為主，加速為輔)
            straight_score = (r_speed * 0.7) + (r_accel * 0.3)
            
            results[driver] = {
                'corner_score': corner_score,
                'straight_score': straight_score
            }
            
        return results

    def determine_setup_and_suitability(self, driver, corner_score, straight_score):
        """
        核心算法：設定推導與賽道適應性匹配
        """
        # --- Step 1: 推導設定 (Setup Inference) ---
        
        # Advantage Score > 0: 直線排名差(數值大) - 彎道排名好(數值小) = 高下壓力
        advantage = straight_score - corner_score
        
        setup_type = "Balanced"
        if advantage > self.RANK_DIFF_THRESHOLD:
            setup_type = "High Downforce"
        elif advantage < -self.RANK_DIFF_THRESHOLD:
            setup_type = "Low Downforce"
            
        # --- Step 2: 賽道特徵分析 (Track Profiling) ---
        
        # 從 F100 獲取數據
        track_dist = self.f100['data']['speed_distribution']
        high_speed_pct = track_dist['high_speed_percentage']
        low_speed_pct = track_dist['low_speed_percentage']
        
        track_char = "Balanced Track"
        if high_speed_pct > 60: 
            track_char = "High Speed Track" # e.g. Monza, Spa
        elif low_speed_pct > 35: # 閾值可調
            track_char = "Low Speed Track" # e.g. Monaco, Singapore
            
        # --- Step 3: 適應性匹配 (Suitability Matching) ---
        
        suitability_score = 0
        reason = ""
        
        if track_char == "High Speed Track":
            if setup_type == "Low Downforce":
                suitability_score = 9.0
                reason = "完美匹配：高速賽道採用低阻力設定，極速優勢明顯。"
            elif setup_type == "High Downforce":
                suitability_score = 4.0
                reason = "策略風險：高速賽道採用高阻力設定，直道易受攻擊 (Sitting Duck)。"
            else:
                suitability_score = 7.0
                reason = "中規中矩：平衡設定。"
                
        elif track_char == "Low Speed Track":
            if setup_type == "High Downforce":
                suitability_score = 9.5
                reason = "完美匹配：低速賽道採用高下壓力，最大化機械抓地力。"
            elif setup_type == "Low Downforce":
                suitability_score = 3.0
                reason = "嚴重失誤：低速賽道缺乏下壓力，輪胎滑動將導致圈速大損。"
            else:
                suitability_score = 6.5
                reason = "尚可：但在扭曲路段可能缺乏競爭力。"
                
        else: # Balanced Track
            if setup_type == "Balanced":
                suitability_score = 9.0
                reason = "適合：平衡型賽道採用平衡設定。"
            else:
                suitability_score = 7.5
                reason = f"偏科設定 ({setup_type})：可能在特定路段有優勢，但整體妥協。"

        return {
            "driver": driver,
            "inferred_setup": setup_type,
            "track_character": track_char,
            "suitability_score": suitability_score,
            "verdict": reason,
            "metrics": {
                "corner_rank_score": round(corner_score, 1),
                "straight_rank_score": round(straight_score, 1),
                "setup_bias": round(advantage, 1)
            }
        }

    def run_full_analysis(self):
        # 1. 計算所有排名
        rank_scores = self.calculate_rankings()
        
        # 2. 生成報告
        report = []
        for driver, scores in rank_scores.items():
            result = self.determine_setup_and_suitability(
                driver, 
                scores['corner_score'], 
                scores['straight_score']
            )
            report.append(result)
            
        return report