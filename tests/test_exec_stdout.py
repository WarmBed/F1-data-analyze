"""
測試 exec() 環境中的 stdout 捕獲
診斷為什麼 objgraph_window 中無法捕獲輸出
"""
import io
import sys

print("=" * 60)
print("測試 1: 基本的 exec + stdout 捕獲")
print("=" * 60)

# 測試 1: 最簡單的情況
code1 = 'print("Hello from exec")'
buffer1 = io.StringIO()
old_stdout = sys.stdout
sys.stdout = buffer1
exec(code1)
sys.stdout = old_stdout
result1 = buffer1.getvalue()
print(f"✅ 測試 1 結果: '{result1.strip()}'")
print()

print("=" * 60)
print("測試 2: exec 帶 globals（包含 sys）")
print("=" * 60)

# 測試 2: exec_globals 包含 sys（舊方法）
code2 = '''
import sys
print(f"sys.stdout type: {type(sys.stdout)}")
print("Hello with sys in globals")
'''
buffer2 = io.StringIO()
old_stdout = sys.stdout
exec_globals2 = {
    '__builtins__': __builtins__,
    'sys': sys  # ❌ 這會導致問題
}
sys.stdout = buffer2
exec(code2, exec_globals2)
sys.stdout = old_stdout
result2 = buffer2.getvalue()
print(f"✅ 測試 2 結果: '{result2.strip()}'")
print()

print("=" * 60)
print("測試 3: exec 不包含 sys（新方法）")
print("=" * 60)

# 測試 3: exec_globals 不包含 sys（新方法）
code3 = '''
import sys
print(f"sys.stdout type: {type(sys.stdout)}")
print("Hello WITHOUT sys in globals")
'''
buffer3 = io.StringIO()
old_stdout = sys.stdout
sys.stdout = buffer3  # 先替換
exec_globals3 = {
    '__builtins__': __builtins__
    # ✅ 不包含 sys，讓代碼自己 import
}
exec(code3, exec_globals3)
sys.stdout = old_stdout
result3 = buffer3.getvalue()
print(f"✅ 測試 3 結果: '{result3.strip()}'")
print()

print("=" * 60)
print("測試 4: objgraph 在 exec 中")
print("=" * 60)

# 測試 4: 使用 objgraph
try:
    import objgraph
    code4 = '''
import objgraph, gc
gc.collect()
count = objgraph.count("_DummyThread")
print(f"DummyThread 數量: {count}")
'''
    buffer4 = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer4
    exec_globals4 = {
        '__builtins__': __builtins__,
        'objgraph': objgraph,
        'gc': __import__('gc')
    }
    exec(code4, exec_globals4)
    sys.stdout = old_stdout
    result4 = buffer4.getvalue()
    print(f"✅ 測試 4 結果: '{result4.strip()}'")
except ImportError:
    print("⚠️ objgraph 未安裝，跳過測試 4")
print()

print("=" * 60)
print("測試 5: 模擬 PyQt 環境（無 QApplication）")
print("=" * 60)

# 測試 5: 檢查是否是 import 順序問題
code5 = '''
import threading, gc
gc.collect()
active = threading._active
print(f"threading._active 執行緒數: {len(active)}")
dummy_count = sum(1 for t in active.values() if type(t).__name__ == "_DummyThread")
print(f"其中 DummyThread: {dummy_count} 個")
'''
buffer5 = io.StringIO()
old_stdout = sys.stdout
sys.stdout = buffer5
exec_globals5 = {
    '__builtins__': __builtins__,
    'threading': __import__('threading'),
    'gc': __import__('gc')
}
exec(code5, exec_globals5)
sys.stdout = old_stdout
result5 = buffer5.getvalue()
print(f"✅ 測試 5 結果: '{result5.strip()}'")
print()

print("=" * 60)
print("所有測試完成！")
print("=" * 60)
