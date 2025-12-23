#!/usr/bin/env python3
"""
測試 Sprint 數據載入 - 驗證 track_specific_trainer_v3.py 的 Sprint fallback
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3

def test_sprint_tracks():
    """測試 Austria/Brazil/Qatar Sprint 數據載入"""
    trainer = TrackSpecificTrainerV3(verbose=True)
    
    sprint_tracks = [
        ('Austria', 'Austrian'),
        ('Brazil', 'Brazilian'),
        ('Qatar', 'Qatar')
    ]
    
    print("="*70)
    print("測試 Sprint Weekend 數據載入")
    print("="*70)
    
    for track_name, _ in sprint_tracks:
        print(f"\n{'='*70}")
        print(f"[測試] {track_name}")
        print(f"{'='*70}")
        
        df = trainer.load_training_data_v3(track_name)
        
        if df.empty:
            print(f"❌ {track_name}: 數據載入失敗")
        else:
            print(f"✅ {track_name}: {len(df)} 樣本")
            print(f"   年份分布: {df.groupby(df.index // 20).size().to_dict() if len(df) > 0 else 'N/A'}")
            print(f"   特徵數量: {len(df.columns) - 2}")

if __name__ == "__main__":
    test_sprint_tracks()
