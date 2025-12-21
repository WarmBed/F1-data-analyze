"""
F1 預測系統強化學習優化器
使用 PPO 算法自動調整模型配置以最大化 Top5 準確率
"""

import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
import json
from pathlib import Path
from typing import Dict, Tuple, List
import subprocess
import time

class F1OptimizationEnv(gym.Env):
    """
    F1 預測優化環境
    
    狀態空間: 10 個賽道的特徵權重配置 (20 維)
    動作空間: 調整某個賽道的某個特徵權重
    獎勵函數: Top5 準確率的變化
    """
    
    metadata = {'render.modes': ['human']}
    
    def __init__(self, mode='fast'):
        super().__init__()
        
        # 模式：'fast' 使用代理模型，'real' 真實重新訓練
        self.mode = mode
        
        # 賽道列表
        self.tracks = [
            'Bahrain', 'Saudi_Arabia', 'Japan', 'Monaco', 'Canada',
            'Great_Britain', 'Hungary', 'Netherlands', 'Italy', 'Azerbaijan'
        ]
        
        # 狀態空間：10 賽道 × 2 特徵 (改進率權重, 速度權重)
        self.observation_space = gym.spaces.Box(
            low=0.0, high=1.0, shape=(20,), dtype=np.float32
        )
        
        # 動作空間：[賽道索引, 特徵索引, 調整量]
        self.action_space = gym.spaces.Box(
            low=np.array([0, 0, -0.3], dtype=np.float32),
            high=np.array([9, 1, 0.3], dtype=np.float32),
            dtype=np.float32
        )
        
        # 初始配置（v3.5 默認）
        self.config = self._init_default_config()
        
        # 當前最佳準確率
        self.best_accuracy = 0.58  # v3.5 基準
        
        # 步數計數
        self.episode_steps = 0
        self.max_steps = 50  # 每個 episode 最多 50 步
        
        # 歷史記錄
        self.history = []
        
        # 代理模型（快速估計）
        if mode == 'fast':
            self.surrogate_model = self._init_surrogate_model()
        
        print(f"[F1OptimizationEnv] 初始化完成，模式: {mode}")
        print(f"[F1OptimizationEnv] 基準準確率: {self.best_accuracy:.2%}")
    
    def _init_default_config(self) -> np.ndarray:
        """初始化默認配置（v3.5 權重）"""
        # 每個賽道 2 個特徵：[改進率權重, 速度權重]
        config = np.array([
            # Bahrain
            [0.3, 0.7],
            # Saudi Arabia
            [0.5, 0.5],
            # Japan
            [0.4, 0.6],
            # Monaco (問題賽道)
            [0.7, 0.3],  # 改進率過高
            # Canada
            [0.2, 0.8],
            # Great Britain (問題賽道)
            [0.3, 0.7],
            # Hungary
            [0.5, 0.5],
            # Netherlands
            [0.2, 0.8],
            # Italy
            [0.6, 0.4],
            # Azerbaijan
            [0.8, 0.2],
        ], dtype=np.float32)
        
        return config.flatten()
    
    def _init_surrogate_model(self):
        """初始化代理模型（快速估計準確率）"""
        # 簡化版：使用規則估計
        # 實際應該訓練一個神經網絡
        return None
    
    def reset(self, seed=None, options=None):
        """重置環境"""
        super().reset(seed=seed)
        
        # 重置到初始配置（添加小噪聲）
        self.config = self._init_default_config()
        if seed is not None:
            np.random.seed(seed)
            self.config += np.random.normal(0, 0.05, self.config.shape)
            self.config = np.clip(self.config, 0.0, 1.0)
        
        self.episode_steps = 0
        self.current_accuracy = self.best_accuracy
        
        return self.config.astype(np.float32), {}
    
    def step(self, action: np.ndarray) -> Tuple:
        """執行動作"""
        # 解析動作
        track_idx = int(np.clip(action[0], 0, 9))
        feature_idx = int(np.clip(action[1], 0, 1))
        delta = np.clip(action[2], -0.3, 0.3)
        
        # 應用動作
        old_config = self.config.copy()
        config_idx = track_idx * 2 + feature_idx
        self.config[config_idx] += delta
        self.config[config_idx] = np.clip(self.config[config_idx], 0.0, 1.0)
        
        # 評估新配置
        if self.mode == 'fast':
            new_accuracy = self._estimate_accuracy_fast()
        else:
            new_accuracy = self._evaluate_accuracy_real()
        
        # 計算獎勵
        reward = (new_accuracy - self.current_accuracy) * 100
        
        # 額外獎勵：如果超過歷史最佳
        if new_accuracy > self.best_accuracy:
            reward += 10
            self.best_accuracy = new_accuracy
            print(f"  [NEW BEST] 準確率: {new_accuracy:.2%} (+{reward:.1f})")
        
        # 記錄歷史（轉換為 Python 原生類型）
        self.history.append({
            'step': int(self.episode_steps),
            'track': self.tracks[track_idx],
            'feature': ['improvement_weight', 'speed_weight'][feature_idx],
            'delta': float(delta),
            'old_value': float(old_config[config_idx]),
            'new_value': float(self.config[config_idx]),
            'accuracy': float(new_accuracy),
            'reward': float(reward)
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
            'track': self.tracks[track_idx],
            'feature': feature_idx,
            'delta': delta
        }
        
        return self.config.astype(np.float32), reward, done, truncated, info
    
    def _estimate_accuracy_fast(self) -> float:
        """
        快速估計準確率（使用規則或代理模型）
        這裡使用簡化的規則估計
        """
        config_2d = self.config.reshape(10, 2)
        
        # 規則 1: Monaco 改進率權重應該低（< 0.3）
        monaco_improvement = config_2d[3, 0]  # Monaco 索引 3
        monaco_penalty = max(0, monaco_improvement - 0.3) * 0.1
        
        # 規則 2: Azerbaijan 改進率權重應該高（> 0.7）
        azerbaijan_improvement = config_2d[9, 0]  # Azerbaijan 索引 9
        azerbaijan_bonus = max(0, azerbaijan_improvement - 0.7) * 0.1
        
        # 規則 3: Netherlands 改進率權重應該低（< 0.3）
        netherlands_improvement = config_2d[7, 0]  # Netherlands 索引 7
        netherlands_penalty = max(0, netherlands_improvement - 0.3) * 0.05
        
        # 規則 4: 權重應該總和接近 1.0
        weight_sum_penalty = 0
        for i in range(10):
            weight_sum = config_2d[i, 0] + config_2d[i, 1]
            weight_sum_penalty += abs(weight_sum - 1.0) * 0.02
        
        # 基準準確率 + 獎勵 - 懲罰
        estimated_accuracy = 0.58 + azerbaijan_bonus - monaco_penalty - netherlands_penalty - weight_sum_penalty
        
        # 添加噪聲模擬不確定性
        noise = np.random.normal(0, 0.01)
        estimated_accuracy += noise
        
        return np.clip(estimated_accuracy, 0.0, 1.0)
    
    def _evaluate_accuracy_real(self) -> float:
        """
        真實評估準確率（重新訓練模型）
        ⚠️ 這會花費 5-10 分鐘
        """
        print(f"  [REAL EVAL] 開始重新訓練...")
        start_time = time.time()
        
        # 保存當前配置到文件
        config_file = Path('temp_rl_config.json')
        config_2d = self.config.reshape(10, 2)
        config_dict = {
            self.tracks[i]: {
                'improvement_weight': float(config_2d[i, 0]),
                'speed_weight': float(config_2d[i, 1])
            }
            for i in range(10)
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)
        
        # 調用重新訓練腳本（需要你實現這個腳本）
        # subprocess.run(['python', 'retrain_with_config.py', str(config_file)])
        
        # 模擬：隨機生成結果（實際應該讀取訓練結果）
        time.sleep(2)  # 模擬訓練時間
        accuracy = np.random.uniform(0.55, 0.65)
        
        elapsed = time.time() - start_time
        print(f"  [REAL EVAL] 完成，準確率: {accuracy:.2%}，耗時: {elapsed:.1f}s")
        
        return accuracy
    
    def render(self, mode='human'):
        """可視化當前狀態"""
        config_2d = self.config.reshape(10, 2)
        print(f"\n{'='*60}")
        print(f"Episode Step: {self.episode_steps}/{self.max_steps}")
        print(f"Current Accuracy: {self.current_accuracy:.2%}")
        print(f"Best Accuracy: {self.best_accuracy:.2%}")
        print(f"\n配置:")
        for i, track in enumerate(self.tracks):
            imp_w, spd_w = config_2d[i]
            print(f"  {track:15s}: 改進率 {imp_w:.3f}, 速度 {spd_w:.3f}")
        print(f"{'='*60}\n")


class TrainingCallback(BaseCallback):
    """訓練過程回調，用於記錄和可視化"""
    
    def __init__(self, save_freq=100, save_path='./rl_checkpoints/', verbose=1):
        super().__init__(verbose)
        self.save_freq = save_freq
        self.save_path = Path(save_path)
        self.save_path.mkdir(exist_ok=True)
        self.best_mean_reward = -np.inf
    
    def _on_step(self) -> bool:
        # 每 N 步保存一次
        if self.n_calls % self.save_freq == 0:
            # 獲取環境信息
            if len(self.model.ep_info_buffer) > 0:
                mean_reward = np.mean([ep_info['r'] for ep_info in self.model.ep_info_buffer])
                
                if mean_reward > self.best_mean_reward:
                    self.best_mean_reward = mean_reward
                    model_path = self.save_path / f'best_model_step_{self.n_calls}.zip'
                    self.model.save(model_path)
                    if self.verbose > 0:
                        print(f"\n[CHECKPOINT] 保存最佳模型: {model_path}")
                        print(f"[CHECKPOINT] 平均獎勵: {mean_reward:.2f}\n")
        
        return True


def train_rl_optimizer(
    total_timesteps=5000,
    mode='fast',
    log_dir='./tensorboard_logs/'
):
    """
    訓練 RL 優化器
    
    Args:
        total_timesteps: 訓練步數
        mode: 'fast' 或 'real'
        log_dir: TensorBoard 日誌目錄
    """
    print(f"\n{'='*60}")
    print(f"開始訓練 F1 預測優化器 (PPO)")
    print(f"模式: {mode}")
    print(f"總步數: {total_timesteps}")
    print(f"{'='*60}\n")
    
    # 創建環境
    env = F1OptimizationEnv(mode=mode)
    
    # 創建 PPO 模型
    model = PPO(
        "MlpPolicy",  # 多層感知器策略
        env,
        learning_rate=3e-4,
        n_steps=2048,  # 每次更新前收集的步數
        batch_size=64,
        n_epochs=10,
        gamma=0.99,  # 折扣因子
        gae_lambda=0.95,  # GAE 參數
        clip_range=0.2,  # PPO 裁剪範圍
        verbose=1,
        tensorboard_log=log_dir
    )
    
    # 創建回調
    callback = TrainingCallback(save_freq=100)
    
    # 開始訓練
    model.learn(
        total_timesteps=total_timesteps,
        callback=callback,
        progress_bar=True
    )
    
    # 保存最終模型
    model.save("f1_rl_optimizer_final")
    print(f"\n[COMPLETE] 訓練完成，模型已保存: f1_rl_optimizer_final.zip")
    
    # 保存歷史記錄
    history_file = Path('rl_training_history.json')
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(env.history, f, indent=2, ensure_ascii=False)
    print(f"[COMPLETE] 訓練歷史已保存: {history_file}")
    
    return model, env


def test_trained_model(model_path='f1_rl_optimizer_final.zip', n_episodes=5):
    """測試訓練好的模型"""
    print(f"\n{'='*60}")
    print(f"測試訓練好的模型")
    print(f"{'='*60}\n")
    
    # 載入模型
    model = PPO.load(model_path)
    env = F1OptimizationEnv(mode='fast')
    
    for episode in range(n_episodes):
        print(f"\n--- Episode {episode + 1}/{n_episodes} ---")
        obs, _ = env.reset()
        done = False
        total_reward = 0
        
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, done, truncated, info = env.step(action)
            total_reward += reward
            
            if info['accuracy'] > 0.60:  # 發現改進
                print(f"  Step {env.episode_steps}: {info['track']} "
                      f"特徵 {info['feature']} 調整 {info['delta']:.3f} "
                      f"→ 準確率: {info['accuracy']:.2%}")
        
        print(f"\nEpisode {episode + 1} 結束:")
        print(f"  總獎勵: {total_reward:.2f}")
        print(f"  最終準確率: {env.current_accuracy:.2%}")
        print(f"  最佳準確率: {env.best_accuracy:.2%}")
        
        env.render()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='F1 預測系統 RL 優化器')
    parser.add_argument('--mode', choices=['train', 'test'], default='train',
                       help='訓練或測試模式')
    parser.add_argument('--timesteps', type=int, default=5000,
                       help='訓練步數（僅訓練模式）')
    parser.add_argument('--eval-mode', choices=['fast', 'real'], default='fast',
                       help='評估模式：fast=代理模型，real=真實重新訓練')
    parser.add_argument('--model-path', type=str, default='f1_rl_optimizer_final.zip',
                       help='模型路徑（僅測試模式）')
    
    args = parser.parse_args()
    
    if args.mode == 'train':
        train_rl_optimizer(
            total_timesteps=args.timesteps,
            mode=args.eval_mode
        )
    else:
        test_trained_model(model_path=args.model_path)
