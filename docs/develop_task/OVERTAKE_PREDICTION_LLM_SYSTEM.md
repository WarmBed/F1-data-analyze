# 超車預測 LLM 系統開發方案

**建立日期**: 2025-12-05  
**狀態**: 開發中 (Phase 1)  
**優先級**: 高  
**預估開發週期**: 6-9 週

---

## 0. 開發進度追蹤

### F81-F85 功能狀態

| 功能 ID | 功能名稱 | 狀態 | 完成日期 | 說明 |
|---------|----------|------|----------|------|
| F81 | 超車事件數據收集器 | ✅ 完成 | 2025-12-05 | 從 LiveF1 JSON 收集訓練數據 |
| F82 | 超車預測模型訓練器 | 🔄 開發中 | - | XGBoost 模型訓練 |
| F83 | 超車預測推理器 | ⏳ 待開發 | - | 模型推理 + 即時預測 |
| F84 | 超車預測 LLM 解說器 | ⏳ 待開發 | - | GPT-4/Claude 解說生成 |
| F85 | 即時超車監控 | ⏳ 待開發 | - | Live Timing 整合 |

### F81 收集結果 (2024 年度)

| 指標 | 數值 |
|------|------|
| 處理賽事數 | 15 場 |
| 超車事件總數 | 3,488 次 |
| 訓練樣本總數 | 75,802 筆 |
| 正樣本比例 | 5.90% |
| 最多超車賽事 | Las Vegas (358 次) |
| 最少超車賽事 | British (116 次) |

### 輸出檔案

| 檔案 | 路徑 | 說明 |
|------|------|------|
| 超車事件 | `data/overtake_prediction/overtake_events.csv` | 每次超車的詳細記錄 |
| 訓練樣本 | `data/overtake_prediction/training_samples.csv` | 模型訓練用樣本 |

---

## 1. 專案目標

建立一個基於機器學習 + LLM 的即時超車預測系統，能夠：

1. **預測超車**: 在超車發生前預測可能性
2. **分析原因**: 超車發生後自動分析關鍵因素
3. **自然語言輸出**: 使用 LLM 生成易懂的解釋
4. **Live 整合**: 在 Live Timing 中即時顯示

---

## 2. 系統架構

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Overtake Prediction System v1.0                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────────────┐   │
│  │  Data Layer    │   │  ML Layer      │   │  LLM Layer                 │   │
│  │                │   │                │   │                            │   │
│  │  SignalR API   │──▶│  XGBoost       │──▶│  GPT-4 / Claude / Gemini   │   │
│  │  • Position.z  │   │  Classifier    │   │  • 原因解釋生成            │   │
│  │  • CarData.z   │   │                │   │  • 策略建議                │   │
│  │  • TimingData  │   │  LSTM          │   │  • 多語言支援              │   │
│  │                │   │  Sequence      │   │                            │   │
│  └────────────────┘   └────────────────┘   └────────────────────────────┘   │
│           │                   │                        │                     │
│           ▼                   ▼                        ▼                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         Output Layer                                    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │ Live Timing  │  │ API Endpoint │  │ Notification │                  │ │
│  │  │ MDI Widget   │  │ REST/WebSocket│ │ Push Alert   │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 數據資產盤點

### 3.1 現有可用數據

| 數據類型 | 來源檔案 | 說明 |
|----------|----------|------|
| 超車歷史統計 | `train_overtake_rate.py` | 2023-2024 每場比賽超車統計 |
| 賽道超車難度 | `analyze_circuit_overtake_v2.py` | Q→R 位置保持率計算 |
| 車手超車能力 | `train_overtake_rate.py` | 淨超車數、超車比率 |
| 輪胎影響分析 | `train_overtake_rate.py` | 輪胎年齡差對超車的影響 |
| 即時遙測 | `signalr_client.py` | CarData.z, Position.z |
| 勝率模型框架 | `live_win_probability/` | XGBoost 訓練框架 |

### 3.2 需要新增收集的數據

