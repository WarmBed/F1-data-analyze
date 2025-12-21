"""
Chase Strategy 預測準確度驗證腳本

目的：
1. 回放歷史比賽數據（Lap 15-25），模擬 Chase Strategy 的預測
2. 比較預測的追趕圈數 vs 實際發生的追趕圈數
3. 評估 Trend/Theory 權重分配（90%/10%）是否合理

測試場景：
- 2025 日本站：TSU (P4) vs NOR (P6)
- 在 Lap 19 時預測 NOR 會在 Lap 63 追上 TSU
- 驗證實際追趕是否發生

輸出：
- 預測追趕圈數 vs 實際追趕圈數
- 預測誤差（圈數差異）
- Trend/Theory 各自的貢獻度
- 建議的權重調整
"""

import sys
import pickle
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.gui.live_timing.live_timing_modules.chase_strategy import StrategyCalculator


class ChaseValidation:
    """Chase Strategy 預測驗證器"""
    
    def __init__(self, year: int, race: str, session: str):
        self.year = year
        self.race = race
        self.session = session
        self.calculator = StrategyCalculator()
        
        # 載入比賽數據
        self.race_data = self._load_race_data()
        
    def _load_race_data(self) -> Optional[Dict]:
        """載入比賽的 Live Timing 數據"""
        # 從 data/live_timing_cache/ 目錄載入 pkl 檔案
        pkl_patterns = [
            f"data/live_timing_cache/{self.year}/{self.race}_Race.pkl",
            f"data/live_timing_cache/{self.year}/{self.race.replace(' ', '_')}_Race.pkl",
        ]
        
        for pattern in pkl_patterns:
            pkl_file = Path(pattern)
            if pkl_file.exists():
                with open(pkl_file, 'rb') as f:
                    data = pickle.load(f)
                    print(f"✅ 載入數據: {pkl_file}")
                    print(f"   Snapshots: {len(data.get('snapshots', []))} 筆")
                    return data
        
        print(f"❌ 找不到比賽數據: {self.year} {self.race} {self.session}")
        print(f"   嘗試路徑: {pkl_patterns}")
        return None
    
    def simulate_chase_at_lap(self, test_lap: int, p1_driver: str, p2_driver: str) -> Dict:
        """
        在指定圈數模擬 Chase Strategy 預測
        
        Args:
            test_lap: 測試圈數（例如 Lap 19）
            p1_driver: 前方車手代碼（例如 "TSU"）
            p2_driver: 後方車手代碼（例如 "NOR"）
        
        Returns:
            預測結果字典
        """
        if not self.race_data:
            return {"error": "No race data"}
        
        # 提取該圈的狀態
        lap_snapshot = self._get_lap_snapshot(test_lap, p1_driver, p2_driver)
        if not lap_snapshot:
            return {"error": f"No data for Lap {test_lap}"}
        
        # 計算 Gap Trend（單圈比較）
        gap_trend = self._calculate_gap_trend(test_lap, p1_driver, p2_driver)
        
        # 計算理論輪胎優勢
        theory_advantage = self._calculate_theoretical_advantage(
            lap_snapshot['p1_compound'],
            lap_snapshot['p1_tyre_age'],
            lap_snapshot['p2_compound'],
            lap_snapshot['p2_tyre_age']
        )
        
        # ========== 完全複製 Chase Strategy 邏輯 ==========
        # 轉換 gap_trend → trend_advantage
        # gap_trend 正值 = Gap 擴大（P1 拉開）→ trend_advantage 負值（P2 無優勢）
        # gap_trend 負值 = Gap 縮小（P2 追近）→ trend_advantage 正值（P2 有優勢）
        trend_advantage = -gap_trend
        
        # 動態權重分配（與 Chase Strategy 完全一致）
        abs_trend = abs(gap_trend)
        if abs_trend >= 0.5:
            weight_trend = 0.90
            trend_level = ">>>"
        elif abs_trend >= 0.3:
            weight_trend = 0.70
            trend_level = ">>"
        elif abs_trend >= 0.1:
            weight_trend = 0.50
            trend_level = ">"
        else:
            weight_trend = 0.20
            trend_level = "-"
        
        weight_theory = 1.0 - weight_trend
        
        # 加權優勢（與 Chase Strategy 完全一致）
        weighted_advantage = weight_trend * trend_advantage + weight_theory * theory_advantage
        
        # 計算預測追趕圈數
        current_gap = lap_snapshot['gap']
        remaining_laps = lap_snapshot['total_laps'] - test_lap
        
        if weighted_advantage <= 0:
            predicted_catchup_lap = None
            feasible = False
        else:
            laps_to_catch = int(current_gap / weighted_advantage) + 1
            predicted_catchup_lap = test_lap + laps_to_catch
            feasible = laps_to_catch <= remaining_laps
        
        return {
            'test_lap': test_lap,
            'p1_driver': p1_driver,
            'p2_driver': p2_driver,
            'current_gap': current_gap,
            'gap_trend': gap_trend,
            'trend_advantage': trend_advantage,
            'theory_advantage': theory_advantage,
            'weight_trend': weight_trend,
            'weight_theory': weight_theory,
            'trend_level': trend_level,
            'weighted_advantage': weighted_advantage,
            'predicted_catchup_lap': predicted_catchup_lap,
            'feasible': feasible,
            'p1_compound': lap_snapshot['p1_compound'],
            'p1_tyre_age': lap_snapshot['p1_tyre_age'],
            'p2_compound': lap_snapshot['p2_compound'],
            'p2_tyre_age': lap_snapshot['p2_tyre_age'],
        }
    
    def validate_prediction(self, test_lap: int, p1_driver: str, p2_driver: str) -> Dict:
        """
        驗證預測準確度
        
        比較預測的追趕圈數 vs 實際追趕圈數
        """
        prediction = self.simulate_chase_at_lap(test_lap, p1_driver, p2_driver)
        if 'error' in prediction:
            return prediction
        
        # 尋找實際追趕圈數（Gap 變為負數或 0 的圈數）
        actual_catchup_lap = self._find_actual_catchup(
            test_lap, 
            p1_driver, 
            p2_driver,
            prediction['predicted_catchup_lap']
        )
        
        # 計算誤差
        if prediction['predicted_catchup_lap'] and actual_catchup_lap:
            error_laps = prediction['predicted_catchup_lap'] - actual_catchup_lap
            error_percent = (error_laps / (actual_catchup_lap - test_lap)) * 100
        else:
            error_laps = None
            error_percent = None
        
        return {
            **prediction,
            'actual_catchup_lap': actual_catchup_lap,
            'error_laps': error_laps,
            'error_percent': error_percent,
        }
    
    def _get_lap_snapshot(self, lap: int, p1_driver: str, p2_driver: str) -> Optional[Dict]:
        """提取指定圈的車手狀態"""
        if not self.race_data or 'snapshots' not in self.race_data:
            return None
        
        # 找到該圈的 snapshot（從 snapshots 列表中搜索 current_lap == lap 的）
        target_snapshot = None
        for snap in self.race_data['snapshots']:
            if snap.get('current_lap') == lap:
                target_snapshot = snap
                break
        
        if not target_snapshot or 'drivers' not in target_snapshot:
            print(f"⚠️  找不到 Lap {lap} 的數據")
            return None
        
        drivers = target_snapshot['drivers']
        
        # 找到兩位車手的數據
        p1_data = None
        p2_data = None
        
        for driver in drivers.values():
            if driver.get('driver_tla') == p1_driver:
                p1_data = driver
            if driver.get('driver_tla') == p2_driver:
                p2_data = driver
        
        if not p1_data or not p2_data:
            print(f"⚠️  Lap {lap} 找不到車手數據: {p1_driver}, {p2_driver}")
            return None
        
        # ✅ 修正：使用最簡單且正確的方法
        p1_pos = p1_data.get('position')
        p2_pos = p2_data.get('position')
        p1_gap_to_leader = float(p1_data.get('gap_to_leader', 0) or 0)
        p2_gap_to_leader = float(p2_data.get('gap_to_leader', 0) or 0)
        
        # Gap 定義：P1 相對於 P2 的差距
        # gap = p1_gap_to_leader - p2_gap_to_leader
        # - 正值: P1 落後 P2（P2 在前，需要追趕）
        # - 負值: P1 領先 P2（P1 在前，已經超越）
        gap = p1_gap_to_leader - p2_gap_to_leader
        
        # 從 driver_stints 獲取輪胎數據
        p1_compound, p1_tyre_age = self._get_tyre_info(lap, p1_driver)
        p2_compound, p2_tyre_age = self._get_tyre_info(lap, p2_driver)
        
        total_laps = self.race_data.get('race_info', {}).get('total_laps', 58)
        
        return {
            'gap': gap,
            'p1_compound': p1_compound,
            'p1_tyre_age': p1_tyre_age,
            'p2_compound': p2_compound,
            'p2_tyre_age': p2_tyre_age,
            'total_laps': total_laps,
            'p1_position': p1_data.get('position'),
            'p2_position': p2_data.get('position'),
        }
    
    def _get_tyre_info(self, lap: int, driver_tla: str) -> Tuple[str, int]:
        """
        獲取指定圈的輪胎配方和齡
        
        ⚠️ 修正：driver_stints 使用車號作為鍵，需要先從 driver_info 轉換 TLA → 車號
        """
        if 'driver_stints' not in self.race_data or 'driver_info' not in self.race_data:
            return 'MEDIUM', 10  # 預設值
        
        # 步驟 1: 從 driver_info 找到 TLA 對應的車號
        driver_number = None
        driver_info = self.race_data.get('driver_info', {})
        
        for number, info in driver_info.items():
            if info.get('driver_tla') == driver_tla or info.get('tla') == driver_tla:
                driver_number = number
                break
        
        if not driver_number:
            return 'MEDIUM', 10
        
        # 步驟 2: 用車號查詢 driver_stints
        stints = self.race_data.get('driver_stints', {}).get(driver_number, [])
        
        if not stints:
            return 'MEDIUM', 10
        
        # 步驟 3: 計算 start_lap 和 end_lap（從 total_laps 推算）
        current_lap_in_race = 1
        for stint in stints:
            total_laps = stint.get('total_laps', 0)
            stint_start = current_lap_in_race
            stint_end = current_lap_in_race + total_laps - 1
            
            if stint_start <= lap <= stint_end:
                compound = stint.get('compound', 'MEDIUM')
                tyre_age = lap - stint_start + 1
                return compound, tyre_age
            
            current_lap_in_race += total_laps
        
        return 'MEDIUM', 10
    
    def _calculate_gap_trend(self, current_lap: int, p1_driver: str, p2_driver: str, window: int = 5) -> float:
        """
        計算 Gap 趨勢（完全複製 Chase Strategy 邏輯）
        
        ✅ 真實 Chase Strategy 邏輯：
        - gap_seconds = P2 對 P1 的距離（永遠取絕對值）
        - gap_trend = 當前圈 gap_seconds - 上一圈 gap_seconds
        - 負值: gap 縮小 = P2 追近
        - 正值: gap 擴大 = P2 拉開
        
        ⚠️ 重要：
        - 不使用「相對 gap」（p1_gap_to_leader - p2_gap_to_leader）
        - 使用「絕對距離」（兩車之間的實際間距）
        """
        if not self.race_data or 'snapshots' not in self.race_data:
            return 0.0
        
        # 獲取當前圈和上一圈的 Gap
        current_lap_data = self._get_lap_snapshot(current_lap, p1_driver, p2_driver)
        prev_lap_data = self._get_lap_snapshot(current_lap - 1, p1_driver, p2_driver)
        
        if not current_lap_data or not prev_lap_data:
            print(f"⚠️  Gap 數據不足，無法計算趨勢")
            return 0.0
        
        # ✅ 修正：使用絕對距離（P2 對 P1 的間距）
        current_gap_abs = abs(current_lap_data['gap'])
        prev_gap_abs = abs(prev_lap_data['gap'])
        
        # 單圈變化量
        gap_trend = current_gap_abs - prev_gap_abs
        
        print(f"   Gap Trend 計算: Lap {current_lap-1} ({prev_gap_abs:.3f}s) → Lap {current_lap} ({current_gap_abs:.3f}s) = {gap_trend:+.4f} s/lap")
        
        return gap_trend  # 負值 = 追近，正值 = 拉開
    
    def _calculate_theoretical_advantage(self, p1_compound: str, p1_age: int, 
                                         p2_compound: str, p2_age: int) -> float:
        """
        計算理論輪胎優勢（完全複製 Chase Strategy 邏輯）
        
        ✅ 真實 Chase Strategy 邏輯：
        - 使用 StrategyCalculator.get_tyre_degradation() 獲取輪胎衰退率
        - theory_advantage = P1 的衰退 - P2 的衰退
        - 正值: P2 輪胎更快（P2 有優勢）
        - 負值: P1 輪胎更快（P1 有優勢）
        """
        try:
            # 使用真實的 StrategyCalculator（會查詢輪胎數據庫）
            p1_deg = self.calculator.get_tyre_degradation(p1_compound, p1_age)
            p2_deg = self.calculator.get_tyre_degradation(p2_compound, p2_age)
            
            # theory_advantage = P1 的單圈時間損失 - P2 的單圈時間損失
            # 正值 = P2 輪胎更快（P2 有優勢）
            theory_advantage = p1_deg - p2_deg
            
            return theory_advantage
        except Exception as e:
            print(f"⚠️  無法計算理論優勢: {e}")
            # 降級處理：使用簡化公式
            age_diff = p1_age - p2_age
            compound_factor = 0.0
            
            # 配方差異（SOFT > MEDIUM > HARD）
            compounds = {'SOFT': 3, 'MEDIUM': 2, 'HARD': 1}
            p1_level = compounds.get(p1_compound, 2)
            p2_level = compounds.get(p2_compound, 2)
            compound_factor = (p1_level - p2_level) * 0.1
            
            return age_diff * 0.05 + compound_factor
    
    def _find_actual_catchup(self, start_lap: int, p1_driver: str, p2_driver: str, 
                            max_search_lap: Optional[int]) -> Optional[int]:
        """尋找實際追趕發生的圈數"""
        if not self.race_data or 'snapshots' not in self.race_data:
            return None
        
        search_limit = max_search_lap or (start_lap + 50)
        
        for lap in range(start_lap + 1, search_limit + 1):
            lap_data = self._get_lap_snapshot(lap, p1_driver, p2_driver)
            
            if not lap_data:
                continue
            
            # 檢查位置是否反轉（P2 超越 P1）
            if lap_data['p2_position'] and lap_data['p1_position']:
                if lap_data['p2_position'] <= lap_data['p1_position']:
                    print(f"✅ 實際追趕發生在 Lap {lap}")
                    print(f"   {p2_driver} 位置: {lap_data['p2_position']}, {p1_driver} 位置: {lap_data['p1_position']}")
                    return lap
            
            # 或檢查 Gap 是否變為 0 或負數
            if lap_data['gap'] is not None and lap_data['gap'] <= 0:
                print(f"✅ Gap 變為 0 或負數在 Lap {lap} (Gap = {lap_data['gap']:.3f}s)")
                return lap
        
        print(f"⚠️  在 Lap {start_lap}-{search_limit} 之間未發生追趕")
        return None
    
    def print_validation_report(self, result: Dict):
        """打印驗證報告"""
        print("\n" + "=" * 80)
        print(f"📊 Chase Strategy 預測準確度驗證報告")
        print("=" * 80)
        
        print(f"\n🏁 比賽: {self.year} {self.race} {self.session}")
        print(f"👥 車手: {result['p1_driver']} (P1) vs {result['p2_driver']} (P2)")
        print(f"📍 測試圈數: Lap {result['test_lap']}")
        
        print(f"\n📏 當前狀態:")
        print(f"  Gap: {result['current_gap']:.3f}s")
        print(f"  {result['p1_driver']}: {result['p1_compound']}(age {result['p1_tyre_age']})")
        print(f"  {result['p2_driver']}: {result['p2_compound']}(age {result['p2_tyre_age']})")
        
        print(f"\n📈 趨勢分析:")
        print(f"  Gap Trend (單圈變化): {result['gap_trend']:+.4f} s/lap {result.get('trend_level', '')}")
        print(f"  Trend Advantage (轉換): {result.get('trend_advantage', -result['gap_trend']):+.4f} s/lap")
        print(f"  Theory Advantage: {result['theory_advantage']:+.4f} s/lap")
        
        print(f"\n⚖️  權重分配:")
        print(f"  Trend Weight: {result['weight_trend']:.0%}")
        print(f"  Theory Weight: {result['weight_theory']:.0%}")
        print(f"  Weighted Advantage: {result['weighted_advantage']:+.4f} s/lap")
        
        print(f"\n🎯 預測結果:")
        if result['predicted_catchup_lap']:
            print(f"  預測追趕圈數: Lap {result['predicted_catchup_lap']}")
        else:
            print(f"  預測: 無法追上")
        
        if result.get('actual_catchup_lap'):
            print(f"  實際追趕圈數: Lap {result['actual_catchup_lap']}")
            if result['error_laps'] is not None:
                print(f"  誤差: {result['error_laps']:+.0f} 圈 ({result['error_percent']:+.1f}%)")
                
                # 準確度評估
                if abs(result['error_laps']) <= 2:
                    accuracy = "✅ 非常準確"
                elif abs(result['error_laps']) <= 5:
                    accuracy = "⚠️  尚可接受"
                else:
                    accuracy = "❌ 偏差較大"
                print(f"  準確度: {accuracy}")
        else:
            print(f"  實際追趕圈數: 未發生或無數據")
        
        print("\n" + "=" * 80)


