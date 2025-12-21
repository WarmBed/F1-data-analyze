# Function 77: 車手特徵增強計畫

## 專案概述

**目標**: 改進 Function 77 賽道特定模型，加入車手個人特徵以提升排名預測能力（Spearman 相關係數）  
**當前狀態**: 墨西哥模型 MAE 0.891s (優秀)，但 Spearman 0.6015 (未達標)  
**目標提升**: Spearman 從 0.60 → 0.80+，Top-5 準確率從 60% → 80%+  
**訓練數據**: 2022-2024（符合新技術規則）  
**驗證數據**: 2025 墨西哥站（Race 20）

---

## 問題診斷回顧

### 當前模型的核心問題

```python
# 墨西哥 2025 預測失誤
實際 Top-5: NOR (P1), LEC (P2), HAM (P3), RUS (P4), VER (P5)
預測 Top-5: NOR (P1), ANT (P2), HAM (P3), RUS (P4), HAD (P5)

❌ 問題：
- LEC (P2) 被預測為 P6
- VER (P5) 被預測為 P10
- ANT (P6) 被誤判為 P2
- HAD (P9) 被誤判為 P5

根本原因：模型只看 FP3 表現，忽略車手長期實力差異
```

### 預測方差過小問題

```
訓練數據 (2022-2024): 平均 77.914s ± 1.265s
2025 實際: 平均 76.730s ± 0.7s

預測輸出: 77.3-77.6s（僅 0.3s 範圍！）
→ 所有車手「壓縮成一團」
→ 無法區分排名細微差異
```

---

## Phase 1: 數據收集與整理（預估 2-3 天）

### 1.1 建立車手資料庫

**目標**: 建立包含所有車手基本資訊的 JSON 檔案

**檔案位置**: `data/driver_database.json`

**數據結構**:
```json
{
  "drivers": {
    "VER": {
      "full_name": "Max Verstappen",
      "number": 1,
      "team_2024": "Red Bull Racing",
      "team_2025": "Red Bull Racing",
      "nationality": "Dutch",
      "birth_year": 1997,
      "career_start_year": 2015,
      "career_wins": 61,
      "career_poles": 40,
      "career_podiums": 109,
      "world_championships": 3,
      "career_points": 2900.5,
      "career_fastest_laps": 33
    },
    "HAM": {
      "full_name": "Lewis Hamilton",
      "number": 44,
      "team_2024": "Mercedes",
      "team_2025": "Ferrari",
      "nationality": "British",
      "birth_year": 1985,
      "career_start_year": 2007,
      "career_wins": 105,
      "career_poles": 104,
      "career_podiums": 201,
      "world_championships": 7,
      "career_points": 4700.5,
      "career_fastest_laps": 66
    }
  }
}
```

**數據來源**:
- 官方 F1 網站: https://www.formula1.com/en/drivers.html
- Wikipedia F1 車手頁面
- Ergast API: http://ergast.com/mrd/

**實作任務**:
- [ ] 建立 `scripts/collect_driver_database.py` 腳本
- [ ] 從 Ergast API 抓取車手生涯統計
- [ ] 手動補充 2025 年車隊歸屬
- [ ] 驗證所有 2022-2025 參賽車手資料完整

**驗證標準**:
```python
# 必須包含所有參賽車手
required_drivers = [
    'VER', 'HAM', 'LEC', 'NOR', 'PIA', 'SAI', 'RUS', 'PER', 
    'ALO', 'STR', 'GAS', 'OCO', 'HUL', 'MAG', 'TSU', 'RIC',
    'ALB', 'SAR', 'BOT', 'ZHO', 'ANT', 'BEA', 'LAW', 'HAD'
]
assert all(d in driver_database['drivers'] for d in required_drivers)
```

---

### 1.2 提取賽道歷史表現

**目標**: 從現有 JSON 檔案提取每位車手在各賽道的歷史表現

**檔案位置**: `data/driver_track_history.json`

**數據結構**:
```json
{
  "Mexico": {
    "VER": {
      "appearances": 10,
      "avg_qualifying_position": 2.3,
      "best_qualifying_position": 1,
      "avg_race_position": 1.8,
      "best_race_position": 1,
      "podium_count": 8,
      "podium_rate": 0.8,
      "dnf_count": 1,
      "dnf_rate": 0.1,
      "avg_qualifying_time": 76.234,
      "best_qualifying_time": 75.946
    },
    "HAM": {
      "appearances": 15,
      "avg_qualifying_position": 3.1,
      ...
    }
  },
  "Monaco": {
    "HAM": {
      "appearances": 18,
      "avg_qualifying_position": 2.1,
      "best_qualifying_position": 1,
      "podium_count": 16,
      "podium_rate": 0.89
    }
  }
}
```

**數據來源**:
```python
# 從現有 FP/Q/R JSON 檔案提取
source_files = [
    "json/track_features_*.json",      # 賽道特徵檔案
    "json/qualifying_analysis_*.json", # 排位賽分析
    "json/race_analysis_*.json"        # 正賽分析
]
```