| 數據類型 | 收集方式 | 用途 |
|----------|----------|------|
| 超車事件標註 | 從 Position 變化自動偵測 | 訓練標籤 |
| DRS 區域位置 | 賽道 JSON 配置 | 判斷 DRS 可用性 |
| 超車發生區段 | 結合賽道座標 | 預測超車地點 |
| 車手對戰歷史 | 歷史數據彙整 | H2H 特徵 |

---

## 4. 特徵工程設計

### 4.1 即時特徵 (Real-time Features)

```python
REALTIME_FEATURES = {
    # === 間距特徵 ===
    "gap_seconds": {
        "description": "與前車間距 (秒)",
        "source": "Position.z / TimingData",
        "importance": "HIGH"
    },
    "gap_delta": {
        "description": "間距變化率 (秒/圈)",
        "source": "計算: 當前間距 - 上圈間距",
        "importance": "HIGH"
    },
    "closing_rate": {
        "description": "追近速度 (秒/圈，正值=追近)",
        "source": "計算: 3圈移動平均",
        "importance": "HIGH"
    },
    
    # === 速度特徵 ===
    "speed_trap_delta": {
        "description": "Speed Trap 速度差 (km/h)",
        "source": "TimingData",
        "importance": "MEDIUM"
    },
    "sector_speed_advantage": {
        "description": "各區間速度優勢",
        "source": "CarData.z channel 2",
        "importance": "MEDIUM"
    },
    
    # === DRS 特徵 ===
    "drs_available": {
        "description": "DRS 是否可用 (gap < 1s)",
        "source": "計算: gap_seconds < 1.0",
        "importance": "CRITICAL"
    },
    "drs_zones_remaining": {
        "description": "本圈剩餘 DRS 區數量",
        "source": "賽道配置 + Position",
        "importance": "MEDIUM"
    },
    
    # === 輪胎特徵 ===
    "tyre_compound_attacker": {
        "description": "進攻者輪胎配方",
        "source": "TimingAppData",
        "importance": "HIGH"
    },
    "tyre_compound_defender": {
        "description": "防守者輪胎配方",
        "source": "TimingAppData",
        "importance": "HIGH"
    },
    "tyre_age_diff": {
        "description": "輪胎壽命差 (正值=進攻者較新)",
        "source": "TimingAppData",
        "importance": "HIGH"
    },
    "tyre_cliff_risk_defender": {
        "description": "防守者是否接近輪胎懸崖",
        "source": "計算: 根據配方和壽命",
        "importance": "MEDIUM"
    }
}
```

### 4.2 靜態特徵 (Static Features)

```python
STATIC_FEATURES = {
    # === 賽道特徵 ===
    "circuit_overtake_rate": {
        "description": "賽道每圈平均超車次數",
        "source": "train_overtake_rate.py 訓練結果",
        "values": {
            "Monza": 0.45,
            "Spa": 0.42,
            "Bahrain": 0.38,
            "Monaco": 0.08,
            "Singapore": 0.12,
            # ... 完整列表見 config
        }
    },
    "circuit_drs_zones": {
        "description": "DRS 區數量",
        "source": "賽道配置",
        "importance": "MEDIUM"
    },
    "circuit_overtake_sectors": {
        "description": "主要超車區段",
        "source": "賽道配置",
        "importance": "MEDIUM"
    },
    
    # === 車手特徵 ===
    "driver_overtake_skill": {
        "description": "車手超車能力評分 (0.7-1.3)",
        "source": "train_overtake_rate.py 訓練結果",
        "values": {
            "VER": 1.25,
            "HAM": 1.20,
            "ALO": 1.18,
            "NOR": 1.15,
            # ... 完整列表見 config
        }
    },
    "driver_defense_skill": {
        "description": "車手防守能力評分",
        "source": "被超車率反推",
        "importance": "MEDIUM"
    },
    
    # === 對戰歷史 ===
    "h2h_overtake_record": {
        "description": "兩車手歷史對戰超車記錄",
        "source": "歷史數據彙整",
        "importance": "LOW"
    }
}
```

### 4.3 情境特徵 (Context Features)

