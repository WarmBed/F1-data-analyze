"""
測試功能 100: 歷年旗幟統計分析 (Japan 2022-2025)
"""
from CLI_modules.cli.analyzer.historical_flags_analysis import run_historical_flags_analysis_json

print("=" * 80)
print("測試功能 100: Japan (Suzuka) 2022-2025 歷年旗幟統計")
print("=" * 80)

result = run_historical_flags_analysis_json('Japan', 2022, 2025, 'R')

if result.get('success'):
    data = result['data']
    meta = data['metadata']
    trends = data['trends']
    
    print(f"\n✅ 分析成功！")
    print(f"\n賽道資訊:")
    print(f"  名稱: {meta['circuit_name']}")
    print(f"  國家: {meta['country']}")
    print(f"  分析年份: {meta['years_analyzed']}")
    print(f"  彎道數: {meta['corners_count']}")
    
    print(f"\n年度統計:")
    for year, stats in sorted(data['yearly_summary'].items()):
        print(f"  {year}: Y={stats['yellow_flags']} DY={stats['double_yellow_flags']} R={stats['red_flags']} SC={stats['safety_cars']} (總計 {stats['total_incidents']})")
    
    print(f"\n趨勢分析:")
    print(f"  總旗幟事件: {trends['total_flags_all_years']}")
    print(f"  平均每年: {trends['average_flags_per_year']}")
    print(f"  最危險彎道: {trends['most_dangerous_corner']}")
    print(f"  事故最多年份: {trends['highest_incident_year']}")
    print(f"  安全車出動: {trends['safety_car_deployments']}")
    
    print(f"\n最危險彎道 Top 5:")
    corner_analysis = data['corner_analysis']
    sorted_corners = sorted(corner_analysis.items(), 
                          key=lambda x: x[1]['total_flags'], 
                          reverse=True)
    
    for i, (corner_key, corner_data) in enumerate(sorted_corners[:5], 1):
        if corner_data['total_flags'] > 0:
            print(f"  {i}. {corner_key}: {corner_data['total_flags']:.2f} 次")
    
    print(f"\nJSON 檔案: {result.get('json_path')}")
    
else:
    print(f"\n❌ 分析失敗: {result.get('message')}")