**實作任務**:
- [ ] 建立 `scripts/extract_driver_track_history.py`
- [ ] 遍歷所有 2018-2024 的 JSON 檔案
- [ ] 計算每位車手在每個賽道的統計數據
- [ ] 處理缺失值（車手未參加該站）

**處理邏輯**:
```python
def extract_track_history(track_name, year_range=(2018, 2024)):
    """
    提取車手賽道歷史
    """
    history = defaultdict(lambda: {
        'appearances': 0,
        'qualifying_positions': [],
        'race_positions': [],
        'qualifying_times': [],
        'dnf_flags': []
    })
    
    for year in range(*year_range):
        json_files = glob(f"json/*{track_name}*{year}*.json")
        for file in json_files:
            data = load_json(file)
            # 提取車手數據...
            
    # 計算統計量
    for driver, stats in history.items():
        stats['avg_qualifying_position'] = np.mean(stats['qualifying_positions'])
        stats['podium_rate'] = sum(p <= 3 for p in stats['race_positions']) / len(stats['race_positions'])
        ...
```

---

### 1.3 收集 2025 賽季當前表現

**目標**: 抓取 2025 賽季前 19 場的車手表現數據

**檔案位置**: `data/season_2025_performance.json`

**數據結構**:
```json
{
  "season": 2025,
  "races_completed": 19,
  "last_update": "2025-10-27T12:00:00Z",
  "drivers": {
    "NOR": {
      "championship_position": 1,
      "total_points": 389,
      "avg_qualifying_position": 2.1,
      "avg_race_position": 2.5,
      "wins": 4,
      "poles": 6,
      "podiums": 12,
      "dnf_count": 1,
      "last_3_qualifying": [1, 2, 1],
      "last_3_races": [1, 3, 2],
      "last_5_qualifying": [2, 1, 2, 1, 3],
      "form_trend": "improving"
    },
    "VER": {
      "championship_position": 2,
      "total_points": 331,
      "avg_qualifying_position": 3.5,
      "avg_race_position": 3.8,
      "last_3_qualifying": [5, 4, 6],
      "form_trend": "declining"
    }
  }
}
```

**數據來源**:
- FastF1 API (2025 R1-R19)
- 官方 F1 積分榜
- 已收集的 2025 JSON 檔案

**實作任務**:
- [ ] 建立 `scripts/collect_2025_season_stats.py`
- [ ] 使用 FastF1 API 抓取 R1-R19 數據
- [ ] 計算趨勢指標（form_trend）
- [ ] 設定自動更新機制（每場賽後）

**趨勢計算**:
```python
def calculate_form_trend(recent_positions):
    """
    計算車手狀態趨勢
    """
    if len(recent_positions) < 3:
        return "insufficient_data"
    
    # 線性回歸斜率
    x = np.arange(len(recent_positions))
    slope, _ = np.polyfit(x, recent_positions, 1)
    
    if slope < -0.5:
        return "improving"     # 名次下降 = 表現提升
    elif slope > 0.5:
        return "declining"     # 名次上升 = 表現下滑
    else:
        return "stable"
```

---

### 1.4 建立車隊實力數據

**目標**: 提取車隊層級的競爭力指標

**檔案位置**: `data/team_performance.json`

**數據結構**:
```json
{
  "2025": {
    "McLaren": {
      "championship_position": 1,
      "total_points": 593,
      "avg_qualifying_position": 2.8,
      "avg_race_position": 3.1,
      "podium_count": 18,
      "driver_lineup": ["NOR", "PIA"]
    },
    "Ferrari": {
      "championship_position": 2,
      "total_points": 557,
      "avg_qualifying_position": 3.5,
      "driver_lineup": ["LEC", "SAI"]
    },
    "Red Bull Racing": {
      "championship_position": 3,
      "avg_qualifying_position": 4.2
    }
  },
  "track_specific": {
    "Mexico": {
      "Red Bull Racing": {
        "historical_avg_position": 2.1,
        "best_result": 1,
        "podium_rate": 0.85
      },
      "McLaren": {
        "historical_avg_position": 3.2
      }
    }
  }
}
```

**實作任務**:
- [ ] 建立 `scripts/collect_team_performance.py`
- [ ] 從 2025 賽季數據計算車隊統計
- [ ] 從歷史數據提取賽道專精
- [ ] 處理車隊更名（例如 AlphaTauri → RB）

---

## Phase 2: 特徵工程實作（預估 3-4 天）

### 2.1 建立 DriverFeatureEngineer 類別

**檔案位置**: `CLI_modules/cli/prediction/driver_feature_engineer.py`

