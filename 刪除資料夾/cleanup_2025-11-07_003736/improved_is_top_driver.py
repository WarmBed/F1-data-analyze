"""
is_top_driver 特徵改進 - 簡化實現範例
基於車手積分排名動態計算
"""

import pandas as pd
import numpy as np

class ImprovedTopDriverCalculator:
    """改進版的 is_top_driver 特徵計算器"""
    
    def __init__(self, top_n: int = 8):
        """
        初始化
        
        Args:
            top_n: 前 N 名視為頂尖車手（預設 8）
        """
        self.top_n = top_n
        self.points_cache = {}  # 積分緩存
    
    def calculate_is_top_driver(self, df: pd.DataFrame, method: str = 'season_total') -> pd.DataFrame:
        """
        計算 is_top_driver 特徵
        
        Args:
            df: 訓練數據（必須包含 driver, year, round 欄位）
            method: 計算方法
                - 'season_total': 使用賽季總積分（回溯歷史）
                - 'before_race': 使用比賽前積分（需額外數據）
                - 'hybrid': 混合模式（賽季初用上季積分）
        
        Returns:
            添加 is_top_driver 欄位的 DataFrame
        """
        df = df.copy()
        
        if method == 'season_total':
            return self._calculate_by_season_total(df)
        elif method == 'before_race':
            return self._calculate_by_race_points(df)
        elif method == 'hybrid':
            return self._calculate_hybrid(df)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _calculate_by_season_total(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        方法 1: 基於賽季總積分（最簡單）
        
        邏輯：該賽季積分最高的前 N 名車手 = 頂尖車手
        優點：實現簡單，無需額外數據
        缺點：無法反映賽季中的變化
        """
        # 計算每個車手在每個賽季的總積分
        # 注意：這裡假設 df 有 'points' 欄位（比賽後積分）
        if 'points' not in df.columns:
            # 如果沒有 points，使用 ideal_lap 排名作為替代
            print("[警告] 無 'points' 欄位，使用 ideal_lap 排名作為替代")
            return self._calculate_by_performance_ranking(df)
        
        # 按年份分組，計算每個車手的總積分
        season_points = df.groupby(['year', 'driver'])['points'].sum().reset_index()
        
        # 每年取前 N 名
        top_drivers_per_year = (
            season_points.sort_values(['year', 'points'], ascending=[True, False])
            .groupby('year')
            .head(self.top_n)
        )
        
        # 創建 (year, driver) → is_top_driver 的映射
        top_driver_set = set(zip(top_drivers_per_year['year'], top_drivers_per_year['driver']))
        
        # 應用到原始數據
        df['is_top_driver'] = df.apply(
            lambda row: int((row['year'], row['driver']) in top_driver_set),
            axis=1
        )
        
        return df
    
    def _calculate_by_performance_ranking(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        替代方法：基於 FP3 表現排名（無需積分數據）
        
        邏輯：該賽季平均 ideal_lap 最快的前 N 名車手 = 頂尖車手
        """
        # 計算每個車手在每個賽季的平均 ideal_lap
        avg_performance = df.groupby(['year', 'driver'])['ideal_lap'].mean().reset_index()
        
        # 每年取平均最快的前 N 名
        top_drivers_per_year = (
            avg_performance.sort_values(['year', 'ideal_lap'], ascending=[True, True])
            .groupby('year')
            .head(self.top_n)
        )
        
        # 創建映射
        top_driver_set = set(zip(top_drivers_per_year['year'], top_drivers_per_year['driver']))
        
        # 應用
        df['is_top_driver'] = df.apply(
            lambda row: int((row['year'], row['driver']) in top_driver_set),
            axis=1
        )
        
        return df
    
    def _calculate_by_race_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        方法 2: 基於比賽前積分（理想方案）
        
        需要額外數據：points_before_race
        """
        if 'points_before_race' not in df.columns:
            print("[警告] 無 'points_before_race' 欄位，回退到 season_total 方法")
            return self._calculate_by_season_total(df)
        
        # 每場比賽按積分排名取前 N 名
        df['rank_before_race'] = (
            df.groupby(['year', 'round'])['points_before_race']
            .rank(method='min', ascending=False)
        )
        
        df['is_top_driver'] = (df['rank_before_race'] <= self.top_n).astype(int)
        
        return df
    
    def _calculate_hybrid(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        方法 3: 混合模式
        
        邏輯：
        - 賽季前 3 場：使用上一賽季的積分榜
        - 第 4 場起：使用本賽季積分榜
        """
        # TODO: 實現混合邏輯
        return self._calculate_by_season_total(df)


# ========== 使用範例 ==========

def example_usage():
    """示範如何使用改進版的 is_top_driver 計算"""
    
    # 模擬訓練數據
    data = {
        'year': [2024] * 10,
        'round': [1] * 5 + [2] * 5,
        'driver': ['VER', 'HAM', 'LEC', 'NOR', 'ALO'] * 2,
        'ideal_lap': [80.1, 80.3, 80.2, 80.4, 80.9, 79.8, 80.0, 79.9, 80.1, 80.8],
    }
    
    df = pd.DataFrame(data)
    
    print("=" * 70)
    print("is_top_driver 改進版範例")
    print("=" * 70)
    
    # 硬編碼方法（舊版）
    print("\n[舊版] 硬編碼方法:")
    hardcoded_top = ['VER', 'HAM', 'LEC', 'NOR', 'PIA', 'SAI', 'RUS', 'PER']
    df['is_top_driver_old'] = df['driver'].isin(hardcoded_top).astype(int)
    print(df[['driver', 'is_top_driver_old']].drop_duplicates())
    
    # 動態方法（新版）
    print("\n[新版] 動態計算方法:")
    calculator = ImprovedTopDriverCalculator(top_n=3)  # 示範：前 3 名
    df_new = calculator.calculate_is_top_driver(df, method='season_total')
    print(df_new[['driver', 'is_top_driver']].drop_duplicates())
    
    # 對比
    print("\n[對比] 差異分析:")
    old_top = set(df[df['is_top_driver_old'] == 1]['driver'].unique())
    new_top = set(df_new[df_new['is_top_driver'] == 1]['driver'].unique())
    
    print(f"  硬編碼: {sorted(old_top)}")
    print(f"  動態計算: {sorted(new_top)}")
    
    if old_top != new_top:
        print(f"\n  ⚠️  差異:")
        print(f"    僅在硬編碼: {sorted(old_top - new_top)}")
        print(f"    僅在動態計算: {sorted(new_top - old_top)}")


if __name__ == "__main__":
    example_usage()
