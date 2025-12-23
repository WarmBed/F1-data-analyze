"""
F125 車輛性能綜合分析 - 使用範例

本腳本展示如何使用 F125 功能進行車輛性能分析
"""

from CLI_modules.cli.analyzer.f125_vehicle_performance import run_vehicle_performance_analysis
import json


def example_1_basic_usage():
    """範例 1: 基本使用方式"""
    print("\n" + "="*80)
    print("  範例 1: 基本使用 - 2025 Abu Dhabi FP2")
    print("="*80)

    result = run_vehicle_performance_analysis(
        year=2025,
        race="Abu Dhabi",
        session="FP2"  # 建議使用 FP2，資料較完整
    )

    if result['success']:
        print(f"\n[SUCCESS] 分析完成")
        print(f"賽道: {result['track_info']['circuit_name']}")
        print(f"類型: {result['track_info']['track_type']}")
        print(f"分析車手數: {result['summary']['total_drivers']}")
    else:
        print(f"\n[ERROR] {result['message']}")


def example_2_top_performers():
    """範例 2: 查看最佳表現車手"""
    print("\n" + "="*80)
    print("  範例 2: 最佳表現車手分析")
    print("="*80)

    result = run_vehicle_performance_analysis(
        year=2025,
        race="Abu Dhabi",
        session="R"  # 使用正賽資料
    )

    if not result['success']:
        print(f"[ERROR] {result['message']}")
        return

    print(f"\n賽道類型: {result['track_info']['track_type']}\n")
    print("前 5 名最適合的車手:")
    print("-" * 60)

    # 排序所有車手（按適應性分數）
    sorted_drivers = sorted(
        result['driver_results'],
        key=lambda x: x['suitability_score'],
        reverse=True
    )

    for idx, driver in enumerate(sorted_drivers[:5], 1):
        print(f"{idx}. {driver['driver']:<5} | "
              f"設定: {driver['inferred_setup']:<18} | "
              f"適應性: {driver['suitability_score']:.1f}/10 | "
              f"信心: {driver['confidence']}")


def example_3_setup_analysis():
    """範例 3: 設定分布分析"""
    print("\n" + "="*80)
    print("  範例 3: 車輛設定分布分析")
    print("="*80)

    result = run_vehicle_performance_analysis(
        year=2025,
        race="Abu Dhabi",
        session="R"
    )

    if not result['success']:
        print(f"[ERROR] {result['message']}")
        return

    print(f"\n賽道: {result['track_info']['circuit_name']} ({result['track_info']['track_type']})")
    print(f"速度分布: 高速 {result['track_info']['speed_distribution']['high_speed_percentage']:.1f}% | "
          f"中速 {result['track_info']['speed_distribution']['mid_speed_percentage']:.1f}% | "
          f"低速 {result['track_info']['speed_distribution']['low_speed_percentage']:.1f}%\n")

    print("設定分布:")
    for setup, count in result['summary']['setup_distribution'].items():
        percentage = count / result['summary']['total_drivers'] * 100
        print(f"  {setup:<18}: {count} 人 ({percentage:.1f}%)")

    # 分組顯示
    print("\n各設定車手列表:")
    for setup_type in ["Low Downforce", "Balanced", "High Downforce"]:
        drivers = [d for d in result['driver_results'] if d['inferred_setup'] == setup_type]
        if drivers:
            print(f"\n  [{setup_type}]")
            for d in drivers:
                print(f"    {d['driver']}: 適應性 {d['suitability_score']:.1f}/10")


