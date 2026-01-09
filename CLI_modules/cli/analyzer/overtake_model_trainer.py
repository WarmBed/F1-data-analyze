"""
F138: 超車成功率模型訓練器

訓練 Logistic Regression 模型預測超車成功率，用於位置追蹤模擬器。

特徵工程:
  - 賽道超車難度係數 (from F136)
  - 車隊性能差 (from F137)
  - 攻擊方車手歷史成功率
  - 防守方車手歷史防守率
  - 輪胎圈數差 (攻擊方 - 防守方)
  - DRS 狀態 (0/1)

輸出:
  - overtake_success_model.pkl          # 訓練好的模型
  - overtake_model_coefficients.json    # 模型係數 (可解釋)
"""

import json
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 嘗試導入 sklearn
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score, train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, 
        f1_score, roc_auc_score, confusion_matrix
    )
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[F138] Warning: scikit-learn not available, model training disabled")


class OvertakeSuccessModelTrainer:
    """超車成功率模型訓練器"""
    
    def __init__(self):
        self.json_dir = Path("json")
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)
        
        # 輸出路徑
        self.model_path = self.model_dir / "overtake_success_model.pkl"
        self.coefficients_path = self.json_dir / "overtake_model_coefficients.json"
        self.scaler_path = self.model_dir / "overtake_feature_scaler.pkl"
        
        # 載入依賴數據
        self.track_difficulty = {}
        self.team_performance = {}
        self.team_stats = {}
        self.driver_stats = {}  # 原始 F134 數據
        self.driver_coefficients = {}  # F139 修正後的數據
        
    def train(self) -> Dict[str, Any]:
        """執行模型訓練"""
        print("\n" + "="*60)
        print("F138: Overtake Success Model Trainer")
        print("="*60)
        
        if not SKLEARN_AVAILABLE:
            print("[F138] Error: scikit-learn required for model training")
            return {"error": "sklearn not available"}
            
        # 載入依賴數據
        if not self._load_dependencies():
            return {"error": "Failed to load dependencies"}
            
        # 準備訓練數據
        X, y, feature_names = self._prepare_training_data()
        if X is None or len(X) == 0:
            print("[F138] Error: No training data available")
            return {"error": "No training data"}
            
        print(f"\n[F138] Training data prepared:")
        print(f"  - Total samples: {len(y)}")
        print(f"  - Success samples: {sum(y)}")
        print(f"  - Failed samples: {len(y) - sum(y)}")
        print(f"  - Features: {feature_names}")
        
        # 特徵標準化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # 訓練測試分割
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # 訓練 Logistic Regression
        model = LogisticRegression(
            max_iter=1000,
            class_weight='balanced',  # 處理類別不平衡
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # 評估模型
        evaluation = self._evaluate_model(model, X_test, y_test, X_scaled, y)
        
        # 提取係數
        coefficients = self._extract_coefficients(model, feature_names, scaler)
        
        # 計算特徵重要性
        feature_importance = self._calculate_feature_importance(model, feature_names)
        
        # 組建結果
        result = {
            "model_type": "LogisticRegression",
            "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sample_size": {
                "total": len(y),
                "success": int(sum(y)),
                "failed": int(len(y) - sum(y))
            },
            "feature_names": feature_names,
            "coefficients": coefficients,
            "feature_importance": feature_importance,
            "evaluation": evaluation,
            "scaler_mean": scaler.mean_.tolist(),
            "scaler_std": scaler.scale_.tolist()
        }
        
        # 保存模型和係數
        self._save_model(model, scaler, result)
        
        return result
        
    def _load_dependencies(self) -> bool:
        """載入依賴的分析數據"""
        print("\n[F138] Loading dependencies...")
        
        # 載入賽道難度 (F136)
        track_data = self._load_json("track_overtake_difficulty.json")
        if track_data:
            self.track_difficulty = track_data.get('tracks', {})
            print(f"  - Track difficulty: {len(self.track_difficulty)} tracks")
        else:
            print("  - Warning: Track difficulty data not found")
            
        # 載入車隊性能 (F137)
        team_data = self._load_json("team_performance_matrix.json")
        if team_data:
            self.team_performance = team_data.get('overtake_success_matrix', {})
            self.team_stats = team_data.get('team_stats', {})
            print(f"  - Team performance: {len(self.team_performance)} teams")
        else:
            print("  - Warning: Team performance data not found")
            
        # 載入車手統計 (from F134)
        overtake_data = self._load_json("overtake_events_history_2024_2025.json")
        if overtake_data:
            self.driver_stats = overtake_data.get('driver_stats', {})
            print(f"  - Driver stats (F134): {len(self.driver_stats)} drivers")
        else:
            print("  - Warning: Driver stats not found")
            
        # 載入修正後的車手係數 (F139) - 優先使用
        coef_data = self._load_json("driver_coefficients_complete.json")
        if coef_data:
            self.driver_coefficients = coef_data.get('drivers', {})
            print(f"  - Driver coefficients (F139): {len(self.driver_coefficients)} drivers")
        else:
            print("  - Warning: Driver coefficients not found, will use F134 data")
            
        return True
        
    def _load_json(self, filename: str) -> Optional[Dict]:
        """讀取 JSON 檔案"""
        filepath = self.json_dir / filename
        if not filepath.exists():
            return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
            
    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """準備訓練數據"""
        print("\n[F138] Preparing training data...")
        
        # 載入成功和失敗事件
        success_data = self._load_json("overtake_events_history_2024_2025.json")
        failed_data = self._load_json("overtake_attempts_failed_2024_2025.json")
        
        if not success_data or not failed_data:
            return None, None, []
            
        features = []
        labels = []
        
        feature_names = [
            'track_difficulty',
            'team_attack_rate',
            'team_defense_rate', 
            'attacker_success_rate',
            'defender_defense_rate',
            'tyre_age_delta',
            'drs_active'
        ]
        
        # 處理成功事件
        for event in success_data.get('events', []):
            feat = self._extract_features(event, is_success=True)
            if feat:
                features.append(feat)
                labels.append(1)
                
        print(f"  - Success events processed: {len(labels)}")
        success_count = len(labels)
        
        # 處理失敗事件
        for event in failed_data.get('events', []):
            feat = self._extract_features(event, is_success=False)
            if feat:
                features.append(feat)
                labels.append(0)
                
        print(f"  - Failed events processed: {len(labels) - success_count}")
        
        if not features:
            return None, None, []
            
        return np.array(features), np.array(labels), feature_names
        
    def _extract_features(self, event: Dict, is_success: bool) -> Optional[List[float]]:
        """從事件提取特徵向量"""
        try:
            # 1. 賽道難度
            track = event.get('track', '')
            track_diff = self.track_difficulty.get(track, {}).get('difficulty_coefficient', 0.5)
            
            # 2-3. 車隊攻擊/防守率
            if is_success:
                # F134 結構: attacker.team, defender.team
                attacker_data = event.get('attacker', {})
                defender_data = event.get('defender', {})
                attacker_team = attacker_data.get('team', '') if isinstance(attacker_data, dict) else ''
                defender_team = defender_data.get('team', '') if isinstance(defender_data, dict) else ''
                attacker_driver = attacker_data.get('driver', '') if isinstance(attacker_data, dict) else ''
                defender_driver = defender_data.get('driver', '') if isinstance(defender_data, dict) else ''
                tyre_age_attacker = attacker_data.get('tyre_age_laps', 10) if isinstance(attacker_data, dict) else 10
                tyre_age_defender = defender_data.get('tyre_age_laps', 10) if isinstance(defender_data, dict) else 10
                drs_active = 1 if attacker_data.get('drs_active', False) else 0
            else:
                # F135 結構: attacker_team, defender_team
                attacker_team = event.get('attacker_team', '')
                defender_team = event.get('defender_team', '')
                attacker_driver = event.get('attacker', '')
                defender_driver = event.get('defender', '')
                tyre_age_attacker = 10  # F135 沒有輪胎數據
                tyre_age_defender = 10
                drs_active = 1 if event.get('drs_active', False) else 0
                
            # 車隊攻擊率
            team_attack = self.team_stats.get(attacker_team, {}).get('attack_success_rate', 0.1)
            team_defense = self.team_stats.get(defender_team, {}).get('defense_success_rate', 0.9)
            
            # 4-5. 車手歷史成功率 - 優先使用 F139 修正數據
            if self.driver_coefficients:
                attacker_coef = self.driver_coefficients.get(attacker_driver, {})
                defender_coef = self.driver_coefficients.get(defender_driver, {})
                attacker_success = attacker_coef.get('attack_success_rate', 0.12)
                defender_defense = defender_coef.get('defense_success_rate', 0.88)
            else:
                # Fallback 到 F134 (注意: F134 的 attack_success_rate 全是 1.0)
                attacker_stats = self.driver_stats.get(attacker_driver, {})
                defender_stats = self.driver_stats.get(defender_driver, {})
                attacker_success = attacker_stats.get('attack_success_rate', 0.12)
                defender_defense = defender_stats.get('defense_success_rate', 0.88)
            
            # 6. 輪胎圈數差 (防守方 - 攻擊方，正數表示攻擊方輪胎較新)
            tyre_delta = tyre_age_defender - tyre_age_attacker
            
            # 7. DRS 狀態
            # drs_active 已經在上面處理
            
            return [
                track_diff,
                team_attack,
                team_defense,
                attacker_success,
                defender_defense,
                tyre_delta,
                drs_active
            ]
            
        except Exception as e:
            return None
            
    def _evaluate_model(
        self, 
        model, 
        X_test: np.ndarray, 
        y_test: np.ndarray,
        X_all: np.ndarray,
        y_all: np.ndarray
    ) -> Dict[str, float]:
        """評估模型性能"""
        print("\n[F138] Evaluating model...")
        
        # 測試集預測
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        # 計算指標
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc_roc = roc_auc_score(y_test, y_prob)
        
        # 交叉驗證
        cv_scores = cross_val_score(model, X_all, y_all, cv=5, scoring='accuracy')
        
        # 混淆矩陣
        cm = confusion_matrix(y_test, y_pred)
        
        evaluation = {
            'accuracy': round(accuracy, 4),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'auc_roc': round(auc_roc, 4),
            'cv_accuracy_mean': round(cv_scores.mean(), 4),
            'cv_accuracy_std': round(cv_scores.std(), 4),
            'confusion_matrix': {
                'true_negative': int(cm[0, 0]),
                'false_positive': int(cm[0, 1]),
                'false_negative': int(cm[1, 0]),
                'true_positive': int(cm[1, 1])
            }
        }
        
        print(f"  - Accuracy: {accuracy:.4f}")
        print(f"  - Precision: {precision:.4f}")
        print(f"  - Recall: {recall:.4f}")
        print(f"  - F1 Score: {f1:.4f}")
        print(f"  - AUC-ROC: {auc_roc:.4f}")
        print(f"  - CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
        
        return evaluation
        
    def _extract_coefficients(
        self, 
        model, 
        feature_names: List[str],
        scaler: StandardScaler
    ) -> Dict[str, float]:
        """提取模型係數"""
        coefficients = {
            'intercept': round(float(model.intercept_[0]), 4)
        }
        
        for name, coef in zip(feature_names, model.coef_[0]):
            coefficients[name] = round(float(coef), 4)
            
        return coefficients
        
    def _calculate_feature_importance(
        self, 
        model, 
        feature_names: List[str]
    ) -> Dict[str, float]:
        """計算特徵重要性 (基於係數絕對值)"""
        abs_coefs = np.abs(model.coef_[0])
        total = abs_coefs.sum()
        
        importance = {}
        for name, coef in zip(feature_names, abs_coefs):
            importance[name] = round(float(coef / total), 4)
            
        # 按重要性排序
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        print("\n[F138] Feature Importance:")
        for name, imp in importance.items():
            print(f"  - {name}: {imp:.4f} ({imp*100:.1f}%)")
            
        return importance
        
    def _save_model(self, model, scaler, result: Dict):
        """保存模型和係數"""
        # 保存模型
        with open(self.model_path, 'wb') as f:
            pickle.dump(model, f)
        print(f"\n[F138] Model saved to: {self.model_path}")
        
        # 保存 scaler
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        print(f"[F138] Scaler saved to: {self.scaler_path}")
        
        # 保存係數 JSON
        self.json_dir.mkdir(exist_ok=True)
        with open(self.coefficients_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[F138] Coefficients saved to: {self.coefficients_path}")


class OvertakePredictor:
    """超車成功率預測器 (用於推理)"""
    
    def __init__(self, model_dir: str = "models", json_dir: str = "json"):
        self.model_dir = Path(model_dir)
        self.json_dir = Path(json_dir)
        
        self.model = None
        self.scaler = None
        self.coefficients = None
        
    def load(self) -> bool:
        """載入模型"""
        try:
            with open(self.model_dir / "overtake_success_model.pkl", 'rb') as f:
                self.model = pickle.load(f)
            with open(self.model_dir / "overtake_feature_scaler.pkl", 'rb') as f:
                self.scaler = pickle.load(f)
            with open(self.json_dir / "overtake_model_coefficients.json", 'r') as f:
                self.coefficients = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
            
    def predict(
        self,
        track_difficulty: float,
        team_attack_rate: float,
        team_defense_rate: float,
        attacker_success_rate: float,
        defender_defense_rate: float,
        tyre_age_delta: float,
        drs_active: bool
    ) -> float:
        """預測超車成功率"""
        if self.model is None:
            raise RuntimeError("Model not loaded")
            
        features = np.array([[
            track_difficulty,
            team_attack_rate,
            team_defense_rate,
            attacker_success_rate,
            defender_defense_rate,
            tyre_age_delta,
            1 if drs_active else 0
        ]])
        
        features_scaled = self.scaler.transform(features)
        probability = self.model.predict_proba(features_scaled)[0, 1]
        
        return float(probability)


def execute_overtake_model_trainer(
    year: int = None,
    race: str = None,
    session: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    執行超車成功率模型訓練
    
    這是 CLI 模組的入口點
    """
    trainer = OvertakeSuccessModelTrainer()
    return trainer.train()


# 直接執行測試
if __name__ == "__main__":
    result = execute_overtake_model_trainer()
    
    if "error" not in result:
        print(f"\n[F138] Training complete!")
        print(f"  - Model accuracy: {result['evaluation']['accuracy']:.4f}")
        print(f"  - AUC-ROC: {result['evaluation']['auc_roc']:.4f}")
    else:
        print(f"\n[F138] Training failed: {result['error']}")
