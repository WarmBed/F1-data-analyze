from pathlib import Path
import sys
sys.path.append(r'C:\Users\mike2\OneDrive\Code\F1-data-analyze')
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3

tracks = [
    'Australia', 'China', 'Japan', 'Bahrain', 'Saudi Arabia', 'Miami',
    'Emilia Romagna', 'Monaco', 'Spain', 'Canada', 'Austria', 'Great Britain',
    'Belgium', 'Hungary', 'Netherlands', 'Italy', 'Azerbaijan', 'Singapore',
    'United States', 'Mexico', 'Brazil', 'Las Vegas', 'Qatar', 'Abu Dhabi'
]

models_dir = Path('models/track_specific_v3.8')
trainer = TrackSpecificTrainerV3(verbose=True)

print('\nChecking trained models and available training data:\n')
for t in tracks:
    model_exists = (models_dir / f"{t}.pkl").exists()
    print(f"Track: {t:15s} | ModelExists: {model_exists}")
    if not model_exists:
        df = trainer.load_training_data_v3(t, start_year=2022, end_year=2024)
        if df.empty:
            print(f"  -> load_training_data_v3: NO DATA (可能缺少 FP3/Corner JSON 或樣本被過濾)")
        else:
            print(f"  -> load_training_data_v3: {len(df)} samples (可訓練)\n  Sample columns: {list(df.columns)[:10]}")

print('\nDone.')
