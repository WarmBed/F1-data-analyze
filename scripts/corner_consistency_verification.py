"""
彎道一致性驗證腳本 - 驗證彎道識別算法的穩定性

目標: 分析 2022-2025 年美國站正賽最快車手的彎道識別結果，
     檢查識別出的彎道位置是否年年一致。

基於 F55 彎道分析開發文件的理論。
"""

import fastf1
import numpy as np
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
from typing import Dict, List, Tuple

# 設定中文字體
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


class CornerConsistencyVerifier:
    """彎道一致性驗證器"""
    
    def __init__(self):
        self.cache_dir = Path('f1_analysis_cache')
        self.output_dir = Path('json') / 'corner_consistency'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 啟用 FastF1 緩存
        fastf1.Cache.enable_cache(str(self.cache_dir))
        
        self.results = {}
        
    def _identify_corners_from_speed(self, telemetry: pd.DataFrame) -> Dict[int, Dict]:
        """
        從速度變化識別彎道 - 改進版
        
        改進點:
        1. 使用速度局部極小值檢測彎心
        2. 限制彎道長度避免異常範圍
        3. 增加彎道合併邏輯
        
        Args:
            telemetry: 包含 Speed 和 Distance 的遙測數據
            
        Returns:
            彎道字典 {彎道編號: {start_distance, end_distance, min_speed, ...}}
        """
        try:
            from scipy.signal import find_peaks
            
            speeds = telemetry['Speed'].values
            distances = telemetry['Distance'].values
            
            # 使用 scipy 找到速度局部極小值（彎心候選點）
            # 反轉速度以使用 find_peaks
            inverted_speeds = -speeds
            
            # 找到局部極小值，設定最小距離和最小突出度
            peaks, properties = find_peaks(
                inverted_speeds, 
                distance=30,  # 至少間隔 30 個數據點（約 200m）
                prominence=15  # 速度下降至少 15 km/h
            )
            
            if len(peaks) == 0:
                print(f"⚠️  未找到明顯的速度極小值點")
                return {}
            
            print(f"🔍 找到 {len(peaks)} 個速度極小值點（彎心候選）")
            
            # 為每個彎心構建彎道範圍
            corners_data = {}
            
            for corner_num, apex_idx in enumerate(peaks, start=1):
                apex_distance = distances[apex_idx]
                apex_speed = speeds[apex_idx]
                
                # 向前找彎道起點（速度開始下降）
                start_idx = apex_idx
                for i in range(apex_idx - 1, max(0, apex_idx - 50), -1):
                    if speeds[i] > apex_speed * 1.3:  # 速度高於彎心 30%
                        start_idx = i
                        break
                
                # 向後找彎道終點（速度開始上升）
                end_idx = apex_idx
                for i in range(apex_idx + 1, min(len(speeds), apex_idx + 50)):
                    if speeds[i] > apex_speed * 1.3:  # 速度高於彎心 30%
                        end_idx = i
                        break
                
                # 計算彎道統計
                corner_speeds = speeds[start_idx:end_idx+1]
                corner_distances = distances[start_idx:end_idx+1]
                
                if len(corner_speeds) > 5:  # 過濾太短的彎道
                    # 檢查彎道長度是否合理（不超過 500m）
                    corner_length = corner_distances[-1] - corner_distances[0]
                    if corner_length > 500:
                        print(f"⚠️  彎道 {corner_num} 長度異常 ({corner_length:.0f}m)，跳過")
                        continue
                    
                    corners_data[corner_num] = {
                        'start_distance': float(corner_distances[0]),
                        'end_distance': float(corner_distances[-1]),
                        'apex_distance': float(apex_distance),
                        'min_speed': float(apex_speed),
                        'max_speed': float(np.max(corner_speeds)),
                        'avg_speed': float(np.mean(corner_speeds)),
                        'speed_drop': float(np.max(corner_speeds) - apex_speed),
                        'corner_length': float(corner_length)
                    }
            
            # 重新編號（去除跳過的彎道）
            renumbered_corners = {}
            for new_num, (old_num, data) in enumerate(corners_data.items(), start=1):
                renumbered_corners[new_num] = data
            
            return renumbered_corners
            
        except Exception as e:
            print(f"❌ [ERROR] 識別彎道失敗: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _classify_corner_by_speed(self, min_speed: float) -> str:
        """
        根據最低速度分類彎道類型
        
        依照 F55 文件的分類標準:
        - 低速彎: < 120 km/h
        - 中速彎: 120-180 km/h  
        - 高速彎: > 180 km/h
        """
        if min_speed < 120:
            return "低速彎"
        elif min_speed < 180:
            return "中速彎"
        else:
            return "高速彎"
    
    def analyze_year(self, year: int, race_name: str = "United States", session_type: str = "R") -> Dict:
        """
        分析單一年份的彎道識別結果
        
        Args:
            year: 賽季年份
            race_name: 賽事名稱（預設: United States）
            session_type: 會話類型（R=正賽, Q=排位賽）
            
        Returns:
            分析結果字典
        """
        print(f"\n{'='*60}")
        print(f"📊 分析 {year} 年 {race_name} 站 (Session: {session_type})")
        print(f"{'='*60}")
        
        try:
            # 載入會話數據
            print(f"⏳ 載入 {year} 年賽事數據...")
            session = fastf1.get_session(year, race_name, session_type)
            session.load()
            
            # 找到最快車手
            fastest_lap = session.laps.pick_fastest()
            driver_code = fastest_lap['Driver']
            lap_time = fastest_lap['LapTime']
            
            print(f"🏎️  最快車手: {driver_code}")
            print(f"⏱️  最快圈速: {lap_time}")
            
            # 獲取遙測數據
            telemetry = fastest_lap.get_car_data().add_distance()
            
            if telemetry.empty:
                print(f"❌ 無法獲取遙測數據")
                return None
            
            print(f"✅ 遙測數據點數: {len(telemetry)}")
            
            # 識別彎道
            print(f"🔍 執行彎道識別...")
            corners = self._identify_corners_from_speed(telemetry)
            
            if not corners:
                print(f"❌ 未識別到彎道")
                return None
            
            print(f"✅ 識別到 {len(corners)} 個彎道")
            
            # 分類彎道類型
            corner_types_count = {"低速彎": 0, "中速彎": 0, "高速彎": 0}
            for corner_data in corners.values():
                corner_type = self._classify_corner_by_speed(corner_data['min_speed'])
                corner_data['type'] = corner_type
                corner_types_count[corner_type] += 1
            
            # 計算賽道總長度
            track_length = telemetry['Distance'].max()
            
            result = {
                'year': year,
                'race': race_name,
                'session': session_type,
                'fastest_driver': driver_code,
                'lap_time': str(lap_time),
                'track_length': float(track_length),
                'corners_detected': len(corners),
                'corner_types': corner_types_count,
                'corners': corners,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            print(f"\n📈 彎道類型分布:")
            for corner_type, count in corner_types_count.items():
                print(f"   {corner_type}: {count} 個")
            
            return result
            
        except Exception as e:
            print(f"❌ [ERROR] 分析 {year} 年數據失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def compare_multi_year(self, years: List[int], race_name: str = "United States") -> Dict:
        """
        比較多年份的彎道識別結果
        
        Args:
            years: 要比較的年份列表
            race_name: 賽事名稱
            
        Returns:
            比較結果字典
        """
        print(f"\n{'='*60}")
        print(f"🔬 多年份彎道一致性驗證")
        print(f"{'='*60}")
        print(f"📅 分析年份: {years}")
        print(f"🏁 賽道: {race_name}")
        
        # 分析每個年份
        yearly_results = {}
        for year in years:
            result = self.analyze_year(year, race_name, "R")
            if result:
                yearly_results[year] = result
        
        if not yearly_results:
            print(f"❌ 沒有成功的分析結果")
            return None
        
        # 比較彎道位置一致性
        print(f"\n{'='*60}")
        print(f"📊 跨年度彎道位置比較")
        print(f"{'='*60}")
        
        comparison = self._compare_corner_positions(yearly_results)
        
        # 生成報告
        report = {
            'verification_type': 'corner_consistency_multi_year',
            'race': race_name,
            'years_analyzed': list(yearly_results.keys()),
            'yearly_results': yearly_results,
            'consistency_analysis': comparison,
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _compare_corner_positions(self, yearly_results: Dict) -> Dict:
        """
        比較年度間彎道位置的一致性
        
        改進點:
        1. 使用彎心位置匹配不同年份的彎道
        2. 容忍彎道數量差異
        3. 計算匹配率和位置偏差
        
        Args:
            yearly_results: 各年份的分析結果
            
        Returns:
            一致性分析結果
        """
        years = sorted(yearly_results.keys())
        
        # 統計各年識別的彎道數量
        corner_counts = {year: data['corners_detected'] for year, data in yearly_results.items()}
        
        print(f"\n📈 各年識別彎道數量:")
        for year, count in corner_counts.items():
            print(f"   {year}: {count} 個彎道")
        
        # 檢查彎道數量一致性
        unique_counts = set(corner_counts.values())
        count_consistency = len(unique_counts) == 1
        
        if count_consistency:
            print(f"✅ 彎道數量一致: 所有年份都識別到 {list(unique_counts)[0]} 個彎道")
        else:
            print(f"⚠️  彎道數量不一致: {unique_counts}")
            print(f"💡 使用彎心位置匹配算法進行跨年比較...")
        
        # 建立彎道匹配矩陣
        # 使用第一年作為參考基準
        reference_year = years[0]
        reference_corners = yearly_results[reference_year]['corners']
        
        print(f"\n🔍 以 {reference_year} 年為基準，匹配彎道位置:")
        
        # 提取所有年份的彎心位置
        all_corners_by_year = {}
        for year in years:
            corners = yearly_results[year]['corners']
            all_corners_by_year[year] = {
                int(k): v['apex_distance'] 
                for k, v in corners.items()
            }
        
        # 建立匹配關係（使用 50m 容差）
        matching_tolerance = 50.0  # 米
        matched_corners = []
        
        ref_apex_positions = list(all_corners_by_year[reference_year].values())
        
        for ref_corner_num, ref_apex in enumerate(ref_apex_positions, start=1):
            corner_match = {
                'reference_corner': ref_corner_num,
                'reference_apex': ref_apex,
                'matches': {reference_year: ref_apex}
            }
            
            # 在其他年份中尋找匹配的彎道
            for year in years[1:]:
                year_apexes = all_corners_by_year[year]
                
                # 找到最接近的彎道
                min_distance = float('inf')
                matched_corner_num = None
                matched_apex = None
                
                for corner_num, apex in year_apexes.items():
                    distance = abs(apex - ref_apex)
                    if distance < min_distance:
                        min_distance = distance
                        matched_corner_num = corner_num
                        matched_apex = apex
                
                # 如果距離在容差內，視為匹配
                if min_distance <= matching_tolerance:
                    corner_match['matches'][year] = matched_apex
            
            # 計算統計
            matched_years = list(corner_match['matches'].keys())
            if len(matched_years) >= 2:  # 至少兩年有匹配
                positions = list(corner_match['matches'].values())
                corner_match['mean_position'] = float(np.mean(positions))
                corner_match['std_deviation'] = float(np.std(positions))
                corner_match['max_deviation'] = float(max(positions) - min(positions))
                corner_match['matched_years_count'] = len(matched_years)
                corner_match['is_consistent'] = corner_match['max_deviation'] < matching_tolerance
                
                matched_corners.append(corner_match)
        
        # 輸出匹配結果
        print(f"\n📊 彎道匹配結果:")
        for corner in matched_corners:
            ref_num = corner['reference_corner']
            mean_pos = corner['mean_position']
            std_dev = corner['std_deviation']
            max_dev = corner['max_deviation']
            matched_count = corner['matched_years_count']
            
            status = "✅" if corner['is_consistent'] else "⚠️"
            print(f"{status} 彎道 {ref_num}: "
                  f"平均位置={mean_pos:.0f}m, "
                  f"標準差={std_dev:.1f}m, "
                  f"最大偏差={max_dev:.0f}m, "
                  f"匹配年份={matched_count}/{len(years)}")
            
            # 顯示各年位置
            for year, pos in sorted(corner['matches'].items()):
                print(f"      {year}: {pos:.0f}m")
        
        # 計算整體一致性分數
        consistent_corners = sum(1 for c in matched_corners if c['is_consistent'])
        total_matched = len(matched_corners)
        
        if total_matched > 0:
            consistency_score = (consistent_corners / total_matched * 100)
        else:
            consistency_score = 0.0
        
        # 計算匹配率
        max_corners = max(corner_counts.values())
        matching_rate = (total_matched / max_corners * 100) if max_corners > 0 else 0.0
        
        print(f"\n{'='*60}")
        print(f"📊 整體一致性評分: {consistency_score:.1f}%")
        print(f"   一致彎道: {consistent_corners}/{total_matched}")
        print(f"📊 彎道匹配率: {matching_rate:.1f}%")
        print(f"   成功匹配: {total_matched}/{max_corners} 個彎道")
        print(f"{'='*60}")
        
        return {
            'corner_counts': corner_counts,
            'count_consistency': count_consistency,
            'matched_corners': matched_corners,
            'consistency_score': consistency_score,
            'consistent_corners': consistent_corners,
            'total_matched_corners': total_matched,
            'matching_rate': matching_rate,
            'matching_tolerance': matching_tolerance
        }
    
    def generate_visualization(self, report: Dict):
        """
        生成視覺化圖表
        
        Args:
            report: 比較報告
        """
        yearly_results = report['yearly_results']
        years = sorted(yearly_results.keys())
        consistency_analysis = report['consistency_analysis']
        
        # 創建多子圖
        fig = plt.figure(figsize=(16, 12))
        
        # 圖表 1: 彎道數量比較
        ax1 = plt.subplot(2, 2, 1)
        corner_counts = [yearly_results[year]['corners_detected'] for year in years]
        ax1.bar(years, corner_counts, color='steelblue', alpha=0.7)
        ax1.set_xlabel('年份', fontsize=12)
        ax1.set_ylabel('識別彎道數量', fontsize=12)
        ax1.set_title('各年識別彎道數量比較', fontsize=14, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        
        # 圖表 2: 彎道位置偏差
        ax2 = plt.subplot(2, 2, 2)
        matched_corners = consistency_analysis['matched_corners']
        
        if matched_corners:
            corner_nums = [c['reference_corner'] for c in matched_corners]
            max_devs = [c['max_deviation'] for c in matched_corners]
            colors = ['green' if c['is_consistent'] else 'red' for c in matched_corners]
            
            ax2.bar(corner_nums, max_devs, color=colors, alpha=0.7)
            ax2.axhline(y=50, color='orange', linestyle='--', 
                       label=f'{consistency_analysis["matching_tolerance"]:.0f}m 容差線')
            ax2.set_xlabel('彎道編號（基準年）', fontsize=12)
            ax2.set_ylabel('最大位置偏差 (m)', fontsize=12)
            ax2.set_title('彎道位置年際偏差', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(axis='y', alpha=0.3)
        
        # 圖表 3: 所有匹配彎道的位置散點圖
        ax3 = plt.subplot(2, 2, 3)
        if matched_corners:
            for corner in matched_corners[:5]:  # 只顯示前5個彎道避免過擠
                corner_num = corner['reference_corner']
                positions = corner['matches']
                
                years_list = list(positions.keys())
                pos_list = list(positions.values())
                
                ax3.plot(years_list, pos_list, 'o-', 
                        label=f'彎道 {corner_num}', alpha=0.7, linewidth=2)
            
            ax3.set_xlabel('年份', fontsize=12)
            ax3.set_ylabel('彎心位置 (m)', fontsize=12)
            ax3.set_title('前 5 個彎道位置變化趨勢', fontsize=14, fontweight='bold')
            ax3.legend(loc='best', fontsize=9)
            ax3.grid(True, alpha=0.3)
        
        # 圖表 4: 一致性與匹配率雙圓餅圖
        ax4 = plt.subplot(2, 2, 4)
        
        consistency_score = consistency_analysis['consistency_score']
        matching_rate = consistency_analysis['matching_rate']
        
        # 創建嵌套圓餅圖
        size = 0.3
        
        # 外圈：匹配率
        outer_vals = [matching_rate, 100 - matching_rate]
        outer_colors = ['#66b3ff', '#ff9999']
        outer_wedges, outer_texts = ax4.pie(
            outer_vals, radius=1, colors=outer_colors,
            wedgeprops=dict(width=size, edgecolor='white')
        )
        
        # 內圈：一致性分數
        inner_vals = [consistency_score, 100 - consistency_score]
        inner_colors = ['green', 'red']
        inner_wedges, inner_texts = ax4.pie(
            inner_vals, radius=1-size, colors=inner_colors,
            wedgeprops=dict(width=size, edgecolor='white')
        )
        
        # 添加標籤
        ax4.text(0, 0, f'匹配率\n{matching_rate:.1f}%\n\n一致性\n{consistency_score:.1f}%',
                ha='center', va='center', fontsize=12, fontweight='bold')
        
        ax4.set_title('彎道識別質量評估', fontsize=14, fontweight='bold')
        
        # 添加圖例
        ax4.legend(['外圈：匹配率（藍=匹配，紅=未匹配）\n內圈：一致性（綠=一致，紅=不一致）'],
                  loc='upper left', bbox_to_anchor=(-0.1, 1.1), fontsize=9)
        
        plt.tight_layout()
        
        # 儲存圖表
        output_file = self.output_dir / f"corner_consistency_{report['race']}_{'-'.join(map(str, years))}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\n✅ 視覺化圖表已儲存: {output_file}")
        
        plt.close()
        return str(output_file)
    
    def save_report(self, report: Dict):
        """
        儲存分析報告為 JSON
        
        Args:
            report: 比較報告
        """
        years_str = '-'.join(map(str, report['years_analyzed']))
        output_file = self.output_dir / f"corner_consistency_{report['race']}_{years_str}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 報告已儲存: {output_file}")
        return str(output_file)


def main():
    """主函數"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║     F1 彎道識別一致性驗證工具                                  ║
    ║     Corner Detection Consistency Verification                 ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # 創建驗證器
    verifier = CornerConsistencyVerifier()
    
    # 測試年份：2022-2025
    years = [2022, 2023, 2024, 2025]
    race_name = "United States"
    
    # 執行多年度比較
    report = verifier.compare_multi_year(years, race_name)
    
    if report:
        # 儲存報告
        verifier.save_report(report)
        
        # 生成視覺化
        verifier.generate_visualization(report)
        
        print(f"\n{'='*60}")
        print(f"✅ 驗證完成！")
        print(f"{'='*60}")
    else:
        print(f"\n❌ 驗證失敗")


if __name__ == "__main__":
    main()
