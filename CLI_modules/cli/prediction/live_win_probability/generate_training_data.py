#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Win Probability - Training Data Generation Script

此腳本用於批量提取訓練數據並導出為 CSV 檔案。

使用方法:
    python generate_training_data.py --years 2023 2024 --output data/training_data.csv
    
輸出:
    - training_data.csv: 訓練數據（2023-2024）
    - validation_data.csv: 驗證數據（2025）
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import logging
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到路徑
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from CLI_modules.cli.prediction.live_win_probability.data_extractor import (
    LiveWinProbabilityDataExtractor
)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_training_data(
    years: list,
    output_path: str,
    base_path: str = "json/LiveF1"
) -> None:
    """
    生成訓練數據 CSV
    
    Args:
        years: 年份列表
        output_path: 輸出 CSV 路徑
        base_path: LiveF1 JSON 數據根目錄
    """
    extractor = LiveWinProbabilityDataExtractor(base_path=base_path)
    
    all_samples = []
    for year in years:
        logger.info(f"Extracting data for {year}...")
        samples = extractor.extract_all_races(year)
        all_samples.extend(samples)
        logger.info(f"  {year}: {len(samples)} samples")
    
    if not all_samples:
        logger.error("No samples extracted!")
        return
        
    # 轉換為 DataFrame
    df = extractor.to_dataframe(all_samples)
    
    # 確保輸出目錄存在
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 導出 CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"Saved {len(df)} samples to {output_file}")
    
    # 輸出統計
    print(f"\n{'='*60}")
    print(f"Training Data Statistics")
    print(f"{'='*60}")
    print(f"Total samples: {len(df)}")
    print(f"Years: {years}")
    print(f"Races: {df.groupby(['year', 'race_name']).ngroups}")
    print(f"Drivers: {df['driver_code'].nunique()}")
    print(f"\nFeatures (18):")
    feature_cols = [
        'position', 'gap_to_leader', 'gap_to_ahead', 'lap_time', 'best_lap_time',
        'tyre_compound', 'tyre_age', 'pit_count', 'laps_remaining',
        'track_status', 'air_temp', 'rainfall',
        'driver_win_rate', 'driver_podium_rate', 'team_rating',
        'circuit_overtake_rate', 'circuit_sc_rate', 'qualifying_position'
    ]
    for col in feature_cols:
        if col in df.columns:
            print(f"  - {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}")
    
    print(f"\nLabel distribution (final_position):")
    for pos in range(1, 22):
        count = (df['final_position'] == pos).sum()
        if count > 0:
            print(f"  P{pos}: {count} ({count/len(df)*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Generate training data for Live Win Probability model"
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024],
        help="Years to extract data from (default: 2023 2024)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/live_win_probability/training_data.csv",
        help="Output CSV file path"
    )
    parser.add_argument(
        "--validation-years",
        nargs="+",
        type=int,
        default=[2025],
        help="Years for validation data (default: 2025)"
    )
    parser.add_argument(
        "--validation-output",
        type=str,
        default="data/live_win_probability/validation_data.csv",
        help="Validation CSV file path"
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default="json/LiveF1",
        help="Base path for LiveF1 JSON data"
    )
    
    args = parser.parse_args()
    
    # 切換到專案根目錄
    import os
    os.chdir(project_root)
    
    print(f"\n{'='*60}")
    print(f"Live Win Probability - Training Data Generator")
    print(f"{'='*60}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Project root: {project_root}")
    print(f"Base path: {args.base_path}")
    
    # 生成訓練數據
    print(f"\n[1/2] Generating training data ({args.years})...")
    generate_training_data(
        years=args.years,
        output_path=args.output,
        base_path=args.base_path
    )
    
    # 生成驗證數據
    print(f"\n[2/2] Generating validation data ({args.validation_years})...")
    generate_training_data(
        years=args.validation_years,
        output_path=args.validation_output,
        base_path=args.base_path
    )
    
    print(f"\n{'='*60}")
    print("Data generation complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