**類別架構**:
```python
class DriverFeatureEngineer:
    """
    車手特徵工程器
    
    整合多種數據源，為每位車手生成全面的特徵向量
    """
    
    def __init__(self):
        self.driver_db = self._load_driver_database()
        self.track_history = self._load_track_history()
        self.season_stats = self._load_season_stats()
        self.team_stats = self._load_team_stats()
        
    def extract_features(self, driver: str, track: str, year: int, 
                        fp3_data: dict) -> dict:
        """
        提取車手特徵向量
        
        Args:
            driver: 車手代碼（例如 'VER'）
            track: 賽道名稱（例如 'Mexico'）
            year: 年份（例如 2025）
            fp3_data: FP3 數據字典
            
        Returns:
            特徵字典（43 個特徵）
        """
        features = {}
        
        # 1. 基礎實力特徵（5 個）
        features.update(self._get_career_stats(driver))
        
        # 2. 賽道專精特徵（5 個）
        features.update(self._get_track_performance(driver, track))
        
        # 3. 當前狀態特徵（4 個）
        features.update(self._get_current_form(driver, year))
        
        # 4. 車隊實力特徵（4 個）
        features.update(self._get_team_strength(driver, track, year))
        
        # 5. FP3 表現特徵（21 個，原有）
        features.update(self._extract_fp3_features(fp3_data))
        
        # 6. 衍生特徵（4 個）
        features.update(self._create_derived_features(features))
        
        return features
        
    def _get_career_stats(self, driver: str) -> dict:
        """基礎實力特徵"""
        profile = self.driver_db['drivers'].get(driver, {})
        return {
            'driver_career_wins': profile.get('career_wins', 0),
            'driver_career_poles': profile.get('career_poles', 0),
            'driver_championships': profile.get('world_championships', 0),
            'driver_experience_years': 2025 - profile.get('career_start_year', 2025),
            'driver_age': 2025 - profile.get('birth_year', 2000)
        }
        
    def _get_track_performance(self, driver: str, track: str) -> dict:
        """賽道專精特徵"""
        history = self.track_history.get(track, {}).get(driver, {})
        return {
            'driver_avg_position_this_track': history.get('avg_qualifying_position', 10.0),
            'driver_best_position_this_track': history.get('best_qualifying_position', 20),
            'driver_podium_rate_this_track': history.get('podium_rate', 0.0),
            'driver_dnf_rate_this_track': history.get('dnf_rate', 0.0),
            'driver_track_appearances': history.get('appearances', 0)
        }
        
    def _get_current_form(self, driver: str, year: int) -> dict:
        """當前狀態特徵"""
        season = self.season_stats.get(str(year), {}).get('drivers', {}).get(driver, {})
        
        # 計算最近表現
        last_3 = season.get('last_3_qualifying', [10, 10, 10])
        form_score = self._calculate_form_score(last_3)
        
        return {
            'driver_season_avg_position': season.get('avg_qualifying_position', 10.0),
            'driver_last_3_avg': np.mean(last_3),
            'driver_championship_position': season.get('championship_position', 20),
            'driver_form_score': form_score
        }
        
    def _get_team_strength(self, driver: str, track: str, year: int) -> dict:
        """車隊實力特徵"""
        team = self._get_driver_team(driver, year)
        team_data = self.team_stats.get(str(year), {}).get(team, {})
        track_data = self.team_stats.get('track_specific', {}).get(track, {}).get(team, {})
        
        return {
            'team_avg_position_this_year': team_data.get('avg_qualifying_position', 10.0),
            'team_championship_position': team_data.get('championship_position', 10),
            'team_avg_position_this_track': track_data.get('historical_avg_position', 10.0),
            'team_podium_rate_this_track': track_data.get('podium_rate', 0.0)
        }
        
    def _create_derived_features(self, features: dict) -> dict:
        """衍生特徵"""
        return {
            # 經驗 × 當前狀態
            'experience_form_interaction': (
                features['driver_experience_years'] * 
                (11 - features['driver_form_score']) / 10
            ),
            # 生涯成就 × 賽道專精
            'career_track_interaction': (
                features['driver_career_wins'] * 
                features['driver_podium_rate_this_track']
            ),
            # 車隊實力 × 個人表現
            'team_driver_synergy': (
                (11 - features['team_avg_position_this_year']) * 
                (11 - features['driver_season_avg_position'])
            ),
            # 賽道熟悉度評分
            'track_familiarity_score': min(
                features['driver_track_appearances'] / 10, 1.0
            )
        }
```

**實作任務**:
- [ ] 建立 `DriverFeatureEngineer` 類別
- [ ] 實作 5 個特徵提取方法
- [ ] 添加缺失值處理邏輯
- [ ] 編寫單元測試

---

### 2.2 整合至 TrackSpecificTrainer

**檔案位置**: `CLI_modules/cli/prediction/track_specific_trainer.py`

