"""
GUI 內部調用鏈追蹤器
在 GUI 運行時追蹤 update_all_lap_analysis 的完整調用鏈
"""

import sys
import threading
import traceback
from datetime import datetime

class CallChainTracer:
    """調用鏈追蹤器"""
    
    def __init__(self):
        self.trace_enabled = False
        self.thread_creation_stacks = []
        self.original_thread_init = None
    
    def enable_tracing(self):
        """啟用追蹤"""
        print("🔍 [TRACER] 啟用執行緒創建追蹤")
        self.trace_enabled = True
        self._patch_thread_creation()
    
    def disable_tracing(self):
        """停用追蹤"""
        print("🔍 [TRACER] 停用執行緒創建追蹤")
        self.trace_enabled = False
        self._unpatch_thread_creation()
    
    def _patch_thread_creation(self):
        """修補 threading.Thread.__init__ 來追蹤執行緒創建"""
        self.original_thread_init = threading.Thread.__init__
        
        def traced_init(thread_self, *args, **kwargs):
            # 調用原始 __init__
            self.original_thread_init(thread_self, *args, **kwargs)
            
            # 記錄調用堆疊
            if self.trace_enabled:
                stack = traceback.extract_stack()[:-1]  # 排除當前幀
                stack_info = {
                    'timestamp': datetime.now(),
                    'thread_name': thread_self.name,
                    'thread_type': type(thread_self).__name__,
                    'stack': stack
                }
                self.thread_creation_stacks.append(stack_info)
                
                print(f"\n{'='*80}")
                print(f"🆕 [TRACER] 執行緒創建：{thread_self.name} ({type(thread_self).__name__})")
                print(f"{'='*80}")
                print("📋 調用堆疊:")
                for frame in stack[-10:]:  # 只顯示最後 10 層
                    print(f"  {frame.filename}:{frame.lineno} in {frame.name}")
                    if frame.line:
                        print(f"    {frame.line.strip()}")
                print(f"{'='*80}\n")
        
        threading.Thread.__init__ = traced_init
    
    def _unpatch_thread_creation(self):
        """恢復原始的 threading.Thread.__init__"""
        if self.original_thread_init:
            threading.Thread.__init__ = self.original_thread_init
    
    def print_summary(self):
        """打印摘要"""
        print(f"\n{'='*80}")
        print(f"📊 執行緒創建摘要")
        print(f"{'='*80}")
        print(f"總共創建了 {len(self.thread_creation_stacks)} 個執行緒\n")
        
        # 按類型分組
        by_type = {}
        for info in self.thread_creation_stacks:
            thread_type = info['thread_type']
            if thread_type not in by_type:
                by_type[thread_type] = []
            by_type[thread_type].append(info)
        
        for thread_type, infos in sorted(by_type.items()):
            print(f"\n🔹 {thread_type}: {len(infos)} 個")
            
            # 找出共同的創建位置
            creation_points = {}
            for info in infos:
                # 找到非標準庫的最深層調用
                for frame in reversed(info['stack']):
                    if 'F1-data-analyze' in frame.filename:
                        location = f"{frame.filename}:{frame.lineno}"
                        if location not in creation_points:
                            creation_points[location] = []
                        creation_points[location].append(info['thread_name'])
                        break
            
            for location, thread_names in sorted(creation_points.items(), key=lambda x: len(x[1]), reverse=True):
                print(f"  📍 {location}")
                print(f"     創建了 {len(thread_names)} 個執行緒")
                if len(thread_names) <= 5:
                    for name in thread_names:
                        print(f"       • {name}")
        
        print(f"{'='*80}\n")
    
    def clear(self):
        """清除記錄"""
        self.thread_creation_stacks.clear()
        print("🧹 [TRACER] 已清除記錄")

# 全局追蹤器實例
tracer = CallChainTracer()

def inject_into_gui():
    """將追蹤器注入到 GUI 主程式"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🔍 GUI 調用鏈追蹤器 - 注入指南                          ║
║                                                                            ║
║  將以下代碼添加到 f1t_gui_main.py 的 update_all_lap_analysis 方法開頭： ║
║                                                                            ║
║  from diagnose_thread_leak_callchain import tracer                         ║
║  tracer.clear()  # 清除舊記錄                                              ║
║  tracer.enable_tracing()  # 開始追蹤                                       ║
║                                                                            ║
║  然後在方法結尾添加：                                                      ║
║  tracer.disable_tracing()  # 停止追蹤                                      ║
║  tracer.print_summary()  # 打印摘要                                        ║
║                                                                            ║
║  或者手動在 Python Console 中操作：                                        ║
║  >>> from diagnose_thread_leak_callchain import tracer                     ║
║  >>> tracer.enable_tracing()                                               ║
║  >>> # 點擊 Update All Analysis 按鈕                                       ║
║  >>> tracer.disable_tracing()                                              ║
║  >>> tracer.print_summary()                                                ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    inject_into_gui()
