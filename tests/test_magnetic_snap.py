"""
測試視窗磁吸對齊功能
"""
import sys
from PyQt5.QtWidgets import QApplication, QMdiSubWindow, QLabel
from PyQt5.QtCore import Qt, QTimer
from f1t_gui_main import CustomMdiArea

def test_magnetic_snap():
    app = QApplication(sys.argv)
    
    # 創建 MDI 區域
    mdi = CustomMdiArea()
    mdi.setWindowTitle("🧲 磁吸對齊測試")
    mdi.resize(1200, 800)
    
    # 檢查磁吸功能已初始化
    print(f"✅ 磁吸啟用: {mdi._magnetic_snap_enabled}")
    print(f"✅ 磁吸距離: {mdi._magnetic_snap_distance}px")
    
    # 創建三個測試視窗
    colors = [
        ("🔴 視窗 A", "#e74c3c", (50, 50, 300, 200)),
        ("🟢 視窗 B", "#2ecc71", (400, 50, 300, 200)),
        ("🔵 視窗 C", "#3498db", (750, 50, 300, 200))
    ]
    
    for title, color, (x, y, w, h) in colors:
        label = QLabel(f"{title}\n\n拖曳我靠近其他視窗\n試試磁吸對齊功能！")
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 20px;
                border-radius: 5px;
            }}
        """)
        label.setAlignment(Qt.AlignCenter)
        
        sub_window = QMdiSubWindow()
        sub_window.setWidget(label)
        sub_window.setWindowTitle(title)
        sub_window.setGeometry(x, y, w, h)
        
        mdi.addSubWindow(sub_window)
        sub_window.show()
    
    print("\n📌 測試說明：")
    print("1. 拖曳任一視窗靠近另一個視窗的邊緣")
    print("2. 當距離 < 15px 時，應該會自動吸附對齊")
    print("3. 支援 8 種對齊方式：左右邊緣、上下邊緣、四角對齊")
    print("4. 關閉視窗結束測試\n")
    
    mdi.show()
    
    # 3 秒後自動啟動磁吸提示
    def show_tip():
        print("💡 提示: 現在可以拖曳視窗測試磁吸對齊了！")
    
    QTimer.singleShot(3000, show_tip)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_magnetic_snap()
