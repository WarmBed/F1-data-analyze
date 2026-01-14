#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
診斷 paintEvent 和 mouseMoveEvent 性能問題
執行方式：在 GUI 啟動時 import 這個模組來啟用診斷
"""

import time
import functools

# 儲存性能統計
_perf_stats = {
    'paintEvent': {'count': 0, 'total_ms': 0, 'max_ms': 0},
    'mouseMoveEvent': {'count': 0, 'total_ms': 0, 'max_ms': 0},
    '_check_hover_point': {'count': 0, 'total_ms': 0, 'max_ms': 0},
    '_check_hover_data_point': {'count': 0, 'total_ms': 0, 'max_ms': 0},
    '_draw_legend': {'count': 0, 'total_ms': 0, 'max_ms': 0},
    '_draw_custom_tooltip': {'count': 0, 'total_ms': 0, 'max_ms': 0},
    '_draw_smart_markers': {'count': 0, 'total_ms': 0, 'max_ms': 0},
}

_last_report_time = time.time()
_report_interval = 5  # 每 5 秒輸出一次報告

def perf_wrapper(method_name):
    """性能包裝器裝飾器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            global _last_report_time
            
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                
                if method_name in _perf_stats:
                    stats = _perf_stats[method_name]
                    stats['count'] += 1
                    stats['total_ms'] += elapsed_ms
                    stats['max_ms'] = max(stats['max_ms'], elapsed_ms)
                
                # 每隔一段時間輸出報告
                now = time.time()
                if now - _last_report_time >= _report_interval:
                    _last_report_time = now
                    print_perf_report()
        
        return wrapper
    return decorator


def print_perf_report():
    """輸出性能報告"""
    print("\n" + "="*70)
    print("🔍 性能診斷報告")
    print("="*70)
    print(f"{'方法名稱':<30} {'調用次數':>10} {'總耗時(ms)':>12} {'平均(ms)':>10} {'最大(ms)':>10}")
    print("-"*70)
    
    for name, stats in _perf_stats.items():
        if stats['count'] > 0:
            avg_ms = stats['total_ms'] / stats['count']
            print(f"{name:<30} {stats['count']:>10} {stats['total_ms']:>12.2f} {avg_ms:>10.2f} {stats['max_ms']:>10.2f}")
    
    print("="*70 + "\n")


def reset_stats():
    """重置統計數據"""
    for stats in _perf_stats.values():
        stats['count'] = 0
        stats['total_ms'] = 0
        stats['max_ms'] = 0


# 用法示例：
# 在目標模組中添加：
# from debug_paint_performance import perf_wrapper
# 
# @perf_wrapper('paintEvent')
# def paintEvent(self, event):
#     ...

if __name__ == "__main__":
    print("這個模組用於診斷 PyQt5 繪圖性能問題")
    print("請在目標模組中 import 並使用 @perf_wrapper 裝飾器")
