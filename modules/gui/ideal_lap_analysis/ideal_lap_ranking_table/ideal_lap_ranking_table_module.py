#!/usr/bin/env python3
"""
理想圈排名表格模組
Ideal Lap Ranking Table Module

實作 IAnalysisModule 介面，提供統一的模組介面給主 GUI 使用

作者: F1T Team
日期: 2025-10-09
版本: 1.0.0
"""

import sys
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget

# 導入介面
try:
    from modules.gui.interfaces.analysis_module import IAnalysisModule
except ImportError:
    from ...interfaces.analysis_module import IAnalysisModule

# 導入 MDI
try:
    from .ideal_lap_ranking_table_mdi import IdealLapRankingTableMDI
except ImportError:
    from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_mdi import IdealLapRankingTableMDI


class IdealLapRankingTableModule(IAnalysisModule):
    """
    理想圈排名表格模組 - 實作 IAnalysisModule 介面
    
    提供統一的模組介面給主 GUI 使用，管理 IdealLapRankingTableMDI 的生命週期
    """
    
    def __init__(self, parent=None, year=None, race=None, session=None):
        """
        初始化模組
        
        Args:
            parent: 父元件
            year: 賽季年份
            race: 賽事名稱
            session: 賽段類型
        """
        super().__init__(parent)
        
        # ✅ 添加 analysis_type 屬性以支援批次更新
        self.analysis_type = 'ideal_lap_ranking'
        
        # 模組基本資訊
        self._module_name = "IdealLapRankingTable"
        self._display_name = "Ideal Lap Ranking Table"
        self._version = "1.0.0"
        self._description = "All Drivers Ideal Lap Ranking Analysis"
        
        # 參數
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        # 內部核心實例
        self._ranking_core: Optional[IdealLapRankingTableMDI] = None
        
        # 主要元件
        self._main_widget: Optional[QWidget] = None
        
        # 狀態
        self._is_initialized = False
        
        print(f"[RANKING_MODULE] 模組已創建: {year} {race} {session}")
    
    # ========== IAnalysisModule 屬性實作 ==========
    
    @property
    def module_name(self) -> str:
        """模組名稱"""
        return self._module_name
    
    @property
    def display_name(self) -> str:
        """顯示名稱"""
        return self._display_name
    
    @property
    def version(self) -> str:
        """版本號"""
        return self._version
    
    @property
    def description(self) -> str:
        """模組描述"""
        return self._description
    
    # ========== IAnalysisModule 介面實作 ==========
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組
        
        Args:
            parent_widget: 父元件
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            print("[RANKING_MODULE] 開始初始化模組...")
            
            if self._is_initialized:
                print("[RANKING_MODULE] 模組已初始化，跳過")
                return True
            
            # 檢查參數
            if not self.current_year or not self.current_race or not self.current_session:
                print("❌ [RANKING_MODULE] 缺少必要參數 (year/race/session)")
                return False
            
            # 創建 MDI 核心實例
            if not self._ranking_core:
                print(f"[RANKING_MODULE] 創建 MDI 核心: {self.current_year} {self.current_race} {self.current_session}")
                # ✅ MDI 構造函數只接受 parent 參數
                self._ranking_core = IdealLapRankingTableMDI(parent=parent_widget)
                
                # ✅ 在初始化前設置必要的屬性
                self._ranking_core.current_year = self.current_year
                self._ranking_core.current_race = self.current_race
                self._ranking_core.current_session = self.current_session
                
                # ✅ 初始化 MDI 核心
                print("[RANKING_MODULE] 初始化 MDI 核心...")
                if not self._ranking_core.initialize_module():
                    print("❌ [RANKING_MODULE] MDI 核心初始化失敗")
                    return False
                print("✅ [RANKING_MODULE] MDI 核心初始化成功")
            
            # 獲取主要元件
            self._main_widget = self._ranking_core.get_widget()
            
            if not self._main_widget:
                print("❌ [RANKING_MODULE] 無法獲取主要元件")
                return False
            
            self._is_initialized = True
            print("✅ [RANKING_MODULE] 模組初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ [RANKING_MODULE] 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_data(self, **kwargs) -> bool:
        """
        載入資料
        
        Args:
            **kwargs: 載入參數
            
        Returns:
            bool: 載入是否成功
        """
        try:
            print("[RANKING_MODULE] 載入資料...")
            
            if not self._is_initialized:
                print("❌ [RANKING_MODULE] 模組未初始化")
                return False
            
            if not self._ranking_core:
                print("❌ [RANKING_MODULE] MDI 核心未創建")
                return False
            
            # 觸發 MDI 載入資料
            self._ranking_core.load_initial_data()
            
            print("✅ [RANKING_MODULE] 資料載入已觸發")
            return True
            
        except Exception as e:
            print(f"❌ [RANKING_MODULE] 載入資料失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_parameters(self, year: int, race: str, session: str, **kwargs) -> bool:
        """
        更新分析參數
        
        Args:
            year: 年份
            race: 賽事
            session: 賽段
            **kwargs: 額外參數
            
        Returns:
            bool: 更新是否成功
        """
        try:
            print(f"[RANKING_MODULE] 更新參數: {year} {race} {session}")
            
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            
            if self._ranking_core:
                return self._ranking_core.update_analysis_parameters(
                    year=str(year),
                    race=race,
                    session=session
                )
            
            return False
            
        except Exception as e:
            print(f"❌ [RANKING_MODULE] 參數更新錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def refresh_analysis(self) -> bool:
        """
        刷新分析
        
        Returns:
            bool: 刷新是否成功
        """
        try:
            print("[RANKING_MODULE] 刷新分析...")
            
            if not self._ranking_core:
                print("❌ [RANKING_MODULE] MDI 核心未創建")
                return False
            
            # 重新載入資料
            self._ranking_core.load_initial_data()
            
            print("✅ [RANKING_MODULE] 分析已刷新")
            return True
            
        except Exception as e:
            print(f"❌ [RANKING_MODULE] 刷新失敗: {e}")
            return False
    
    def clear_data(self) -> bool:
        """
        清空資料
        
        Returns:
            bool: 清空是否成功
        """
        try:
            print("[RANKING_MODULE] 清空資料...")
            
            if self._ranking_core and hasattr(self._ranking_core, 'chart_widget'):
                self._ranking_core.chart_widget.clear_table()
                print("✅ [RANKING_MODULE] 資料已清空")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ [RANKING_MODULE] 清空資料失敗: {e}")
            return False
    
    def export_data(self, export_path: str, export_format: str = "csv") -> bool:
        """
        匯出資料
        
        Args:
            export_path: 匯出路徑
            export_format: 匯出格式
            
        Returns:
            bool: 匯出是否成功
        """
        try:
            print(f"[RANKING_MODULE] 匯出資料到: {export_path} (格式: {export_format})")
            
            # TODO: 實作匯出功能
            print("⚠️ [RANKING_MODULE] 匯出功能尚未實作")
            return False
            
        except Exception as e:
            print(f"❌ [RANKING_MODULE] 匯出失敗: {e}")
            return False
    
    def get_widget(self) -> Optional[QWidget]:
        """
        獲取主要元件
        
        Returns:
            QWidget: 主要元件（用於顯示在 MDI 視窗中）
        """
        return self._main_widget
    
    def get_title(self) -> str:
        """
        獲取模組標題
        
        Returns:
            str: 標題字串
        """
        if self.current_year and self.current_race and self.current_session:
            return f"Ideal Lap Ranking - {self.current_year} {self.current_race} {self.current_session}"
        return "Ideal Lap Ranking Table"
    
    def get_default_size(self) -> tuple:
        """
        獲取默認視窗尺寸
        
        Returns:
            tuple: (width, height)
        """
        return (1400, 900)
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """
        獲取當前資料
        
        Returns:
            Dict: 當前載入的資料
        """
        if self._ranking_core:
            return self._ranking_core._current_data
        return None
    
    def is_initialized(self) -> bool:
        """
        檢查模組是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._is_initialized
    
    def get_module_info(self) -> Dict[str, str]:
        """
        獲取模組資訊
        
        Returns:
            Dict: 模組資訊字典
        """
        return {
            "name": self._module_name,
            "display_name": self._display_name,
            "version": self._version,
            "description": self._description,
            "year": self.current_year or "N/A",
            "race": self.current_race or "N/A",
            "session": self.current_session or "N/A"
        }


# ========== 測試代碼 ==========
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow
    
    print("=" * 60)
    print("理想圈排名表格模組 - 獨立測試")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # 創建主視窗和 MDI 區域
    main_window = QMainWindow()
    main_window.setWindowTitle("Ideal Lap Ranking Module - Test")
    main_window.resize(1600, 1000)
    
    mdi_area = QMdiArea()
    main_window.setCentralWidget(mdi_area)
    
    # 創建模組
    print("\n📦 創建模組實例...")
    module = IdealLapRankingTableModule(
        parent=main_window,
        year="2025",
        race="Japan",
        session="R"
    )
    
    # 初始化模組
    print("\n🔧 初始化模組...")
    success = module.initialize_module(parent_widget=main_window)
    
    if success:
        print("✅ 模組初始化成功")
        
        # 獲取元件
        widget = module.get_widget()
        if widget:
            print(f"✅ 獲取元件成功: {type(widget).__name__}")
            
            # 如果 widget 有自己的 show 方法，直接顯示
            if hasattr(widget, 'show') and hasattr(widget, 'resize'):
                widget.setWindowTitle(module.get_title())
                widget.resize(1400, 900)
                widget.show()
            else:
                # 否則創建 MDI 子視窗
                sub_window = QMdiSubWindow()
                sub_window.setWidget(widget)
                sub_window.setWindowTitle(module.get_title())
                mdi_area.addSubWindow(sub_window)
                sub_window.show()
            
            # 載入資料
            print("\n📊 載入資料...")
            module.load_data()
            
            # 顯示模組資訊
            print("\n📋 模組資訊:")
            info = module.get_module_info()
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print("❌ 無法獲取元件")
    else:
        print("❌ 模組初始化失敗")
    
    main_window.show()
    
    sys.exit(app.exec_())
