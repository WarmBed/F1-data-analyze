"""
快速應用雙圈比較模式到其他遙測模組

此腳本用於將 Speed Analysis 的雙圈比較邏輯應用到其他遙測模組。

使用方法:
    python apply_dual_lap_mode.py --module throttle
    python apply_dual_lap_mode.py --module rpm
    python apply_dual_lap_mode.py --all
"""

import argparse
import re
from pathlib import Path

# 模組映射
MODULE_MAPPING = {
    'throttle': {
        'name': 'Throttle Analysis',
        'file': 'modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py',
        'data_type': 'throttle',
        'set_method': 'set_throttle_data',
        'update_method': 'update_throttle_data'
    },
    'rpm': {
        'name': 'RPM Analysis',
        'file': 'modules/gui/lap_analysis/rpm_analysis/rpm_analysis_chart_widget.py',
        'data_type': 'rpm',
        'set_method': 'set_rpm_data',
        'update_method': 'update_rpm_data'
    },
    'brake': {
        'name': 'Brake Analysis',
        'file': 'modules/gui/lap_analysis/brake_analysis/brake_analysis_chart_widget.py',
        'data_type': 'brake',
        'set_method': 'set_brake_data',
        'update_method': 'update_brake_data'
    },
    'gear': {
        'name': 'Gear Analysis',
        'file': 'modules/gui/lap_analysis/gear_analysis/gear_analysis_chart_widget.py',
        'data_type': 'gear',
        'set_method': 'set_gear_data',
        'update_method': 'update_gear_data'
    }
}


def show_modification_guide(module_key):
    """顯示修改指南"""
    module = MODULE_MAPPING[module_key]
    
    print(f"\n{'=' * 80}")
    print(f"📋 {module['name']} 雙圈比較模式實施指南")
    print(f"{'=' * 80}\n")
    
    print(f"📂 目標檔案: {module['file']}\n")
    
    print("🔧 需要修改的方法:\n")
    
    # 修改 1: set_*_data() 方法簽名
    print(f"1️⃣ 修改 {module['set_method']}() 方法簽名")
    print("-" * 80)
    print("在方法參數中新增 lap1 和 lap2:")
    print(f"""
def {module['set_method']}(self, distance: List[float], 
                  driver1_{module['data_type']}: List[float], 
                  driver2_{module['data_type']}: List[float],
                  driver1_name: str = "Driver 1", 
                  driver2_name: str = "Driver 2", 
                  sectors: List[Dict] = None,
                  lap1: int = None,  # 🆕 新增
                  lap2: int = None   # 🆕 新增
                 ):
    """)
    
    # 修改 2: 判斷邏輯
    print("\n2️⃣ 修改單/雙車手模式判斷邏輯")
    print("-" * 80)
    print("替換原本的判斷邏輯:")
    print("""
# 🆕 雙圈比較模式：判斷是否為同車手不同圈數比較
is_dual_lap_mode = False
if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
    # 同車手不同圈數 → 雙圈比較模式
    is_dual_lap_mode = True
    self.driver1_name = f"{driver1_name} - 第{lap1}圈"
    self.driver2_name = f"{driver2_name} - 第{lap2}圈"
    print(f"[{module['data_type'].upper()}_CHART] 🔄 雙圈比較模式: {{self.driver1_name}} vs {{self.driver2_name}}")
else:
    # 正常模式：直接使用車手名稱
    self.driver1_name = driver1_name
    self.driver2_name = driver2_name

# 判斷單車手模式
if not driver2_{module['data_type']} or driver2_name == "":
    self.is_single_driver = True
elif driver1_name == driver2_name:
    if lap1 is not None and lap2 is not None and lap1 != lap2:
        # 同車手不同圈數 → 雙圈比較模式
        self.is_single_driver = False
        print(f"[{module['data_type'].upper()}_CHART] 🔍 雙圈比較模式（同車手不同圈數）")
    else:
        # 同車手相同圈數或無圈數信息 → 單車手模式
        self.is_single_driver = True
        print(f"[{module['data_type'].upper()}_CHART] 🔍 單車手模式（同車手相同圈數）")
else:
    # 不同車手 → 雙車手比較模式
    self.is_single_driver = False
    """)
    
    # 修改 3: update_*_data() 方法
    print(f"\n3️⃣ 修改 {module['update_method']}() 方法")
    print("-" * 80)
    print("在提取車手信息時，同時提取圈數:")
    print("""
# 提取圈數信息
lap1 = None
lap2 = None
if len(drivers) >= 2:
    driver1_name = drivers[0].get('code', driver1_name)
    driver2_name = drivers[1].get('code', driver2_name)
    lap1 = drivers[0].get('lap_number')  # 🆕 新增
    lap2 = drivers[1].get('lap_number')  # 🆕 新增
    """)
    
    print("\n在判斷邏輯中加入雙圈比較模式:")
    print("""
# 🆕 雙圈比較模式判斷邏輯
is_single_driver_mode = False
is_dual_lap_mode = False

if metadata.get('is_single_driver', False):
    is_single_driver_mode = True
elif driver1_name == driver2_name:
    if lap1 is not None and lap2 is not None and lap1 != lap2:
        # 🆕 同車手不同圈數 → 雙圈比較模式
        is_dual_lap_mode = True
        is_single_driver_mode = False
        print(f"[{module['data_type'].upper()}_CHART] 🔄 檢測到雙圈比較模式: {{driver1_name}} 第{{lap1}}圈 vs 第{{lap2}}圈")
    else:
        is_single_driver_mode = True
elif len(drivers) == 1:
    is_single_driver_mode = True

if is_single_driver_mode:
    driver2_{module['data_type']} = []
    driver2_name = ""
    lap2 = None
elif is_dual_lap_mode:
    self.is_single_driver = False
else:
    self.is_single_driver = False
    """)
    
    print(f"\n在調用 {module['set_method']}() 時傳遞圈數:")
    print(f"""
self.chart_widget.{module['set_method']}(
    distance=distance,
    driver1_{module['data_type']}=driver1_{module['data_type']},
    driver2_{module['data_type']}=driver2_{module['data_type']},
    driver1_name=driver1_name,
    driver2_name=driver2_name,
    sectors=sectors,
    lap1=lap1,  # 🆕 新增
    lap2=lap2   # 🆕 新增
)
    """)
    
    print("\n" + "=" * 80)
    print("✅ 修改完成後，請執行測試確認功能正常")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='應用雙圈比較模式到遙測分析模組',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 顯示 Throttle Analysis 的修改指南
  python apply_dual_lap_mode.py --module throttle
  
  # 顯示 RPM Analysis 的修改指南
  python apply_dual_lap_mode.py --module rpm
  
  # 顯示所有模組的修改指南
  python apply_dual_lap_mode.py --all
        """
    )
    
    parser.add_argument(
        '--module',
        choices=['throttle', 'rpm', 'brake', 'gear'],
        help='要修改的模組'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='顯示所有模組的修改指南'
    )
    
    args = parser.parse_args()
    
    if args.all:
        print("\n" + "=" * 80)
        print("📚 所有遙測模組雙圈比較模式實施指南")
        print("=" * 80)
        
        for module_key in MODULE_MAPPING.keys():
            show_modification_guide(module_key)
            input("\n按 Enter 繼續下一個模組...")
    elif args.module:
        show_modification_guide(args.module)
    else:
        parser.print_help()
        print("\n💡 提示: 請使用 --module 或 --all 參數")


if __name__ == "__main__":
    main()
