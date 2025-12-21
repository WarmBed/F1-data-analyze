"""
測試 Function 15 多年度超車統計分析功能

測試場景：
1. 執行 2022-2025 日本站多年度分析
2. 驗證 JSON 輸出結構
3. 檢查多年度摘要數據
"""

import subprocess
import os
import json
import glob
from datetime import datetime

def test_multi_year_overtaking():
    """測試多年度超車統計分析"""
    
    print("=" * 80)
    print("🧪 Function 15 多年度超車統計分析測試")
    print("=" * 80)
    
    # 測試命令
    cmd = [
        "python",
        "f1_analysis_modular_main.py",
        "-f", "15",
        "--start-year", "2022",
        "--end-year", "2025",
        "-r", "Japan",
        "-s", "R"
    ]
    
    print("\n📝 執行命令：")
    print(" ".join(cmd))
    print()
    
    # 執行分析
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5 分鐘超時
        )
        
        print("=" * 80)
        print("📊 CLI 輸出：")
        print("=" * 80)
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ 錯誤輸出：")
            print(result.stderr)
        
        # 查找生成的 JSON 檔案
        json_pattern = "json/multi_year_overtaking_Japan_2022-2025_*.json"
        json_files = glob.glob(json_pattern)
        
        if json_files:
            latest_json = max(json_files, key=os.path.getctime)
            print("\n" + "=" * 80)
            print(f"✅ 找到 JSON 檔案：{latest_json}")
            print("=" * 80)
            
            # 讀取並驗證 JSON
            with open(latest_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print("\n📋 JSON 結構驗證：")
            print("-" * 80)
            
            # 驗證 analysis_info
            if 'analysis_info' in data:
                info = data['analysis_info']
                print(f"✅ analysis_info 存在")
                print(f"   - function_id: {info.get('function_id')}")
                print(f"   - analysis_type: {info.get('analysis_type')}")
                print(f"   - start_year: {info.get('start_year')}")
                print(f"   - end_year: {info.get('end_year')}")
                print(f"   - total_years: {info.get('total_years')}")
            else:
                print("❌ analysis_info 缺失")
            
            # 驗證 yearly_statistics
            if 'yearly_statistics' in data:
                yearly = data['yearly_statistics']
                print(f"\n✅ yearly_statistics 存在")
                print(f"   - 年份數量: {len(yearly)}")
                
                for year_data in yearly:
                    year = year_data.get('year')
                    total_changes = year_data.get('total_position_changes', 0)
                    total_drivers = year_data.get('total_drivers', 0)
                    print(f"   - {year}: {total_changes} 次名次變更 ({total_drivers} 位車手)")
            else:
                print("❌ yearly_statistics 缺失")
            
            # 驗證 multi_year_summary
            if 'multi_year_summary' in data:
                summary = data['multi_year_summary']
                print(f"\n✅ multi_year_summary 存在")
                print(f"   - total_years_analyzed: {summary.get('total_years_analyzed')}")
                print(f"   - average_position_changes_per_year: {summary.get('average_position_changes_per_year'):.2f}")
                
                if 'most_active_year' in summary:
                    most_active = summary['most_active_year']
                    print(f"   - 最激烈年份: {most_active['year']} ({most_active['total_position_changes']} 次)")
                
                if 'least_active_year' in summary:
                    least_active = summary['least_active_year']
                    print(f"   - 最平靜年份: {least_active['year']} ({least_active['total_position_changes']} 次)")
                
                if 'year_by_year_changes' in summary:
                    print(f"\n   📈 年度趨勢：")
                    for item in summary['year_by_year_changes']:
                        bar = '█' * (item['position_changes'] // 10)
                        print(f"      {item['year']}: {bar} {item['position_changes']} 次")
            else:
                print("❌ multi_year_summary 缺失")
            
            print("\n" + "=" * 80)
            print("🎉 測試完成！")
            print("=" * 80)
            
        else:
            print("\n❌ 找不到生成的 JSON 檔案")
            print(f"搜索模式：{json_pattern}")
    
    except subprocess.TimeoutExpired:
        print("\n❌ 命令執行超時（超過 5 分鐘）")
    except Exception as e:
        print(f"\n❌ 測試失敗：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_multi_year_overtaking()
