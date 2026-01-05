#!/usr/bin/env python3
"""
GUI 响应性优化测试

测试在 1000 次迭代时 GUI 是否保持响应

Author: F1T Team
Date: 2026-01-05
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QProgressBar, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QTimer
import time

class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GUI 响应性测试 - 1000 次迭代")
        self.setGeometry(100, 100, 500, 200)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Status label
        self.status_label = QLabel("准备开始测试...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximum(1000)
        layout.addWidget(self.progress)
        
        # Info label
        self.info_label = QLabel("测试将模拟 1000 次迭代，每 10 次更新一次 UI")
        layout.addWidget(self.info_label)
        
        # Start test after window is shown
        QTimer.singleShot(500, self.run_test)
    
    def run_test(self):
        """运行测试"""
        print("\n" + "="*70)
        print("GUI 响应性测试 - 1000 次迭代")
        print("="*70)
        print("\n请观察:")
        print("1. ✅ 进度条是否流畅移动")
        print("2. ✅ 窗口是否可以移动")
        print("3. ✅ 状态文本是否定期更新")
        print("4. ✅ GUI 是否显示 '(无响应)'\n")
        
        start_time = time.time()
        
        for i in range(1000):
            # 模拟计算
            dummy = sum(j * j for j in range(1000))
            
            # 每 10 次迭代更新 UI (优化后的频率)
            if i % 10 == 0:
                self.progress.setValue(i)
                self.status_label.setText(f"迭代中: {i}/1000 ({i/10:.1f}%)")
                
                # 关键: 让 UI 保持响应
                QApplication.processEvents()
                
                # 打印日志
                if i % 100 == 0:
                    elapsed = time.time() - start_time
                    print(f"[TEST] Iteration {i}/1000 (已用时 {elapsed:.1f}s)")
        
        # 完成
        self.progress.setValue(1000)
        elapsed = time.time() - start_time
        self.status_label.setText(f"✅ 测试完成！总用时: {elapsed:.1f} 秒")
        
        print("\n" + "="*70)
        print(f"✅ 测试完成! 总用时: {elapsed:.1f} 秒")
        print("="*70)
        print("\n验证结果:")
        print("  - 如果窗口始终可以移动 → UI 保持响应 ✅")
        print("  - 如果窗口曾显示 '(无响应)' → 需要更多优化 ❌")
        print("  - 进度条流畅更新 → processEvents() 生效 ✅")
        print("\n预期性能:")
        print(f"  - 1000 次迭代应该在 1-3 秒完成")
        print(f"  - 实际用时: {elapsed:.1f} 秒")
        
        if elapsed < 5:
            print(f"  - ✅ 性能良好")
        elif elapsed < 10:
            print(f"  - ⚠️  性能一般，可接受")
        else:
            print(f"  - ❌ 性能较差，需要检查")

def test_without_processEvents():
    """对比测试: 不使用 processEvents()"""
    print("\n" + "="*70)
    print("对比测试: 不使用 processEvents() 的情况")
    print("="*70)
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("无优化测试 - 会冻结!")
    window.setGeometry(100, 100, 500, 200)
    
    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    
    status = QLabel("测试开始...")
    layout.addWidget(status)
    
    progress = QProgressBar()
    progress.setMaximum(1000)
    layout.addWidget(progress)
    
    window.show()
    QApplication.processEvents()  # 只在开始时处理一次
    
    print("\n⚠️  警告: 接下来窗口将冻结 1-3 秒...")
    time.sleep(0.5)
    
    start_time = time.time()
    for i in range(1000):
        dummy = sum(j * j for j in range(1000))
        
        if i % 10 == 0:
            progress.setValue(i)
            status.setText(f"迭代中: {i}/1000")
            # ❌ 没有调用 processEvents()!
    
    elapsed = time.time() - start_time
    progress.setValue(1000)
    status.setText(f"完成! 用时: {elapsed:.1f}s (但窗口冻结了)")
    QApplication.processEvents()
    
    print(f"\n❌ 窗口冻结了 {elapsed:.1f} 秒!")
    print("   - 用户无法移动窗口")
    print("   - 进度条不更新")
    print("   - 系统显示 '(无响应)'\n")
    
    time.sleep(2)
    window.close()

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║           GUI 响应性优化测试 - processEvents() 效果验证             ║
╚════════════════════════════════════════════════════════════════════╝

此测试将：
1. 模拟 1000 次迭代（类似 Monte Carlo 模拟）
2. 每 10 次迭代更新 UI（优化后的策略）
3. 调用 processEvents() 保持 GUI 响应

请在测试运行时尝试：
- 移动窗口
- 查看进度条是否流畅
- 检查是否显示 "(无响应)"

按 Enter 开始测试...
""")
    input()
    
    app = QApplication(sys.argv)
    
    # Test 1: 使用 processEvents() (优化后)
    print("\n[TEST 1] 使用 processEvents() 优化...")
    window = TestWindow()
    window.show()
    app.exec_()
    
    # Test 2: 不使用 processEvents() (优化前对比)
    print("\n" + "="*70)
    print("是否运行对比测试？(会看到冻结效果)")
    print("输入 'y' 继续，任意键跳过...")
    choice = input().lower()
    
    if choice == 'y':
        test_without_processEvents()
        app.exec_()
    
    print("\n✅ 所有测试完成!")
    print("\n总结:")
    print("  - processEvents() 让 GUI 保持响应")
    print("  - 每 10 次迭代调用一次是最佳平衡")
    print("  - 1000 次迭代不会冻结界面")
