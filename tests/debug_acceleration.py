#!/usr/bin/env python3
"""調試加速數據計算失敗的原因"""

import sys
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_acceleration.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def debug_acceleration_calculation():
    """調試為什麼加速數據全是 0"""
    try:
        # 載入數據
        logger.info("Step 1: 載入 2025 Singapore 數據...")
        from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
        
        data_loader = CompatibleF1DataLoader()
        success = data_loader.load_race_data(2025, "Singapore", "R")
        
        if not success:
            logger.error("數據載入失敗")
            return False
        
        logger.info("✅ 數據載入成功")
        
        # 創建分析器
        logger.info("\nStep 2: 創建分析器...")
        from CLI_modules.cli.analyzer.all_drivers_straight_line_speed import AllDriversStraightLineSpeedAnalysis
        
        analyzer = AllDriversStraightLineSpeedAnalysis(
            data_loader,
            year=2025,
            race="Singapore",
            session="R"
        )
        
        logger.info("✅ 分析器創建成功")
        
        # 手動執行關鍵步驟
        logger.info("\nStep 3: 找最速圈...")
        result = analyzer._find_overall_fastest_lap()
        
        if not result:
            logger.error("❌ 找不到最速圈")
            return False
        
        driver, lap_obj = result
        logger.info(f"✅ 最速圈: {driver}")
        
        # 識別主直線段
        logger.info("\nStep 4: 識別主直線段...")
        reference_segment = analyzer._identify_main_straight_position(driver, lap_obj)
        
        if not reference_segment:
            logger.error("❌ 無法識別主直線段")
            return False
        
        logger.info(f"✅ 主直線段:")
        logger.info(f"   起點: {reference_segment['segment_distance_start']:.1f}m")
        logger.info(f"   終點: {reference_segment['segment_distance_end']:.1f}m")
        logger.info(f"   長度: {reference_segment['segment_length']:.1f}m")
        
        # 測試單個車手的加速計算
        logger.info("\nStep 5: 測試 HAM 的加速數據計算...")
        
        session = data_loader.session
        laps = session.laps
        
        # 獲取 HAM 的最速圈
        ham_laps = laps.pick_driver('HAM')
        if ham_laps.empty:
            logger.error("❌ 找不到 HAM 的圈速")
            return False
        
        valid_laps = ham_laps[ham_laps['LapTime'].notna()]
        if valid_laps.empty:
            logger.error("❌ HAM 沒有有效圈速")
            return False
        
        fastest_lap_idx = valid_laps['LapTime'].idxmin()
        fastest_lap = valid_laps.loc[fastest_lap_idx]
        lap_number = int(fastest_lap['LapNumber'])
        
        logger.info(f"HAM 最速圈: 第{lap_number}圈")
        
        # 獲取遙測數據
        ham_driver_laps = session.laps.pick_driver('HAM')
        ham_lap_obj = ham_driver_laps.pick_lap(lap_number)
        
        if ham_lap_obj is None:
            logger.error("❌ 無法獲取 HAM 的圈對象")
            return False
        
        # 獲取車輛數據
        car_data = analyzer._extract_car_data(ham_lap_obj)
        if car_data is None or car_data.empty:
            logger.error("❌ HAM 車輛數據為空")
            return False
        
        logger.info(f"✅ HAM 車輛數據: {len(car_data)} 個數據點")
        logger.info(f"   欄位: {car_data.columns.tolist()}")
        
        # 檢查 Distance 欄位
        if 'Distance' not in car_data.columns:
            logger.error("❌ 沒有 Distance 欄位！")
            return False
        
        logger.info(f"✅ Distance 欄位存在")
        logger.info(f"   Distance 範圍: {car_data['Distance'].min():.1f}m - {car_data['Distance'].max():.1f}m")
        
        # 測試速度查找
        logger.info("\nStep 6: 在位置範圍內找速度...")
        speed_result = analyzer._find_speed_in_position_range(
            car_data,
            reference_segment['segment_distance_start'],
            reference_segment['segment_distance_end']
        )
        
        if not speed_result:
            logger.error("❌ 找不到速度數據")
            return False
        
        logger.info(f"✅ 找到速度數據:")
        logger.info(f"   最高速度: {speed_result['max_speed']:.1f} km/h")
        logger.info(f"   可計算加速: {speed_result.get('can_calculate_acceleration', False)}")
        logger.info(f"   找到 100 km/h: {speed_result.get('speed_100_found', False)}")
        
        # 如果有加速數據，檢查詳細內容
        if 'acceleration_data' in speed_result and speed_result['acceleration_data']:
            acc_data = speed_result['acceleration_data']
            logger.info(f"\n✅ 加速數據存在:")
            logger.info(f"   起始速度: {acc_data.get('start_speed', 'N/A')} km/h")
            logger.info(f"   結束速度: {acc_data.get('end_speed', 'N/A')} km/h")
            logger.info(f"   時間差: {acc_data.get('time_seconds', 'N/A')}s")
            logger.info(f"   距離: {acc_data.get('distance_m', 'N/A')}m")
            logger.info(f"   平均加速度: {acc_data.get('avg_acceleration_ms2', 'N/A')} m/s²")
        else:
            logger.error("❌ 沒有加速數據！")
            logger.info("\n調試 _find_speed_in_position_range 的返回值:")
            logger.info(f"完整返回: {speed_result}")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ 調試過程中發生異常: {e}")
        return False

if __name__ == "__main__":
    logger.info("啟動加速數據調試...\n")
    
    success = debug_acceleration_calculation()
    
    if success:
        logger.info("\n✅ 調試完成")
    else:
        logger.error("\n❌ 調試失敗")
    
    sys.exit(0 if success else 1)
