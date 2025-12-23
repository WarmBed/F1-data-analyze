#!/usr/bin/env python3
"""
F1T GUI 性能對比分析工具
對比不同場景的性能差異，生成視覺化對比報告

使用場景:
- 對比不同數量 Live timing 視窗的性能影響
- 對比優化前後的性能變化
- 識別性能瓶頸和改進機會
"""

import sys
import json
import pstats
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非互動式後端


class PerformanceComparator:
    """性能對比分析器"""
    
    def __init__(self, output_dir: str = "reports/profiling"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 支援中文顯示
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
    def compare_profiles(self, profile_files: List[Path], labels: List[str]):
        """對比多個性能分析檔案
        
        Args:
            profile_files: .prof 檔案路徑列表
            labels: 對應的標籤（例如: "2個視窗", "5個視窗", "10個視窗"）
        """
        if len(profile_files) != len(labels):
            raise ValueError("profile_files 和 labels 數量必須相同")
            
        print("=" * 70)
        print("📊 性能對比分析")
        print("=" * 70)
        
        # 收集統計數據
        stats_data = []
        for pf, label in zip(profile_files, labels):
            if not pf.exists():
                print(f"⚠️  檔案不存在: {pf}")
                continue
                
            print(f"⏳ 分析: {label} ({pf.name})")
            stats = pstats.Stats(str(pf))
            
            # 提取關鍵指標
            data = self._extract_key_metrics(stats, label)
            stats_data.append(data)
            
        if len(stats_data) < 2:
            print("❌ 需要至少 2 個有效的性能檔案進行對比")
            return
            
        # 生成對比報告
        self._generate_comparison_report(stats_data)
        self._generate_comparison_charts(stats_data)
        
    def _extract_key_metrics(self, stats: pstats.Stats, label: str) -> Dict[str, Any]:
        """提取關鍵性能指標"""
        stats.calc_callees()
        
        # 獲取統計數據
        total_calls = stats.total_calls
        prim_calls = stats.prim_calls
        total_time = stats.total_tt
        
        # 找出最慢的函數（累計時間）
        stats.sort_stats('cumulative')
        top_functions = []
        
        # 獲取前 10 個最慢的函數
        for func, (cc, nc, tt, ct, callers) in list(stats.stats.items())[:10]:
            filename, line, func_name = func
            top_functions.append({
                'name': f"{Path(filename).name}:{func_name}",
                'cumtime': ct,
                'tottime': tt,
                'ncalls': nc
            })
            
        return {
            'label': label,
            'total_calls': total_calls,
            'prim_calls': prim_calls,
            'total_time': total_time,
            'top_functions': top_functions
        }
        
    def _generate_comparison_report(self, stats_data: List[Dict[str, Any]]):
        """生成文字對比報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"comparison_report_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("F1T GUI 性能對比報告\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            
            # 總體指標對比
            f.write("📊 總體指標對比\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'場景':<20} {'總調用次數':<15} {'總執行時間(秒)':<15} {'平均時間/調用(ms)'}\n")
            f.write("-" * 70 + "\n")
            
            for data in stats_data:
                avg_time = (data['total_time'] / data['total_calls'] * 1000) if data['total_calls'] > 0 else 0
                f.write(f"{data['label']:<20} {data['total_calls']:<15} {data['total_time']:<15.3f} {avg_time:.6f}\n")
                
            # 最慢函數對比
            f.write("\n\n🔥 最慢函數對比 (累計時間 Top 5)\n")
            f.write("-" * 70 + "\n")
            
            for data in stats_data:
                f.write(f"\n{data['label']}:\n")
                for i, func in enumerate(data['top_functions'][:5], 1):
                    f.write(f"  {i}. {func['name']:<50} {func['cumtime']:.3f}秒\n")
                    
            # 性能變化分析
            if len(stats_data) >= 2:
                f.write("\n\n📈 性能變化分析\n")
                f.write("-" * 70 + "\n")
                
                baseline = stats_data[0]
                for data in stats_data[1:]:
                    time_increase = ((data['total_time'] - baseline['total_time']) / baseline['total_time']) * 100
                    calls_increase = ((data['total_calls'] - baseline['total_calls']) / baseline['total_calls']) * 100
                    
                    f.write(f"\n{baseline['label']} → {data['label']}:\n")
                    f.write(f"  執行時間變化: {time_increase:+.2f}%\n")
                    f.write(f"  調用次數變化: {calls_increase:+.2f}%\n")
                    
        print(f"\n✅ 對比報告已生成: {report_file}")
        
    def _generate_comparison_charts(self, stats_data: List[Dict[str, Any]]):
        """生成視覺化對比圖表"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('F1T GUI 性能對比分析', fontsize=16, fontweight='bold')
        
        labels = [data['label'] for data in stats_data]
        
        # 圖表 1: 總執行時間對比
        ax1 = axes[0, 0]
        total_times = [data['total_time'] for data in stats_data]
        bars1 = ax1.bar(labels, total_times, color='steelblue', alpha=0.8)
        ax1.set_title('總執行時間對比', fontsize=12, fontweight='bold')
        ax1.set_ylabel('時間 (秒)')
        ax1.grid(axis='y', alpha=0.3)
        
        # 添加數值標籤
        for bar, value in zip(bars1, total_times):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.2f}s',
                    ha='center', va='bottom', fontsize=10)
        
        # 圖表 2: 總調用次數對比
        ax2 = axes[0, 1]
        total_calls = [data['total_calls'] for data in stats_data]
        bars2 = ax2.bar(labels, total_calls, color='coral', alpha=0.8)
        ax2.set_title('總調用次數對比', fontsize=12, fontweight='bold')
        ax2.set_ylabel('調用次數')
        ax2.grid(axis='y', alpha=0.3)
        
        # 添加數值標籤
        for bar, value in zip(bars2, total_calls):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:,}',
                    ha='center', va='bottom', fontsize=10)
        
        # 圖表 3: Top 5 最慢函數（累計時間）
        ax3 = axes[1, 0]
        
        # 只顯示第一個和最後一個場景的對比
        if len(stats_data) >= 2:
            first_data = stats_data[0]
            last_data = stats_data[-1]
            
            func_names = [f"{i+1}. {func['name'][:30]}..." 
                         for i, func in enumerate(first_data['top_functions'][:5])]
            first_times = [func['cumtime'] for func in first_data['top_functions'][:5]]
            last_times = [func['cumtime'] for func in last_data['top_functions'][:5]]
            
            x = range(len(func_names))
            width = 0.35
            
            ax3.barh([i - width/2 for i in x], first_times, width, 
                    label=first_data['label'], color='steelblue', alpha=0.8)
            ax3.barh([i + width/2 for i in x], last_times, width,
                    label=last_data['label'], color='coral', alpha=0.8)
            
            ax3.set_yticks(x)
            ax3.set_yticklabels(func_names, fontsize=8)
            ax3.set_xlabel('累計時間 (秒)')
            ax3.set_title('Top 5 最慢函數對比', fontsize=12, fontweight='bold')
            ax3.legend()
            ax3.grid(axis='x', alpha=0.3)
        
        # 圖表 4: 性能增長趨勢
        ax4 = axes[1, 1]
        
        if len(stats_data) >= 2:
            baseline_time = stats_data[0]['total_time']
            time_ratios = [(data['total_time'] / baseline_time) * 100 for data in stats_data]
            
            ax4.plot(labels, time_ratios, marker='o', linewidth=2, 
                    markersize=8, color='darkgreen')
            ax4.axhline(y=100, color='red', linestyle='--', alpha=0.5, label='基準線')
            ax4.set_title('執行時間增長趨勢', fontsize=12, fontweight='bold')
            ax4.set_ylabel('相對基準的百分比 (%)')
            ax4.grid(True, alpha=0.3)
            ax4.legend()
            
            # 添加數值標籤
            for i, (label, ratio) in enumerate(zip(labels, time_ratios)):
                ax4.text(i, ratio, f'{ratio:.1f}%', 
                        ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        # 保存圖表
        chart_file = self.output_dir / f"comparison_charts_{timestamp}.png"
        plt.savefig(chart_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 對比圖表已生成: {chart_file}")
        
    def generate_html_report(self, stats_data: List[Dict[str, Any]]):
        """生成 HTML 互動式報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_file = self.output_dir / f"comparison_report_{timestamp}.html"
        
        html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F1T GUI 性能對比報告</title>
    <style>
        body {
            font-family: 'Microsoft JhengHei', 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            padding: 30px;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #667eea;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .metric-card {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            min-width: 200px;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
        }
        .metric-label {
            font-size: 14px;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏎️ F1T GUI 性能對比報告</h1>
        <p>生成時間: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        
        <h2>📊 總體指標</h2>
        <table>
            <thead>
                <tr>
                    <th>場景</th>
                    <th>總調用次數</th>
                    <th>總執行時間 (秒)</th>
                    <th>平均時間/調用 (ms)</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for data in stats_data:
            avg_time = (data['total_time'] / data['total_calls'] * 1000) if data['total_calls'] > 0 else 0
            html_content += f"""
                <tr>
                    <td><strong>{data['label']}</strong></td>
                    <td>{data['total_calls']:,}</td>
                    <td>{data['total_time']:.3f}</td>
                    <td>{avg_time:.6f}</td>
                </tr>
"""
        
        html_content += """
            </tbody>
        </table>
        
        <h2>🔥 最慢函數 Top 5</h2>
"""
        
        for data in stats_data:
            html_content += f"<h3>{data['label']}</h3><table><thead><tr><th>排名</th><th>函數</th><th>累計時間 (秒)</th><th>調用次數</th></tr></thead><tbody>"
            
            for i, func in enumerate(data['top_functions'][:5], 1):
                html_content += f"""
                <tr>
                    <td>{i}</td>
                    <td><code>{func['name']}</code></td>
                    <td>{func['cumtime']:.3f}</td>
                    <td>{func['ncalls']:,}</td>
                </tr>
"""
            
            html_content += "</tbody></table>"
        
        html_content += """
    </div>
</body>
</html>
"""
        
        html_file.write_text(html_content, encoding='utf-8')
        print(f"✅ HTML 報告已生成: {html_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="F1T GUI 性能對比分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 先用 profile_gui.py 或 profile_gui_pyspy.py 生成多個性能檔案
  python tools/profile_gui.py --mode live --windows 2
  python tools/profile_gui.py --mode live --windows 5
  python tools/profile_gui.py --mode live --windows 10
  
  # 然後對比這些檔案
  python tools/compare_performance.py \\
      --files reports/profiling/gui_live_timing_stress_*.prof \\
      --labels "2個視窗" "5個視窗" "10個視窗"
        """
    )
    
    parser.add_argument(
        '--files',
        nargs='+',
        required=True,
        help='.prof 檔案路徑列表'
    )
    
    parser.add_argument(
        '--labels',
        nargs='+',
        required=True,
        help='對應的標籤'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='reports/profiling',
        help='輸出目錄'
    )
    
    args = parser.parse_args()
    
    # 轉換為 Path 對象
    profile_files = [Path(f) for f in args.files]
    
    comparator = PerformanceComparator(output_dir=args.output)
    comparator.compare_profiles(profile_files, args.labels)


if __name__ == "__main__":
    main()
