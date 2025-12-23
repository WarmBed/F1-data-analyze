#!/usr/bin/env python3
"""
從 V3.8 模型檔案重新生成訓練結果 JSON
"""
import pickle
import json
from pathlib import Path
from datetime import datetime


def regenerate_v38_results():
    """從 .pkl 模型檔案重新生成 v3.8_training_results.json"""
    models_dir = Path("models/track_specific_v3.8")
    
    if not models_dir.exists():
        print(f"❌ 找不到 {models_dir}")
        return
    
    model_files = list(models_dir.glob("*.pkl"))
    
    if not model_files:
        print(f"❌ {models_dir} 中沒有 .pkl 檔案")
        return
    
    print(f"找到 {len(model_files)} 個模型檔案")
    
    results = {
        'metadata': {
            'version': 'v3.8',
            'feature_count': 17,
            'is_top_driver_method': 'hardcoded',
            'training_date': datetime.now().isoformat(),
            'tracks_trained': len(model_files),
            'regenerated': True,
            'regeneration_note': 'Regenerated from .pkl files due to JSON corruption'
        },
        'results': {}
    }
    
    for model_file in sorted(model_files):
        track_name = model_file.stem
        
        try:
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)
            
            results['results'][track_name] = {
                'track': track_name,
                'cv_mae': float(model_data.get('cv_mae', 0)),
                'train_mae': float(model_data.get('train_mae', 0)),
                'train_r2': float(model_data.get('train_r2', 0)),
                'sample_count': int(model_data.get('sample_count', 0)),
                'best_params': model_data.get('best_params', {}),
                'feature_importance': {
                    k: float(v) for k, v in model_data.get('feature_importance', {}).items()
                }
            }
            
            print(f"✅ {track_name:<20} R²={model_data.get('train_r2', 0):.4f}, "
                  f"CV MAE={model_data.get('cv_mae', 0):.3f}s")
        
        except Exception as e:
            print(f"❌ {track_name:<20} 讀取失敗: {e}")
    
    # 保存 JSON
    output_file = Path("v3.8_training_results.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 已重新生成 {output_file}")
    print(f"   包含 {len(results['results'])} 個賽道的結果")


if __name__ == '__main__':
    regenerate_v38_results()
