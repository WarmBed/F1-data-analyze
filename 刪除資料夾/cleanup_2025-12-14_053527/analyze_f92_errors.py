"""
F92 深度誤差分析工具
分析單圈誤差分佈、進站影響、配方差異
"""
import sys
import json
import fastf1
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from smart_base_time_extractor import extract_base_time_robust

# 中文字體設定
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Import F92
sys.path.insert(0, 'CLI_modules/cli/prediction')
from f92_hybrid_predictor import F92HybridPredictor


class F92ErrorAnalyzer:
    """F92 誤差深度分析器"""
    
    def __init__(self):
        self.f92 = F92HybridPredictor()
        fastf1.Cache.enable_cache('f1_analysis_cache/')
    
    def analyze_race(self, year: int, race: str, driver: str, 
                     stints: list, verbose: bool = True):
        """
        深度分析單場比賽
        
        Args:
            year: 賽季
            race: 賽事名稱
            driver: 車手代碼
            stints: [(stint_start, stint_end, compound), ...]
            verbose: 是否顯示詳細輸出
        
        Returns:
            dict: {
                'overall_mae': float,
                'overall_bias': float,
                'by_stint_position': {...},
                'by_compound': {...},
                'by_stint': [...],
                'lap_errors': pd.DataFrame
            }
        """
        print(f"\n{'='*80}")
        print(f"🔬 F92 深度誤差分析: {year} {race} {driver}")
        print(f"{'='*80}\n")
        
        # 1. 獲取智能 base_time 和 SC 圈
        print("📊 Step 1: 提取 base_time 與 SC 圈...")
        base_time, info = extract_base_time_robust(year, race, driver)
        skip_laps = info.get('sc_laps', [])
        
        print(f"  ✅ Base Time: {base_time:.3f}s")
        print(f"  ⚠️  SC 圈: {skip_laps} (共 {len(skip_laps)} 圈)")
        
        # 2. 執行 F92 預測
        print("\n🤖 Step 2: 執行 F92 預測...")
        result = self.f92.predict(
            year=year, race=race, driver=driver,
            base_time=base_time,
            stints=stints,
            skip_laps=skip_laps,  # ← 跳過 SC 圈
            use_ml=True
        )
        
        if not result or 'predictions' not in result:
            print("❌ F92 預測失敗！")
            return None
        
        predictions = result['predictions']
        print(f"  ✅ 預測圈數: {len(predictions)}")
        
        # 3. 載入實際圈速
        print("\n📥 Step 3: 載入實際圈速...")
        session = fastf1.get_session(year, race, 'R')
        session.load()
        driver_laps = session.laps.pick_driver(driver)
        driver_laps = driver_laps[driver_laps['LapTime'].notna()]
        driver_laps['LapTimeSeconds'] = driver_laps['LapTime'].dt.total_seconds()
        
        # 4. 合併預測與實際
        lap_errors = []
        for pred in predictions:
            lap_num = pred['lap']
            
            # 找實際圈速
            actual_lap = driver_laps[driver_laps['LapNumber'] == lap_num]
            if actual_lap.empty:
                continue
            
            actual_time = actual_lap['LapTimeSeconds'].iloc[0]
            
            # 跳過異常圈（SC、事故等）
            if actual_time > 120:
                continue
            
            # 判斷進站階段
            stint_idx = self._find_stint_index(lap_num, stints)
            stint_start, stint_end, compound = stints[stint_idx]
            stint_lap = lap_num - stint_start + 1
            
            # 分類進站位置
            stint_length = stint_end - stint_start + 1
            if stint_lap <= 3:
                stint_phase = 'New Tyre'
            elif stint_lap >= stint_length - 3:
                stint_phase = 'Pre-Pit'
            elif stint_lap <= 15:
                stint_phase = 'Mid-Stint'
            else:
                stint_phase = 'Old Tyre'
            
            error = pred['predicted_time'] - actual_time
            
            lap_errors.append({
                'lap': lap_num,
                'actual': actual_time,
                'predicted': pred['predicted_time'],
                'error': error,
                'abs_error': abs(error),
                'stint_idx': stint_idx + 1,
                'stint_lap': stint_lap,
                'stint_phase': stint_phase,
                'compound': compound,
                'physics_pred': pred.get('physics_pred', 0),
                'fuel_effect': pred.get('fuel_effect', 0),
                'tire_deg': pred.get('tire_degradation', 0),
                'ml_correction': pred.get('ml_correction', 0)
            })
        
        df = pd.DataFrame(lap_errors)
        
        if df.empty:
            print("❌ 無可用數據！")
            return None
        
        print(f"  ✅ 有效圈數: {len(df)}")
        
        # 5. 整體統計
        overall_mae = df['abs_error'].mean()
        overall_bias = df['error'].mean()
        overall_std = df['error'].std()
        
        print(f"\n{'='*80}")
        print(f"📈 整體統計:")
        print(f"{'='*80}")
        print(f"  MAE:  {overall_mae:.3f}s")
        print(f"  Bias: {overall_bias:+.3f}s  ({'偏快' if overall_bias < 0 else '偏慢'})")
        print(f"  Std:  {overall_std:.3f}s")
        
        # 6. 按進站階段分析
        print(f"\n{'='*80}")
        print(f"📊 按進站階段分析:")
        print(f"{'='*80}")
        
        phase_stats = {}
        for phase in ['New Tyre', 'Mid-Stint', 'Old Tyre', 'Pre-Pit']:
            phase_df = df[df['stint_phase'] == phase]
            if phase_df.empty:
                continue
            
            mae = phase_df['abs_error'].mean()
            bias = phase_df['error'].mean()
            count = len(phase_df)
            
            phase_stats[phase] = {
                'mae': mae,
                'bias': bias,
                'count': count
            }
            
            print(f"  {phase:12s}: MAE={mae:.3f}s, Bias={bias:+.3f}s, N={count}")
        
        # 7. 按配方分析
        print(f"\n{'='*80}")
        print(f"🏎️  按配方分析:")
        print(f"{'='*80}")
        
        compound_stats = {}
        for compound in df['compound'].unique():
            comp_df = df[df['compound'] == compound]
            
            mae = comp_df['abs_error'].mean()
            bias = comp_df['error'].mean()
            count = len(comp_df)
            
            compound_stats[compound] = {
                'mae': mae,
                'bias': bias,
                'count': count
            }
            
            print(f"  {compound:8s}: MAE={mae:.3f}s, Bias={bias:+.3f}s, N={count}")
        
        # 8. 按進站分析
        print(f"\n{'='*80}")
        print(f"🔄 按進站分析:")
        print(f"{'='*80}")
        
        stint_stats = []
        for stint_idx in range(len(stints)):
            stint_df = df[df['stint_idx'] == stint_idx + 1]
            if stint_df.empty:
                continue
            
            stint_start, stint_end, compound = stints[stint_idx]
            mae = stint_df['abs_error'].mean()
            bias = stint_df['error'].mean()
            count = len(stint_df)
            
            stint_stats.append({
                'stint_idx': stint_idx + 1,
                'laps': f"{stint_start}-{stint_end}",
                'compound': compound,
                'mae': mae,
                'bias': bias,
                'count': count
            })
            
            print(f"  Stint {stint_idx+1} ({stint_start}-{stint_end}) {compound:8s}: MAE={mae:.3f}s, Bias={bias:+.3f}s, N={count}")
        
        # 9. 視覺化
        self._plot_error_analysis(df, stints, year, race, driver)
        
        return {
            'overall_mae': overall_mae,
            'overall_bias': overall_bias,
            'overall_std': overall_std,
            'by_stint_phase': phase_stats,
            'by_compound': compound_stats,
            'by_stint': stint_stats,
            'lap_errors': df
        }
    
    def _find_stint_index(self, lap: int, stints: list) -> int:
        """找到當前圈數對應的進站索引"""
        for idx, (start, end, compound) in enumerate(stints):
            if start <= lap <= end:
                return idx
        return len(stints) - 1
    
    def _plot_error_analysis(self, df: pd.DataFrame, stints: list, 
                             year: int, race: str, driver: str):
        """視覺化誤差分析"""
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        fig.suptitle(f'F92 誤差深度分析: {year} {race} {driver}', 
                     fontsize=16, fontweight='bold')
        
        # 圖 1: 單圈誤差趨勢 + 進站邊界
        ax1 = axes[0]
        ax1.plot(df['lap'], df['error'], 'o-', label='誤差', markersize=4)
        ax1.axhline(0, color='black', linestyle='--', linewidth=1)
        ax1.fill_between(df['lap'], df['error'], 0, 
                         where=(df['error'] > 0), alpha=0.3, color='red', label='預測偏慢')
        ax1.fill_between(df['lap'], df['error'], 0, 
                         where=(df['error'] < 0), alpha=0.3, color='blue', label='預測偏快')
        
        # 進站邊界
        for idx, (start, end, compound) in enumerate(stints):
            if idx > 0:
                ax1.axvline(start, color='orange', linestyle='--', linewidth=2, alpha=0.7)
                ax1.text(start, ax1.get_ylim()[1] * 0.9, f'Pit → {compound}', 
                        rotation=90, va='top', fontsize=9)
        
        ax1.set_xlabel('圈數')
        ax1.set_ylabel('誤差 (秒)')
        ax1.set_title('單圈誤差趨勢')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # 圖 2: 按進站階段分組箱形圖
        ax2 = axes[1]
        phases = ['New Tyre', 'Mid-Stint', 'Old Tyre', 'Pre-Pit']
        phase_data = [df[df['stint_phase'] == phase]['error'].values 
                      for phase in phases if not df[df['stint_phase'] == phase].empty]
        phase_labels = [phase for phase in phases 
                       if not df[df['stint_phase'] == phase].empty]
        
        bp = ax2.boxplot(phase_data, labels=phase_labels, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')
        ax2.axhline(0, color='black', linestyle='--', linewidth=1)
        ax2.set_ylabel('誤差 (秒)')
        ax2.set_title('按進站階段誤差分佈')
        ax2.grid(True, alpha=0.3)
        
        # 圖 3: 按配方分組箱形圖
        ax3 = axes[2]
        compounds = df['compound'].unique()
        compound_data = [df[df['compound'] == comp]['error'].values for comp in compounds]
        
        bp = ax3.boxplot(compound_data, labels=compounds, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightgreen')
        ax3.axhline(0, color='black', linestyle='--', linewidth=1)
        ax3.set_ylabel('誤差 (秒)')
        ax3.set_title('按配方誤差分佈')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 儲存圖片
        output_path = f'reports/f92_error_analysis_{year}_{race}_{driver}.png'
        plt.savefig(output_path, dpi=150)
        print(f"\n📊 圖表已儲存: {output_path}")
        plt.show()


def main():
    """主程式"""
    analyzer = F92ErrorAnalyzer()
    
    # ===== 測試案例 1: Japan 2025 =====
    print("\n" + "="*100)
    print("測試案例 1: Japan 2025 VER")
    print("="*100)
    
    japan_result = analyzer.analyze_race(
        year=2025,
        race="Japan",
        driver="VER",
        stints=[
            (1, 21, "MEDIUM"),
            (22, 53, "HARD")
        ]
    )
    
    # ===== 測試案例 2: Mexico 2024 =====
    print("\n" + "="*100)
    print("測試案例 2: Mexico 2024 VER")
    print("="*100)
    
    mexico_result = analyzer.analyze_race(
        year=2024,
        race="Mexico",
        driver="VER",
        stints=[
            (1, 26, "MEDIUM"),
            (27, 71, "HARD")
        ]
    )
    
    # ===== 總結比較 =====
    print("\n" + "="*100)
    print("總結比較")
    print("="*100)
    
    if japan_result and mexico_result:
        print(f"\n  Japan 2025:")
        print(f"    MAE:  {japan_result['overall_mae']:.3f}s")
        print(f"    Bias: {japan_result['overall_bias']:+.3f}s")
        
        print(f"\n  Mexico 2024:")
        print(f"    MAE:  {mexico_result['overall_mae']:.3f}s")
        print(f"    Bias: {mexico_result['overall_bias']:+.3f}s")
        
        print(f"\n  {'='*80}")
        print(f"  💡 關鍵發現:")
        print(f"  {'='*80}")
        
        # Japan 階段分析
        if 'New Tyre' in japan_result['by_stint_phase']:
            new_tyre_mae = japan_result['by_stint_phase']['New Tyre']['mae']
            print(f"    Japan 新胎誤差: {new_tyre_mae:.3f}s")
        
        # Mexico 階段分析
        if 'New Tyre' in mexico_result['by_stint_phase']:
            new_tyre_mae = mexico_result['by_stint_phase']['New Tyre']['mae']
            print(f"    Mexico 新胎誤差: {new_tyre_mae:.3f}s")
        
        print(f"\n  ✅ 分析完成！")


if __name__ == "__main__":
    main()