```python
CONTEXT_FEATURES = {
    "race_progress": {
        "description": "比賽進度 (0.0-1.0)",
        "source": "current_lap / total_laps",
        "importance": "MEDIUM"
    },
    "laps_remaining": {
        "description": "剩餘圈數",
        "source": "total_laps - current_lap",
        "importance": "MEDIUM"
    },
    "track_status": {
        "description": "賽道狀態 (Green/Yellow/SC/VSC/Red)",
        "source": "TrackStatus",
        "importance": "HIGH"
    },
    "weather_condition": {
        "description": "天氣狀況 (Dry/Damp/Wet)",
        "source": "WeatherData",
        "importance": "MEDIUM"
    },
    "position_attacker": {
        "description": "進攻者當前位置",
        "source": "Position.z",
        "importance": "LOW"
    },
    "championship_pressure": {
        "description": "積分壓力指數",
        "source": "積分榜計算",
        "importance": "LOW"
    }
}
```

---

## 5. 模型設計

### 5.1 超車預測模型 (OvertakePredictor)

**目標**: 預測未來 N 秒/圈內是否會發生超車

```python
class OvertakePredictionModel:
    """
    超車預測模型
    
    輸入: 兩車手的當前狀態特徵
    輸出: 
        - overtake_probability: 超車機率 (0.0-1.0)
        - estimated_laps: 預估超車所需圈數
        - likely_sector: 最可能發生超車的區段
    """
    
    def __init__(self):
        # 主分類器: XGBoost
        self.classifier = XGBClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            objective='binary:logistic',
            eval_metric='auc',
            use_label_encoder=False
        )
        
        # 序列模型: LSTM (用於時序特徵)
        self.sequence_model = None  # Phase 2
        
        # 特徵名稱
        self.feature_names = []
        
    def extract_features(self, 
                        attacker: dict, 
                        defender: dict,
                        circuit_info: dict,
                        race_state: dict) -> np.ndarray:
        """
        從原始數據提取特徵向量
        """
        features = []
        
        # 間距特徵
        features.append(attacker['gap_to_ahead'])
        features.append(attacker.get('gap_delta', 0))
        features.append(attacker.get('closing_rate', 0))
        
        # DRS 特徵
        features.append(1 if attacker['gap_to_ahead'] < 1.0 else 0)
        features.append(circuit_info.get('drs_zones', 2))
        
        # 輪胎特徵
        features.append(self._encode_compound(attacker['tyre_compound']))
        features.append(self._encode_compound(defender['tyre_compound']))
        features.append(defender['tyre_age'] - attacker['tyre_age'])
        
        # 賽道特徵
        features.append(circuit_info['overtake_rate'])
        
        # 車手特徵
        features.append(self._get_driver_skill(attacker['driver']))
        features.append(self._get_driver_defense(defender['driver']))
        
        # 情境特徵
        features.append(race_state['progress'])
        features.append(1 if race_state['track_status'] == 'GREEN' else 0)
        
        return np.array(features).reshape(1, -1)
    
    def predict(self, features: np.ndarray) -> dict:
        """
        預測超車機率
        """
        prob = self.classifier.predict_proba(features)[0][1]
        
        return {
            "probability": float(prob),
            "will_attempt": prob > 0.6,
            "confidence": "HIGH" if prob > 0.8 or prob < 0.2 else "MEDIUM",
            "likely_sector": self._predict_sector(features)
        }
    
    def _encode_compound(self, compound: str) -> int:
        """輪胎配方編碼"""
        mapping = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2, 
                   'INTERMEDIATE': 3, 'WET': 4}
        return mapping.get(compound.upper(), 1)
    
    def _get_driver_skill(self, driver_code: str) -> float:
        """獲取車手超車能力"""
        # 從 config 載入
        return DRIVER_OVERTAKE_SKILL.get(driver_code, 1.0)
    
    def _get_driver_defense(self, driver_code: str) -> float:
        """獲取車手防守能力"""
        return DRIVER_DEFENSE_SKILL.get(driver_code, 1.0)
    
    def _predict_sector(self, features: np.ndarray) -> str:
        """預測最可能發生超車的區段"""
        # 基於賽道配置返回
        return "Main Straight"  # 簡化版
```

