import pickle
from pathlib import Path

models_dir = Path('models/fp2_race_ml_v2.0')
files = sorted(models_dir.glob('*.pkl'), key=lambda x: x.stat().st_mtime, reverse=True)

print('\n最新訓練的模型:\n')
for i, f in enumerate(files[:5], 1):
    data = pickle.load(open(f, 'rb'))
    print(f'{i}. {f.name}')
    print(f'   訓練樣本: {data["training_samples"]}')
    print(f'   訓練圈數: {data["total_laps_trained"]}')
    print(f'   MAE: {data["mae"]:.6f}')
    print(f'   R²: {data["r2"]:.6f}')
    print(f'   訓練時間: {data.get("trained_at", "N/A")}')
    print()
