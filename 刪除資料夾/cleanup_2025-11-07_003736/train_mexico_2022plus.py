"""
重新訓練墨西哥模型 - 僅使用 2022-2024 數據
針對 F1 2022 技術規則改制後的數據
"""
import sys
import pickle
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from CLI_modules.cli.prediction.track_specific_trainer import TrackSpecificTrainer

def train_mexico_2022_plus():
    """訓練墨西哥模型（只用 2022-2024 數據）"""
    print("="*80)
    print("墨西哥模型重訓練 - 2022-2024 數據專用")
    print("="*80)
    
    # 1. 初始化訓練器
    trainer = TrackSpecificTrainer()
    
    # 2. 載入訓練數據
    print("\n[步驟 1] 載入訓練數據...")
    success = trainer.load_training_data()
    if not success:
        print("[錯誤] 訓練數據載入失敗")
        return False
    
    # 計算總數據量
    total_samples = sum(len(df) for df in trainer.track_data.values())
    print(f"[OK] 載入 {total_samples} 筆訓練數據")
    print(f"[OK] 識別出 {len(trainer.track_data)} 個賽道")
    
    # 3. 檢查墨西哥數據
    if 'Mexico' not in trainer.track_data:
        print("[錯誤] 找不到墨西哥賽道數據")
        print(f"可用賽道: {list(trainer.track_data.keys())[:10]}")
        return False
    
    mexico_all = trainer.track_data['Mexico']
    print(f"\n[步驟 2] 墨西哥原始數據統計:")
    print(f"  總樣本數: {len(mexico_all)}")
    print(f"  年份範圍: {mexico_all['year'].min()} - {mexico_all['year'].max()}")
    
    # 4. 過濾為 2022-2024
    mexico_2022_plus = mexico_all[mexico_all['year'] >= 2022].copy()
    
    print(f"\n[步驟 3] 過濾為 2022+ 數據:")
    print(f"  2022-2024 樣本數: {len(mexico_2022_plus)}")
    print(f"  保留比例: {len(mexico_2022_plus)/len(mexico_all)*100:.1f}%")
    
    # 顯示年份分布
    year_counts = mexico_2022_plus['year'].value_counts().sort_index()
    print(f"\n  年份分布:")
    for year, count in year_counts.items():
        print(f"    {year}: {count} 場")
    
    # 5. 添加歷史特徵（基於 2022+ 數據）
    print(f"\n[步驟 4] 添加車手歷史特徵...")
    # 重新計算歷史特徵（基於 2022+ 數據）
    trainer._calculate_track_history(mexico_2022_plus)
    mexico_2022_plus = trainer.add_track_history_features(mexico_2022_plus, 'Mexico')
    
    print(f"[OK] 特徵維度: {mexico_2022_plus.shape[1]} 個特徵")
    
    # 6. 訓練模型
    print(f"\n[步驟 5] 訓練 XGBoost 模型...")
    
    # 暫時替換 trainer 的墨西哥數據
    original_mexico = trainer.track_data['Mexico']
    trainer.track_data['Mexico'] = mexico_2022_plus
    
    results = trainer.train_track_model('Mexico')
    
    # 還原原始數據
    trainer.track_data['Mexico'] = original_mexico
    
    if results is None:
        print("[錯誤] 模型訓練失敗")
        return False
    
    # 7. 顯示訓練結果
    print(f"\n[步驟 6] 訓練結果:")
    print(f"  訓練樣本數: {len(mexico_2022_plus)}")
    print(f"  特徵數量: {mexico_2022_plus.shape[1]}")
    print(f"  訓練集 MAE: {results['train_mae']:.3f}s")
    print(f"  測試集 MAE: {results['test_mae']:.3f}s")
    print(f"  測試集 R2: {results['test_r2']:.4f}")
    if 'training_time' in results:
        print(f"  訓練時間: {results['training_time']:.2f}s")
    
    # 8. 保存模型（覆蓋舊的）
    print(f"\n[步驟 7] 保存模型...")
    model_dir = Path('models/track_specific')
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_file = model_dir / 'Mexico.pkl'
    
    # 備份舊模型
    if model_file.exists():
        backup_file = model_dir / 'Mexico_old.pkl'
        import shutil
        shutil.copy(model_file, backup_file)
        print(f"[OK] 舊模型備份至: {backup_file}")
    
    # 保存新模型（從 trainer.track_models 取得）
    trained_model = trainer.track_models.get('Mexico')
    if trained_model is None:
        print("[錯誤] 無法取得訓練好的模型")
        return False
    
    with open(model_file, 'wb') as f:
        pickle.dump({
            'model': trained_model,
            'track_name': 'Mexico',
            'n_samples': len(mexico_2022_plus),
            'n_features': mexico_2022_plus.shape[1],
            'train_mae': results['train_mae'],
            'test_mae': results['test_mae'],
            'test_r2': results['test_r2'],
            'training_time': results.get('training_time', 0),
            'feature_names': list(mexico_2022_plus.drop(columns=['q_time', 'year', 'race', 'driver'], errors='ignore').columns),
            'year_range': '2022-2024',
            'training_date': '2025-11-03'
        }, f)
    
    print(f"[OK] 新模型已保存至: {model_file}")
    
    # 9. 比較新舊模型
    print(f"\n[步驟 8] 新舊模型對比:")
    print(f"  舊模型 (2018-2024): 測試 MAE 0.973s, R2 -2.4961")
    print(f"  新模型 (2022-2024): 測試 MAE {results['test_mae']:.3f}s, R2 {results['test_r2']:.4f}")
    
    if results['test_mae'] < 0.973:
        print(f"  [成功] MAE 改善 {(0.973 - results['test_mae']):.3f}s ({(1 - results['test_mae']/0.973)*100:.1f}%)")
    else:
        print(f"  [警告] MAE 未改善")
    
    print("\n" + "="*80)
    print("墨西哥模型重訓練完成")
    print("="*80)
    
    return True

if __name__ == '__main__':
    train_mexico_2022_plus()