### 5.2 訓練數據生成

```python
class OvertakeDataCollector:
    """
    從歷史賽事收集超車訓練數據
    
    標註邏輯:
    - 正樣本: 位置變化發生 (A 超越 B)
    - 負樣本: 保持在 DRS 範圍內但未超車的情況
    """
    
    def collect_from_race(self, year: int, race: str) -> pd.DataFrame:
        """
        從單場比賽收集超車數據
        """
        session = fastf1.get_session(year, race, 'R')
        session.load(laps=True, telemetry=True)
        
        samples = []
        laps = session.laps
        
        # 按圈遍歷
        for lap_num in range(2, int(laps['LapNumber'].max())):
            lap_data = laps[laps['LapNumber'] == lap_num]
            prev_lap_data = laps[laps['LapNumber'] == lap_num - 1]
            
            # 偵測位置變化
            overtakes = self._detect_overtakes(prev_lap_data, lap_data)
            
            # 為每個潛在超車機會生成樣本
            for attacker, defender in self._get_close_pairs(lap_data):
                is_overtake = (attacker, defender) in overtakes
                
                features = self._extract_features(
                    attacker, defender, lap_data, session
                )
                
                samples.append({
                    **features,
                    'overtake': 1 if is_overtake else 0,
                    'year': year,
                    'race': race,
                    'lap': lap_num
                })
        
        return pd.DataFrame(samples)
    
    def _detect_overtakes(self, prev_lap, curr_lap) -> set:
        """偵測超車事件"""
        overtakes = set()
        
        prev_positions = dict(zip(
            prev_lap['Driver'], 
            prev_lap['Position']
        ))
        curr_positions = dict(zip(
            curr_lap['Driver'], 
            curr_lap['Position']
        ))
        
        for driver, curr_pos in curr_positions.items():
            prev_pos = prev_positions.get(driver)
            if prev_pos and curr_pos < prev_pos:
                # 找出被超越的車手
                for other, other_curr in curr_positions.items():
                    other_prev = prev_positions.get(other)
                    if other_prev and prev_pos > other_prev and curr_pos < other_curr:
                        overtakes.add((driver, other))
        
        return overtakes
    
    def _get_close_pairs(self, lap_data, threshold=2.0) -> list:
        """獲取間距小於閾值的車手對"""
        pairs = []
        sorted_drivers = lap_data.sort_values('Position')
        
        for i in range(1, len(sorted_drivers)):
            attacker = sorted_drivers.iloc[i]
            defender = sorted_drivers.iloc[i-1]
            
            gap = attacker.get('GapToLeader', 0) - defender.get('GapToLeader', 0)
            if abs(gap) < threshold:
                pairs.append((attacker['Driver'], defender['Driver']))
        
        return pairs
```

---

## 6. LLM 整合設計

### 6.1 Prompt 模板

