import gc
import sys
import traceback

print("=" * 80)
print("深度 Frame 診斷")
print("=" * 80)

# 1. 檢查 sys 模組的 traceback
print("\n[1] sys 模組檢查:")
print(f"  sys.last_type: {getattr(sys, 'last_type', None)}")
print(f"  sys.last_value: {getattr(sys, 'last_value', None)}")
print(f"  sys.last_traceback: {getattr(sys, 'last_traceback', None)}")

# 2. 統計所有對象
print("\n[2] 對象統計:")
all_objects = gc.get_objects()
frames = [obj for obj in all_objects if type(obj).__name__ == 'frame']
tracebacks = [obj for obj in all_objects if type(obj).__name__ == 'traceback']
print(f"  總對象數: {len(all_objects)}")
print(f"  frame 對象: {len(frames)}")
print(f"  traceback 對象: {len(tracebacks)}")

# 3. 分析 frame 的文件分佈
print("\n[3] frame 文件分佈:")
frame_files = {}
for f in frames:
    try:
        filename = f.f_code.co_filename
        lineno = f.f_lineno
        key = f"{filename}:{lineno}"
        frame_files[key] = frame_files.get(key, 0) + 1
    except:
        pass

# 只顯示 f1t_gui_main.py 的 frame
print("\n  f1t_gui_main.py 中的 frame:")
for key, count in sorted(frame_files.items()):
    if 'f1t_gui_main.py' in key:
        print(f"    {key}: {count} 個")

# 4. 檢查特定行號的 frame
target_lines = [6826, 6940, 7031, 13390]
print(f"\n[4] 目標行號檢查 {target_lines}:")
for f in frames:
    try:
        if 'f1t_gui_main.py' in f.f_code.co_filename:
            if f.f_lineno in target_lines:
                print(f"   找到 frame: 行 {f.f_lineno}")
                print(f"     函數: {f.f_code.co_name}")
                print(f"     局部變量: {list(f.f_locals.keys())[:10]}")
                
                # 檢查是否持有 SpeedAnalysisModule
                for var_name, var_value in f.f_locals.items():
                    if 'SpeedAnalysis' in str(type(var_value)):
                        print(f"       持有 SpeedAnalysisModule: {var_name} = {type(var_value)}")
    except:
        pass

# 5. 檢查 traceback 對象
print(f"\n[5] traceback 對象分析:")
for i, tb in enumerate(tracebacks[:5]):  # 只看前 5 個
    try:
        print(f"  traceback {i+1}:")
        print(f"    tb_frame: {tb.tb_frame}")
        print(f"    tb_lineno: {tb.tb_lineno}")
        if tb.tb_frame:
            print(f"    文件: {tb.tb_frame.f_code.co_filename}")
            print(f"    函數: {tb.tb_frame.f_code.co_name}")
    except:
        pass

print("\n" + "=" * 80)
