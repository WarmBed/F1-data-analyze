"""
分析 TrackMap 的車手位置計算邏輯
診斷問題所在
"""
import sys
sys.path.insert(0, '.')

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource, LivePositionDataProcessor
from core.logger import get_logger


logger = get_logger(component="gui")

logger.info("=" * 70)
logger.info("TrackMap 車手位置計算邏輯分析")
logger.info("=" * 70)

data_source = LiveF1DataSource(
    year=2025,
    meeting="2025-04-06_Japanese_Grand_Prix",
    session="2025-04-06_Race"
)

logger.info("\n載入資料...")
data_source.load_all_data()

processor = LivePositionDataProcessor(data_source)
processor.process_and_align_data(downsample_factor=1)

snapshots = processor.get_aligned_snapshots()

if snapshots:
    # 選擇一個中段快照
    mid_snapshot = snapshots[len(snapshots)//2]
    
    logger.info(f"\n選擇快照: {mid_snapshot['race_time']}")
    logger.info("=" * 70)
    
    drivers = mid_snapshot['drivers']
    
    logger.info(f"\n車手數: {len(drivers)}")
    logger.info("\n前5位車手的原始資料:")
    logger.info(f"{'排名':>4} {'車手':>4} {'X':>8} {'Y':>8} {'速度':>8} {'圈數':>4} {'與領先差距':>12}")
    logger.info("-" * 70)
    
    sorted_drivers = sorted(
        drivers.items(),
        key=lambda x: x[1].get('position') if x[1].get('position') is not None else 999
    )
    
    for driver_num, driver_data in sorted_drivers[:5]:
        pos = driver_data.get('position', '?')
        x = driver_data.get('x', 0)
        y = driver_data.get('y', 0)
        speed = driver_data.get('speed', 0)
        lap = driver_data.get('lap', 0)
        gap = driver_data.get('gap_to_leader', 0)
        
        logger.info(f"{str(pos):>4} #{driver_num:>3} {x:>8} {y:>8} {speed:>7.0f} {lap:>4} {gap:>11.3f}s")
    
    logger.info("\n" + "=" * 70)
    logger.info("問題診斷")
    logger.info("=" * 70)
    
    logger.info("\n現在的車手位置計算邏輯:")
    logger.info("  ❌ 第1步: 估算領先者距離 (_estimate_leader_distance)")
    logger.info("      使用: frame_ratio 或 time_ratio × track_length")
    logger.info("      問題: 這是「估算」，不是真實位置！")
    logger.info("")
    logger.info("  ❌ 第2步: 估算其他車手距離 (_estimate_driver_distance)")
    logger.info("      使用: leader_distance - gap_laps × track_length - gap_seconds × speed")
    logger.info("      問題: 基於估算的領先者距離再次估算！")
    logger.info("")
    logger.info("  ❌ 第3步: 插值到賽道座標 (_interpolate_point)")
    logger.info("      使用: 根據「估算距離」在賽道上找對應的 X/Y")
    logger.info("      問題: 根本不使用 Position 資料中的真實 X/Y！")
    
    logger.info("\n" + "=" * 70)
    logger.info("根本問題")
    logger.info("=" * 70)
    
    logger.info("\n✗ 現在的邏輯:")
    logger.info("  Position 資料有真實的 X/Y 座標")
    logger.info("    ↓ (被忽略)")
    logger.info("  估算領先者在賽道上的距離")
    logger.info("    ↓")
    logger.info("  估算其他車手在賽道上的距離")
    logger.info("    ↓")
    logger.info("  插值到賽道座標")
    
    logger.info("\n✓ 應該的邏輯:")
    logger.info("  Position 資料有真實的 X/Y 座標")
    logger.info("    ↓ (直接使用！)")
    logger.info("  在 trackmap 上顯示 X/Y")
    
    logger.info("\n" + "=" * 70)
    logger.info("解決方案")
    logger.info("=" * 70)
    
    logger.info("\n直接使用 Position 資料中的 X/Y 座標！")
    logger.info("\n修改 TrackMapWidget.update_driver_positions:")
    logger.info("  1. 接收 drivers_data，其中每位車手已經有 x, y 座標")
    logger.info("  2. 直接使用這些座標")
    logger.info("  3. 不需要任何估算或插值")
    
    logger.info("\n範例:")
    logger.info(
        "  車手 #1: X={}, Y={} <- 直接來自 Position 資料".format(
            sorted_drivers[0][1].get('x'),
            sorted_drivers[0][1].get('y')
        )
    )