```python
OVERTAKE_EXPLANATION_PROMPT = """
你是一位專業的 F1 賽事分析師。基於以下數據，用簡潔的中文解釋超車預測結果。

## 車手資訊
- 進攻者: {attacker_name} ({attacker_team})
- 防守者: {defender_name} ({defender_team})

## 當前狀態
- 間距: {gap_seconds:.3f} 秒
- 間距變化: {gap_delta:+.3f} 秒/圈 ({"追近中" if gap_delta < 0 else "拉開中"})
- DRS: {"可用" if drs_available else "不可用"}

## 輪胎狀態
- {attacker_name}: {attacker_tyre} 胎 (已跑 {attacker_tyre_age} 圈)
- {defender_name}: {defender_tyre} 胎 (已跑 {defender_tyre_age} 圈)
- 輪胎差距: 進攻者{"較新" if tyre_age_diff > 0 else "較舊"} {abs(tyre_age_diff)} 圈

## 賽道資訊
- 賽道: {circuit_name}
- 超車難度: {overtake_difficulty}
- 剩餘圈數: {laps_remaining}

## 預測結果
- 超車機率: {probability:.1%}
- 預測區段: {likely_sector}

---

請用 50 字以內的中文，解釋為什麼 {attacker_name} {"很可能" if probability > 0.6 else "可能" if probability > 0.4 else "不太可能"} 超越 {defender_name}。
重點分析最關鍵的 1-2 個因素。
"""

OVERTAKE_HAPPENED_ANALYSIS_PROMPT = """
你是一位專業的 F1 賽事分析師。{attacker_name} 剛剛在第 {lap} 圈的 {sector} 成功超越了 {defender_name}。

## 超車前狀態
- 間距: {gap_before:.3f} 秒
- DRS: {"有使用" if drs_used else "未使用"}
- {attacker_name} 輪胎: {attacker_tyre} (壽命 {attacker_tyre_age} 圈)
- {defender_name} 輪胎: {defender_tyre} (壽命 {defender_tyre_age} 圈)

## 賽道特性
- 超車區: {overtake_zone}
- 賽道超車率: {circuit_overtake_rate}

---

請用 60 字以內的中文，分析這次超車成功的關鍵因素。
"""
```

### 6.2 LLM 服務封裝

```python
class OvertakeExplainer:
    """
    使用 LLM 生成超車預測/分析的自然語言解釋
    
    支援:
    - OpenAI GPT-4
    - Anthropic Claude
    - Google Gemini
    - 本地 LLM (Ollama)
    """
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini"):
        self.provider = provider
        self.model = model
        self._init_client()
    
    def _init_client(self):
        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI()
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic()
        elif self.provider == "ollama":
            import ollama
            self.client = ollama
    
    def explain_prediction(self, 
                          prediction: dict,
                          attacker: dict,
                          defender: dict,
                          context: dict) -> str:
        """
        生成超車預測的自然語言解釋
        """
        prompt = OVERTAKE_EXPLANATION_PROMPT.format(
            attacker_name=attacker['name'],
            attacker_team=attacker['team'],
            defender_name=defender['name'],
            defender_team=defender['team'],
            gap_seconds=context['gap_seconds'],
            gap_delta=context.get('gap_delta', 0),
            drs_available=context['drs_available'],
            attacker_tyre=attacker['tyre_compound'],
            attacker_tyre_age=attacker['tyre_age'],
            defender_tyre=defender['tyre_compound'],
            defender_tyre_age=defender['tyre_age'],
            tyre_age_diff=defender['tyre_age'] - attacker['tyre_age'],
            circuit_name=context['circuit'],
            overtake_difficulty=context['overtake_difficulty'],
            laps_remaining=context['laps_remaining'],
            probability=prediction['probability'],
            likely_sector=prediction['likely_sector']
        )
        
        return self._call_llm(prompt)
    
    def analyze_overtake(self,
                        attacker: dict,
                        defender: dict,
                        overtake_info: dict) -> str:
        """
        分析已發生的超車事件
        """
        prompt = OVERTAKE_HAPPENED_ANALYSIS_PROMPT.format(
            attacker_name=attacker['name'],
            defender_name=defender['name'],
            lap=overtake_info['lap'],
            sector=overtake_info['sector'],
            gap_before=overtake_info['gap_before'],
            drs_used=overtake_info.get('drs_used', False),
            attacker_tyre=attacker['tyre_compound'],
            attacker_tyre_age=attacker['tyre_age'],
            defender_tyre=defender['tyre_compound'],
            defender_tyre_age=defender['tyre_age'],
            overtake_zone=overtake_info.get('zone', 'Turn 1'),
            circuit_overtake_rate=overtake_info.get('circuit_rate', 0.3)
        )
        
        return self._call_llm(prompt)
    
    def _call_llm(self, prompt: str) -> str:
        """調用 LLM API"""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif self.provider == "ollama":
                response = self.client.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response['message']['content']
                
        except Exception as e:
            print(f"[OVERTAKE_EXPLAINER] LLM Error: {e}")
            return self._fallback_explanation()
    
    def _fallback_explanation(self) -> str:
        """LLM 失敗時的備用解釋"""
        return "輪胎優勢和 DRS 是關鍵因素。"
```

