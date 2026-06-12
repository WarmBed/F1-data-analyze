#!/usr/bin/env python3
"""
生成 NOR、VER、PLA 三位车手的油门使用率对比分析报告
"""

import json
from pathlib import Path
from typing import Dict, List

def analyze_driver_throttle_comparison():
    """分析指定车手的油门使用率趋势"""
    
    # 目标车手
    target_drivers = ['NOR', 'VER', 'PIA']
    
    # 读取数据
    json_file = Path("json/driver_throttle_ratio_2025_Abu Dhabi_R.json")
    
    if not json_file.exists():
        print(f"错误: 找不到文件 {json_file}")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取车手数据
    drivers_data = data['data']['analysis']['drivers']
    
    # 筛选目标车手
    selected_drivers = {}
    for driver in drivers_data:
        code = driver['driver_code']
        if code in target_drivers:
            selected_drivers[code] = driver
    
    # 生成 Markdown 报告
    output_file = Path("reports/Throttle_Comparison_NOR_VER_PLA_2025_Abu_Dhabi.md")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # 标题
        f.write("# 2025 Abu Dhabi GP - Throttle 95% 对比分析\n\n")
        f.write("## NOR (Norris) vs VER (Verstappen) vs PIA (Piastri)\n\n")
        f.write("---\n\n")
        
        # 元数据
        metadata = data['data']['metadata']
        f.write("## 📊 分析元数据\n\n")
        f.write(f"- **赛事**: {metadata['year']} {metadata['race']}\n")
        f.write(f"- **赛段**: {metadata['session']}\n")
        f.write(f"- **油门阈值**: {metadata['thresholds']['full_throttle'] * 100}%\n")
        f.write(f"- **分析时间**: {metadata['analysis_timestamp']}\n\n")
        f.write("---\n\n")
        
        # 车手摘要
        f.write("## 🏁 车手摘要\n\n")
        f.write("| 车手 | 车队 | 总圈数 | 平均 Throttle 95% | 最高 | 最低 |\n")
        f.write("|------|------|--------|-------------------|------|------|\n")
        
        driver_stats = {}
        for code in target_drivers:
            if code in selected_drivers:
                driver = selected_drivers[code]
                laps = driver['laps']
                
                # 计算统计数据（排除异常圈）
                valid_ratios = [lap['full_throttle_ratio'] * 100 
                               for lap in laps 
                               if lap['full_throttle_ratio'] is not None 
                               and lap['lap_time_seconds'] is not None
                               and lap['lap_time_seconds'] < 200]  # 排除进站圈
                
                if valid_ratios:
                    avg = sum(valid_ratios) / len(valid_ratios)
                    max_val = max(valid_ratios)
                    min_val = min(valid_ratios)
                else:
                    avg = max_val = min_val = 0
                
                driver_stats[code] = {
                    'team': driver['team'],
                    'total_laps': len(laps),
                    'avg': avg,
                    'max': max_val,
                    'min': min_val
                }
                
                f.write(f"| {code} | {driver['team']} | {len(laps)} | "
                       f"{avg:.2f}% | {max_val:.2f}% | {min_val:.2f}% |\n")
        
        f.write("\n---\n\n")
        
        # 逐圈详细数据
        f.write("## 📈 逐圈详细数据\n\n")
        
        for code in target_drivers:
            if code not in selected_drivers:
                continue
            
            driver = selected_drivers[code]
            f.write(f"### {code} - {driver['team']}\n\n")
            
            # 表头
            f.write("| Lap | Lap Time | Throttle 95% | Avg Throttle | Duration (s) | Compound | Tyre Life | Speed Avg |\n")
            f.write("|-----|----------|--------------|--------------|--------------|----------|-----------|----------|\n")
            
            laps = driver['laps']
            lap_data = []
            
            for lap in laps:
                lap_num = lap['lap_number']
                lap_time = lap.get('lap_time_seconds')
                throttle_95 = lap['full_throttle_ratio']
                avg_throttle = lap['average_throttle']
                duration = lap['full_throttle_duration_s']
                compound = lap.get('compound', 'N/A')
                tyre_life = lap.get('tyre_life', 'N/A')
                speed_avg = lap.get('speed_avg_kmh')
                
                # 格式化输出
                lap_time_str = f"{lap_time:.3f}s" if lap_time else "N/A"
                throttle_str = f"{throttle_95 * 100:.2f}%" if throttle_95 is not None else "N/A"
                avg_str = f"{avg_throttle * 100:.2f}%" if avg_throttle is not None else "N/A"
                duration_str = f"{duration:.2f}" if duration is not None else "N/A"
                speed_str = f"{speed_avg:.1f}" if speed_avg is not None else "N/A"
                
                f.write(f"| {lap_num} | {lap_time_str} | {throttle_str} | {avg_str} | "
                       f"{duration_str} | {compound} | {tyre_life} | {speed_str} |\n")
                
                # 保存数据用于趋势分析
                if throttle_95 is not None and lap_time and lap_time < 200:
                    lap_data.append({
                        'lap': lap_num,
                        'throttle': throttle_95 * 100,
                        'time': lap_time
                    })
            
            # 趋势分析
            if lap_data:
                f.write(f"\n#### 趋势分析\n\n")
                
                # 计算前10圈和后10圈的平均值
                first_10 = [d['throttle'] for d in lap_data[:10]]
                last_10 = [d['throttle'] for d in lap_data[-10:]]
                
                avg_first = sum(first_10) / len(first_10) if first_10 else 0
                avg_last = sum(last_10) / len(last_10) if last_10 else 0
                trend = avg_last - avg_first
                
                f.write(f"- **前10圈平均**: {avg_first:.2f}%\n")
                f.write(f"- **后10圈平均**: {avg_last:.2f}%\n")
                f.write(f"- **趋势**: {'+' if trend > 0 else ''}{trend:.2f}% ")
                f.write(f"({'上升' if trend > 0 else '下降' if trend < 0 else '持平'})\n")
                
                # 找出最高和最低的圈
                max_lap = max(lap_data, key=lambda x: x['throttle'])
                min_lap = min(lap_data, key=lambda x: x['throttle'])
                
                f.write(f"- **最高使用率圈**: Lap {max_lap['lap']} ({max_lap['throttle']:.2f}%)\n")
                f.write(f"- **最低使用率圈**: Lap {min_lap['lap']} ({min_lap['throttle']:.2f}%)\n")
                
                # 稳定性分析（标准差）
                import statistics
                if len(lap_data) > 1:
                    std_dev = statistics.stdev([d['throttle'] for d in lap_data])
                    f.write(f"- **稳定性 (标准差)**: {std_dev:.2f}%\n")
            
            f.write("\n---\n\n")
        
        # 三车手对比图
        f.write("## 🔍 三车手对比分析\n\n")
        
        # 平均值排名
        f.write("### 平均 Throttle 95% 排名\n\n")
        ranked = sorted(driver_stats.items(), key=lambda x: x[1]['avg'], reverse=True)
        
        for i, (code, stats) in enumerate(ranked, 1):
            bar_length = int(stats['avg'] / 2)  # 缩放到合适长度
            bar = '█' * bar_length
            f.write(f"{i}. **{code}** - {stats['avg']:.2f}% {bar}\n")
        
        f.write("\n")
        
        # 关键发现
        f.write("### 🔑 关键发现\n\n")
        
        winner = ranked[0]
        f.write(f"1. **最高平均油门使用率**: {winner[0]} ({winner[1]['avg']:.2f}%)\n")
        
        # 找出谁的稳定性最好
        f.write(f"2. **油门使用范围**:\n")
        for code, stats in driver_stats.items():
            range_val = stats['max'] - stats['min']
            f.write(f"   - {code}: {stats['min']:.2f}% - {stats['max']:.2f}% (范围 {range_val:.2f}%)\n")
        
        # 趋势对比
        f.write(f"3. **赛程趋势**: 查看各车手的前后10圈对比，了解轮胎衰退或策略调整影响\n")
        
        f.write("\n---\n\n")
        
        # 结论
        f.write("## 📌 结论\n\n")
        f.write("此报告展示了三位车手在 2025 Abu Dhabi GP 正赛中的油门使用率对比。\n\n")
        f.write("**建议关注点**:\n")
        f.write("- 油门使用率与圈速的相关性\n")
        f.write("- 轮胎生命周期对油门策略的影响\n")
        f.write("- 不同赛段的油门使用模式变化\n\n")
        
        f.write("---\n\n")
        f.write("*Generated by: `generate_driver_throttle_comparison.py`*\n")
        f.write(f"*Data source: `driver_throttle_ratio_2025_Abu Dhabi_R.json`*\n")
    
    print(f"✅ 报告已生成: {output_file}")
    print(f"📊 已分析车手: {', '.join(target_drivers)}")

if __name__ == "__main__":
    analyze_driver_throttle_comparison()
