"""
測試分頁架構修復
=================

測試目標：
1. ✅ 程式啟動時只顯示主頁，不自動創建分頁一
2. ✅ 點擊模組時創建"分頁一"（不是空白標題）
3. ✅ 不出現 "Analysis Workspace" toolbar
4. ✅ + 按鈕在左上角（白底黑字）
5. ✅ Show All Data 和 Close All Windows 在右上角

測試步驟：
1. 啟動 GUI
2. 確認只有"主頁"標籤
3. 點擊 Rain Analysis
4. 確認創建"分頁一"
5. 確認沒有 Analysis Workspace toolbar
"""

import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

def test_tab_architecture():
    """測試分頁架構"""
    print("=" * 60)
    print("🧪 測試分頁架構修復")
    print("=" * 60)
    
    # 導入主視窗
    sys.path.insert(0, r'C:\Users\mike2\OneDrive\Code\F1-data-analyze')
    from f1t_gui_main import F1AnalysisMainWindow
    
    app = QApplication(sys.argv)
    window = F1AnalysisMainWindow()
    
    # 測試 1: 檢查初始狀態
    print("\n📋 測試 1: 檢查初始狀態")
    print(f"分頁數量: {window.tab_widget.count()}")
    
    if window.tab_widget.count() == 1:
        first_tab = window.tab_widget.widget(0)
        tab_title = window.tab_widget.tabText(0)
        print(f"✅ 只有一個分頁: '{tab_title}'")
        
        if first_tab.objectName() == "welcome_tab":
            print(f"✅ 第一個分頁是主頁")
        else:
            print(f"❌ 第一個分頁不是主頁: {first_tab.objectName()}")
    else:
        print(f"❌ 分頁數量錯誤: {window.tab_widget.count()}")
    
    # 測試 2: 檢查按鈕位置
    print("\n📋 測試 2: 檢查按鈕位置")
    from PyQt5.QtCore import Qt
    
    left_widget = window.tab_widget.cornerWidget(Qt.TopLeftCorner)
    right_widget = window.tab_widget.cornerWidget(Qt.TopRightCorner)
    
    if left_widget:
        print(f"✅ 左上角有 CornerWidget")
        # 查找 + 按鈕
        add_btn = left_widget.findChild(object, "AddTabButton")
        if add_btn:
            print(f"✅ 找到 + 按鈕")
        else:
            print(f"❌ 未找到 + 按鈕")
    else:
        print(f"❌ 左上角沒有 CornerWidget")
    
    if right_widget:
        print(f"✅ 右上角有 CornerWidget")
    else:
        print(f"❌ 右上角沒有 CornerWidget")
    
    # 測試 3: 模擬點擊模組
    print("\n📋 測試 3: 模擬創建分頁一")
    
    def simulate_module_click():
        print("🖱️ 模擬調用 check_and_remove_welcome_page()...")
        window.check_and_remove_welcome_page()
        
        # 檢查結果
        print(f"\n分頁數量: {window.tab_widget.count()}")
        
        if window.tab_widget.count() == 2:
            print(f"✅ 成功創建新分頁")
            
            # 檢查第二個分頁的標題
            tab_title = window.tab_widget.tabText(1)
            print(f"第二個分頁標題: '{tab_title}'")
            
            if tab_title == "分頁一":
                print(f"✅ 分頁標題正確: '分頁一'")
            elif tab_title == "":
                print(f"❌ 分頁標題是空白！")
            else:
                print(f"⚠️ 分頁標題異常: '{tab_title}'")
            
            # 檢查第二個分頁是否有 toolbar
            second_tab = window.tab_widget.widget(1)
            from PyQt5.QtWidgets import QLabel
            
            # 查找是否有 "Analysis Workspace" 文字
            labels = second_tab.findChildren(QLabel)
            has_analysis_workspace = False
            for label in labels:
                if "Analysis Workspace" in label.text():
                    has_analysis_workspace = True
                    print(f"❌ 發現 'Analysis Workspace' toolbar！")
                    break
            
            if not has_analysis_workspace:
                print(f"✅ 沒有 'Analysis Workspace' toolbar")
                
        else:
            print(f"❌ 分頁數量錯誤: {window.tab_widget.count()}")
        
        # 測試完成
        print("\n" + "=" * 60)
        print("🎉 測試完成！")
        print("=" * 60)
        
        # 關閉視窗
        QTimer.singleShot(1000, window.close)
    
    # 延遲執行測試（等待 GUI 完全初始化）
    QTimer.singleShot(3000, simulate_module_click)
    
    # 顯示視窗
    window.show()
    
    # 執行應用程式
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_tab_architecture()
