"""
F125 算法測試腳本

使用實際數據測試車輛性能分析算法的正確性

測試案例：
1. 2025 Abu Dhabi FP2（如果有數據）
2. 2024 Bahrain FP2（作為備選）
"""

import json
import os
from CLI_modules.cli.analyzer.f125_vehicle_performance import run_vehicle_performance_analysis

def print_section(title):
    """打印章節標題"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_f125_analysis():
    """測試 F125 分析"""

    print_section("F125 車輛性能分析測試")

    # 測試參數（使用正賽數據，因為有完整的 F120/F121/F122/F100）
    YEAR = 2025
    RACE = "Abu Dhabi"
    SESSION = "R"  # 使用正賽數據測試算法

    print(f"\n[INFO] 測試數據: {YEAR} {RACE} {SESSION}")
    print(f"目標：驗證動態權重系統與物理邏輯")

    # 執行分析
    print("\n[RUNNING] 執行分析...")
    result = run_vehicle_performance_analysis(
        year=YEAR,
        race=RACE,
        session=SESSION
    )

    # 檢查結果
    if not result.get('success'):
        print(f"\n[ERROR] 分析失敗: {result.get('message')}")
        if 'required_files' in result:
            print("\n缺少的檔案:")
            for name, path in result['required_files'].items():
                exists = "[OK]" if os.path.exists(path) else "[MISSING]"
                print(f"  {exists} {name}: {path}")
        return False

    # === 顯示結果 ===

    # 1. 賽道資訊
    print_section("賽道資訊")
    track_info = result['track_info']
    print(f"賽道: {track_info['circuit_name']} ({track_info['country']})")
    print(f"賽道類型: {track_info['track_type']}")

    speed_dist = track_info['speed_distribution']
    print(f"\n速度分布:")
    print(f"  - 低速區 (<120 km/h): {speed_dist['low_speed_percentage']:.1f}%")
    print(f"  - 中速區 (120-200 km/h): {speed_dist['mid_speed_percentage']:.1f}%")
    print(f"  - 高速區 (>200 km/h): {speed_dist['high_speed_percentage']:.1f}%")

    elev = track_info['elevation_profile']
    if elev['available']:
        print(f"\n高程數據:")
        print(f"  - 最低點: {elev['min_elevation']:.1f}m")
        print(f"  - 最高點: {elev['max_elevation']:.1f}m")
        print(f"  - 高低落差: {elev['elevation_change']:.1f}m")

    print(f"\n使用的權重:")
    corner_w = track_info['corner_weights_used']
    straight_w = track_info['straight_weights_used']
    print(f"  - 彎道: 高速={corner_w['high']}, 中速={corner_w['mid']}, 低速={corner_w['low']}")
    print(f"  - 直線: 極速={straight_w['speed']}, 加速={straight_w['accel']}")

    # 2. 統計摘要
    print_section("統計摘要")
    summary = result['summary']
    print(f"總車手數: {summary['total_drivers']}")
    print(f"\n設定分布:")
    for setup, count in summary['setup_distribution'].items():
        pct = count / summary['total_drivers'] * 100
        print(f"  - {setup}: {count} ({pct:.1f}%)")

    print(f"\n前 3 名最適合的車手:")
    for idx, driver_info in enumerate(summary['top_3_suited_drivers'], 1):
        print(f"  {idx}. {driver_info['driver']} - {driver_info['setup']} (適應性: {driver_info['suitability']}/10)")

    # 3. 詳細車手分析
    print_section("車手詳細分析")

    # 表頭
    print(f"{'車手':<8} {'設定':<18} {'信心':<8} {'適應性':<6} {'彎道排名':<8} {'直線排名':<8} {'優勢分數':<8}")
    print("-" * 80)

    # 顯示所有車手
    for driver_result in result['driver_results']:
        driver = driver_result['driver']
        setup = driver_result['inferred_setup']
        conf = driver_result['confidence']
        suit = driver_result['suitability_score']

        metrics = driver_result['metrics']
        corner = metrics['corner_rank_score']
        straight = metrics['straight_rank_score']
        bias = metrics['setup_bias']

        print(f"{driver:<8} {setup:<18} {conf:<8} {suit:<6.1f} {corner:<8.2f} {straight:<8.2f} {bias:<8.2f}")

    # 4. 重點案例分析
    print_section("重點案例分析")

    # 找出極端案例
    high_df_drivers = [r for r in result['driver_results'] if r['inferred_setup'] == "High Downforce"]
    low_df_drivers = [r for r in result['driver_results'] if r['inferred_setup'] == "Low Downforce"]

    if high_df_drivers:
        print("\n[HIGH DF] 高下壓力設定車手:")
        for r in high_df_drivers[:3]:
            print(f"\n  {r['driver']}:")
            print(f"    優勢分數: {r['metrics']['setup_bias']:.2f} (直線差 - 彎道好)")
            print(f"    適應性: {r['suitability_score']}/10")
            print(f"    評語: {r['verdict']}")

    if low_df_drivers:
        print("\n[LOW DF] 低下壓力設定車手:")
        for r in low_df_drivers[:3]:
            print(f"\n  {r['driver']}:")
            print(f"    優勢分數: {r['metrics']['setup_bias']:.2f} (直線好 - 彎道差)")
            print(f"    適應性: {r['suitability_score']}/10")
            print(f"    評語: {r['verdict']}")

    # 5. 物理邏輯驗證
    print_section("物理邏輯驗證")

    track_type = track_info['track_type']
    print(f"\n賽道類型: {track_type}")

    if track_type == "High Speed Track":
        print("\n[EXPECTED] 預期:")
        print("  - 低下壓力設定應該獲得高適應性分數 (9+)")
        print("  - 高下壓力設定應該獲得低適應性分數 (4-5)")

        # 檢查實際結果
        print("\n[RESULT] 實際結果:")
        if low_df_drivers:
            avg_suit = sum(r['suitability_score'] for r in low_df_drivers) / len(low_df_drivers)
            print(f"  - 低下壓力平均適應性: {avg_suit:.1f}/10")
        if high_df_drivers:
            avg_suit = sum(r['suitability_score'] for r in high_df_drivers) / len(high_df_drivers)
            print(f"  - 高下壓力平均適應性: {avg_suit:.1f}/10")

    elif track_type == "Low Speed Track":
        print("\n[EXPECTED] 預期:")
        print("  - 高下壓力設定應該獲得高適應性分數 (9+)")
        print("  - 低下壓力設定應該獲得低適應性分數 (3-4)")

        # 檢查實際結果
        print("\n[RESULT] 實際結果:")
        if high_df_drivers:
            avg_suit = sum(r['suitability_score'] for r in high_df_drivers) / len(high_df_drivers)
            print(f"  - 高下壓力平均適應性: {avg_suit:.1f}/10")
        if low_df_drivers:
            avg_suit = sum(r['suitability_score'] for r in low_df_drivers) / len(low_df_drivers)
            print(f"  - 低下壓力平均適應性: {avg_suit:.1f}/10")

    # 6. 儲存結果
    output_path = f"json/vehicle_performance_report_{YEAR}_{RACE}_{SESSION}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n\n[SAVED] 報告已儲存至: {output_path}")
    print("\n[SUCCESS] 測試完成！")

    return True

if __name__ == "__main__":
    try:
        success = test_f125_analysis()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] 測試中斷")
        exit(1)
    except Exception as e:
        print(f"\n\n[FAILED] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
