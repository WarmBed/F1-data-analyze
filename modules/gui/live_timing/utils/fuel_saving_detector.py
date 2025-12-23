"""
实时油门省油模式检测器
Live Throttle Fuel-Saving Mode Detector

用于在 Live Timing 中检测车手是否进入省油驾驶状态
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import statistics


@dataclass
class ThrottleHistory:
    """车手油门使用历史"""
    driver_code: str
    throttle_95_history: deque = field(default_factory=lambda: deque(maxlen=10))  # 最近10圈
    baseline_throttle: Optional[float] = None  # 基线油门使用率
    current_throttle: Optional[float] = None  # 当前圈油门使用率
    
    def update(self, throttle_95: float):
        """更新油门数据"""
        self.current_throttle = throttle_95
        self.throttle_95_history.append(throttle_95)
        
        # 更新基线（使用中位数更稳健）
        if len(self.throttle_95_history) >= 3:
            self.baseline_throttle = statistics.median(self.throttle_95_history)
    
    def get_deviation(self) -> Optional[float]:
        """获取当前与基线的偏差（百分比）"""
        if self.baseline_throttle is None or self.current_throttle is None:
            return None
        return self.current_throttle - self.baseline_throttle
    
    def get_trend(self, last_n: int = 3) -> Optional[float]:
        """获取最近N圈的趋势（上升/下降）"""
        if len(self.throttle_95_history) < last_n:
            return None
        
        recent = list(self.throttle_95_history)[-last_n:]
        first_half = statistics.mean(recent[:len(recent)//2])
        second_half = statistics.mean(recent[len(recent)//2:])
        
        return second_half - first_half


@dataclass
class FuelSavingDetection:
    """省油检测结果"""
    is_fuel_saving: bool
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    deviation_percent: float
    reason: str
    baseline_throttle: float
    current_throttle: float
    
    def to_dict(self) -> dict:
        return {
            "is_fuel_saving": self.is_fuel_saving,
            "confidence": self.confidence,
            "deviation_percent": round(self.deviation_percent, 2),
            "reason": self.reason,
            "baseline": round(self.baseline_throttle, 2),
            "current": round(self.current_throttle, 2)
        }


class FuelSavingDetector:
    """
    实时省油模式检测器
    
    检测逻辑：
    1. 与该车手的基线对比（最近10圈中位数）
    2. 检测油门使用率的突然下降
    3. 排除进站圈、黄旗等外部因素
    """
    
    def __init__(
        self,
        threshold_high: float = -5.0,    # 高置信度阈值：-5% 以下
        threshold_medium: float = -3.0,  # 中等置信度阈值：-3% 到 -5%
        min_laps_for_baseline: int = 3   # 建立基线所需最少圈数
    ):
        """
        初始化检测器
        
        Args:
            threshold_high: 高置信度省油判定阈值（百分比）
            threshold_medium: 中等置信度省油判定阈值（百分比）
            min_laps_for_baseline: 建立基线所需的最少圈数
        """
        self.threshold_high = threshold_high
        self.threshold_medium = threshold_medium
        self.min_laps_for_baseline = min_laps_for_baseline
        
        # 存储每个车手的历史数据
        self.driver_histories: Dict[str, ThrottleHistory] = {}
    
    def update_driver_throttle(
        self,
        driver_code: str,
        throttle_95: float,
        is_pit_lap: bool = False,
        is_yellow_flag: bool = False,
        is_safety_car: bool = False
    ) -> None:
        """
        更新车手的油门数据
        
        Args:
            driver_code: 车手代码（如 "VER", "NOR"）
            throttle_95: 油门95%使用率（0-100）
            is_pit_lap: 是否为进站圈
            is_yellow_flag: 是否有黄旗
            is_safety_car: 是否有安全车
        """
        # 跳过异常圈（进站、黄旗、安全车）
        if is_pit_lap or is_yellow_flag or is_safety_car:
            return
        
        # 初始化车手历史
        if driver_code not in self.driver_histories:
            self.driver_histories[driver_code] = ThrottleHistory(driver_code=driver_code)
        
        # 更新数据
        self.driver_histories[driver_code].update(throttle_95)
    
    def detect_fuel_saving(
        self,
        driver_code: str,
        current_lap_time: Optional[float] = None
    ) -> Optional[FuelSavingDetection]:
        """
        检测车手是否在省油
        
        Args:
            driver_code: 车手代码
            current_lap_time: 当前圈速（秒），可选
        
        Returns:
            FuelSavingDetection 对象，如果数据不足则返回 None
        """
        if driver_code not in self.driver_histories:
            return None
        
        history = self.driver_histories[driver_code]
        
        # 检查是否有足够的历史数据
        if len(history.throttle_95_history) < self.min_laps_for_baseline:
            return None
        
        if history.baseline_throttle is None or history.current_throttle is None:
            return None
        
        # 计算偏差
        deviation = history.get_deviation()
        
        if deviation is None:
            return None
        
        # 判断是否省油
        is_fuel_saving = False
        confidence = "LOW"
        reason = "正常驾驶"
        
        if deviation <= self.threshold_high:
            # 高置信度省油
            is_fuel_saving = True
            confidence = "HIGH"
            reason = f"油门使用率显著低于基线 {abs(deviation):.1f}%"
            
        elif deviation <= self.threshold_medium:
            # 中等置信度省油
            is_fuel_saving = True
            confidence = "MEDIUM"
            reason = f"油门使用率低于基线 {abs(deviation):.1f}%"
            
        else:
            # 未检测到省油
            is_fuel_saving = False
            confidence = "LOW"
            if deviation > 0:
                reason = f"油门使用率高于基线 +{deviation:.1f}%"
            else:
                reason = "油门使用率接近基线"
        
        # 检查趋势强化判断
        trend = history.get_trend(last_n=3)
        if trend is not None and trend < -2.0 and is_fuel_saving:
            reason += "（持续下降趋势）"
            if confidence == "MEDIUM":
                confidence = "HIGH"
        
        return FuelSavingDetection(
            is_fuel_saving=is_fuel_saving,
            confidence=confidence,
            deviation_percent=deviation,
            reason=reason,
            baseline_throttle=history.baseline_throttle,
            current_throttle=history.current_throttle
        )
    
    def get_all_fuel_saving_status(self) -> Dict[str, FuelSavingDetection]:
        """
        获取所有车手的省油状态
        
        Returns:
            车手代码 -> FuelSavingDetection 的字典
        """
        results = {}
        for driver_code in self.driver_histories.keys():
            detection = self.detect_fuel_saving(driver_code)
            if detection is not None:
                results[driver_code] = detection
        return results
    
    def reset_driver(self, driver_code: str):
        """重置某个车手的历史数据"""
        if driver_code in self.driver_histories:
            del self.driver_histories[driver_code]
    
    def reset_all(self):
        """重置所有车手的历史数据"""
        self.driver_histories.clear()


# ==================== 使用示例 ====================

def example_usage():
    """使用示例：模拟实时检测"""
    
    detector = FuelSavingDetector(
        threshold_high=-5.0,
        threshold_medium=-3.0,
        min_laps_for_baseline=3
    )
    
    # 模拟 VER 的油门数据（正常驾驶）
    print("=" * 80)
    print("示例：Verstappen (VER) 油门数据")
    print("=" * 80)
    
    normal_laps = [54.0, 53.5, 54.2, 53.8, 54.1, 53.9, 54.3, 54.0]
    fuel_saving_laps = [52.0, 50.5, 49.8]  # 省油圈
    
    all_laps = normal_laps + fuel_saving_laps
    
    for lap_num, throttle in enumerate(all_laps, start=1):
        # 更新数据
        detector.update_driver_throttle("VER", throttle)
        
        # 检测省油
        result = detector.detect_fuel_saving("VER")
        
        if result:
            status = "🔴 省油" if result.is_fuel_saving else "🟢 正常"
            print(f"\nLap {lap_num:2d}: Throttle 95% = {throttle:.1f}%")
            print(f"  状态: {status} ({result.confidence})")
            print(f"  基线: {result.baseline_throttle:.1f}%")
            print(f"  偏差: {result.deviation_percent:+.1f}%")
            print(f"  原因: {result.reason}")
    
    print("\n" + "=" * 80)
    print("示例：多车手对比")
    print("=" * 80)
    
    # 模拟多个车手
    drivers_data = {
        "VER": [54.0, 53.5, 54.2, 48.0],  # VER 最后一圈省油
        "NOR": [51.5, 51.2, 51.8, 51.3],  # NOR 正常
        "PIA": [52.0, 51.5, 52.3, 47.5],  # PIA 最后一圈省油
    }
    
    detector_multi = FuelSavingDetector()
    
    # 模拟4圈数据
    for lap in range(4):
        print(f"\n--- Lap {lap + 1} ---")
        
        for driver, throttles in drivers_data.items():
            detector_multi.update_driver_throttle(driver, throttles[lap])
            result = detector_multi.detect_fuel_saving(driver)
            
            if result and lap >= 2:  # 前2圈建立基线
                status_icon = "🔴" if result.is_fuel_saving else "🟢"
                print(f"{driver}: {status_icon} {throttles[lap]:.1f}% "
                      f"(基线 {result.baseline_throttle:.1f}%, "
                      f"偏差 {result.deviation_percent:+.1f}%)")


if __name__ == "__main__":
    example_usage()