**修改內容**:
```python
class TrackSpecificTrainer:
    """
    賽道特定模型訓練器 v2.0
    新增車手特徵支援
    """
    
    def __init__(self, enable_driver_features=True):
        self.enable_driver_features = enable_driver_features
        if enable_driver_features:
            self.driver_engineer = DriverFeatureEngineer()
        
    def prepare_training_data(self, track_name: str, year_range=(2022, 2024)):
        """
        準備訓練數據（加入車手特徵）
        """
        X = []
        y = []
        
        for year in range(*year_range):
            # 載入該年的排位數據
            data = self._load_track_data(track_name, year)
            
            for driver_record in data:
                # 原有特徵
                features = self._extract_base_features(driver_record)
                
                # 新增車手特徵
                if self.enable_driver_features:
                    driver_features = self.driver_engineer.extract_features(
                        driver=driver_record['driver'],
                        track=track_name,
                        year=year,
                        fp3_data=driver_record['fp3']
                    )
                    features.update(driver_features)
                
                X.append(features)
                y.append(driver_record['qualifying_time'])
        
        return pd.DataFrame(X), np.array(y)
    
    def train_track_model(self, track_name: str):
        """
        訓練賽道特定模型（v2.0）
        """
        print(f"\n{'='*60}")
        print(f"訓練 {track_name} 模型（v2.0 - 含車手特徵）")
        print(f"{'='*60}\n")
        
        # 準備數據
        X, y = self.prepare_training_data(track_name)
        
        print(f"特徵數量: {X.shape[1]} 個")
        print(f"樣本數量: {X.shape[0]} 筆")
        print(f"特徵列表: {list(X.columns)}\n")
        
        # 切分訓練/測試集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 特徵標準化
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # 訓練模型
        model = XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            reg_alpha=0.1,    # L1 正則化
            reg_lambda=1.0,   # L2 正則化
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # 評估
        train_pred = model.predict(X_train_scaled)
        test_pred = model.predict(X_test_scaled)
        
        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        test_r2 = r2_score(y_test, test_pred)
        
        print(f"訓練 MAE: {train_mae:.3f}s")
        print(f"測試 MAE: {test_mae:.3f}s")
        print(f"測試 R²: {test_r2:.4f}")
        
        # 儲存模型
        model_data = {
            'model': model,
            'scaler': scaler,
            'track_name': track_name,
            'version': '2.0',
            'feature_names': list(X.columns),
            'performance': {
                'samples': len(X),
                'train_mae': train_mae,
                'test_mae': test_mae,
                'test_r2': test_r2,
                'features_count': X.shape[1]
            },
            'train_date': datetime.now().isoformat()
        }
        
        output_path = f"models/track_specific_v2/{track_name}.pkl"
        with open(output_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        return model_data
```

**實作任務**:
- [ ] 修改 `prepare_training_data()` 方法
- [ ] 添加特徵標準化
- [ ] 添加 L1/L2 正則化
- [ ] 更新模型版本標記為 v2.0

---

### 2.3 特徵選擇與重要性分析

**檔案位置**: `scripts/analyze_feature_importance.py`

**實作內容**:
```python
import shap
from sklearn.feature_selection import SelectKBest, f_regression

def analyze_feature_importance(model_data, X_test, y_test):
    """
    分析特徵重要性
    """
    model = model_data['model']
    feature_names = model_data['feature_names']
    
    # 1. XGBoost 內建重要性
    importance = model.feature_importances_
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    print("\n=== Top 20 重要特徵 ===")
    print(feature_importance.head(20))
    
    # 2. SHAP 分析
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    # SHAP 摘要圖
    shap.summary_plot(shap_values, X_test, feature_names=feature_names, 
                     show=False, plot_size=(12, 8))
    plt.savefig('reports/feature_importance_shap.png', dpi=300, bbox_inches='tight')
    
    # 3. Permutation Importance
    from sklearn.inspection import permutation_importance
    perm_importance = permutation_importance(
        model, X_test, y_test, n_repeats=10, random_state=42
    )
    
    perm_df = pd.DataFrame({
        'feature': feature_names,
        'importance': perm_importance.importances_mean
    }).sort_values('importance', ascending=False)
    
    print("\n=== Permutation Importance (Top 20) ===")
    print(perm_df.head(20))
    
    return feature_importance, perm_df

def select_best_features(X_train, y_train, k=20):
    """
    選擇最佳 K 個特徵
    """
    selector = SelectKBest(score_func=f_regression, k=k)
    selector.fit(X_train, y_train)
    
    selected_features = X_train.columns[selector.get_support()].tolist()
    print(f"\n=== 選擇的 {k} 個特徵 ===")
    for i, feat in enumerate(selected_features, 1):
        print(f"{i}. {feat}")
    
    return selected_features
```

**實作任務**:
- [ ] 實作 SHAP 分析
- [ ] 實作 Permutation Importance
- [ ] 生成特徵重要性報告
- [ ] 確定最佳特徵子集（防止過擬合）

---

## Phase 3: 模型訓練與驗證（預估 2-3 天）

### 3.1 墨西哥模型重訓練（v2.0）

**執行腳本**: `scripts/train_mexico_v2.py`

**訓練配置**:
```python
# 訓練參數
TRAINING_CONFIG = {
    'track_name': 'Mexico',
    'year_range': (2022, 2024),
    'test_size': 0.2,
    'random_state': 42,
    'enable_driver_features': True,
    'feature_selection': {
        'method': 'shap',      # 'all', 'shap', 'kbest'
        'top_k': 30            # 從 43 個中選 30 個
    },
    'model_params': {
        'n_estimators': 200,
        'max_depth': 6,
        'learning_rate': 0.05,
        'reg_alpha': 0.1,      # L1 正則化
        'reg_lambda': 1.0,     # L2 正則化
        'subsample': 0.8,      # 樣本採樣比例
        'colsample_bytree': 0.8  # 特徵採樣比例
    }
}
```

