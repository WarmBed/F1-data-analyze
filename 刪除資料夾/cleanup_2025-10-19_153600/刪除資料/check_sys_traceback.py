import sys
import gc

# 檢查 sys 模組中的 traceback 引用
print("檢查 sys 模組中的 traceback 引用:")
print(f"sys.last_type: {getattr(sys, 'last_type', None)}")
print(f"sys.last_value: {getattr(sys, 'last_value', None)}")
print(f"sys.last_traceback: {getattr(sys, 'last_traceback', None)}")

# 清理殘留的 traceback
if hasattr(sys, 'last_traceback'):
    sys.last_type = None
    sys.last_value = None
    sys.last_traceback = None
    print("\n已清理 sys.last_traceback")

# 強制 GC
collected = gc.collect()
print(f"\nGC 回收: {collected} 個對象")

# 統計 frame 對象數量
frames = [obj for obj in gc.get_objects() if type(obj).__name__ == 'frame']
print(f"\n當前 frame 對象數量: {len(frames)}")

# 檢查是否有 traceback 對象
tracebacks = [obj for obj in gc.get_objects() if type(obj).__name__ == 'traceback']
print(f"當前 traceback 對象數量: {len(tracebacks)}")
