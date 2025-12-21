"""
F1 單賽道 PPO 優化器 - 真實 XGBoost 評估版本
每條賽道獨立訓練，使用實際模型性能作為獎勵
"""

import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
import json
from pathlib import Path
from typing import Dict, Tuple
import subprocess
import time
import pickle

class SingleTrackOptimizationEnv(gym.Env):
    """
    單賽道特徵權重優化環境
    
    狀態空間: 20 個特徵的權重 [0, 1]
    動作空間: 調整某個特徵的權重 (特徵索引, 調整量)
    獎勵函數: 實際 Top5 準確率變化
    """
    
    metadata = {'render.modes': ['human']}
    
    def __init__(self, track_name: str, year: int = 2025):
        super().__init__()
        
        self.track_name = track_name
        self.year = year
        
        # 20 個特徵（v3.5）
        self.feature_names = [
            # 基礎 14 特徵
            'max_speed', 'avg_speed', 'min_speed',
            'sector_1_time', 'sector_2_time', 'sector_3_time',
            'throttle_pct', 'brake_pct', 'gear_changes', 'drs_usage',
            'tire_type', 'compound', 'track_temp', 'air_temp',
            # 改進率 6 特徵
            'improvement_rate_max_speed', 'improvement_rate_avg_speed',
            'improvement_rate_throttle', 'improvement_rate_brake',
            'improvement_rate_gear_changes', 'improvement_rate_drs'
        ]
        
        # 狀態空間: 20 維特徵權重
        self.observation_space = gym.spaces.Box(
            low=0.0, high=1.0, shape=(20,), dtype=np.float32
        )
        
        # 動作空間: [特徵索引 (0-19), 調整量 (-0.2 到 +0.2)]
        self.action_space = gym.spaces.Box(
            low=np.array([0, -0.2], dtype=np.float32),
            high=np.array([19, 0.2], dtype=np.float32),
            dtype=np.float32
        )
        
        # 初始配置（均勻權重）
        self.config = np.ones(20, dtype=np.float32) / 20.0
        
        # v3.5 基準性能
        self.baseline_accuracy = self._get_baseline_accuracy()
        self.best_accuracy = self.baseline_accuracy
        self.current_accuracy = self.baseline_accuracy
        
        # 訓練計數
        self.training_count = 0
        self.episode_steps = 0
        self.max_steps = 30  # 每個 episode 最多 30 步
        
        # 歷史記錄
        self.history = []
        
        # 緩存目錄
        self.cache_dir = Path(f'rl_cache/{track_name}')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*70}")
        print(f"[{self.track_name}] 單賽道優化環境初始化")
        print(f"  基準準確率: {self.baseline_accuracy:.2%}")
        print(f"  特徵數量: {len(self.feature_names)}")
        print(f"  最大步數: {self.max_steps}")
        print(f"{'='*70}\n")
    
    def _get_baseline_accuracy(self) -> float:
        """獲取 v3.5 基準準確率"""
        # 從驗證報告中讀取
        baseline_map = {
            'Bahrain': 0.40,
            'Saudi_Arabia': 1.00,
            'Japan': 0.80,
            'Monaco': 0.60,
            'Canada': 0.20,
            'Great_Britain': 0.20,
            'Hungary': 0.40,
            'Netherlands': 0.60,
            'Italy': 0.80,
            'Azerbaijan': 0.80
        }
        return baseline_map.get(self.track_name, 0.60)
    
    def reset(self, seed=None, options=None):
        """重置環境"""
        super().reset(seed=seed)
        
        # 重置為初始配置（添加小噪聲）
        self.config = np.ones(20, dtype=np.float32) / 20.0
        if seed is not None:
            np.random.seed(seed)
            noise = np.random.normal(0, 0.01, self.config.shape)
            self.config += noise
            self.config = np.clip(self.config, 0.01, 1.0)
        
        # 歸一化權重
        self.config = self.config / self.config.sum()
        
        self.episode_steps = 0
        self.current_accuracy = self.baseline_accuracy
        
        return self.config.astype(np.float32), {}
    
    def step(self, action: np.ndarray) -> Tuple:
        """執行動作並評估"""
        # 解析動作
        feature_idx = int(np.clip(action[0], 0, 19))
        delta = np.clip(action[1], -0.2, 0.2)
        
        # 保存舊配置
        old_config = self.config.copy()
        old_value = self.config[feature_idx]
        
        # 應用動作
        self.config[feature_idx] += delta
        self.config = np.clip(self.config, 0.01, 1.0)
        
        # 歸一化權重（保持總和為 1）
        self.config = self.config / self.config.sum()
        
        new_value = self.config[feature_idx]
        
        print(f"\n[Step {self.episode_steps + 1}/{self.max_steps}] "
              f"調整 {self.feature_names[feature_idx]}")
        print(f"  權重: {old_value:.4f} → {new_value:.4f} ({delta:+.4f})")
        
        # 真實評估：重新訓練 XGBoost
        new_accuracy = self._evaluate_with_real_training()
        
        # 計算獎勵
        improvement = new_accuracy - self.current_accuracy
        reward = improvement * 100  # 放大獎勵信號
        
        # 額外獎勵：超過歷史最佳
        if new_accuracy > self.best_accuracy:
            bonus = 20
            reward += bonus
            self.best_accuracy = new_accuracy
            print(f"  [NEW BEST] 準確率: {new_accuracy:.2%} "
                  f"(+{(new_accuracy - self.baseline_accuracy)*100:.2f}% vs 基準)")
            print(f"  獎勵: {reward:.2f} (改進 {improvement*100:+.2f}% + 獎金 {bonus})")
        else:
            print(f"  準確率: {new_accuracy:.2%} ({improvement*100:+.2f}%)")
            print(f"  獎勵: {reward:.2f}")
        
        # 記錄歷史
        self.history.append({
            'step': int(self.episode_steps),
            'feature': self.feature_names[feature_idx],
            'feature_idx': int(feature_idx),
            'delta': float(delta),
            'old_value': float(old_value),
            'new_value': float(new_value),
            'accuracy': float(new_accuracy),
            'reward': float(reward),
            'improvement': float(improvement),
            'training_count': int(self.training_count)
        })
        
        # 更新狀態
        self.current_accuracy = new_accuracy
        self.episode_steps += 1
        
        # 判斷是否結束
        done = self.episode_steps >= self.max_steps
        truncated = False
        
        info = {
            'accuracy': new_accuracy,
            'best_accuracy': self.best_accuracy,
            'baseline_accuracy': self.baseline_accuracy,
            'improvement': improvement,
            'feature': self.feature_names[feature_idx],
            'training_count': self.training_count
        }
        
        return self.config.astype(np.float32), reward, done, truncated, info
    
    def _evaluate_with_real_training(self) -> float:
        """
        真實評估：重新訓練 XGBoost 並計算 Top5 準確率
        """
        print(f"  [TRAINING] 開始訓練 (第 {self.training_count + 1} 次)...")
        start_time = time.time()
        
        # 保存當前權重配置
        config_file = self.cache_dir / f'config_{self.training_count}.json'
        config_dict = {
            'track': self.track_name,
            'weights': {
                self.feature_names[i]: float(self.config[i])
                for i in range(20)
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        # 調用訓練腳本
        script_path = Path('train_single_track_with_weights.py')
        
        try:
            # Windows 環境使用 cp950 編碼
            import sys
            encoding = 'cp950' if sys.platform == 'win32' else 'utf-8'
            
            result = subprocess.run(
                [
                    'python', str(script_path),
                    '--track', self.track_name,
                    '--year', str(self.year),
                    '--config', str(config_file),
                    '--output', str(self.cache_dir / f'result_{self.training_count}.json')
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 分鐘超時
                encoding=encoding,
                errors='ignore'  # 忽略無法解碼的字符
            )
            
            # 讀取結果
            result_file = self.cache_dir / f'result_{self.training_count}.json'
            if result_file.exists():
                with open(result_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                
                accuracy = result_data.get('top5_accuracy', self.baseline_accuracy)
                
                elapsed = time.time() - start_time
                print(f"  [TRAINING] 完成，準確率: {accuracy:.2%}，耗時: {elapsed:.1f}s")
                
                self.training_count += 1
                return accuracy
            else:
                print(f"  [ERROR] 結果文件不存在")
                return self.current_accuracy
                
        except subprocess.TimeoutExpired:
            print(f"  [ERROR] 訓練超時")
            return self.current_accuracy
        except Exception as e:
            print(f"  [ERROR] 訓練失敗: {e}")
            return self.current_accuracy
    
    def render(self, mode='human'):
        """可視化當前狀態"""
        print(f"\n{'='*70}")
        print(f"[{self.track_name}] Episode Step: {self.episode_steps}/{self.max_steps}")
        print(f"  當前準確率: {self.current_accuracy:.2%}")
        print(f"  最佳準確率: {self.best_accuracy:.2%}")
        print(f"  基準準確率: {self.baseline_accuracy:.2%}")
        print(f"  改進幅度: {(self.best_accuracy - self.baseline_accuracy)*100:+.2f}%")
        print(f"\n權重配置 (Top 10):")
        
        # 顯示權重最高的 10 個特徵
        sorted_indices = np.argsort(self.config)[::-1][:10]
        for i, idx in enumerate(sorted_indices, 1):
            print(f"  {i:2d}. {self.feature_names[idx]:30s}: {self.config[idx]:.4f}")
        
        print(f"{'='*70}\n")


class SingleTrackCallback(BaseCallback):
    """單賽道訓練回調"""
    
    def __init__(self, track_name: str, save_freq=5, verbose=1):
        super().__init__(verbose)
        self.track_name = track_name
        self.save_freq = save_freq
        self.save_path = Path(f'rl_checkpoints/{track_name}')
        self.save_path.mkdir(parents=True, exist_ok=True)
        self.best_mean_reward = -np.inf
        self.episode_count = 0
    
    def _on_step(self) -> bool:
        # 每 N 步保存
        if self.n_calls % self.save_freq == 0:
            if len(self.model.ep_info_buffer) > 0:
                mean_reward = np.mean([ep_info['r'] for ep_info in self.model.ep_info_buffer])
                
                if mean_reward > self.best_mean_reward:
                    self.best_mean_reward = mean_reward
                    model_path = self.save_path / f'best_step_{self.n_calls}.zip'
                    self.model.save(model_path)
                    
                    if self.verbose > 0:
                        print(f"\n[CHECKPOINT] {self.track_name}")
                        print(f"  保存模型: {model_path}")
                        print(f"  平均獎勵: {mean_reward:.2f}\n")
        
        return True


def train_single_track(
    track_name: str,
    total_timesteps: int = 1000,
    year: int = 2025
):
    """
    訓練單個賽道的 PPO 優化器
    
    Args:
        track_name: 賽道名稱
        total_timesteps: 訓練步數
        year: 驗證年份
    """
    print(f"\n{'='*70}")
    print(f"開始訓練 {track_name} 優化器 (PPO + 真實評估)")
    print(f"  訓練步數: {total_timesteps}")
    print(f"  驗證年份: {year}")
    print(f"{'='*70}\n")
    
    # 創建環境
    env = SingleTrackOptimizationEnv(track_name=track_name, year=year)
    
    # 創建 PPO 模型
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=64,  # 減少步數（因為每步訓練時間長）
        batch_size=16,
        n_epochs=5,
        gamma=0.95,
        gae_lambda=0.90,
        clip_range=0.2,
        verbose=1,
        tensorboard_log=f'./tensorboard_logs/{track_name}'
    )
    
    # 創建回調
    callback = SingleTrackCallback(track_name=track_name, save_freq=5)
    
    # 開始訓練
    model.learn(
        total_timesteps=total_timesteps,
        callback=callback,
        progress_bar=True
    )
    
    # 保存最終模型
    final_model_path = f'rl_optimizers/{track_name}_final.zip'
    Path('rl_optimizers').mkdir(exist_ok=True)
    model.save(final_model_path)
    print(f"\n[COMPLETE] 訓練完成，模型已保存: {final_model_path}")
    
    # 保存歷史記錄
    history_file = Path(f'rl_history/{track_name}_history.json')
    history_file.parent.mkdir(exist_ok=True)
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(env.history, f, indent=2, ensure_ascii=False)
    print(f"[COMPLETE] 訓練歷史已保存: {history_file}")
    
    # 保存最佳權重配置
    best_config_file = Path(f'rl_optimizers/{track_name}_best_weights.json')
    best_config = {
        'track': track_name,
        'baseline_accuracy': float(env.baseline_accuracy),
        'best_accuracy': float(env.best_accuracy),
        'improvement': float(env.best_accuracy - env.baseline_accuracy),
        'weights': {
            env.feature_names[i]: float(env.config[i])
            for i in range(20)
        }
    }
    
    with open(best_config_file, 'w', encoding='utf-8') as f:
        json.dump(best_config, f, indent=2, ensure_ascii=False)
    print(f"[COMPLETE] 最佳權重已保存: {best_config_file}")
    
    # 顯示最終結果
    env.render()
    
    return model, env


def train_all_tracks(timesteps_per_track: int = 300):
    """訓練所有 10 條賽道"""
    tracks = [
        'Bahrain', 'Saudi_Arabia', 'Japan', 'Monaco', 'Canada',
        'Great_Britain', 'Hungary', 'Netherlands', 'Italy', 'Azerbaijan'
    ]
    
    results = {}
    
    for i, track in enumerate(tracks, 1):
        print(f"\n{'#'*70}")
        print(f"# 訓練進度: {i}/{len(tracks)} - {track}")
        print(f"{'#'*70}\n")
        
        try:
            model, env = train_single_track(
                track_name=track,
                total_timesteps=timesteps_per_track,
                year=2025
            )
            
            results[track] = {
                'baseline': env.baseline_accuracy,
                'best': env.best_accuracy,
                'improvement': env.best_accuracy - env.baseline_accuracy,
                'training_count': env.training_count
            }
            
        except Exception as e:
            print(f"\n[ERROR] {track} 訓練失敗: {e}\n")
            results[track] = {'error': str(e)}
    
    # 保存總結
    summary_file = Path('rl_optimizers/all_tracks_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"全部訓練完成！總結:")
    print(f"{'='*70}\n")
    
    for track, result in results.items():
        if 'error' not in result:
            print(f"{track:20s}: {result['baseline']:.2%} → {result['best']:.2%} "
                  f"({result['improvement']*100:+.2f}%, {result['training_count']} 次訓練)")
        else:
            print(f"{track:20s}: 訓練失敗")
    
    print(f"\n總結已保存: {summary_file}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='F1 單賽道 PPO 優化器（真實評估）')
    parser.add_argument('--mode', choices=['single', 'all'], default='single',
                       help='single=單賽道, all=全部賽道')
    parser.add_argument('--track', type=str, default='Monaco',
                       help='賽道名稱（僅 single 模式）')
    parser.add_argument('--timesteps', type=int, default=300,
                       help='訓練步數')
    parser.add_argument('--year', type=int, default=2025,
                       help='驗證年份')
    
    args = parser.parse_args()
    
    if args.mode == 'single':
        train_single_track(
            track_name=args.track,
            total_timesteps=args.timesteps,
            year=args.year
        )
    else:
        train_all_tracks(timesteps_per_track=args.timesteps)