**訓練流程**:
```python
def train_mexico_v2():
    """
    訓練墨西哥模型 v2.0（含車手特徵）
    """
    print("\n" + "="*80)
    print("Function 77 v2.0: 墨西哥模型訓練（2022-2024）")
    print("="*80 + "\n")
    
    # 1. 初始化訓練器
    trainer = TrackSpecificTrainer(enable_driver_features=True)
    
    # 2. 準備數據
    print("[1/5] 準備訓練數據...")
    X, y = trainer.prepare_training_data('Mexico', (2022, 2024))
    print(f"✓ 樣本數: {len(X)} 筆")
    print(f"✓ 特徵數: {X.shape[1]} 個")
    print(f"✓ 年份分布:")
    print(f"  - 2022: {len([r for r in X.index if '2022' in str(r)])} 筆")
    print(f"  - 2023: {len([r for r in X.index if '2023' in str(r)])} 筆")
    print(f"  - 2024: {len([r for r in X.index if '2024' in str(r)])} 筆")
    
    # 3. 特徵選擇（可選）
    if TRAINING_CONFIG['feature_selection']['method'] != 'all':
        print(f"\n[2/5] 特徵選擇（{TRAINING_CONFIG['feature_selection']['method']}）...")
        selected_features = select_best_features(
            X, y, k=TRAINING_CONFIG['feature_selection']['top_k']
        )
        X = X[selected_features]
        print(f"✓ 保留 {len(selected_features)} 個特徵")
    
    # 4. 訓練模型
    print("\n[3/5] 訓練模型...")
    model_data = trainer.train_track_model('Mexico')
    
    # 5. 特徵重要性分析
    print("\n[4/5] 分析特徵重要性...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    feature_importance, perm_importance = analyze_feature_importance(
        model_data, X_test, y_test
    )
    
    # 6. 生成報告
    print("\n[5/5] 生成訓練報告...")
    generate_training_report(model_data, feature_importance, perm_importance)
    
    print("\n" + "="*80)
    print("✓ 墨西哥模型 v2.0 訓練完成！")
    print(f"✓ 模型檔案: models/track_specific_v2/Mexico.pkl")
    print(f"✓ 訓練報告: reports/Mexico_v2_training_report.md")
    print("="*80 + "\n")
    
    return model_data
```

**實作任務**:
- [ ] 編寫 `train_mexico_v2.py` 腳本
- [ ] 執行訓練並記錄日誌
- [ ] 生成訓練報告
- [ ] 比較 v1.0 vs v2.0 性能

**預期結果**:
```
預期改善：
- 測試 MAE: 0.323s → 0.25-0.35s (維持或略降)
- 測試 R²: 0.7613 → 0.75-0.85 (提升)
- 特徵數: 26 → 30-35 (增加車手特徵)
```

---

### 3.2 2025 墨西哥站驗證測試

**執行腳本**: `scripts/validate_mexico_2025_v2.py`

