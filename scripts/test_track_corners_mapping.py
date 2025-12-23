"""
測試 Function 2 的官方彎道映射功能
"""
import sys
sys.path.insert(0, 'C:\\Users\\mike2\\OneDrive\\Code\\F1-data-analyze')

from CLI_modules.cli.core.base import DataLoader
from CLI_modules.cli.analyzer.track_position_analysis import run_track_position_analysis
import json

print("=== 測試 Function 2 官方彎道映射 ===\n")

# 初始化數據載入器
print("載入 2024 日本站正賽數據...")
data_loader = DataLoader(year=2024, race='Japan', session_type='R')

if data_loader is None or data_loader.session is None:
    print("❌ 數據載入失敗")
    sys.exit(1)

print("✅ 數據載入成功\n")

# 執行分析
print("執行賽道位置分析...")
result = run_track_position_analysis(data_loader, show_detailed_output=False)

if result and result.get('success'):
    data = result.get('data', {})
    
    # 檢查官方彎道資訊
    official_corners = data.get('official_corners', {})
    
    print("\n=== 官方彎道映射結果 ===\n")
    print(f"是否可用: {official_corners.get('available')}")
    print(f"彎道數量: {official_corners.get('count')}")
    
    if official_corners.get('available'):
        quality = official_corners.get('mapping_quality', {})
        print(f"\n映射品質:")
        print(f"  平均誤差: {quality.get('average_error_m')}m")
        print(f"  最大誤差: {quality.get('max_error_m')}m")
        print(f"  最小誤差: {quality.get('min_error_m')}m")
        
        print(f"\n前 5 個彎道:")
        corners = official_corners.get('corners', [])
        for corner in corners[:5]:
            print(f"  T{corner['number']:2d}: "
                  f"Distance={corner['mapped_distance']:7.1f}m, "
                  f"Angle={corner['angle']:7.1f}°, "
                  f"Error={corner['mapping_error']:5.1f}m")
        
        # 保存到測試檔案
        test_file = "test_json_output/test_track_analysis_with_corners.json"
        import os
        os.makedirs("test_json_output", exist_ok=True)
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 測試完成！結果已保存到: {test_file}")
    else:
        print("⚠️ 官方彎道資訊不可用")
else:
    print("❌ 分析失敗")