def main():
    """主程式"""
    print("🏎️  Chase Strategy 預測驗證腳本")
    print("=" * 80)
    
    # 測試案例 1: 2025 阿布達比站
    validator = ChaseValidation(year=2025, race="Abu_Dhabi", session="R")
    
    if not validator.race_data:
        print("❌ 無法載入數據，請確認 pkl 檔案存在")
        return
    
    # 請用戶輸入車手代碼
    print("\n請輸入要測試的車手代碼（例如: TSU NOR）")
    print("可用的車手代碼請查看 pkl 檔案中的 driver_tla")
    
    user_input = input("P1車手 P2車手 (例如: TSU NOR): ").strip().split()
    
    if len(user_input) == 2:
        p1_driver, p2_driver = user_input
    else:
        # 預設值
        p1_driver, p2_driver = "LEC", "SAI"
        print(f"使用預設值: {p1_driver} (P1) vs {p2_driver} (P2)")
    
    # 顯示完整的 Lap 15-25 數據
    print("\n" + "=" * 80)
    print(f"🔍 Lap 15-25 完整數據與預測（{p1_driver} vs {p2_driver}）")
    print("=" * 80)
    
    for lap in range(15, 26):
        # 獲取當前圈的數據
        lap_data = validator._get_lap_snapshot(lap, p1_driver, p2_driver)
        
        if not lap_data:
            print(f"\nLap {lap}: ❌ 數據不足")
            continue
        
        # 計算預測
        result = validator.simulate_chase_at_lap(lap, p1_driver, p2_driver)
        
        if 'error' in result:
            print(f"\nLap {lap}: ❌ {result['error']}")
            continue
        
        # 顯示數據
        gap = lap_data['gap']
        p1_compound = lap_data['p1_compound']
        p1_age = lap_data['p1_tyre_age']
        p2_compound = lap_data['p2_compound']
        p2_age = lap_data['p2_tyre_age']
        p1_pos = lap_data['p1_position']
        p2_pos = lap_data['p2_position']
        
        gap_trend = result['gap_trend']
        trend_adv = result['trend_advantage']
        theory_adv = result['theory_advantage']
        weighted_adv = result['weighted_advantage']
        trend_level = result.get('trend_level', '-')
        weight_trend = result['weight_trend']
        weight_theory = result['weight_theory']
        predicted_lap = result['predicted_catchup_lap']
        
        # 格式化輸出
        gap_str = f"{gap:+.3f}s"
        gap_trend_str = f"{gap_trend:+.4f} s/lap"
        trend_adv_str = f"{trend_adv:+.4f} s/lap"
        theory_str = f"{theory_adv:+.4f} s/lap"
        weighted_str = f"{weighted_adv:+.4f} s/lap"
        
        if predicted_lap:
            prediction_str = f"Lap {predicted_lap}"
        elif weighted_adv <= 0:
            prediction_str = "無法追上"
        else:
            prediction_str = "計算中..."
        
        print(f"\nLap {lap}:")
        print(f"   {p1_driver}: P{p1_pos}, {p1_compound} age {p1_age}")
        print(f"   {p2_driver}: P{p2_pos}, {p2_compound} age {p2_age}")
        print(f"   Gap ({p1_driver} vs {p2_driver}): {gap_str} ({p1_driver} {'落後' if gap > 0 else '領先' if gap < 0 else '並列'})")
        print(f"   Gap Trend: {gap_trend_str} {trend_level}")
        print(f"   Trend Advantage: {trend_adv_str}")
        print(f"   Theory Advantage: {theory_str}")
        print(f"   權重: Trend {weight_trend:.0%}, Theory {weight_theory:.0%}")
        print(f"   Weighted Advantage: {weighted_str}")
        print(f"   預測追趕: {prediction_str}")
    
    # 接著顯示詳細的測試報告（原有的測試圈數）
    print("\n" + "=" * 80)
    print("📊 詳細測試報告（選定圈數）")
    print("=" * 80)
    
    test_laps = [15, 17, 19, 21, 23, 25]
    results = []
    
    for test_lap in test_laps:
        print(f"\n{'=' * 80}")
        print(f"測試 Lap {test_lap}")
        print(f"{'=' * 80}")
        
        result = validator.validate_prediction(
            test_lap=test_lap,
            p1_driver=p1_driver,
            p2_driver=p2_driver
        )
        
        if 'error' not in result:
            validator.print_validation_report(result)
            results.append(result)
        else:
            print(f"❌ {result['error']}")
    
    
    # 統計分析
    if results:
        print("\n\n📈 統計分析")
        print("=" * 80)
        
        successful_predictions = [r for r in results if r.get('predicted_catchup_lap') and r.get('actual_catchup_lap')]
        
        if successful_predictions:
            errors = [r['error_laps'] for r in successful_predictions]
            avg_error = sum(errors) / len(errors)
            print(f"平均誤差: {avg_error:+.1f} 圈")
            print(f"最小誤差: {min(errors):+.0f} 圈")
            print(f"最大誤差: {max(errors):+.0f} 圈")
            
            # 權重建議
            if avg_error > 5:
                print("\n💡 建議: 預測偏晚，考慮提高 Trend 權重（當前 90%）")
            elif avg_error < -5:
                print("\n💡 建議: 預測過早，考慮降低 Trend 權重（當前 90%）")
            else:
                print("\n✅ 權重配置合理（90% Trend / 10% Theory）")
    
    # 權重敏感度分析（只針對一個圈數）
    if results:
        print("\n\n📊 權重敏感度分析 (Lap 19)")
        print("=" * 80)
        
        # 重新計算 Lap 19 的預測，使用不同權重
        lap_19_result = validator.simulate_chase_at_lap(19, p1_driver, p2_driver)
        
        if 'error' not in lap_19_result:
            weight_configs = [
                (0.95, 0.05, "極度依賴 Trend"),
                (0.90, 0.10, "當前配置"),
                (0.80, 0.20, "平衡配置"),
                (0.70, 0.30, "理論權重較高"),
                (0.50, 0.50, "完全平衡"),
            ]
            
            print(f"\n{'Trend%':<10} {'Theory%':<10} {'Weighted Adv':<18} {'Catchup Lap':<15} {'描述'}")
            print("-" * 80)
            
            for trend_w, theory_w, desc in weight_configs:
                weighted_adv = trend_w * (-lap_19_result['gap_trend']) + theory_w * lap_19_result['theory_advantage']
                
                if weighted_adv > 0:
                    laps_to_catch = int(lap_19_result['current_gap'] / weighted_adv) + 1
                    catchup_lap = lap_19_result['test_lap'] + laps_to_catch
                    catchup_str = f"Lap {catchup_lap}"
                else:
                    catchup_str = "無法追上"
                
                trend_pct = f"{trend_w:.0%}"
                theory_pct = f"{theory_w:.0%}"
                adv_str = f"{weighted_adv:+.4f} s/lap"
                print(f"{trend_pct:<10} {theory_pct:<10} {adv_str:<18} {catchup_str:<15} {desc}")


if __name__ == "__main__":
    main()