**測試流程**:
```python
def validate_mexico_2025_v2():
    """
    使用 v2.0 模型預測 2025 墨西哥站
    """
    print("\n" + "="*80)
    print("Function 77 v2.0: 2025 墨西哥站驗證測試")
    print("="*80 + "\n")
    
    # 1. 載入模型
    print("[1/6] 載入模型...")
    with open('models/track_specific_v2/Mexico.pkl', 'rb') as f:
        model_data = pickle.load(f)
    print(f"✓ 模型版本: {model_data['version']}")
    print(f"✓ 訓練日期: {model_data['train_date']}")
    print(f"✓ 特徵數量: {model_data['performance']['features_count']}")
    
    # 2. 載入 2025 數據
    print("\n[2/6] 載入 2025 墨西哥站數據...")
    test_data = load_2025_mexico_data()
    print(f"✓ 測試車手: {len(test_data)} 位")
    
    # 3. 特徵工程
    print("\n[3/6] 提取車手特徵...")
    driver_engineer = DriverFeatureEngineer()
    X_test = []
    drivers = []
    actual_times = []
    
    for record in test_data:
        features = driver_engineer.extract_features(
            driver=record['driver'],
            track='Mexico',
            year=2025,
            fp3_data=record['fp3']
        )
        X_test.append(features)
        drivers.append(record['driver'])
        actual_times.append(record['qualifying_time'])
    
    X_test = pd.DataFrame(X_test)
    X_test = X_test[model_data['feature_names']]  # 確保特徵順序一致
    
    # 4. 預測
    print("\n[4/6] 執行預測...")
    scaler = model_data['scaler']
    model = model_data['model']
    
    X_test_scaled = scaler.transform(X_test)
    predictions = model.predict(X_test_scaled)
    
    # 5. 評估
    print("\n[5/6] 評估預測性能...")
    results_df = pd.DataFrame({
        'driver': drivers,
        'actual_time': actual_times,
        'predicted_time': predictions,
        'error': predictions - actual_times,
        'abs_error': np.abs(predictions - actual_times)
    })
    
    results_df['actual_rank'] = results_df['actual_time'].rank()
    results_df['predicted_rank'] = results_df['predicted_time'].rank()
    
    # 絕對誤差指標
    mae = results_df['abs_error'].mean()
    median_error = results_df['abs_error'].median()
    std_error = results_df['abs_error'].std()
    
    print("\n=== 絕對誤差 (MAE) 評估 ===")
    print(f"MAE: {mae:.3f}s")
    print(f"中位數誤差: {median_error:.3f}s")
    print(f"標準差: {std_error:.3f}s")
    print(f"最大誤差: {results_df['abs_error'].max():.3f}s ({results_df.loc[results_df['abs_error'].idxmax(), 'driver']})")
    print(f"最小誤差: {results_df['abs_error'].min():.3f}s ({results_df.loc[results_df['abs_error'].idxmin(), 'driver']})")
    
    # 趨勢驗證指標
    from scipy.stats import spearmanr
    spearman_corr, _ = spearmanr(results_df['actual_rank'], results_df['predicted_rank'])
    
    print("\n=== 趨勢驗證 (Spearman) 評估 ===")
    print(f"Spearman 相關係數: {spearman_corr:.4f}")
    
    # Top-N 準確率
    top_5_actual = set(results_df.nsmallest(5, 'actual_time')['driver'])
    top_5_predicted = set(results_df.nsmallest(5, 'predicted_time')['driver'])
    top_5_accuracy = len(top_5_actual & top_5_predicted) / 5
    
    top_10_actual = set(results_df.nsmallest(10, 'actual_time')['driver'])
    top_10_predicted = set(results_df.nsmallest(10, 'predicted_time')['driver'])
    top_10_accuracy = len(top_10_actual & top_10_predicted) / 10
    
    print(f"Top-5 準確率: {top_5_accuracy*100:.1f}%")
    print(f"Top-10 準確率: {top_10_accuracy*100:.1f}%")
    
    # 預測方差分析
    pred_std = results_df['predicted_time'].std()
    actual_std = results_df['actual_time'].std()
    
    print("\n=== 預測分布分析 ===")
    print(f"預測標準差: {pred_std:.3f}s")
    print(f"實際標準差: {actual_std:.3f}s")
    print(f"方差比率: {pred_std/actual_std:.2f}")
    
    # 6. 生成詳細報告
    print("\n[6/6] 生成驗證報告...")
    generate_validation_report(results_df, {
        'mae': mae,
        'spearman': spearman_corr,
        'top_5_accuracy': top_5_accuracy,
        'top_10_accuracy': top_10_accuracy,
        'pred_std': pred_std,
        'actual_std': actual_std
    })
    
    print("\n" + "="*80)
    print("✓ 2025 墨西哥站驗證完成！")
    print(f"✓ 驗證報告: reports/Mexico_2025_validation_v2.md")
    print("="*80 + "\n")
    
    return results_df
```

**實作任務**:
- [ ] 編寫 `validate_mexico_2025_v2.py`
- [ ] 載入 2025 墨西哥站數據
- [ ] 執行預測並計算指標
- [ ] 生成對比報告（v1.0 vs v2.0）

**評估指標**:
```python
# 成功標準
SUCCESS_CRITERIA = {
    'mae': {
        'target': '< 1.0s',
        'excellent': '< 0.7s'
    },
    'spearman': {
        'target': '>= 0.8',
        'excellent': '>= 0.85'
    },
    'top_5_accuracy': {
        'target': '>= 60%',
        'excellent': '>= 80%'
    },
    'top_10_accuracy': {
        'target': '>= 70%',
        'excellent': '>= 85%'
    },
    'variance_ratio': {
        'target': '0.6-1.4',
        'excellent': '0.8-1.2'
    }
}
```

---

### 3.3 v1.0 vs v2.0 對比分析

**對比報告**: `reports/Mexico_v1_vs_v2_comparison.md`

**對比內容**:

| 指標 | v1.0（僅 FP3） | v2.0（含車手特徵） | 改善 |
|------|---------------|------------------|------|
| **特徵數** | 26 | 30-35 | +15-35% |
| **訓練 MAE** | 0.004s | ？ | ？ |
| **測試 MAE** | 0.323s | ？ | ？ |
| **測試 R²** | 0.7613 | ？ | ？ |
| **2025 MAE** | 0.891s | ？ | ？ |
| **2025 Spearman** | 0.6015 | ？ | ？ |
| **Top-5 準確率** | 60% | ？ | ？ |
| **Top-10 準確率** | 80% | ？ | ？ |
| **預測方差** | 0.15s | ？ | ？ |

**實作任務**:
- [ ] 生成對比表格
- [ ] 視覺化性能提升
- [ ] 分析改善原因
- [ ] 確認是否達標

---

## Phase 4: 擴展與優化（預估 5-7 天）

### 4.1 擴展至其他原型賽道

**目標賽道**: Monaco, Singapore, Brazil, Japan, Spain, Bahrain, Abu Dhabi

**執行腳本**: `scripts/train_all_tracks_v2.py`

