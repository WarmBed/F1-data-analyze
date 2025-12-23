"""
实时 Sector 级别省油检测器
Live Sector-Based Fuel-Saving Detector

在 Live Timing 中按 S1/S2/S3 实时检测省油状态
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
from collections import deque
import statistics
from enum import Enum


class SectorType(Enum):
    """Sector 类型"""
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"


@dataclass
class SectorThrottleHistory:
    """单个 Sector 的油门历史（动态滚动基线）"""
    sector: SectorType
    throttle_history: deque = field(default_factory=lambda: deque(maxlen=10))
    baseline: Optional[float] = None
    
    def update(self, throttle_percent: float):
        """更新油门数据"""
        self.throttle_history.append(throttle_percent)
        
        # 使用动态滚动基线（至少3圈数据）
        if len(self.throttle_history) >= 3:
            # 过滤异常值（进站圈等）- 排除过低的值
            filtered = [t for t in self.throttle_history if t > 0]
            if filtered:
                baseline_candidate = statistics.median(filtered)
                # 进一步过滤：排除明显低于基线70%的值（可能是进站圈）
                filtered_strict = [t for t in filtered if t > baseline_candidate * 0.7]
                if len(filtered_strict) >= 3:
                    self.baseline = statistics.median(filtered_strict)
                else:
                    self.baseline = statistics.median(filtered)
    
    def get_deviation(self, current: float) -> Optional[float]:
        """计算当前值与基线的偏差"""
        if self.baseline is None:
            return None
        return current - self.baseline
    
    def get_dynamic_baseline(self) -> Optional[float]:
        """获取当前的动态基线"""
        return self.baseline


@dataclass
class DriverSectorData:
    """车手的所有 Sector 数据"""
    driver_code: str
    s1_history: SectorThrottleHistory = field(default_factory=lambda: SectorThrottleHistory(SectorType.S1))
    s2_history: SectorThrottleHistory = field(default_factory=lambda: SectorThrottleHistory(SectorType.S2))
    s3_history: SectorThrottleHistory = field(default_factory=lambda: SectorThrottleHistory(SectorType.S3))
    
    def get_sector_history(self, sector: SectorType) -> SectorThrottleHistory:
        """获取指定 Sector 的历史"""
        if sector == SectorType.S1:
            return self.s1_history
        elif sector == SectorType.S2:
            return self.s2_history
        else:
            return self.s3_history


@dataclass
class SectorFuelSavingStatus:
    """单个 Sector 的省油状态"""
    sector: SectorType
    is_fuel_saving: bool
    confidence: str  # "HIGH", "MEDIUM", "LOW", "UNKNOWN"
    current_throttle: float
    baseline_throttle: Optional[float]
    deviation: Optional[float]
    lamp_color: str  # "🔴", "🟡", "🟢", "⚪"
    message: str
    
    def to_dict(self) -> dict:
        return {
            "sector": self.sector.value,
            "is_fuel_saving": self.is_fuel_saving,
            "confidence": self.confidence,
            "current": round(self.current_throttle, 1),
            "baseline": round(self.baseline_throttle, 1) if self.baseline_throttle else None,
            "deviation": round(self.deviation, 1) if self.deviation else None,
            "lamp": self.lamp_color,
            "message": self.message
        }


@dataclass
class DriverFuelSavingStatus:
    """车手整体省油状态（包含所有 Sector）"""
    driver_code: str
    s1_status: SectorFuelSavingStatus
    s2_status: SectorFuelSavingStatus
    s3_status: SectorFuelSavingStatus
    overall_is_fuel_saving: bool
    fuel_saving_sectors: List[str]  # 正在省油的 Sector 列表
    
    def to_display_string(self) -> str:
        """转换为显示字符串"""
        status_line = f"{self.driver_code}: "
        status_line += f"S1{self.s1_status.lamp_color} "
        status_line += f"S2{self.s2_status.lamp_color} "
        status_line += f"S3{self.s3_status.lamp_color}"
        
        if self.overall_is_fuel_saving:
            status_line += f" | 省油中: {', '.join(self.fuel_saving_sectors)}"
        
        return status_line


class LiveSectorFuelSavingDetector:
    """
    实时 Sector 级别省油检测器
    
    检测逻辑：
    1. 每个车手的 S1/S2/S3 分别维护历史基线
    2. 实时接收当前 Sector 的油门数据
    3. 与该 Sector 的历史基线对比
    4. 立即显示灯号：🔴省油 🟢正常 🟡可能省油 ⚪数据不足
    """
    
    def __init__(
        self,
        threshold_high: float = -5.0,      # 高置信度阈值
        threshold_medium: float = -3.0,    # 中等置信度阈值
        threshold_low: float = -1.5,       # 低置信度阈值
        min_laps_for_baseline: int = 3     # 建立基线所需圈数
    ):
        """
        初始化检测器
        
        Args:
            threshold_high: 高置信度阈值（-5% 以下）
            threshold_medium: 中等置信度阈值（-3% 到 -5%）
            threshold_low: 低置信度阈值（-1.5% 到 -3%）
            min_laps_for_baseline: 建立基线所需最少圈数
        """
        self.threshold_high = threshold_high
        self.threshold_medium = threshold_medium
        self.threshold_low = threshold_low
        self.min_laps_for_baseline = min_laps_for_baseline
        
        # 存储每个车手的 Sector 数据
        self.drivers_data: Dict[str, DriverSectorData] = {}
    
    def update_sector_data(
        self,
        driver_code: str,
        sector: SectorType,
        throttle_percent: float,
        is_yellow_flag: bool = False,
        is_safety_car: bool = False
    ):
        """
        更新车手某个 Sector 的油门数据（用于建立历史基线）
        
        Args:
            driver_code: 车手代码
            sector: Sector 类型 (S1/S2/S3)
            throttle_percent: 该 Sector 的油门使用率
            is_yellow_flag: 是否有黄旗
            is_safety_car: 是否有安全车
        """
        # 跳过异常情况
        if is_yellow_flag or is_safety_car:
            return
        
        # 初始化车手数据
        if driver_code not in self.drivers_data:
            self.drivers_data[driver_code] = DriverSectorData(driver_code)
        
        # 更新对应 Sector 的历史
        sector_history = self.drivers_data[driver_code].get_sector_history(sector)
        sector_history.update(throttle_percent)
    
    def detect_sector_fuel_saving(
        self,
        driver_code: str,
        sector: SectorType,
        current_throttle: float
    ) -> SectorFuelSavingStatus:
        """
        检测单个 Sector 的实时省油状态
        
        Args:
            driver_code: 车手代码
            sector: Sector 类型
            current_throttle: 当前 Sector 的油门使用率
        
        Returns:
            SectorFuelSavingStatus 对象
        """
        # 检查是否有历史数据
        if driver_code not in self.drivers_data:
            return SectorFuelSavingStatus(
                sector=sector,
                is_fuel_saving=False,
                confidence="UNKNOWN",
                current_throttle=current_throttle,
                baseline_throttle=None,
                deviation=None,
                lamp_color="⚪",
                message="数据不足"
            )
        
        sector_history = self.drivers_data[driver_code].get_sector_history(sector)
        
        # 检查基线是否建立
        if sector_history.baseline is None:
            return SectorFuelSavingStatus(
                sector=sector,
                is_fuel_saving=False,
                confidence="UNKNOWN",
                current_throttle=current_throttle,
                baseline_throttle=None,
                deviation=None,
                lamp_color="⚪",
                message=f"建立基线中 ({len(sector_history.throttle_history)}/{self.min_laps_for_baseline})"
            )
        
        # 计算偏差
        deviation = sector_history.get_deviation(current_throttle)
        
        # 判断省油状态
        if deviation <= self.threshold_high:
            # 高置信度省油 🔴
            return SectorFuelSavingStatus(
                sector=sector,
                is_fuel_saving=True,
                confidence="HIGH",
                current_throttle=current_throttle,
                baseline_throttle=sector_history.baseline,
                deviation=deviation,
                lamp_color="🔴",
                message=f"省油 {abs(deviation):.1f}%"
            )
        
        elif deviation <= self.threshold_medium:
            # 中等置信度省油 🔴
            return SectorFuelSavingStatus(
                sector=sector,
                is_fuel_saving=True,
                confidence="MEDIUM",
                current_throttle=current_throttle,
                baseline_throttle=sector_history.baseline,
                deviation=deviation,
                lamp_color="🔴",
                message=f"可能省油 {abs(deviation):.1f}%"
            )
        
        elif deviation <= self.threshold_low:
            # 低置信度异常 🟡
            return SectorFuelSavingStatus(
                sector=sector,
                is_fuel_saving=False,
                confidence="LOW",
                current_throttle=current_throttle,
                baseline_throttle=sector_history.baseline,
                deviation=deviation,
                lamp_color="🟡",
                message=f"略低 {abs(deviation):.1f}%"
            )
        
        else:
            # 正常 🟢
            return SectorFuelSavingStatus(
                sector=sector,
                is_fuel_saving=False,
                confidence="NORMAL",
                current_throttle=current_throttle,
                baseline_throttle=sector_history.baseline,
                deviation=deviation,
                lamp_color="🟢",
                message="正常"
            )
    
    def detect_driver_fuel_saving(
        self,
        driver_code: str,
        s1_throttle: float,
        s2_throttle: float,
        s3_throttle: float
    ) -> DriverFuelSavingStatus:
        """
        检测车手整体省油状态（所有 Sector）
        
        Args:
            driver_code: 车手代码
            s1_throttle: S1 油门使用率
            s2_throttle: S2 油门使用率
            s3_throttle: S3 油门使用率
        
        Returns:
            DriverFuelSavingStatus 对象
        """
        s1_status = self.detect_sector_fuel_saving(driver_code, SectorType.S1, s1_throttle)
        s2_status = self.detect_sector_fuel_saving(driver_code, SectorType.S2, s2_throttle)
        s3_status = self.detect_sector_fuel_saving(driver_code, SectorType.S3, s3_throttle)
        
        # 判断整体是否省油
        fuel_saving_sectors = []
        if s1_status.is_fuel_saving:
            fuel_saving_sectors.append("S1")
        if s2_status.is_fuel_saving:
            fuel_saving_sectors.append("S2")
        if s3_status.is_fuel_saving:
            fuel_saving_sectors.append("S3")
        
        overall_is_fuel_saving = len(fuel_saving_sectors) > 0
        
        return DriverFuelSavingStatus(
            driver_code=driver_code,
            s1_status=s1_status,
            s2_status=s2_status,
            s3_status=s3_status,
            overall_is_fuel_saving=overall_is_fuel_saving,
            fuel_saving_sectors=fuel_saving_sectors
        )
    
    def reset_driver(self, driver_code: str):
        """重置车手数据"""
        if driver_code in self.drivers_data:
            del self.drivers_data[driver_code]
    
    def reset_all(self):
        """重置所有数据"""
        self.drivers_data.clear()


# ==================== 使用示例 ====================

def example_live_timing_simulation():
    """模拟 Live Timing 场景"""
    
    detector = LiveSectorFuelSavingDetector(
        threshold_high=-5.0,
        threshold_medium=-3.0,
        threshold_low=-1.5,
        min_laps_for_baseline=3
    )
    
    print("=" * 100)
    print("Live Timing - Sector 级别实时省油检测模拟")
    print("=" * 100)
    print()
    
    # 模拟 VER 的数据（正常 → 省油）
    ver_laps = [
        # Lap 1-3: 正常圈（建立基线）
        {"lap": 1, "s1": 55.0, "s2": 54.5, "s3": 53.0},
        {"lap": 2, "s1": 54.5, "s2": 55.0, "s3": 53.5},
        {"lap": 3, "s1": 55.5, "s2": 54.0, "s3": 53.0},
        # Lap 4-5: 开始省油
        {"lap": 4, "s1": 54.0, "s2": 50.0, "s3": 49.0},  # S2/S3 省油
        {"lap": 5, "s1": 53.0, "s2": 48.5, "s3": 48.0},  # S1/S2/S3 都省油
    ]
    
    for lap_data in ver_laps:
        lap_num = lap_data["lap"]
        
        print(f"\n{'='*100}")
        print(f"Lap {lap_num} - VER 实时数据")
        print(f"{'='*100}")
        
        # 先更新历史（用于建立基线）
        if lap_num <= 3:
            detector.update_sector_data("VER", SectorType.S1, lap_data["s1"])
            detector.update_sector_data("VER", SectorType.S2, lap_data["s2"])
            detector.update_sector_data("VER", SectorType.S3, lap_data["s3"])
        
        # S1 完成时检测
        print(f"\n🏁 S1 完成 (油门: {lap_data['s1']:.1f}%)")
        s1_status = detector.detect_sector_fuel_saving("VER", SectorType.S1, lap_data["s1"])
        print(f"   {s1_status.lamp_color} {s1_status.message}")
        if s1_status.baseline_throttle:
            print(f"   基线: {s1_status.baseline_throttle:.1f}%, 偏差: {s1_status.deviation:+.1f}%")
        
        # S2 完成时检测
        print(f"\n🏁 S2 完成 (油门: {lap_data['s2']:.1f}%)")
        s2_status = detector.detect_sector_fuel_saving("VER", SectorType.S2, lap_data["s2"])
        print(f"   {s2_status.lamp_color} {s2_status.message}")
        if s2_status.baseline_throttle:
            print(f"   基线: {s2_status.baseline_throttle:.1f}%, 偏差: {s2_status.deviation:+.1f}%")
        
        # S3 完成时检测（整圈结束）
        print(f"\n🏁 S3 完成 (油门: {lap_data['s3']:.1f}%)")
        s3_status = detector.detect_sector_fuel_saving("VER", SectorType.S3, lap_data["s3"])
        print(f"   {s3_status.lamp_color} {s3_status.message}")
        if s3_status.baseline_throttle:
            print(f"   基线: {s3_status.baseline_throttle:.1f}%, 偏差: {s3_status.deviation:+.1f}%")
        
        # 整圈状态
        driver_status = detector.detect_driver_fuel_saving(
            "VER", lap_data["s1"], lap_data["s2"], lap_data["s3"]
        )
        print(f"\n📊 整圈状态: {driver_status.to_display_string()}")
    
    print("\n\n" + "=" * 100)
    print("多车手实时对比")
    print("=" * 100)
    
    # 模拟3个车手当前圈的 Sector 数据
    current_lap_data = {
        "VER": {"s1": 53.0, "s2": 48.5, "s3": 48.0},  # 省油
        "NOR": {"s1": 51.5, "s2": 51.0, "s3": 51.5},  # 正常
        "PIA": {"s1": 52.0, "s2": 52.5, "s3": 47.0},  # S3 省油
    }
    
    # 先建立其他车手的基线
    detector.update_sector_data("NOR", SectorType.S1, 51.5)
    detector.update_sector_data("NOR", SectorType.S2, 51.0)
    detector.update_sector_data("NOR", SectorType.S3, 51.5)
    
    detector.update_sector_data("PIA", SectorType.S1, 52.5)
    detector.update_sector_data("PIA", SectorType.S2, 52.0)
    detector.update_sector_data("PIA", SectorType.S3, 52.5)
    
    for i in range(2):
        for driver in ["NOR", "PIA"]:
            detector.update_sector_data(driver, SectorType.S1, current_lap_data[driver]["s1"])
            detector.update_sector_data(driver, SectorType.S2, current_lap_data[driver]["s2"])
            detector.update_sector_data(driver, SectorType.S3, current_lap_data[driver]["s3"])
    
    # 显示所有车手状态
    print("\n当前圈实时状态:")
    print("-" * 100)
    
    for driver, data in current_lap_data.items():
        status = detector.detect_driver_fuel_saving(driver, data["s1"], data["s2"], data["s3"])
        print(status.to_display_string())
        
        if status.overall_is_fuel_saving:
            print(f"  └─ ⚠️ 检测到省油行为")
            if status.s1_status.is_fuel_saving:
                print(f"     S1: {status.s1_status.current_throttle:.1f}% (基线 {status.s1_status.baseline_throttle:.1f}%)")
            if status.s2_status.is_fuel_saving:
                print(f"     S2: {status.s2_status.current_throttle:.1f}% (基线 {status.s2_status.baseline_throttle:.1f}%)")
            if status.s3_status.is_fuel_saving:
                print(f"     S3: {status.s3_status.current_throttle:.1f}% (基线 {status.s3_status.baseline_throttle:.1f}%)")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    example_live_timing_simulation()
