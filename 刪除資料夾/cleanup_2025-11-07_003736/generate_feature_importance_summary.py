"""
生成所有賽道的前五項特徵重要性總表
讀取 v3.8 訓練模型並提取特徵重要性數據
"""

import pickle
import json
from pathlib import Path
from datetime import datetime

def load_model_feature_importance(model_path):
    """從 pickle 模型檔案中提取特徵重要性"""
    try:
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning)
        
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        # 模型數據結構: {'model': XGBoost 模型, 'feature_names': [...], 'params': {...}}
        if 'model' in model_data and 'feature_names' in model_data:
            model = model_data['model']
            feature_names = model_data['feature_names']
            
            # 從 XGBoost 模型獲取特徵重要性
            feature_importances = model.feature_importances_
            
            # 建立字典：特徵名稱 -> 重要性
            importance_dict = dict(zip(feature_names, feature_importances))
            
            # 排序並返回前5項
            top5 = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:5]
            return top5
        else:
            return None
            
    except Exception as e:
        print(f"  [錯誤] 無法讀取 {model_path.name}: {e}")
        return None

def generate_summary():
    """生成所有賽道的特徵重要性總表"""
    models_dir = Path("models/track_specific_v3.8")
    
    if not models_dir.exists():
        print(f"[錯誤] 目錄不存在: {models_dir}")
        return
    
    # 2025 賽季所有賽道
    tracks = [
        'Australia', 'China', 'Japan', 'Bahrain', 'Saudi Arabia', 'Miami',
        'Emilia Romagna', 'Monaco', 'Spain', 'Canada', 'Austria', 'Great Britain',
        'Belgium', 'Hungary', 'Netherlands', 'Italy', 'Azerbaijan', 'Singapore',
        'United States', 'Mexico', 'Brazil', 'Las Vegas', 'Qatar', 'Abu Dhabi'
    ]
    
    summary = {}
    
    print(f"\n{'='*80}")
    print(f"V3.8 模型特徵重要性總表 - 前五項特徵")
    print(f"{'='*80}\n")
    
    for track in tracks:
        model_file = models_dir / f"{track}.pkl"
        
        if not model_file.exists():
            print(f"[跳過] {track:20s} - 模型檔案不存在")
            continue
        
        top5 = load_model_feature_importance(model_file)
        
        if top5:
            print(f"\n{track}")
            print(f"{'-'*70}")
            for i, (feature, importance) in enumerate(top5, 1):
                print(f"  {i}. {feature:35s}  {importance*100:6.2f}%")
            
            # 保存到 summary (確保轉換為 Python float 類型)
            summary[track] = {
                'features': [
                    {
                        'rank': i,
                        'feature': feature,
                        'importance_pct': round(float(importance) * 100, 2)
                    }
                    for i, (feature, importance) in enumerate(top5, 1)
                ]
            }
        else:
            print(f"[錯誤] {track:20s} - 無法提取特徵重要性")
    
    # 保存為 JSON 檔案
    output_file = Path("reports") / f"feature_importance_summary_v3.8_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(exist_ok=True)
    
    output_data = {
        "metadata": {
            "model_version": "v3.8",
            "generated_at": datetime.now().isoformat(),
            "total_tracks": len(summary),
            "top_n_features": 5
        },
        "tracks": summary
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"[完成] 總表已保存至: {output_file}")
    print(f"[統計] 成功處理 {len(summary)} 個賽道")
    print(f"{'='*80}\n")
    
    return summary

if __name__ == "__main__":
    generate_summary()