**批次訓練**:
```python
def train_all_tracks_v2():
    """
    訓練所有原型賽道模型 v2.0
    """
    tracks = [
        'Monaco', 'Singapore', 'Brazil', 'Japan', 
        'Spain', 'Bahrain', 'Abu Dhabi', 'Mexico'
    ]
    
    trainer = TrackSpecificTrainer(enable_driver_features=True)
    results = {}
    
    for track in tracks:
        print(f"\n{'='*80}")
        print(f"訓練 {track} 模型...")
        print(f"{'='*80}\n")
        
        try:
            model_data = trainer.train_track_model(track)
            results[track] = {
                'success': True,
                'test_mae': model_data['performance']['test_mae'],
                'test_r2': model_data['performance']['test_r2']
            }
        except Exception as e:
            print(f"❌ {track} 訓練失敗: {e}")
            results[track] = {'success': False, 'error': str(e)}
    
    # 生成彙總報告
    generate_batch_training_report(results)
    
    return results
```

**實作任務**:
- [ ] 編寫批次訓練腳本
- [ ] 依序訓練 8 個賽道
- [ ] 記錄每個賽道的性能指標
- [ ] 生成彙總報告

---

### 4.2 超參數優化

**目標**: 使用 Optuna 自動搜索最佳超參數

**執行腳本**: `scripts/optimize_hyperparameters.py`

**優化範圍**:
```python
def objective(trial):
    """
    Optuna 優化目標函數
    """
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 300),
        'max_depth': trial.suggest_int('max_depth', 4, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.01, 1.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.5, 2.0),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0)
    }
    
    model = XGBRegressor(**params, random_state=42)
    
    # 5-fold 交叉驗證
    scores = cross_val_score(model, X_train, y_train, 
                            cv=5, scoring='neg_mean_absolute_error')
    
    return -scores.mean()  # 返回負值（Optuna 預設最小化）

# 執行優化
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=100)

print(f"最佳參數: {study.best_params}")
print(f"最佳 MAE: {-study.best_value:.3f}s")
```

**實作任務**:
- [ ] 安裝 Optuna: `pip install optuna`
- [ ] 編寫優化腳本
- [ ] 針對墨西哥模型執行 100 次試驗
- [ ] 應用最佳參數重新訓練

---

### 4.3 建立自動更新機制

**目標**: 每場賽事後自動更新對應賽道模型

**執行腳本**: `scripts/auto_update_model.py`

**更新流程**:
```python
def auto_update_track_model(track_name, new_race_data):
    """
    自動更新賽道模型
    
    Args:
        track_name: 賽道名稱
        new_race_data: 最新一場比賽的數據
    """
    print(f"\n{'='*80}")
    print(f"自動更新 {track_name} 模型")
    print(f"{'='*80}\n")
    
    # 1. 載入舊模型
    old_model_path = f"models/track_specific_v2/{track_name}.pkl"
    with open(old_model_path, 'rb') as f:
        old_model_data = pickle.load(f)
    
    # 2. 合併新數據
    print("[1/4] 合併新數據...")
    X_old, y_old = load_training_data(track_name, (2022, 2024))
    X_new, y_new = prepare_new_race_data(new_race_data)
    
    X_combined = pd.concat([X_old, X_new], ignore_index=True)
    y_combined = np.concatenate([y_old, y_new])
    
    print(f"✓ 舊數據: {len(X_old)} 筆")
    print(f"✓ 新數據: {len(X_new)} 筆")
    print(f"✓ 合併後: {len(X_combined)} 筆")
    
    # 3. 重新訓練
    print("\n[2/4] 重新訓練模型...")
    trainer = TrackSpecificTrainer(enable_driver_features=True)
    new_model_data = trainer.train_with_data(X_combined, y_combined, track_name)
    
    # 4. 性能對比
    print("\n[3/4] 性能對比...")
    comparison = {
        'old_test_mae': old_model_data['performance']['test_mae'],
        'new_test_mae': new_model_data['performance']['test_mae'],
        'old_test_r2': old_model_data['performance']['test_r2'],
        'new_test_r2': new_model_data['performance']['test_r2']
    }
    
    print(f"測試 MAE: {comparison['old_test_mae']:.3f}s → {comparison['new_test_mae']:.3f}s")
    print(f"測試 R²: {comparison['old_test_r2']:.4f} → {comparison['new_test_r2']:.4f}")
    
    # 5. 決定是否更新
    if comparison['new_test_mae'] < comparison['old_test_mae'] * 1.1:
        print("\n[4/4] ✓ 性能提升，更新模型...")
        # 備份舊模型
        backup_path = f"models/track_specific_v2/backup/{track_name}_{datetime.now().strftime('%Y%m%d')}.pkl"
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy(old_model_path, backup_path)
        
        # 儲存新模型
        with open(old_model_path, 'wb') as f:
            pickle.dump(new_model_data, f)
        
        print(f"✓ 模型已更新: {old_model_path}")
        print(f"✓ 備份位置: {backup_path}")
    else:
        print("\n[4/4] ⚠️ 性能未提升，保留舊模型")
    
    return new_model_data
```

**實作任務**:
- [ ] 編寫自動更新腳本
- [ ] 設定更新觸發條件
- [ ] 建立模型版本管理
- [ ] 測試更新流程

---

## 預期成果與驗證標準

### 最終目標

