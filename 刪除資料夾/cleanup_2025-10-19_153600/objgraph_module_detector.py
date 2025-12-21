#!/usr/bin/env python3
"""
簡化版 objgraph 模組檢測器
========================

快速檢測 objgraph 報告中開啟的 F1T 分析模組

使用方式：
    python objgraph_module_detector.py objgraph_report_20251015_165921.txt
"""

import sys
import re
from typing import Dict, List

def detect_f1t_modules(content: str) -> List[Dict]:
    """檢測 F1T 分析模組"""
    
    module_patterns = {
        'speed_analysis': ['SpeedAnalysisModule', 'SpeedDataManager', 'SpeedAnalysisChartWidget'],
        'brake_analysis': ['BrakeAnalysisModule', 'BrakeDataManager', 'BrakeAnalysisChartWidget'],
        'throttle_analysis': ['ThrottleAnalysisModule', 'ThrottleDataManager', 'ThrottleAnalysisChartWidget'],
        'gear_analysis': ['GearAnalysisModule', 'GearDataManager', 'GearAnalysisChartWidget'],
        'rpm_analysis': ['RPMAnalysisModule', 'RPMDataManager', 'RPMAnalysisChartWidget'],
        'acceleration_analysis': ['accelerationAnalysisModule', 'AccelerationDataManager', 'accelerationAnalysisChartWidget'],
        'speeddiff_analysis': ['SpeeddiffAnalysisModule', 'speeddiffDataManager', 'SpeeddiffAnalysisChartWidget'],
        'distancediff_analysis': ['distancediffAnalysisModule', 'distancediffDataManager', 'distancediffAnalysisChartWidget'],
        'timediff_analysis': ['timediffAnalysisModule', 'timediffDataManager', 'timediffAnalysisChartWidget']
    }
    
    display_names = {
        'speed_analysis': '🏎️ 速度分析',
        'brake_analysis': '🚩 煞車分析', 
        'throttle_analysis': '⚡ 油門分析',
        'gear_analysis': '⚙️ 檔位分析',
        'rpm_analysis': '🔄 轉速分析',
        'acceleration_analysis': '🚀 加速度分析',
        'speeddiff_analysis': '📈 速度差異分析',
        'distancediff_analysis': '📏 距離差異分析',
        'timediff_analysis': '⏱️ 時間差異分析'
    }
    
    detected_modules = []
    
    for module_name, class_patterns in module_patterns.items():
        found_classes = []
        total_objects = 0
        
        for pattern in class_patterns:
            # 尋找該類別的物件數量
            match = re.search(rf'↑\s*{pattern}\s+(\d+)\s*\(\+(\d+)\)', content)
            if match:
                count = int(match.group(1))
                increase = int(match.group(2))
                found_classes.append({
                    'class_name': pattern,
                    'count': count,
                    'increase': increase
                })
                total_objects += count
        
        if found_classes:
            status = 'fully_loaded' if len(found_classes) >= 3 else 'partially_loaded'
            detected_modules.append({
                'name': module_name,
                'display_name': display_names.get(module_name, module_name),
                'status': status,
                'classes': found_classes,
                'total_objects': total_objects
            })
    
    return sorted(detected_modules, key=lambda x: x['total_objects'], reverse=True)

def main():
    if len(sys.argv) != 2:
        print("使用方式: python objgraph_module_detector.py <report_file.txt>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modules = detect_f1t_modules(content)
        
        print("=" * 60)
        print("🔍 F1T 分析模組檢測結果")
        print("=" * 60)
        print(f"📊 檢測到的模組數量: {len(modules)}")
        print()
        
        if not modules:
            print("❌ 未檢測到任何 F1T 分析模組")
            return
        
        fully_loaded = [m for m in modules if m['status'] == 'fully_loaded']
        partially_loaded = [m for m in modules if m['status'] == 'partially_loaded']
        
        print(f"✅ 完全載入的模組: {len(fully_loaded)}")
        print(f"⚠️ 部分載入的模組: {len(partially_loaded)}")
        print()
        
        for i, module in enumerate(modules, 1):
            status_icon = "✅" if module['status'] == 'fully_loaded' else "⚠️"
            print(f"{i:2d}. {status_icon} {module['display_name']}")
            print(f"    模組名稱: {module['name']}")
            print(f"    物件總數: {module['total_objects']:,}")
            print(f"    檢測類別: {len(module['classes'])}")
            
            for cls in module['classes']:
                print(f"      └─ {cls['class_name']}: {cls['count']} (+{cls['increase']})")
            print()
        
        total_module_objects = sum(m['total_objects'] for m in modules)
        print(f"💾 所有檢測模組的物件總數: {total_module_objects:,}")
        
    except FileNotFoundError:
        print(f"❌ 檔案不存在: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 處理檔案時發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()