def example_4_strategy_insights():
    """範例 4: 策略洞察（Sitting Duck 分析）"""
    print("\n" + "="*80)
    print("  範例 4: 策略風險分析 (Sitting Duck Effect)")
    print("="*80)

    result = run_vehicle_performance_analysis(
        year=2025,
        race="Abu Dhabi",
        session="R"
    )

    if not result['success']:
        print(f"[ERROR] {result['message']}")
        return

    track_type = result['track_info']['track_type']
    print(f"\n賽道類型: {track_type}\n")

    if track_type == "High Speed Track":
        # 找出高下壓力設定的車手（容易被超車）
        high_df_drivers = [d for d in result['driver_results']
                          if d['inferred_setup'] == "High Downforce"]

        if high_df_drivers:
            print("[WARNING] 以下車手可能在直線上易受攻擊 (Sitting Duck):")
            print("-" * 70)
            for d in sorted(high_df_drivers, key=lambda x: x['metrics']['setup_bias'], reverse=True):
                print(f"  {d['driver']}: "
                      f"彎道排名 {d['metrics']['corner_rank_score']:.1f} vs "
                      f"直線排名 {d['metrics']['straight_rank_score']:.1f} "
                      f"(差距: {d['metrics']['setup_bias']:.1f})")

        # 找出低下壓力設定的車手（最佳匹配）
        low_df_drivers = [d for d in result['driver_results']
                         if d['inferred_setup'] == "Low Downforce"]

        if low_df_drivers:
            print("\n[ADVANTAGE] 以下車手設定最適合高速賽道:")
            print("-" * 70)
            for d in sorted(low_df_drivers, key=lambda x: x['suitability_score'], reverse=True):
                print(f"  {d['driver']}: "
                      f"適應性 {d['suitability_score']:.1f}/10, "
                      f"優勢分數 {d['metrics']['setup_bias']:.1f}")


def example_5_export_csv():
    """範例 5: 導出 CSV 格式"""
    print("\n" + "="*80)
    print("  範例 5: 導出分析結果為 CSV")
    print("="*80)

    result = run_vehicle_performance_analysis(
        year=2025,
        race="Abu Dhabi",
        session="R"
    )

    if not result['success']:
        print(f"[ERROR] {result['message']}")
        return

    # 生成 CSV 內容
    csv_lines = []
    csv_lines.append("Driver,Setup,Confidence,Suitability,Corner_Rank,Straight_Rank,Bias,Brake_CV")

    for d in result['driver_results']:
        csv_lines.append(
            f"{d['driver']},"
            f"{d['inferred_setup']},"
            f"{d['confidence']},"
            f"{d['suitability_score']:.1f},"
            f"{d['metrics']['corner_rank_score']:.2f},"
            f"{d['metrics']['straight_rank_score']:.2f},"
            f"{d['metrics']['setup_bias']:.2f},"
            f"{d['metrics']['brake_cv']:.2f}"
        )

    csv_content = "\n".join(csv_lines)

    # 儲存檔案
    output_file = f"f125_analysis_{result['year']}_{result['race']}_{result['session']}.csv"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(csv_content)

    print(f"\n[SAVED] CSV 已儲存至: {output_file}")
    print(f"總計 {len(result['driver_results'])} 筆資料")


def example_6_compare_sessions():
    """範例 6: 比較不同會話（FP2 vs Race）"""
    print("\n" + "="*80)
    print("  範例 6: 比較 FP2 與正賽設定差異")
    print("="*80)

    # 注意: 此範例需要 FP2 資料存在
    result_fp2 = run_vehicle_performance_analysis(
        year=2025,
        race="Abu Dhabi",
        session="FP2"
    )

    result_race = run_vehicle_performance_analysis(
        year=2025,
        race="Abu Dhabi",
        session="R"
    )

    if not result_fp2['success'] or not result_race['success']:
        print("[ERROR] 需要 FP2 和 Race 兩場資料才能比較")
        return

    print("\nFP2 設定分布:")
    for setup, count in result_fp2['summary']['setup_distribution'].items():
        pct = count / result_fp2['summary']['total_drivers'] * 100
        print(f"  {setup:<18}: {count} 人 ({pct:.1f}%)")

    print("\n正賽設定分布:")
    for setup, count in result_race['summary']['setup_distribution'].items():
        pct = count / result_race['summary']['total_drivers'] * 100
        print(f"  {setup:<18}: {count} 人 ({pct:.1f}%)")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("  F125 車輛性能綜合分析 - 使用範例集")
    print("="*80)

    # 執行所有範例
    examples = [
        example_1_basic_usage,
        example_2_top_performers,
        example_3_setup_analysis,
        example_4_strategy_insights,
        example_5_export_csv,
        # example_6_compare_sessions,  # 需要 FP2 資料，預設註解
    ]

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n[ERROR] {example_func.__name__} 執行失敗: {e}")
            import traceback
            traceback.print_exc()

    print("\n\n" + "="*80)
    print("  所有範例執行完成")
    print("="*80 + "\n")