---

## 7. Live Timing 整合

### 7.1 新增 MDI 模組

```python
# modules/gui/live_timing/live_timing_modules/overtake_prediction.py

class OvertakePredictionWidget(QWidget):
    """
    即時超車預測面板
    
    顯示:
    - 高機率超車對 (>60%)
    - 中機率超車對 (40-60%)
    - 最近發生的超車分析
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
        # 載入模型
        self._model = OvertakePredictionModel()
        self._model.load("models/overtake_prediction_v1.pkl")
        
        # LLM 解釋器
        self._explainer = OvertakeExplainer(provider="openai")
        
        # 數據緩存
        self._last_predictions: List[dict] = []
        self._recent_overtakes: List[dict] = []
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel(tr("overtake_prediction", "Overtake Prediction"))
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # 高機率區域
        self._high_prob_list = QListWidget()
        self._high_prob_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #FF4444;
            }
        """)
        layout.addWidget(QLabel(tr("high_probability", "High Probability (>60%)")))
        layout.addWidget(self._high_prob_list)
        
        # 中機率區域
        self._medium_prob_list = QListWidget()
        layout.addWidget(QLabel(tr("medium_probability", "Medium Probability")))
        layout.addWidget(self._medium_prob_list)
        
        # 最近超車
        self._recent_overtakes_list = QListWidget()
        layout.addWidget(QLabel(tr("recent_overtakes", "Recent Overtakes")))
        layout.addWidget(self._recent_overtakes_list)
    
    def update_predictions(self, snapshot: dict):
        """
        根據最新快照更新預測
        """
        drivers = self._extract_drivers(snapshot)
        circuit_info = self._get_circuit_info(snapshot)
        race_state = self._get_race_state(snapshot)
        
        predictions = []
        
        # 分析所有相鄰車手對
        sorted_drivers = sorted(drivers, key=lambda d: d['position'])
        
        for i in range(1, len(sorted_drivers)):
            attacker = sorted_drivers[i]
            defender = sorted_drivers[i-1]
            
            # 只分析間距 < 3 秒的
            if attacker['gap_to_ahead'] > 3.0:
                continue
            
            features = self._model.extract_features(
                attacker, defender, circuit_info, race_state
            )
            prediction = self._model.predict(features)
            
            if prediction['probability'] > 0.3:
                # 生成解釋
                explanation = self._explainer.explain_prediction(
                    prediction, attacker, defender,
                    {
                        'gap_seconds': attacker['gap_to_ahead'],
                        'drs_available': attacker['gap_to_ahead'] < 1.0,
                        'circuit': circuit_info['name'],
                        'overtake_difficulty': circuit_info['overtake_rate'],
                        'laps_remaining': race_state['laps_remaining']
                    }
                )
                
                predictions.append({
                    'attacker': attacker,
                    'defender': defender,
                    'probability': prediction['probability'],
                    'sector': prediction['likely_sector'],
                    'explanation': explanation
                })
        
        self._update_display(predictions)
    
    def _update_display(self, predictions: list):
        """更新 UI 顯示"""
        self._high_prob_list.clear()
        self._medium_prob_list.clear()
        
        for pred in sorted(predictions, key=lambda p: -p['probability']):
            text = (
                f"{pred['attacker']['driver']} → {pred['defender']['driver']} "
                f"[{pred['probability']:.0%}] @ {pred['sector']}\n"
                f"{pred['explanation']}"
            )
            
            if pred['probability'] > 0.6:
                self._high_prob_list.addItem(text)
            elif pred['probability'] > 0.4:
                self._medium_prob_list.addItem(text)


class OvertakePredictionMDI(BaseLiveTimingMDI):
    """
    超車預測 MDI 子視窗
    """
    
    MODULE_NAME = "overtake_prediction"
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        self.setWindowTitle(tr("overtake_prediction", "Overtake Prediction"))
        self.setMinimumSize(400, 500)
    
    def _setup_ui(self):
        self._widget = OvertakePredictionWidget(self)
        self._main_layout.addWidget(self._widget)
    
    def _on_snapshot_updated(self, snapshot: dict):
        """處理數據更新"""
        self._widget.update_predictions(snapshot)
```

