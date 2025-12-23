import gc
import sys

# 強制清理所有 frame 引用
def clear_frames():
    # 清理 sys.exc_info
    sys.exc_clear() if hasattr(sys, 'exc_clear') else None
    
    # 獲取所有 frame 對象
    frames = [obj for obj in gc.get_objects() if type(obj).__name__ == 'frame']
    print(f"發現 {len(frames)} 個 frame 對象")
    
    # 清理 frame 局部變量
    for frame in frames:
        try:
            if hasattr(frame, 'f_locals'):
                # 不直接修改 f_locals（Python 不允許）
                pass
        except:
            pass
    
    # 執行多次 GC
    for i in range(3):
        collected = gc.collect()
        print(f"GC Round {i+1}: 回收 {collected} 個對象")

if __name__ == '__main__':
    clear_frames()
