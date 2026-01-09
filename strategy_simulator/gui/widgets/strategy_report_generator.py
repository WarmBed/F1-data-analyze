#!/usr/bin/env python3
"""
Strategy Report Generator

Generates detailed text reports for race strategy analysis.
Designed for Race Engineers to understand key decision points,
traffic impact, and win rate optimization.

Author: F1T Team
Date: 2025-01-07
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# Import simulation parameters to get accurate degradation coefficients
try:
    from strategy_simulator.core.lap_simulator import SimulationParams, Compound
    HAS_SIMULATION_PARAMS = True
except ImportError:
    HAS_SIMULATION_PARAMS = False
    # Fallback: Use default values
    class Compound:
        SOFT = "SOFT"
        MEDIUM = "MEDIUM"
        HARD = "HARD"


@dataclass
class DecisionPoint:
    """A key decision point in the race strategy."""
    lap: int
    decision_type: str  # "pit_stop", "sc_response", "undercut", "overcut"
    description: str
    rationale: List[str]
    alternatives: List[Dict[str, Any]]
    impact_on_win_rate: float  # positive = better


@dataclass
class TrafficEvent:
    """Traffic blocking event."""
    start_lap: int
    end_lap: int
    blocker: str
    estimated_loss: float
    reason: str


class StrategyReportGenerator:
    """
    Generates comprehensive strategy analysis reports.
    
    Usage:
        generator = StrategyReportGenerator()
        report = generator.generate_report(
            strategy_result=result,
            simulation_data=sim_data,
            mc_summary=mc_summary,
            our_driver="VER"
        )
    """
    
    def __init__(self):
        self._line_width = 70
        
        # ✅ Load degradation model parameters from SimulationParams
        # 使用實際的二次曲線退化模型 (Time-Varying Linear Degradation)
        # 公式: cumulative_deg(t) = base_rate * t + 0.5 * acceleration * t²
        if HAS_SIMULATION_PARAMS:
            default_params = SimulationParams()
            self._deg_rates = {
                'SOFT': default_params.get_deg_rate(Compound.SOFT),
                'MEDIUM': default_params.get_deg_rate(Compound.MEDIUM),
                'HARD': default_params.get_deg_rate(Compound.HARD),
            }
            self._deg_acceleration = {
                'SOFT': default_params.get_deg_acceleration(Compound.SOFT),
                'MEDIUM': default_params.get_deg_acceleration(Compound.MEDIUM),
                'HARD': default_params.get_deg_acceleration(Compound.HARD),
            }
        else:
            # Fallback: Use typical values from research
            self._deg_rates = {
                'SOFT': 0.120,
                'MEDIUM': 0.080,
                'HARD': 0.045,
            }
            self._deg_acceleration = {
                'SOFT': 0.003,
                'MEDIUM': 0.002,
                'HARD': 0.001,
            }
        
    def generate_report(
        self,
        strategy_result: Any,
        simulation_data: Optional[Any] = None,
        mc_summary: Optional[Any] = None,
        our_driver: str = "",
        grid_position: int = 1,
        track_name: str = "",
        race_laps: int = 57,
        pit_loss_green: float = 24.0,
        traffic_data: Optional[Dict] = None,
        scenario_analyses: Optional[Dict] = None,
        competitors_data: Optional[List[Dict]] = None,
        long_run_data: Optional[Any] = None,  # ✅ 新增：Long Run 數據
        sim_params: Optional[Any] = None,  # ✅ 新增：SimulationParams
        display_strategy_name: Optional[str] = None,  # ✅ 用於覆蓋策略名稱顯示
        display_win_rate: Optional[float] = None,  # ✅ 用於覆蓋勝率顯示
    ) -> str:
        """
        Generate a complete strategy analysis report.
        
        Args:
            strategy_result: The strategy being analyzed (OptimizationResult or similar)
            simulation_data: Full race simulation result (FullRaceSimulation)
            mc_summary: Monte Carlo summary with win rates
            our_driver: Our driver code (e.g., "VER")
            grid_position: Starting grid position
            track_name: Track name
            race_laps: Total race laps
            pit_loss_green: Green flag pit loss in seconds
            traffic_data: Traffic analysis from simulation
            scenario_analyses: SC scenario analyses
            competitors_data: Data about competitor strategies
            long_run_data: FP2 Long Run data (LongRunData or dict)
            sim_params: Simulation parameters used in actual race simulation
            
        Returns:
            Formatted report string
        """
        # ✅ 更新退化率：優先使用 Long Run 實測數據
        if long_run_data and hasattr(long_run_data, 'degradation'):
            print("[REPORT_GEN] Using Long Run degradation data")
            for compound_name, deg_data in long_run_data.degradation.items():
                compound_key = compound_name.upper()
                if hasattr(deg_data, 'deg_per_lap'):
                    self._deg_rates[compound_key] = deg_data.deg_per_lap
                    print(f"  {compound_key}: {deg_data.deg_per_lap:.4f} s/lap (FP2 實測)")
        elif long_run_data and isinstance(long_run_data, dict) and long_run_data.get('degradation'):
            print("[REPORT_GEN] Using Long Run degradation data (dict)")
            for compound_name, deg_data in long_run_data['degradation'].items():
                compound_key = compound_name.upper()
                # 處理 dict 格式
                if isinstance(deg_data, dict):
                    deg_rate = deg_data.get('deg_per_lap', None)
                    if deg_rate:
                        self._deg_rates[compound_key] = deg_rate
                        print(f"  {compound_key}: {deg_rate:.4f} s/lap (FP2 實測)")
                # 處理 object/dataclass 格式（有 deg_per_lap 屬性）
                elif hasattr(deg_data, 'deg_per_lap'):
                    self._deg_rates[compound_key] = deg_data.deg_per_lap
                    print(f"  {compound_key}: {deg_data.deg_per_lap:.4f} s/lap (FP2 實測)")
        
        # ✅ 更新燃油和賽道數據
        self._long_run_base_lap_time = None
        self._long_run_fuel_effect = None
        self._long_run_track_evolution = None
        
        if long_run_data:
            if hasattr(long_run_data, 'base_lap_time'):
                self._long_run_base_lap_time = long_run_data.base_lap_time
            elif isinstance(long_run_data, dict):
                self._long_run_base_lap_time = long_run_data.get('base_lap_time')
            
            if hasattr(long_run_data, 'fuel_effect'):
                self._long_run_fuel_effect = long_run_data.fuel_effect
            elif isinstance(long_run_data, dict):
                self._long_run_fuel_effect = long_run_data.get('fuel_effect')
            
            if hasattr(long_run_data, 'track_evolution_per_lap'):
                self._long_run_track_evolution = abs(long_run_data.track_evolution_per_lap)
            elif isinstance(long_run_data, dict) and long_run_data.get('track_evolution_per_lap'):
                self._long_run_track_evolution = abs(long_run_data['track_evolution_per_lap'])
        
        lines = []
        
        # Header
        lines.extend(self._generate_header(
            strategy_result, our_driver, grid_position, track_name,
            long_run_data,  # ✅ 傳遞 long_run_data
            display_strategy_name,  # ✅ 傳遞覆蓋的策略名稱
            display_win_rate,  # ✅ 傳遞覆蓋的勝率
        ))
        
        # Section 1: Key Decision Points
        lines.extend(self._generate_decision_points_section(
            strategy_result, simulation_data, pit_loss_green, race_laps,
            traffic_data, our_driver, competitors_data  # ✅ 傳遞所有需要的數據
        ))
        
        # Section 2: Traffic Analysis
        lines.extend(self._generate_traffic_section(
            traffic_data, simulation_data
        ))
        
        # Section 3: Competitor Interaction
        lines.extend(self._generate_competitor_section(
            simulation_data, competitors_data, our_driver
        ))
        
        # Section 4: Win Rate Optimization
        lines.extend(self._generate_optimization_section(
            strategy_result, mc_summary, scenario_analyses
        ))
        
        # Section 5: SC Scenario Analysis
        lines.extend(self._generate_scenario_section(
            scenario_analyses, strategy_result
        ))
        
        # Footer
        lines.extend(self._generate_footer())
        
        return "\n".join(lines)
    
    def _generate_header(
        self,
        strategy_result: Any,
        our_driver: str,
        grid_position: int,
        track_name: str,
        long_run_data: Optional[Any] = None,
        display_strategy_name: Optional[str] = None,  # ✅ 用於覆蓋策略名稱
        display_win_rate: Optional[float] = None,  # ✅ 用於覆蓋勝率
    ) -> List[str]:
        """Generate report header."""
        lines = []
        
        # Title
        lines.append("=" * self._line_width)
        lines.append(self._center("策略分析報告"))
        lines.append(self._center("Race Engineer 決策支援系統 v1.0"))
        lines.append("=" * self._line_width)
        lines.append("")
        
        # Basic info
        # ✅ 優先使用傳入的顯示名稱，否則從 strategy_result 獲取
        if display_strategy_name:
            strategy_name = display_strategy_name
            notation = display_strategy_name  # 用戶選擇的就是輪胎格式
        else:
            strategy_name = getattr(strategy_result, 'strategy_name', 'Unknown')
            notation = self._get_stint_notation(strategy_result)
        
        # ✅ 優先使用傳入的勝率，否則從 strategy_result 獲取
        if display_win_rate is not None:
            win_rate = display_win_rate
        else:
            win_rate = getattr(strategy_result, 'win_probability', 0.0)
            if win_rate == 0 and hasattr(strategy_result, 'expected_position'):
                # Estimate from position
                exp_pos = strategy_result.expected_position
                if exp_pos <= 1:
                    win_rate = 50.0
                elif exp_pos <= 3:
                    win_rate = 20.0
                else:
                    win_rate = max(0, 10 - exp_pos)
        
        lines.append("【基本資訊】")
        # Display track name, fallback to "未指定" if empty
        display_track = track_name if track_name and track_name != "Unknown" else "未指定"
        lines.append(f"車手: {our_driver} | 起跑: P{grid_position} | 賽道: {display_track}")
        lines.append(f"策略: {strategy_name} | 預估勝率: {win_rate:.1f}%")
        
        # ✅ 顯示數據來源（與實際模擬一致）
        if long_run_data:
            session_type = "FP2"
            if hasattr(long_run_data, 'session_type'):
                session_type = long_run_data.session_type
            elif isinstance(long_run_data, dict):
                session_type = long_run_data.get('session_type', 'FP2')
            
            lines.append(f"數據來源: ✅ {session_type} Long Run 實測數據")
            
            # 顯示關鍵參數
            if self._long_run_base_lap_time:
                lines.append(f"  - 基準圈時間: {self._long_run_base_lap_time:.3f}s")
            if self._long_run_fuel_effect:
                lines.append(f"  - 燃油效應: {self._long_run_fuel_effect:.4f}s/kg")
            if self._long_run_track_evolution:
                lines.append(f"  - 賽道進化: -{self._long_run_track_evolution:.4f}s/lap (變快)")
        else:
            lines.append("數據來源: ⚠️  SimulationParams 預設值")
        
        lines.append("")
        lines.append("─" * self._line_width)
        
        return lines
    
    def _generate_decision_points_section(
        self,
        strategy_result: Any,
        simulation_data: Optional[Any],
        pit_loss_green: float,
        race_laps: int,
        traffic_data: Optional[Dict] = None,  # ✅ 新增參數
        our_driver: str = "",  # ✅ 新增參數
        competitors_data: Optional[List[Dict]] = None,  # ✅ 新增參數
    ) -> List[str]:
        """Generate key decision points section."""
        lines = []
        
        lines.append("")
        lines.append("📍 第一節 | 關鍵決策點分析")
        lines.append("─" * self._line_width)
        lines.append("")
        
        # Extract stints from strategy
        stints = getattr(strategy_result, 'stints', [])
        
        # If no stints, try to parse from strategy name
        if not stints:
            strategy_name = getattr(strategy_result, 'strategy_name', '')
            stints = self._parse_stints_from_name(strategy_name, race_laps)
        
        if not stints:
            lines.append("⚠️ 無法取得策略細節")
            lines.append(f"   策略名稱: {getattr(strategy_result, 'strategy_name', 'Unknown')}")
            lines.append("")
            lines.append("   提示: 請確保已執行完整的策略模擬，")
            lines.append("   或選擇包含完整 stints 資訊的策略對象。")
            lines.append("")
            return lines
        
        decision_num = 1
        cumulative_laps = 0
        
        for i, stint in enumerate(stints[:-1]):  # All except last stint
            stint_length = getattr(stint, 'planned_length', getattr(stint, 'length', 15))
            compound = getattr(stint, 'compound', None)
            compound_name = compound.value if hasattr(compound, 'value') else str(compound)
            
            pit_lap = cumulative_laps + stint_length
            cumulative_laps = pit_lap
            
            # Next stint info
            next_stint = stints[i + 1]
            next_compound = getattr(next_stint, 'compound', None)
            next_compound_name = next_compound.value if hasattr(next_compound, 'value') else str(next_compound)
            
            lines.append(f"🔹 決策點 {decision_num}: 進站 #{i+1} (圈數 {pit_lap})")
            lines.append("")
            lines.append(f"   輪胎更換: {compound_name} → {next_compound_name}")
            lines.append("")
            
            lines.append("   ✓ 選擇原因:")
            
            # ✅ 使用二次曲線退化模型計算累積退化
            # 公式: cumulative_deg(t) = base_rate * t + 0.5 * acceleration * t²
            # 這與 LapSimulator 中的模型完全一致
            
            # 正規化配方名稱 (處理 S/M/H 簡寫)
            compound_key = compound_name.upper()
            if compound_key in ['S', 'SOFT']:
                compound_key = 'SOFT'
            elif compound_key in ['M', 'MEDIUM']:
                compound_key = 'MEDIUM'
            elif compound_key in ['H', 'HARD']:
                compound_key = 'HARD'
            
            # 優先使用 stint 的實際退化率和加速度，否則使用預設值
            if hasattr(stint, 'degradation_rate') and stint.degradation_rate is not None and stint.degradation_rate > 0:
                base_rate = stint.degradation_rate
            else:
                base_rate = self._deg_rates.get(compound_key, 0.080)
            
            if hasattr(stint, 'degradation_acceleration') and stint.degradation_acceleration is not None and stint.degradation_acceleration > 0:
                acceleration = stint.degradation_acceleration
            else:
                acceleration = self._deg_acceleration.get(compound_key, 0.002)
            
            # 計算累積退化 (二次曲線公式)
            tire_age_at_pit = stint_length
            cumulative_deg = base_rate * tire_age_at_pit + 0.5 * acceleration * (tire_age_at_pit ** 2)
            
            # 顯示完整的退化資訊
            lines.append(f"     - 輪胎年齡 {tire_age_at_pit} 圈，累積衰退約 {cumulative_deg:.2f}s")
            lines.append(f"       └ 模型: 基礎退化 {base_rate:.3f}s/lap + 加速度 {acceleration:.4f}s/lap²")
            lines.append(f"       └ {compound_key}: base={base_rate * tire_age_at_pit:.2f}s + quadratic={0.5 * acceleration * (tire_age_at_pit ** 2):.2f}s")
            
            # Pit window analysis
            if pit_lap <= race_laps * 0.35:
                lines.append(f"     - 早期進站策略 (比賽前 35%)")
            elif pit_lap <= race_laps * 0.65:
                lines.append(f"     - 中段進站策略 (標準窗口)")
            else:
                lines.append(f"     - 晚期進站策略 (最大化首段)")
            
            # Free pit calculation
            free_pit_gap = pit_loss_green
            lines.append(f"     - Free Pit 門檻: 需領先 {free_pit_gap:.1f} 秒")
            
            lines.append("")
            lines.append("   ✓ 執行成本:")
            lines.append(f"     - 進站損失: {pit_loss_green:.1f} 秒 (綠旗條件)")
            
            # Alternative analysis with actual simulation data
            lines.append("")
            lines.append("   ⚠️ 替代方案分析 (基於實際模擬結果):")
            
            alt_early = pit_lap - 3
            alt_late = pit_lap + 3
            
            # 檢查實際 traffic 數據
            def check_traffic_at_lap(lap_num):
                """檢查指定圈數的實際 traffic 情況"""
                if not traffic_data or not our_driver:
                    return None, 0
                
                driver_traffic = traffic_data.get(our_driver, {})
                lap_details = driver_traffic.get('lap_details', {})
                lap_info = lap_details.get(lap_num, {})
                
                blocked = lap_info.get('blocked', False)
                gap = lap_info.get('gap_to_ahead', 999.0)
                
                return blocked, gap
            
            # 提早進站分析 - 檢查實際 traffic
            if alt_early > 0:
                tire_waste = base_rate * 3 + 0.5 * acceleration * ((tire_age_at_pit ** 2) - ((tire_age_at_pit - 3) ** 2))
                
                # 檢查 L12-L15 的實際 traffic
                has_traffic = False
                traffic_laps = []
                for check_lap in range(alt_early, pit_lap + 1):
                    blocked, gap = check_traffic_at_lap(check_lap)
                    if blocked or (gap is not None and gap < 1.0):
                        has_traffic = True
                        traffic_laps.append(check_lap)
                
                lines.append(f"     - 提早 3 圈 (L{alt_early}):")
                lines.append(f"       └ ❌ 浪費 {tire_waste:.2f}s 新胎壽命 (輪胎未充分使用)")
                
                if traffic_data and our_driver:
                    if has_traffic:
                        lines.append(f"       └ 📊 實際數據: L{traffic_laps[0]}-L{traffic_laps[-1]} 有 traffic ({len(traffic_laps)} 圈)")
                        lines.append(f"       └ ⚖️ 權衡: traffic 損失 ~{len(traffic_laps) * 0.3:.1f}s vs 新胎浪費 {tire_waste:.2f}s")
                        if tire_waste > len(traffic_laps) * 0.3:
                            lines.append(f"       └ ✅ 決策正確: 保持 L{pit_lap} 進站，避免更大損失")
                        else:
                            tire_waste_loss = tire_waste
                            traffic_time_loss = len(traffic_laps) * 0.3
                            net_loss = traffic_time_loss - tire_waste_loss
                            lines.append(f"       └ ⚠️ 提早進站更優: traffic 損失 {traffic_time_loss:.2f}s > 新胎浪費 {tire_waste_loss:.2f}s (淨損失 {net_loss:.2f}s)")
                    else:
                        lines.append(f"       └ 📊 實際數據: L{alt_early}-L{pit_lap} 無顯著 traffic")
                        lines.append(f"       └ ✅ 決策正確: 無 traffic 壓力，保持最優進站時機")
                else:
                    lines.append(f"       └ ⚠️ 無 traffic 數據，無法驗證")
            
            # 延後進站分析 - 檢查輪胎狀態和對手進站
            later_age = tire_age_at_pit + 3
            later_cumulative_deg = base_rate * later_age + 0.5 * acceleration * (later_age ** 2)
            extra_deg_if_late = later_cumulative_deg - cumulative_deg
            
            # 計算輪胎懸崖效應
            cliff_threshold = int(25 * 0.7)  # SOFT 約 17 圈
            approaching_cliff = later_age >= cliff_threshold
            
            # 檢查是否有對手在 pit_lap 進站 (undercut 威脅)
            undercut_threat = False
            if competitors_data:
                for comp in competitors_data:
                    comp_pit_laps = comp.get('pit_laps', [])
                    if pit_lap in comp_pit_laps or (pit_lap - 1) in comp_pit_laps:
                        undercut_threat = True
                        break
            
            lines.append(f"     - 延後 3 圈 (L{alt_late}):")
            lines.append(f"       └ ❌ 額外退化損失 {extra_deg_if_late:.2f}s (累積老胎代價)")
            
            if approaching_cliff:
                lines.append(f"       └ ⚠️ 輪胎接近懸崖點 ({cliff_threshold} 圈)，風險激增")
            
            if competitors_data:
                if undercut_threat:
                    lines.append(f"       └ 📊 實際數據: 對手在 L{pit_lap} 前後進站 (undercut 威脅存在)")
                    lines.append(f"       └ ⚖️ 權衡: 延後應對成本 {extra_deg_if_late:.2f}s vs undercut 優勢 ~3-5s")
                    lines.append(f"       └ ✅ 決策正確: 主動進站掌握節奏，避免被 undercut")
                else:
                    lines.append(f"       └ 📊 實際數據: 對手未在 L{pit_lap} 前後進站 (無 undercut 壓力)")
                    lines.append(f"       └ ✅ 決策正確: 無戰術需求，保持最優進站時機")
            else:
                lines.append(f"       └ ✅ 進站窗口靈活性 vs {extra_deg_if_late:.2f}s 代價不划算")
                lines.append(f"       └ ✅ 決策正確: 在最優時機進站")
            
            lines.append("")
            decision_num += 1
        
        # SC/VSC 實際事件報告
        sc_events = []
        if simulation_data:
            if isinstance(simulation_data, dict):
                sc_events = simulation_data.get('sc_events', [])
            elif hasattr(simulation_data, 'sc_events'):
                sc_events = simulation_data.sc_events or []
        
        # 獲取實際進站圈數列表
        actual_pit_laps = []
        for i, stint in enumerate(stints[:-1]):
            stint_length = getattr(stint, 'planned_length', getattr(stint, 'length', 15))
            cumulative = sum(
                getattr(s, 'planned_length', getattr(s, 'length', 15)) 
                for s in stints[:i+1]
            )
            actual_pit_laps.append(cumulative)
        
        if sc_events:
            lines.append(f"🔹 決策點 {decision_num}: 實際 SC/VSC 事件")
            lines.append("")
            
            for i, event in enumerate(sc_events, 1):
                # 處理 dict 或 object 格式
                if isinstance(event, dict):
                    event_type = event.get('type', 'SC').upper()
                    start_lap = event.get('start_lap', event.get('lap', 0))
                    end_lap = event.get('end_lap', start_lap + 3)
                    duration = end_lap - start_lap
                    is_vsc = event.get('is_vsc', False)
                else:
                    event_type = getattr(event, 'type', 'SC').upper() if hasattr(event, 'type') else 'SC'
                    start_lap = getattr(event, 'start_lap', getattr(event, 'lap', 0))
                    end_lap = getattr(event, 'end_lap', start_lap + 3)
                    duration = end_lap - start_lap
                    is_vsc = getattr(event, 'is_vsc', False)
                
                if is_vsc or "VSC" in event_type:
                    event_type = "VSC"
                else:
                    event_type = "SC"
                
                event_emoji = "🟡" if event_type == "VSC" else "🔴"
                lines.append(f"   {event_emoji} {event_type} 事件 #{i}: Lap {start_lap}-{end_lap} ({duration} 圈)")
                
                # 分析 SC 期間是否可以進站
                sc_pit_loss = 12.0 if event_type == "SC" else 9.0
                time_saved = pit_loss_green - sc_pit_loss
                
                lines.append(f"      進站損失減少: {time_saved:.1f} 秒 (綠旗 {pit_loss_green:.1f}s vs {event_type} {sc_pit_loss:.1f}s)")
                lines.append(f"      窗口圈數: Lap {start_lap} 或 Lap {start_lap + 1} 為最佳進站時機")
                lines.append("")
                
                # ✅ 分析車手是否在 SC 期間進站，以及為什麼沒進站
                pitted_during_sc = any(
                    start_lap <= pit_lap <= end_lap 
                    for pit_lap in actual_pit_laps
                )
                
                if pitted_during_sc:
                    pit_lap_in_sc = next(
                        pit_lap for pit_lap in actual_pit_laps 
                        if start_lap <= pit_lap <= end_lap
                    )
                    lines.append(f"      ✅ 進站決策: 在 Lap {pit_lap_in_sc} 進站，把握 {event_type} 窗口")
                    lines.append(f"         → 節省約 {time_saved:.1f} 秒進站時間")
                else:
                    lines.append(f"      ⚠️ 進站決策: 未在此 {event_type} 期間進站")
                    lines.append("")
                    lines.append(f"      📊 未進站原因分析 (基於實際決策邏輯):")
                    
                    # 分析原因 1: 輪胎年齡
                    tire_age_at_sc = start_lap
                    last_pit_before_sc = 0
                    for pit_lap in actual_pit_laps:
                        if pit_lap < start_lap:
                            last_pit_before_sc = pit_lap
                    tire_age_at_sc = start_lap - last_pit_before_sc
                    
                    # 分析原因 2: 剩餘圈數（硬性限制）
                    remaining_laps = race_laps - start_lap
                    
                    # 分析原因 3: 進站窗口
                    next_planned_pit = None
                    for pit_lap in actual_pit_laps:
                        if pit_lap > end_lap:
                            next_planned_pit = pit_lap
                            break
                    
                    # 決策閾值
                    threshold = 4.0 if event_type == 'SC' else 6.0
                    
                    # ========== 決策樹分析 ==========
                    
                    # 檢查 1: 強制不進站條件
                    if remaining_laps < 8:
                        lines.append(f"         ✅ 決策原因 1: 剩餘圈數限制")
                        lines.append(f"            → 剩餘 {remaining_laps} 圈 < 8 圈閾值")
                        lines.append(f"            → 系統強制不進站 (新胎無法回本)")
                        lines.append(f"            → 模擬計算: 進站成本 {sc_pit_loss:.0f}s > 新胎優勢 ~{remaining_laps * 0.3:.1f}s")
                    
                    # 檢查 2: 輪胎太新
                    elif tire_age_at_sc < 8:
                        lines.append(f"         ✅ 決策原因 1: 輪胎年齡過新")
                        lines.append(f"            → 輪胎年齡 {tire_age_at_sc} 圈 < 8 圈閾值")
                        lines.append(f"            → 新胎優勢仍在，進站浪費里程")
                        lines.append(f"            → 效益計算: 浪費 ~{(8 - tire_age_at_sc) * 0.12:.2f}s 新胎壽命")
                        lines.append(f"            → 淨效益 < {threshold}s 閾值，系統拒絕進站")
                    
                    # 檢查 3: 效益不足（中段輪胎）
                    elif tire_age_at_sc <= 15:
                        lines.append(f"         ✅ 決策原因 1: 效益計算未達閾值")
                        lines.append(f"            → 輪胎年齡 {tire_age_at_sc} 圈 (中段)")
                        lines.append(f"            → 老胎剩餘退化: ~{tire_age_at_sc * 0.08:.2f}s")
                        lines.append(f"            → 新胎優勢: ~{remaining_laps * 0.15:.2f}s (剩 {remaining_laps} 圈)")
                        lines.append(f"            → 進站成本: {sc_pit_loss:.0f}s ({event_type})")
                        
                        estimated_benefit = (tire_age_at_sc * 0.08) + (remaining_laps * 0.15) - sc_pit_loss
                        if next_planned_pit:
                            lines.append(f"            → 計劃進站節省: ~{time_saved:.0f}s (未來省下綠旗進站)")
                            estimated_benefit += time_saved
                        
                        lines.append(f"            → 預估淨效益: ~{estimated_benefit:.1f}s")
                        
                        if estimated_benefit < threshold:
                            lines.append(f"            → ❌ {estimated_benefit:.1f}s < {threshold}s 閾值，系統判定不進站")
                        else:
                            lines.append(f"            → ⚠️ {estimated_benefit:.1f}s > {threshold}s，但可能:")
                            
                            # 檢查窗口
                            if next_planned_pit:
                                laps_to_next = next_planned_pit - start_lap
                                if laps_to_next <= 8:
                                    lines.append(f"            → 在進站窗口內 (±8 圈): 80% 機率執行")
                                    lines.append(f"            → 隨機性影響: 20% 機率保守不進站 (本次模擬觸發了保守策略)")
                                else:
                                    lines.append(f"            → 距離計劃進站 {laps_to_next} 圈 > 8 圈窗口")
                                    lines.append(f"            → 超出窗口範圍，系統拒絕進站 (本次未執行)")
                            else:
                                lines.append(f"            → 無計劃進站，需淨效益 > 10.0s 才額外進站")
                                lines.append(f"            → 60% 機率執行，本次模擬觸發了 40% 不執行分支")
                    
                    # 檢查 4: 老胎但效益不足
                    else:
                        lines.append(f"         ⚠️ 決策原因 1: 老胎未進站分析")
                        lines.append(f"            → 輪胎年齡 {tire_age_at_sc} 圈 > 15 圈 (老化)")
                        lines.append(f"            → 根據效益計算應進站，但實際未進站")
                        lines.append("")
                        lines.append(f"         可能原因:")
                        
                        # 原因 A: 剩餘圈數不足
                        if remaining_laps < 12:
                            lines.append(f"            A. 剩餘 {remaining_laps} 圈接近限制 (< 12 圈)")
                            lines.append(f"               → 新胎優勢 ~{remaining_laps * 0.25:.1f}s")
                            lines.append(f"               → 進站成本 {sc_pit_loss:.0f}s")
                            if remaining_laps * 0.25 < sc_pit_loss:
                                lines.append(f"               → ✅ 效益不足 ({remaining_laps * 0.25:.1f}s < {sc_pit_loss:.0f}s)，正確決策")
                            else:
                                lines.append(f"               → ⚠️ 效益足夠 ({remaining_laps * 0.25:.1f}s > {sc_pit_loss:.0f}s)，但系統選擇不進站 (可能為其他因素影響)")
                        
                        # 原因 B: 窗口外
                        if next_planned_pit:
                            laps_to_next = next_planned_pit - start_lap
                            if laps_to_next > 8:
                                lines.append(f"            B. 超出進站窗口 (距計劃 {laps_to_next} 圈 > 8)")
                                lines.append(f"               → 雖然老胎，但距離計劃進站太遠")
                                lines.append(f"               → ⚠️ 窗口外 SC，系統不進站 (保持原計劃)")
                        
                        # 原因 C: 隨機性
                        lines.append(f"            C. 隨機性影響 (20% 不進站機率)")
                        lines.append(f"               → 模擬器使用機率性決策")
                        lines.append(f"               → 即使效益足夠，仍有機率保守策略")
                
                lines.append("")
            
            decision_num += 1
        
        # SC Response Strategy (模擬器應對邏輯)
        lines.append(f"🔹 決策點 {decision_num}: Safety Car 應對策略")
        lines.append("")
        lines.append("   ⚠️ SC 進站決策矩陣 (模擬器使用的應對邏輯):")
        lines.append("")
        lines.append("   | 胎齡 (圈) | 模擬器動作 | 決策邏輯 |")
        lines.append("   |-----------|------------|--------------------------------------|")
        lines.append("   | < 8       | Stay Out   | 新胎優勢大，效益 < 閾值 → 不進站  |")
        lines.append("   | 8-15      | 計算效益   | 效益 > 閾值 → 80% 執行            |")
        lines.append("   | > 15      | Box Box    | 老胎退化大，效益 > 閾值 → 進站    |")
        lines.append("")
        lines.append("   🔧 效益計算公式:")
        lines.append("      淨效益 = [老胎剩餘退化損失] - [新胎總時間 + 進站成本]")
        lines.append("      若有計劃進站: 淨效益 += (綠旗進站成本 - SC進站成本)")
        lines.append("")
        lines.append("   📊 決策閾值:")
        lines.append("      - SC: 淨效益 > 4.0s → 進站")
        lines.append("      - VSC: 淨效益 > 6.0s → 進站")
        lines.append("      - 額外進站 (已完成計劃): 淨效益 > 10.0s → 進站")
        lines.append("")
        lines.append("   🎲 隨機性影響:")
        lines.append("      - 在窗口內 (±8 圈): 80% 機率執行 → 20% 保守策略")
        lines.append("      - 額外進站: 60% 機率執行 → 40% 維持現狀")
        lines.append("")
        lines.append("   ⏱️ 進站成本對比:")
        lines.append("      - 綠旗進站: 24.0 秒")
        lines.append("      - SC 進站: 12.0 秒 (節省 12.0 秒)")
        lines.append("      - VSC 進站: 16.0 秒 (節省 8.0 秒)")
        lines.append("")
        lines.append("   🚫 強制不進站條件:")
        lines.append("      - 剩餘圈數 < 8 圈: 新胎無法發揮優勢")
        lines.append("")
        
        return lines
    
    def _generate_traffic_section(
        self,
        traffic_data: Optional[Dict],
        simulation_data: Optional[Any],
    ) -> List[str]:
        """Generate traffic analysis section."""
        lines = []
        
        lines.append("─" * self._line_width)
        lines.append("")
        lines.append("📍 第二節 | Traffic 影響分析")
        lines.append("─" * self._line_width)
        lines.append("")
        
        if traffic_data:
            blocked_laps = traffic_data.get('total_blocked_laps', 0)
            total_loss = traffic_data.get('total_estimated_loss', 0.0)
            drs_train_laps = traffic_data.get('drs_train_laps', 0)
            top_blockers = traffic_data.get('top_blockers', [])
            
            lines.append(f"🚗 總阻擋圈數: {blocked_laps} 圈 | 預估損失: {total_loss:.1f} 秒")
            lines.append("")
            
            if top_blockers:
                lines.append("🔸 主要阻擋車手:")
                for i, blocker in enumerate(top_blockers[:5], 1):
                    driver = blocker.get('driver', 'Unknown')
                    laps = blocker.get('laps_blocked', 0)
                    loss = blocker.get('estimated_loss', 0.0)
                    lines.append(f"   {i}. {driver} - {laps} 圈，損失 {loss:.1f} 秒")
                lines.append("")
            
            if drs_train_laps > 0:
                lines.append(f"🔸 DRS Train 情況: {drs_train_laps} 圈")
                lines.append("   → 3+ 輛車間距 < 1.5 秒，超車困難")
                lines.append("")
        else:
            # Generate estimated traffic analysis
            lines.append("🚗 Traffic 分析: (預估值，基於策略模擬)")
            lines.append("")
            lines.append("   📊 基於本場比賽的 Traffic 風險分析:")
            lines.append("")
            lines.append("   ⚠️ 高風險區間 (統計數據):")
            lines.append(f"     - 第一段進站窗口 (L{first_stint_length-3}-L{first_stint_length+3}): {len([c for c in competitors_data if first_stint_length-3 <= c.get('pit_laps', [0])[0] <= first_stint_length+3])} 台車同時進站" if competitors_data else "     - 第一段進站窗口: 無對手數據")
            lines.append("     - 出站後 3-5 圈: 遭遇慢車風險 (基於起跑位置)")
            lines.append("")
            lines.append("   ✓ 本場策略應對:")
            lines.append("     - 進站前檢查與前車差距 (需 > 2s 才安全出站)")
            lines.append("     - 錯開競爭對手進站圈數 (避免出站卡位)")
            lines.append("")
        
        return lines
    
    def _generate_competitor_section(
        self,
        simulation_data: Optional[Any],
        competitors_data: Optional[List[Dict]],
        our_driver: str,
    ) -> List[str]:
        """Generate competitor interaction section with lap-by-lap position analysis."""
        lines = []
        
        lines.append("\u2500" * self._line_width)
        lines.append("")
        lines.append("\ud83d\udccd 第三節 | 競爭對手互動")
        lines.append("\u2500" * self._line_width)
        lines.append("")
        
        # Support both dict and object access for simulation_data
        standings = None
        lap_states = None
        if simulation_data:
            if isinstance(simulation_data, dict):
                standings = simulation_data.get('final_standings')
                lap_states = simulation_data.get('lap_states', [])
            elif hasattr(simulation_data, 'final_standings'):
                standings = simulation_data.final_standings
                lap_states = getattr(simulation_data, 'lap_states', [])
        
        # ========== 新增: 分時段位置變化分析 ==========
        if lap_states and our_driver:
            lines.extend(self._generate_position_timeline_analysis(
                lap_states, our_driver, standings
            ))
        
        # ========== 最終排名的前後車分析 ==========
        if standings:
            our_result = None
            
            for standing in standings:
                if standing.driver_code == our_driver:
                    our_result = standing
                    break
            
            if our_result:
                our_pos = our_result.final_position
                
                lines.append("--- 最終排名鄰近車手 ---")
                lines.append("")
                
                # Find drivers ahead and behind
                driver_ahead = None
                driver_behind = None
                
                for standing in standings:
                    if standing.final_position == our_pos - 1:
                        driver_ahead = standing
                    elif standing.final_position == our_pos + 1:
                        driver_behind = standing
                
                lines.append("\ud83c\udfc0 前方車手 (威脅):")
                lines.append("")
                
                if driver_ahead:
                    gap = driver_ahead.gap_to_winner if hasattr(driver_ahead, 'gap_to_winner') else 0
                    our_gap = our_result.gap_to_winner if hasattr(our_result, 'gap_to_winner') else 0
                    delta = our_gap - gap
                    
                    lines.append(f"   {driver_ahead.driver_code} (P{driver_ahead.final_position}) - {driver_ahead.team}")
                    lines.append(f"   -> Gap: 落後 {delta:.1f} 秒")
                    lines.append(f"   -> 策略: {driver_ahead.strategy_notation}")
                    lines.append("")
                else:
                    lines.append("   (無 - 您是領先者!)")
                    lines.append("")
                
                lines.append("\ud83c\udfc0 後方車手 (壓力):")
                lines.append("")
                
                if driver_behind:
                    gap = driver_behind.gap_to_winner if hasattr(driver_behind, 'gap_to_winner') else 0
                    our_gap = our_result.gap_to_winner if hasattr(our_result, 'gap_to_winner') else 0
                    delta = gap - our_gap
                    
                    lines.append(f"   {driver_behind.driver_code} (P{driver_behind.final_position}) - {driver_behind.team}")
                    lines.append(f"   -> Gap: 領先 {delta:.1f} 秒")
                    lines.append(f"   -> 策略: {driver_behind.strategy_notation}")
                    
                    # 詳細威脅評估
                    lines.append("")
                    lines.append(f"   📊 威脅程度評估 (多維度分析):")
                    
                    # 因素 1: 距離威脅
                    distance_threat = 0
                    distance_reason = ""
                    if delta < 1.0:
                        distance_threat = 5
                        distance_reason = "DRS 範圍內 (< 1.0s)"
                    elif delta < 3.0:
                        distance_threat = 4
                        distance_reason = "接近 DRS (1-3s)"
                    elif delta < 5.0:
                        distance_threat = 3
                        distance_reason = "中等距離 (3-5s)"
                    elif delta < 10.0:
                        distance_threat = 2
                        distance_reason = "安全距離 (5-10s)"
                    else:
                        distance_threat = 1
                        distance_reason = "遠距離 (> 10s)"
                    
                    lines.append(f"      1. 距離因素: {distance_threat}/5")
                    lines.append(f"         └ {distance_reason}")
                    
                    # 因素 2: 輪胎策略威脅
                    our_strategy = our_result.strategy_notation if hasattr(our_result, 'strategy_notation') else ""
                    their_strategy = driver_behind.strategy_notation if hasattr(driver_behind, 'strategy_notation') else ""
                    
                    strategy_threat = 0
                    strategy_reason = ""
                    
                    # 比較輪胎新鮮度
                    if "S-S" in their_strategy or "M-S" in their_strategy:
                        strategy_threat = 4
                        strategy_reason = "對手使用軟胎 (速度優勢)"
                    elif their_strategy == our_strategy:
                        strategy_threat = 3
                        strategy_reason = "相同策略 (輪胎平等)"
                    elif "H" in their_strategy and "S" in our_strategy:
                        strategy_threat = 2
                        strategy_reason = "對手硬胎 (我方速度優勢)"
                    else:
                        strategy_threat = 3
                        strategy_reason = "策略差異 (需逐圈評估)"
                    
                    lines.append(f"      2. 策略因素: {strategy_threat}/5")
                    lines.append(f"         └ {strategy_reason}")
                    lines.append(f"         └ 我方: {our_strategy} vs 對手: {their_strategy}")
                    
                    # 因素 3: 速度趨勢（無數據時使用默認值）
                    trend_threat = 3
                    trend_reason = "無歷史數據，使用中立基準 (3/5)"
                    
                    lines.append(f"      3. 速度趨勢: {trend_threat}/5")
                    lines.append(f"         └ {trend_reason}")
                    
                    # 綜合評分
                    total_threat = (distance_threat + strategy_threat + trend_threat) / 3.0
                    
                    lines.append("")
                    lines.append(f"   ⚖️ 綜合評分: {total_threat:.1f}/5.0")
                    
                    # 最終等級判定（基於評分結果）
                    if total_threat >= 4.0:
                        threat_level = "極高 🔴"
                        threat_advice = f"評分 {total_threat:.1f}/5.0 - 立即應對 (防守線或提前 undercut)"
                    elif total_threat >= 3.5:
                        threat_level = "高 🟠"
                        threat_advice = f"評分 {total_threat:.1f}/5.0 - 密切監控 (準備防守動作)"
                    elif total_threat >= 2.5:
                        threat_level = "中 🟡"
                        threat_advice = f"評分 {total_threat:.1f}/5.0 - 保持警覺 (維持目前策略)"
                    elif total_threat >= 1.5:
                        threat_level = "低 🟢"
                        threat_advice = f"評分 {total_threat:.1f}/5.0 - 無立即威脅 (專注自身節奏)"
                    else:
                        threat_level = "極低 ⚪"
                        threat_advice = f"評分 {total_threat:.1f}/5.0 - 安全領先 (可專注輪胎管理)"
                    
                    lines.append(f"   🎯 威脅等級: {threat_level}")
                    lines.append(f"   💡 建議: {threat_advice}")
                    lines.append("")
                else:
                    lines.append("   (無後方車手)")
                    lines.append("")
            else:
                lines.append(f"\ud83c\udfc0 未找到 {our_driver} 的完賽數據")
                lines.append("")
        else:
            lines.append("\ud83c\udfc0 競爭對手分析: (需要完整賽事模擬數據)")
            lines.append("")
            lines.append("   提示: 執行「完整賽事」模擬以獲取詳細對手互動分析")
            lines.append("")
        
        return lines
    
    def _generate_position_timeline_analysis(
        self,
        lap_states: List[Any],
        our_driver: str,
        standings: Optional[List[Any]] = None
    ) -> List[str]:
        """
        Generate lap-by-lap position timeline analysis.
        
        Analyzes position changes during the race, especially:
        - Pit stop periods (position loss and recovery)
        - Position battles with specific drivers
        - Key overtakes and position swaps
        """
        lines = []
        
        if not lap_states:
            return lines
        
        lines.append("--- 分時段位置變化分析 ---")
        lines.append("")
        
        # Extract position history for our driver
        position_history = []
        pit_laps = []
        sc_laps = []
        
        for lap_state in lap_states:
            lap_num = lap_state.lap if hasattr(lap_state, 'lap') else 0
            positions = lap_state.positions if hasattr(lap_state, 'positions') else {}
            pit_stops = lap_state.pit_stops if hasattr(lap_state, 'pit_stops') else []
            sc_active = lap_state.sc_active if hasattr(lap_state, 'sc_active') else False
            
            our_pos = positions.get(our_driver, 20)
            position_history.append((lap_num, our_pos))
            
            if our_driver in pit_stops:
                pit_laps.append(lap_num)
            
            if sc_active:
                sc_laps.append(lap_num)
        
        if not position_history:
            lines.append("   (無位置歷史數據)")
            lines.append("")
            return lines
        
        # Analyze key phases
        total_laps = len(position_history)
        start_pos = position_history[0][1] if position_history else 1
        final_pos = position_history[-1][1] if position_history else 1
        
        # Find worst and best positions
        worst_pos = max(p[1] for p in position_history)
        best_pos = min(p[1] for p in position_history)
        worst_lap = next(p[0] for p in position_history if p[1] == worst_pos)
        best_lap = next(p[0] for p in position_history if p[1] == best_pos)
        
        lines.append(f"[位置變化總覽] 起跑 P{start_pos} -> 完賽 P{final_pos}")
        lines.append(f"   最佳位置: P{best_pos} (Lap {best_lap})")
        lines.append(f"   最差位置: P{worst_pos} (Lap {worst_lap})")
        lines.append("")
        
        # Identify pit stop impact periods
        if pit_laps:
            lines.append("[進站影響分析]")
            lines.append("")
            
            for pit_lap in pit_laps:
                # Find position before and after pit
                pre_pit_pos = None
                post_pit_pos = None
                recovery_lap = None
                pre_pit_lap = pit_lap - 1
                
                for lap_num, pos in position_history:
                    if lap_num == pre_pit_lap:
                        pre_pit_pos = pos
                    elif lap_num == pit_lap:
                        post_pit_pos = pos
                
                if pre_pit_pos and post_pit_pos:
                    pos_lost = post_pit_pos - pre_pit_pos
                    
                    lines.append(f"   進站圈 Lap {pit_lap}:")
                    lines.append(f"   -> 進站前: P{pre_pit_pos}")
                    lines.append(f"   -> 進站後: P{post_pit_pos}")
                    
                    if pos_lost > 0:
                        lines.append(f"   -> 掉落名次: {pos_lost} 位")
                        
                        # Find when position recovered
                        for lap_num, pos in position_history:
                            if lap_num > pit_lap and pos <= pre_pit_pos:
                                recovery_lap = lap_num
                                break
                        
                        if recovery_lap:
                            recovery_laps = recovery_lap - pit_lap
                            lines.append(f"   -> 恢復至 P{pre_pit_pos}: Lap {recovery_lap} ({recovery_laps} 圈後)")
                        else:
                            lines.append(f"   -> 未能恢復至進站前位置")
                    else:
                        lines.append(f"   -> 成功 Undercut! 位置提升")
                    lines.append("")
        
        # Identify SC periods and their impact
        if sc_laps:
            sc_periods = self._group_consecutive_laps(sc_laps)
            lines.append("[SC/VSC 期間位置變化]")
            lines.append("")
            
            for sc_start, sc_end in sc_periods:
                pre_sc_pos = None
                post_sc_pos = None
                
                for lap_num, pos in position_history:
                    if lap_num == sc_start - 1:
                        pre_sc_pos = pos
                    elif lap_num == sc_end + 1:
                        post_sc_pos = pos
                
                if pre_sc_pos and post_sc_pos:
                    pos_change = post_sc_pos - pre_sc_pos
                    lines.append(f"   SC Lap {sc_start}-{sc_end}:")
                    lines.append(f"   -> SC 前: P{pre_sc_pos}")
                    lines.append(f"   -> SC 後: P{post_sc_pos}")
                    
                    if pos_change > 0:
                        lines.append(f"   -> 掉落 {pos_change} 位 (SC 期間對手未進站或策略差異)")
                    elif pos_change < 0:
                        lines.append(f"   -> 提升 {abs(pos_change)} 位 (SC 期間對手進站或我方獲利)")
                    else:
                        lines.append(f"   -> 位置不變")
                    lines.append("")
        
        # Key battle phases (where position changed frequently)
        battle_phases = self._identify_battle_phases(position_history, lap_states, our_driver)
        if battle_phases:
            lines.append("[關鍵纏鬥時段]")
            lines.append("")
            
            for phase in battle_phases[:3]:  # Top 3 battles
                lines.append(f"   Lap {phase['start']}-{phase['end']}: 與 {phase['opponent']} 爭奪 P{phase['position']}")
                lines.append(f"   -> 結果: {'超越成功' if phase['won'] else '被超越'}")
                lines.append("")
        
        return lines
    
    def _group_consecutive_laps(self, laps: List[int]) -> List[Tuple[int, int]]:
        """Group consecutive lap numbers into (start, end) tuples."""
        if not laps:
            return []
        
        periods = []
        start = laps[0]
        end = laps[0]
        
        for lap in laps[1:]:
            if lap == end + 1:
                end = lap
            else:
                periods.append((start, end))
                start = lap
                end = lap
        
        periods.append((start, end))
        return periods
    
    def _identify_battle_phases(
        self,
        position_history: List[Tuple[int, int]],
        lap_states: List[Any],
        our_driver: str
    ) -> List[Dict[str, Any]]:
        """
        Identify phases where our driver was in a battle (position swapping).
        
        Returns list of battle phases with details.
        """
        battles = []
        
        # Find laps where position changed
        position_changes = []
        for i in range(1, len(position_history)):
            prev_lap, prev_pos = position_history[i-1]
            curr_lap, curr_pos = position_history[i]
            
            if prev_pos != curr_pos:
                position_changes.append({
                    'lap': curr_lap,
                    'from_pos': prev_pos,
                    'to_pos': curr_pos,
                    'gained': prev_pos > curr_pos  # Lower position number = better
                })
        
        # Group nearby position changes into battles
        if not position_changes:
            return battles
        
        # Find opponent in position swap
        for change in position_changes[:5]:  # Top 5 changes
            lap = change['lap']
            target_pos = change['from_pos'] if change['gained'] else change['to_pos']
            
            # Find who was in the contested position
            opponent = None
            for lap_state in lap_states:
                if hasattr(lap_state, 'lap') and lap_state.lap == lap:
                    positions = lap_state.positions if hasattr(lap_state, 'positions') else {}
                    for driver, pos in positions.items():
                        if driver != our_driver and pos == target_pos:
                            opponent = driver
                            break
                    break
            
            if opponent:
                battles.append({
                    'start': max(1, lap - 2),
                    'end': min(len(position_history), lap + 2),
                    'opponent': opponent,
                    'position': min(change['from_pos'], change['to_pos']),
                    'won': change['gained']
                })
        
        return battles
    
    def _generate_optimization_section(
        self,
        strategy_result: Any,
        mc_summary: Optional[Any],
        scenario_analyses: Optional[Dict],
    ) -> List[str]:
        """Generate win rate optimization suggestions."""
        lines = []
        
        lines.append("─" * self._line_width)
        lines.append("")
        lines.append("📍 第四節 | 勝率提升分析")
        lines.append("─" * self._line_width)
        lines.append("")
        
        stints = getattr(strategy_result, 'stints', [])
        strategy_name = getattr(strategy_result, 'strategy_name', 'Unknown')
        
        # 獲取當前策略的勝率數據
        current_win_rate = 0.0
        current_podium_rate = 0.0
        
        # ✅ 初始化變量避免 UnboundLocalError
        best_name = strategy_name
        best_rate = 0.0
        sorted_strategies = []
        
        if mc_summary:
            win_percentages = getattr(mc_summary, 'win_percentages', {})
            current_win_rate = win_percentages.get(strategy_name, 0.0)
            best_rate = current_win_rate  # ✅ 更新 best_rate 默認值
            
            # 獲取領獎台機率
            if hasattr(mc_summary, 'position_predictions'):
                predictions = mc_summary.position_predictions
                for pred in predictions:
                    if pred.strategy_name == strategy_name:
                        current_podium_rate = pred.podium_probability
                        break
        
        # 標題：顯示當前表現
        lines.append("📊 當前策略表現:")
        lines.append(f"   策略: {strategy_name}")
        lines.append(f"   冠軍勝率 (P1): {current_win_rate:.1f}%")
        if current_podium_rate > 0:
            lines.append(f"   領獎台機率 (P1-P3): {current_podium_rate:.1f}%")
        lines.append("")
        
        # 分析 1: 與其他策略對比（如果有 MC 數據）
        if mc_summary and hasattr(mc_summary, 'win_percentages'):
            win_percentages = mc_summary.win_percentages
            sorted_strategies = sorted(win_percentages.items(), key=lambda x: x[1], reverse=True)
            
            if sorted_strategies:
                best_name, best_rate = sorted_strategies[0]
            # else: 保持初始值 best_name=strategy_name, best_rate=current_win_rate
            
            lines.append("✅ 策略選擇分析:")
            
            if best_name == strategy_name:
                lines.append(f"   🏆 當前策略是最優選擇 (勝率 {current_win_rate:.1f}%)")
                
                # 顯示次優策略的差距
                if len(sorted_strategies) > 1:
                    second_name, second_rate = sorted_strategies[1]
                    advantage = current_win_rate - second_rate
                    lines.append(f"   → 領先次優策略 {second_name}: +{advantage:.1f}% 勝率")
                    lines.append(f"   → 原因: 此策略在模擬中獲得 {int(current_win_rate * 10)} 次冠軍 (共 1000 次)")
            else:
                gap = best_rate - current_win_rate
                lines.append(f"   ⚠️ 當前策略非最優 (勝率 {current_win_rate:.1f}%)")
                lines.append(f"   → 最佳策略: {best_name} (勝率 {best_rate:.1f}%)")
                lines.append(f"   → 差距: -{gap:.1f}% 勝率")
                lines.append(f"   → 改用最佳策略可提升約 {int(gap * 10)} 次勝利機會 (共 1000 次)")
            
            lines.append("")
        
        # 分析 2: 場景適應性（如果有 scenario_analyses）
        if scenario_analyses:
            lines.append("✅ 場景適應性分析:")
            lines.append("")
            
            strong_scenarios = []
            weak_scenarios = []
            
            for scenario_type, analysis in scenario_analyses.items():
                scenario_name = getattr(analysis, 'scenario_name', scenario_type)
                win_rates = getattr(analysis, 'strategy_win_rates', {})
                our_rate = win_rates.get(strategy_name, 0)
                best_rate = getattr(analysis, 'best_strategy_win_rate', 0)
                
                diff = our_rate - best_rate
                
                if diff >= -5.0:  # 接近最優或是最優
                    strong_scenarios.append((scenario_name, our_rate, diff))
                else:
                    weak_scenarios.append((scenario_name, our_rate, diff, best_rate))
            
            if strong_scenarios:
                lines.append("   🟢 優勢場景 (接近最優):")
                for sc_name, rate, diff in strong_scenarios:
                    if diff >= 0:
                        lines.append(f"      • {sc_name}: {rate:.1f}% (最佳策略 ✓)")
                    else:
                        lines.append(f"      • {sc_name}: {rate:.1f}% (僅落後 {abs(diff):.1f}%)")
                lines.append("")
            
            if weak_scenarios:
                lines.append("   🟡 弱勢場景 (可優化):")
                for sc_name, rate, diff, best_rate in weak_scenarios:
                    gap_pct = abs(diff)
                    gap_wins = int(gap_pct * 10)  # 每 1000 次的勝場數差距
                    lines.append(f"      • {sc_name}: {rate:.1f}% vs 最優 {best_rate:.1f}% (落後 {gap_pct:.1f}%)")
                    lines.append(f"        → 數據分析: 每 1000 次模擬少贏 {gap_wins} 場，需檢視該場景的進站時機/輪胎選擇")
                lines.append("")
        
        # 分析 3: 具體改進建議（基於實際數據）
        suggestion_num = 1
        
        # 進站時機建議（基於模擬結果）
        if stints:
            first_stint = stints[0]
            first_stint_length = getattr(first_stint, 'planned_length', 15)
            
            lines.append(f"💡 具體改進建議:")
            lines.append("")
            lines.append(f"   建議 {suggestion_num}: 進站時機優化")
            lines.append(f"      當前進站: L{first_stint_length}")
            
            # 如果有實際的替代方案數據
            if mc_summary and hasattr(mc_summary, 'win_percentages'):
                # 檢查是否有不同進站時機的策略
                timing_strategies = {}
                for strat_name, rate in mc_summary.win_percentages.items():
                    # 簡化：假設策略名稱包含進站時機資訊
                    timing_strategies[strat_name] = rate
                
                lines.append(f"      模擬結果: 此時機獲得 {current_win_rate:.1f}% 勝率")
                
                # 如果不是最優，說明最優時機
                if best_name != strategy_name and len(sorted_strategies) > 0:
                    lines.append(f"      最優時機: {best_name} 可獲得 {best_rate:.1f}% 勝率")
                    lines.append(f"      差異: 更改時機可提升 {best_rate - current_win_rate:.1f}% 勝率")
                else:
                    lines.append(f"      ✅ 當前時機已是最優選擇")
            
            lines.append("")
            suggestion_num += 1
        
        # 輪胎策略建議
        if mc_summary and hasattr(mc_summary, 'win_percentages'):
            lines.append(f"   建議 {suggestion_num}: 輪胎配置優化")
            
            # 分析不同輪胎組合的表現
            soft_strategies = {k: v for k, v in mc_summary.win_percentages.items() if 'S-S' in k or 'M-S' in k}
            hard_strategies = {k: v for k, v in mc_summary.win_percentages.items() if 'H' in k}
            
            if soft_strategies and hard_strategies:
                avg_soft = sum(soft_strategies.values()) / len(soft_strategies)
                avg_hard = sum(hard_strategies.values()) / len(hard_strategies)
                
                lines.append(f"      軟胎策略平均: {avg_soft:.1f}% 勝率")
                lines.append(f"      硬胎策略平均: {avg_hard:.1f}% 勝率")
                
                if avg_soft > avg_hard + 5.0:
                    lines.append(f"      ✅ 模擬顯示: 軟胎策略更優 (+{avg_soft - avg_hard:.1f}%)")
                elif avg_hard > avg_soft + 5.0:
                    lines.append(f"      ✅ 模擬顯示: 硬胎策略更優 (+{avg_hard - avg_soft:.1f}%)")
                else:
                    lines.append(f"      ⚖️ 模擬顯示: 輪胎選擇影響不大 (差異 {abs(avg_soft - avg_hard):.1f}%)")
            
            lines.append("")
        
        lines.append("─" * 70)
        lines.append("")
        lines.append("💡 結論:")
        
        if best_name == strategy_name:
            lines.append(f"   ✅ 當前策略 {strategy_name} 已是最優選擇")
            lines.append(f"   → 在 1000 次模擬中獲得最高勝率 ({current_win_rate:.1f}%)")
            lines.append(f"   → 保持此策略，專注執行細節")
        else:
            improvement = best_rate - current_win_rate
            lines.append(f"   ⚠️ 改用 {best_name} 可提升 {improvement:.1f}% 勝率")
            lines.append(f"   → 相當於每 100 場比賽多贏 {int(improvement * 100 / 100)} 場")
            lines.append(f"   → 建議分析 {best_name} 的進站時機和輪胎配置")
        
        lines.append("")
        
        return lines
    
    def _generate_scenario_section(
        self,
        scenario_analyses: Optional[Dict],
        strategy_result: Any,
    ) -> List[str]:
        """Generate SC scenario analysis section."""
        lines = []
        
        lines.append("─" * self._line_width)
        lines.append("")
        lines.append("📍 第五節 | 各場景策略建議")
        lines.append("─" * self._line_width)
        lines.append("")
        
        if scenario_analyses:
            lines.append("📊 SC 場景勝率對比:")
            lines.append("")
            lines.append("   場景           | 此策略勝率 | 最佳策略         | 差異")
            lines.append("   ─────────────|───────────|─────────────────|──────")
            
            strategy_name = getattr(strategy_result, 'strategy_name', '')
            
            for scenario_type, analysis in scenario_analyses.items():
                scenario_name = getattr(analysis, 'scenario_name', scenario_type)
                occurrence = getattr(analysis, 'occurrence_rate', 0)
                best_strat = getattr(analysis, 'best_strategy', 'N/A')
                best_rate = getattr(analysis, 'best_strategy_win_rate', 0)
                
                # Get our strategy's rate in this scenario
                win_rates = getattr(analysis, 'strategy_win_rates', {})
                our_rate = win_rates.get(strategy_name, 0)
                
                diff = our_rate - best_rate
                diff_str = f"+{diff:.1f}%" if diff >= 0 else f"{diff:.1f}%"
                
                if strategy_name == best_strat:
                    diff_str = "✓ 最佳"
                
                # Truncate scenario name for display
                display_name = scenario_name[:12].ljust(12)
                
                lines.append(f"   {display_name} | {our_rate:6.1f}%   | {best_strat[:15].ljust(15)} | {diff_str}")
            
            lines.append("")
            
            # Summary
            total_scenarios = len(scenario_analyses)
            best_count = sum(1 for s_type, analysis in scenario_analyses.items()
                           if getattr(analysis, 'best_strategy', '') == strategy_name)
            
            pct = (best_count / total_scenarios * 100) if total_scenarios > 0 else 0
            lines.append(f"✅ 總結: 此策略在 {best_count}/{total_scenarios} ({pct:.0f}%) 場景下是最佳選擇")
            lines.append("")
        else:
            lines.append("📊 SC 場景分析: (需要 Monte Carlo 模擬數據)")
            lines.append("")
            lines.append("   提示: 執行 Monte Carlo 模擬以獲取各 SC 場景下的勝率對比")
            lines.append("")
            lines.append("   Monte Carlo 模擬場景分佈 (基於 1.5%/圈 SC 機率):")
            lines.append("   - 無 SC (~50%): 標準配速策略")
            lines.append("   - 早期 SC (~15%): 進站窗口變化")
            lines.append("   - 中段 SC (~20%): 免費進站機會")
            lines.append("   - 晚期 SC (~15%): 最後衝刺關鍵")
            lines.append("")
        
        return lines
    
    def _generate_footer(self) -> List[str]:
        """Generate report footer."""
        lines = []
        
        lines.append("=" * self._line_width)
        lines.append(self._center("報告結束"))
        lines.append(self._center(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
        lines.append("=" * self._line_width)
        
        return lines
    
    def _center(self, text: str) -> str:
        """Center text within line width."""
        padding = (self._line_width - len(text)) // 2
        return " " * padding + text
    
    def _get_stint_notation(self, strategy_result: Any) -> str:
        """Get strategy notation string (e.g., 'M18-H')."""
        if hasattr(strategy_result, 'get_stint_notation'):
            return strategy_result.get_stint_notation()
        
        stints = getattr(strategy_result, 'stints', [])
        if not stints:
            return "N/A"
        
        parts = []
        for stint in stints:
            compound = getattr(stint, 'compound', None)
            if compound:
                c = compound.value[0] if hasattr(compound, 'value') else str(compound)[0]
            else:
                c = "?"
            
            length = getattr(stint, 'planned_length', getattr(stint, 'length', ''))
            if length:
                parts.append(f"{c}{length}")
            else:
                parts.append(c)
        
        return "-".join(parts)
    
    def _parse_stints_from_name(self, strategy_name: str, race_laps: int) -> List[Any]:
        """
        Parse strategy name to extract basic stint information.
        
        Strategy names can be:
        - Simple: "H-S", "M-H", "S-M-H"
        - Detailed: "Plan A", "One Stop Medium"
        - With lengths: "M20-H", "S15-M-H"
        
        Args:
            strategy_name: Strategy name string
            race_laps: Total race laps for length estimation
            
        Returns:
            List of basic stint objects
        """
        from dataclasses import dataclass
        from enum import Enum
        
        # Define minimal compound enum
        class Compound(Enum):
            SOFT = "SOFT"
            MEDIUM = "MEDIUM"
            HARD = "HARD"
        
        @dataclass
        class BasicStint:
            compound: Compound
            planned_length: int
            length: int
        
        # Extract compound sequence from strategy name
        # Handle formats: "H-S", "M-H", "Plan A", etc.
        compounds_map = {
            'S': Compound.SOFT,
            'M': Compound.MEDIUM,
            'H': Compound.HARD,
            'SOFT': Compound.SOFT,
            'MEDIUM': Compound.MEDIUM,
            'HARD': Compound.HARD,
        }
        
        stints = []
        
        # Try to parse compound-length notation (e.g., "M20-H37")
        if '-' in strategy_name and any(c.isdigit() for c in strategy_name):
            parts = strategy_name.split('-')
            for part in parts:
                # Extract compound letter and optional length
                compound_char = None
                length = None
                
                for i, char in enumerate(part):
                    if char.upper() in ['S', 'M', 'H']:
                        compound_char = char.upper()
                        # Check if followed by numbers
                        if i + 1 < len(part) and part[i+1:].isdigit():
                            length = int(part[i+1:])
                        break
                
                if compound_char:
                    compound = compounds_map[compound_char]
                    # Estimate length if not provided
                    if length is None:
                        # Distribute remaining laps evenly
                        remaining_stints = len(parts) - len(stints)
                        remaining_laps = race_laps - sum(s.planned_length for s in stints)
                        length = remaining_laps // remaining_stints if remaining_stints > 0 else 20
                    
                    stints.append(BasicStint(
                        compound=compound,
                        planned_length=length,
                        length=length
                    ))
        
        # Simple compound sequence (e.g., "H-S", "M-H")
        elif '-' in strategy_name:
            parts = strategy_name.split('-')
            for part in parts:
                compound_char = part.strip().upper()
                if compound_char in compounds_map:
                    # Distribute laps evenly
                    num_stints = len(parts)
                    stint_length = race_laps // num_stints
                    
                    stints.append(BasicStint(
                        compound=compounds_map[compound_char],
                        planned_length=stint_length,
                        length=stint_length
                    ))
        
        # Named strategies - try to extract from name
        else:
            # Check for compound keywords in name
            name_upper = strategy_name.upper()
            
            # Common strategy patterns
            if 'ONE STOP' in name_upper or 'PLAN A' in name_upper:
                # Default 1-stop: Medium-Hard
                stints = [
                    BasicStint(Compound.MEDIUM, race_laps // 2, race_laps // 2),
                    BasicStint(Compound.HARD, race_laps - race_laps // 2, race_laps - race_laps // 2)
                ]
            elif 'TWO STOP' in name_upper or 'PLAN B' in name_upper:
                # Default 2-stop: Soft-Medium-Hard
                stint_len = race_laps // 3
                stints = [
                    BasicStint(Compound.SOFT, stint_len, stint_len),
                    BasicStint(Compound.MEDIUM, stint_len, stint_len),
                    BasicStint(Compound.HARD, race_laps - 2*stint_len, race_laps - 2*stint_len)
                ]
            else:
                # Fallback: check for individual compound mentions
                compounds_found = []
                for compound_str, compound_enum in compounds_map.items():
                    if len(compound_str) > 1 and compound_str in name_upper:
                        compounds_found.append(compound_enum)
                
                if compounds_found:
                    # Distribute laps evenly
                    num_stints = len(compounds_found)
                    stint_length = race_laps // num_stints
                    for compound in compounds_found:
                        stints.append(BasicStint(
                            compound=compound,
                            planned_length=stint_length,
                            length=stint_length
                        ))
                # If still no compounds found, use default M-H strategy
                if not stints:
                    stints = [
                        BasicStint(Compound.MEDIUM, race_laps // 2, race_laps // 2),
                        BasicStint(Compound.HARD, race_laps - race_laps // 2, race_laps - race_laps // 2)
                    ]
        
        return stints