### 7.2 模組註冊

```python
# 在 module_factory.py 中新增

MODULE_REGISTRY = {
    # ... 現有模組 ...
    "overtake_prediction": {
        "class": "OvertakePredictionMDI",
        "module": "modules.gui.live_timing.live_timing_modules.overtake_prediction",
        "name": tr("overtake_prediction", "Overtake Prediction"),
        "icon": "⚔️",
        "category": "analysis"
    }
}
```

---

## 8. 開發階段規劃

### Phase 1: 數據收集與標註 (2-3 週)

| 任務 | 優先級 | 預估時間 | 負責 |
|------|--------|----------|------|
| 擴展 `train_overtake_rate.py` 收集 2022-2024 數據 | P0 | 3 天 | |
| 建立超車事件自動偵測邏輯 | P0 | 2 天 | |
| 收集 DRS 區域配置數據 | P1 | 1 天 | |
| 建立車手對戰歷史數據庫 | P1 | 2 天 | |
| 生成訓練數據 CSV | P0 | 2 天 | |
| 數據品質驗證 | P0 | 1 天 | |

**產出物**:
- `data/overtake_prediction/training_data.csv`
- `config/circuit_overtake_config.json`
- `config/driver_overtake_stats.json`

### Phase 2: 模型訓練 (2-3 週)

| 任務 | 優先級 | 預估時間 | 負責 |
|------|--------|----------|------|
| 實作 `OvertakePredictionModel` 類別 | P0 | 2 天 | |
| 特徵工程優化 | P0 | 3 天 | |
| XGBoost 超參數調優 | P0 | 2 天 | |
| 交叉驗證與評估 | P0 | 1 天 | |
| LSTM 序列模型 (可選) | P2 | 3 天 | |
| 模型保存與載入 | P0 | 1 天 | |

**產出物**:
- `models/overtake_prediction_v1.pkl`
- `CLI_modules/cli/prediction/overtake_predictor.py`
- 評估報告

**目標指標**:
- AUC-ROC > 0.75
- Precision > 0.6 (高機率預測)
- Recall > 0.5

### Phase 3: LLM 整合 (1-2 週)

| 任務 | 優先級 | 預估時間 | 負責 |
|------|--------|----------|------|
| 實作 `OvertakeExplainer` 類別 | P0 | 2 天 | |
| Prompt 模板設計與優化 | P0 | 2 天 | |
| 多 LLM 提供商支援 | P1 | 1 天 | |
| 備用解釋邏輯 (無 LLM) | P1 | 1 天 | |
| 解釋品質測試 | P0 | 1 天 | |

**產出物**:
- `core/llm_explainer.py`
- Prompt 模板配置

### Phase 4: Live Timing 整合 (1-2 週)

| 任務 | 優先級 | 預估時間 | 負責 |
|------|--------|----------|------|
| 實作 `OvertakePredictionMDI` | P0 | 2 天 | |
| UI 設計與樣式 | P0 | 1 天 | |
| 與 DataManager 整合 | P0 | 1 天 | |
| 即時超車偵測 | P0 | 1 天 | |
| 效能優化 | P1 | 1 天 | |
| 測試與修復 | P0 | 2 天 | |

**產出物**:
- `modules/gui/live_timing/live_timing_modules/overtake_prediction.py`
- 完整功能測試

---

## 9. 技術依賴

### 9.1 Python 套件

```txt
# requirements_overtake.txt
xgboost>=2.0.0
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
fastf1>=3.0.0

# LLM Providers
openai>=1.0.0
anthropic>=0.18.0
ollama>=0.1.0  # 可選，本地 LLM

# 序列模型 (Phase 2)
tensorflow>=2.15.0  # 或 torch
```