| 指標 | 當前 (v1.0) | 目標 (v2.0) | 評分標準 |
|------|------------|------------|----------|
| **墨西哥 MAE** | 0.891s | **< 0.8s** | ⭐⭐⭐⭐⭐ |
| **墨西哥 Spearman** | 0.6015 | **≥ 0.80** | ⭐⭐⭐⭐⭐ |
| **Top-5 準確率** | 60% | **≥ 80%** | ⭐⭐⭐⭐⭐ |
| **Top-10 準確率** | 80% | **≥ 85%** | ⭐⭐⭐⭐ |
| **預測方差比** | 0.21 | **0.8-1.2** | ⭐⭐⭐⭐⭐ |

### 驗證里程碑

- [ ] **Phase 1 完成**: 所有數據收集完成，數據品質檢查通過
- [ ] **Phase 2 完成**: 特徵工程實作完成，單元測試通過
- [ ] **Phase 3 完成**: 墨西哥模型 v2.0 訓練完成，Spearman ≥ 0.75
- [ ] **Phase 4 完成**: 8 個原型賽道訓練完成，平均 Spearman ≥ 0.70

---

## 風險管理與應對策略

### 風險 1: 過擬合（樣本少 + 特徵多）

**問題**: 墨西哥僅 79 樣本，新增車手特徵後達 43 個

**應對**:
- ✅ 使用 L1/L2 正則化
- ✅ 特徵選擇（保留前 30 個重要特徵）
- ✅ 5-fold 交叉驗證
- ✅ 監控訓練/測試 MAE 差距

### 風險 2: 數據時效性

**問題**: 2025 賽季進行中，數據不完整

**應對**:
- ✅ 滾動窗口策略（R1-R4 用 2024 數據）
- ✅ 每場賽後自動更新
- ✅ 使用最近 5 場表現作為狀態特徵

### 風險 3: 車手轉隊

**問題**: HAM 2025 轉至 Ferrari，車隊特徵失效

**應對**:
- ✅ 動態更新車隊歸屬映射
- ✅ 保留車手個人歷史特徵
- ✅ 使用當前賽季數據更新車隊實力

### 風險 4: Spearman 未達標

**問題**: 即使加入車手特徵，Spearman 仍 < 0.8

**應對**:
- ✅ 方差校正（拉開預測差距）
- ✅ 排名損失函數（LambdaRank）
- ✅ 集成學習（多模型投票）
- ✅ 接受 0.75-0.79 作為可接受範圍

---

## 開發時程

### 第 1 週（Day 1-7）: Phase 1 + Phase 2

- **Day 1-2**: 數據收集（車手資料庫、賽道歷史）
- **Day 3-4**: 2025 賽季數據收集、車隊實力統計
- **Day 5-6**: 實作 DriverFeatureEngineer 類別
- **Day 7**: 整合至 TrackSpecificTrainer，單元測試

### 第 2 週（Day 8-14）: Phase 3

- **Day 8-9**: 墨西哥模型 v2.0 訓練
- **Day 10-11**: 2025 驗證測試
- **Day 12**: 特徵重要性分析（SHAP）
- **Day 13-14**: 生成對比報告，調整參數

### 第 3 週（Day 15-21）: Phase 4

- **Day 15-17**: 批次訓練其他 7 個賽道
- **Day 18-19**: 超參數優化（Optuna）
- **Day 20-21**: 建立自動更新機制

### 第 4 週（Day 22-28）: 整合與文檔

- **Day 22-23**: 整合到 Function Mapper
- **Day 24-25**: 編寫完整文檔
- **Day 26-27**: 全面測試
- **Day 28**: 發布 Function 77 v2.0

---

## 成功標準檢查清單

### 必須達成（P0）

- [ ] ✅ 墨西哥模型 Spearman ≥ 0.75
- [ ] ✅ 墨西哥模型 MAE < 1.0s
- [ ] ✅ Top-5 準確率 ≥ 60%
- [ ] ✅ 所有特徵提取無錯誤
- [ ] ✅ 模型可復現（設定 random_state）

### 期望達成（P1）

- [ ] ⭐ 墨西哥模型 Spearman ≥ 0.80
- [ ] ⭐ Top-5 準確率 ≥ 80%
- [ ] ⭐ 8 個賽道平均 Spearman ≥ 0.70
- [ ] ⭐ 特徵重要性分析完成
- [ ] ⭐ 自動更新機制實作

### 加分項目（P2）

- [ ] 🌟 超參數優化完成
- [ ] 🌟 集成學習實作
- [ ] 🌟 實時預測 API
- [ ] 🌟 可視化儀表板

---

## 參考資料

### 程式碼參考
- 現有 TrackSpecificTrainer: `CLI_modules/cli/prediction/track_specific_trainer.py`
- Function 76 實作: `CLI_modules/cli/prediction/qualifying_predictor.py`

### 數據來源
- FastF1 API: https://docs.fastf1.dev/
- Ergast API: http://ergast.com/mrd/
- 官方 F1: https://www.formula1.com/

### 機器學習參考
- XGBoost 文檔: https://xgboost.readthedocs.io/
- SHAP 文檔: https://shap.readthedocs.io/
- Optuna 文檔: https://optuna.readthedocs.io/

---

**文件版本**: v1.0  
**建立日期**: 2025-11-03  
**作者**: AI Assistant  
**狀態**: 📋 待執行
