"""
Corner Apex Speed Box Plot Generator
彎道 Apex 速度箱型圖生成器

功能：
- 讀取 F47 JSON 數據（all_drivers_cornering_analysis）
- 分析三個彎道（low/mid/high speed）的 apex_speed
- 使用 matplotlib 生成專業級 Box Plot
- 支援中文顯示（Microsoft JhengHei 字體）

作者：AI Assistant
日期：2025-10-27
版本：1.0.0
"""

import json
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class CornerApexBoxPlotGenerator:
    """彎道 Apex 速度箱型圖生成器"""
    
    def __init__(self, json_path: str):
        """
        初始化生成器
        
        Args:
            json_path: F47 JSON 檔案路徑
        """
        self.json_path = Path(json_path)
        self.data: Dict[str, Any] = {}
        self.apex_speeds: Dict[str, List[float]] = {
            'low_speed': [],
            'mid_speed': [],
            'high_speed': []
        }
        
    def load_data(self) -> bool:
        """載入 JSON 數據"""
        try:
            print(f"[INFO] 載入 JSON 檔案: {self.json_path}")
            
            if not self.json_path.exists():
                print(f"[ERROR] 檔案不存在: {self.json_path}")
                return False
            
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            print(f"[SUCCESS] JSON 載入成功")
            print(f"  - Year: {self.data.get('year')}")
            print(f"  - Race: {self.data.get('race')}")
            print(f"  - Session: {self.data.get('session')}")
            print(f"  - Function ID: {self.data.get('function_id')}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 載入 JSON 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_apex_speeds(self) -> bool:
        """從 fastest_lap_analysis 提取 apex_speed 數據"""
        try:
            print("\n[INFO] 提取 apex_speed 數據...")
            
            fastest_lap = self.data.get('fastest_lap_analysis', {})
            drivers = fastest_lap.get('drivers', [])
            
            if not drivers:
                print("[ERROR] 找不到車手數據")
                return False
            
            # 取得彎道名稱
            selected_corners = self.data.get('selected_corners', {})
            corner_names = {
                'low_speed': f"T{selected_corners.get('low_speed', {}).get('corner_number', '?')}",
                'mid_speed': f"T{selected_corners.get('mid_speed', {}).get('corner_number', '?')}",
                'high_speed': f"T{selected_corners.get('high_speed', {}).get('corner_number', '?')}"
            }
            
            self.corner_names = corner_names
            
            # 提取每個彎道的 apex_speed
            for driver_data in drivers:
                driver = driver_data.get('driver')
                corners = driver_data.get('corners', {})
                
                for speed_type in ['low_speed', 'mid_speed', 'high_speed']:
                    corner_key = f"{speed_type}_corner_{selected_corners.get(speed_type, {}).get('corner_number')}"
                    
                    if corner_key in corners:
                        apex_speed = corners[corner_key].get('apex_speed')
                        if apex_speed is not None:
                            self.apex_speeds[speed_type].append(apex_speed)
            
            # 顯示統計
            print("\n[SUCCESS] 數據提取完成:")
            for speed_type, speeds in self.apex_speeds.items():
                corner_name = corner_names[speed_type]
                print(f"  - {speed_type} ({corner_name}): {len(speeds)} 個數據點")
                if speeds:
                    print(f"    範圍: {min(speeds):.1f} - {max(speeds):.1f} km/h")
                    print(f"    中位數: {np.median(speeds):.1f} km/h")
            
            return all(len(speeds) > 0 for speeds in self.apex_speeds.values())
            
        except Exception as e:
            print(f"[ERROR] 提取數據失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_boxplot(self, output_path: str = None, show: bool = True) -> bool:
        """
        生成 Box Plot 圖表
        
        Args:
            output_path: 輸出檔案路徑（None 則不儲存）
            show: 是否顯示圖表
        
        Returns:
            是否成功生成
        """
        try:
            print("\n[INFO] 生成 Box Plot...")
            
            # 準備數據
            data_to_plot = [
                self.apex_speeds['low_speed'],
                self.apex_speeds['mid_speed'],
                self.apex_speeds['high_speed']
            ]
            
            labels = [
                f"{self.corner_names['low_speed']}\n低速彎",
                f"{self.corner_names['mid_speed']}\n中速彎",
                f"{self.corner_names['high_speed']}\n高速彎"
            ]
            
            # 創建圖表
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 繪製 Box Plot
            bp = ax.boxplot(
                data_to_plot,
                labels=labels,
                patch_artist=True,
                notch=True,  # 添加凹槽
                showmeans=True,  # 顯示平均值
                meanprops=dict(marker='D', markerfacecolor='red', markeredgecolor='red', markersize=8),
                medianprops=dict(color='black', linewidth=2),
                boxprops=dict(facecolor='lightblue', edgecolor='blue', linewidth=1.5),
                whiskerprops=dict(color='blue', linewidth=1.5),
                capprops=dict(color='blue', linewidth=1.5),
                flierprops=dict(marker='o', markerfacecolor='red', markersize=6, alpha=0.5)
            )
            
            # 設定標題和標籤
            year = self.data.get('year')
            race = self.data.get('race')
            session = self.data.get('session')
            
            ax.set_title(
                f'{year} {race} Grand Prix - {session} Session\n'
                f'彎道 Apex 速度分布 (最速圈)',
                fontsize=16,
                fontweight='bold',
                pad=20
            )
            ax.set_xlabel('彎道類型', fontsize=13, fontweight='bold')
            ax.set_ylabel('Apex 速度 (km/h)', fontsize=13, fontweight='bold')
            
            # 添加網格
            ax.grid(True, axis='y', alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)
            
            # 添加統計資訊文字
            stats_text = []
            for i, (speed_type, speeds) in enumerate(self.apex_speeds.items(), 1):
                corner_name = self.corner_names[speed_type]
                stats = {
                    'n': len(speeds),
                    'min': np.min(speeds),
                    'q1': np.percentile(speeds, 25),
                    'median': np.median(speeds),
                    'q3': np.percentile(speeds, 75),
                    'max': np.max(speeds),
                    'mean': np.mean(speeds)
                }
                
                stats_text.append(
                    f"{corner_name}: n={stats['n']}, "
                    f"範圍=[{stats['min']:.1f}, {stats['max']:.1f}], "
                    f"中位數={stats['median']:.1f}, "
                    f"平均={stats['mean']:.1f}"
                )
            
            # 在圖表下方添加統計資訊
            fig.text(
                0.5, 0.02,
                '\n'.join(stats_text),
                ha='center',
                fontsize=9,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3)
            )
            
            # 調整佈局
            plt.tight_layout(rect=[0, 0.08, 1, 0.96])
            
            # 儲存圖表
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                print(f"[SUCCESS] 圖表已儲存: {output_path}")
            
            # 顯示圖表
            if show:
                plt.show()
            else:
                plt.close()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 生成 Box Plot 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函數"""
    print("=" * 80)
    print("彎道 Apex 速度箱型圖生成器")
    print("=" * 80)
    
    # JSON 檔案路徑
    json_path = "json/all_drivers_cornering_analysis_2025_Mexico_R.json"
    
    # 輸出路徑
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"output/corner_apex_boxplot_{timestamp}.png"
    
    # 創建生成器
    generator = CornerApexBoxPlotGenerator(json_path)
    
    # 執行流程
    if not generator.load_data():
        print("\n[FAILED] 載入數據失敗")
        return
    
    if not generator.extract_apex_speeds():
        print("\n[FAILED] 提取數據失敗")
        return
    
    if not generator.generate_boxplot(output_path=output_path, show=True):
        print("\n[FAILED] 生成圖表失敗")
        return
    
    print("\n" + "=" * 80)
    print("[SUCCESS] Box Plot 生成完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