### 9.2 API Keys (環境變數)

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 10. 預期輸出範例

### 10.1 Live Timing UI

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚔️ Overtake Prediction                              Lap 42/53   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 🔥 HIGH PROBABILITY (>60%)                                       │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ NOR → VER  [87%]  @ Main Straight                            ││
│ │ "Norris 輪胎較新 8 圈，DRS 已啟用，直線速度優勢明顯。"        ││
│ └──────────────────────────────────────────────────────────────┘│
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ HAM → LEC  [72%]  @ Turn 4                                   ││
│ │ "Hamilton 過去 3 圈每圈追近 0.3 秒，Leclerc 硬胎老化中。"    ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│ ⚡ MEDIUM PROBABILITY (40-60%)                                   │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ RUS → SAI  [52%]  @ Turn 1                                   ││
│ │ "間距 0.9 秒，DRS 可用但賽道超車難度高。"                    ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│ ✅ RECENT OVERTAKES                                              │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ Lap 40: PIA overtook ALO @ Turn 11                           ││
│ │ "Piastri 利用軟胎抓地力優勢，在髮夾彎內線超越 Alonso。"      ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 API 響應格式

```json
{
  "predictions": [
    {
      "attacker": "NOR",
      "defender": "VER",
      "probability": 0.87,
      "likely_sector": "Main Straight",
      "estimated_laps": 2,
      "explanation": "Norris 輪胎較新 8 圈，DRS 已啟用，直線速度優勢明顯。",
      "key_factors": [
        {"factor": "tyre_age_diff", "value": 8, "impact": "positive"},
        {"factor": "drs_available", "value": true, "impact": "positive"},
        {"factor": "speed_delta", "value": 12.5, "impact": "positive"}
      ]
    }
  ],
  "recent_overtakes": [
    {
      "lap": 40,
      "attacker": "PIA",
      "defender": "ALO",
      "sector": "Turn 11",
      "analysis": "Piastri 利用軟胎抓地力優勢，在髮夾彎內線超越 Alonso。"
    }
  ],
  "timestamp": "2025-12-05T14:32:15Z"
}
```

---

## 11. 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| 模型準確度不足 | 中 | 高 | 增加訓練數據、特徵工程優化 |
| LLM API 延遲 | 中 | 中 | 本地快取、備用規則解釋 |
| LLM API 成本 | 中 | 中 | 使用較便宜模型、限制調用頻率 |
| 即時處理效能 | 低 | 高 | 模型輕量化、批次預測 |
| DRS 區域數據不完整 | 低 | 低 | 手動補充配置 |

---

## 12. 成功指標

| 指標 | 目標值 | 測量方式 |
|------|--------|----------|
| 預測準確度 (AUC) | > 0.75 | 測試集評估 |
| 高機率預測精確度 | > 60% | P > 0.7 的預測準確率 |
| 解釋品質評分 | > 4/5 | 人工評估 |
| 預測延遲 | < 200ms | 效能測試 |
| 用戶滿意度 | > 80% | 用戶回饋 |

---

## 13. 後續擴展

### 13.1 Phase 2 功能

- [ ] 多圈序列預測 (LSTM/Transformer)
- [ ] 超車地點熱力圖
- [ ] 防守策略建議
- [ ] 語音播報整合

### 13.2 Phase 3 功能

- [ ] 即時視頻標記
- [ ] 超車回放分析
- [ ] 車隊策略建議
- [ ] 積分影響計算

---

## 附錄 A: 相關程式碼參考

| 檔案 | 說明 |
|------|------|
| `train_overtake_rate.py` | 現有超車統計訓練 |
| `analyze_circuit_overtake_v2.py` | 賽道超車難度分析 |
| `live_win_probability/predictor.py` | 勝率預測器參考 |
| `live_win_probability/model_trainer.py` | XGBoost 訓練參考 |
| `signalr_client.py` | SignalR 數據接收 |
| `ranking_tower.py` | Live Timing MDI 範例 |

---

**文件版本**: v1.0  
**最後更新**: 2025-12-05
