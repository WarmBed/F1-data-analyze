"""
F1 分析模組管理器
統一管理所有分析功能的模組化接口
"""

import os
import sys
import importlib
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

class AnalysisModuleBase(ABC):
    """分析模組基礎類"""
    
    def __init__(self, name: str, description: str, module_id: int):
        self.name = name
        self.description = description 
        self.module_id = module_id
        self.cache_enabled = True
        self.is_available = True
    
    @abstractmethod
    def analyze(self, **kwargs) -> Dict[str, Any]:
        """執行分析的抽象方法"""
        pass
    
    @abstractmethod
    def validate_parameters(self, **kwargs) -> bool:
        """驗證參數的抽象方法"""
        pass
    
    def get_module_info(self) -> Dict[str, Any]:
        """獲取模組資訊"""
        return {
            "name": self.name,
            "description": self.description,
            "module_id": self.module_id,
            "cache_enabled": self.cache_enabled,
            "is_available": self.is_available
        }

class F1AnalysisModuleManager:
    """F1 分析模組管理器"""
    
    def __init__(self):
        self.modules: Dict[int, Dict[str, Any]] = {}
        self.module_categories = {
            "weather": "🌧️ 天氣分析模組",
            "track": "🏁 賽道分析模組", 
            "strategy": "🔧 進站策略模組",
            "incidents": "🚨 意外分析模組",
            "driver": "🏎️ 車手分析模組",
            "comparison": "⚖️ 比較分析模組",
            "statistics": "📊 統計分析模組",
            "performance": "⚡ 性能分析模組",
            "system": "🔧 系統功能模組",
            "gui": "🖥️ GUI界面模組"
        }
        self.gui_modules_location = "modules/gui_modules/"
        self.initialize_modules()
    
    def initialize_modules(self):
        """初始化所有分析模組"""
        # =========================
        # 🌧️ 天氣分析模組
        # =========================
        
        # Function 1: 降雨強度分析
        self.register_module(
            module_id=1,
            name="降雨強度分析",
            description="分析比賽期間的降雨強度和天氣變化",
            category="weather",
            module_file="gui.rain_analysis.rain_intensity_analyzer_json_fixed",
            class_name="RainIntensityAnalyzer",
            parameters=["year", "race", "session"]
        )
        
        # =========================
        # 🏁 賽道分析模組
        # =========================
        
        # Function 2: 賽道分析
        self.register_module(
            module_id=2,
            name="賽道分析",
            description="分析賽道特性和駕駛路線",
            category="track",
            module_file="track_position_analysis",
            class_name="TrackAnalyzer",
            parameters=["year", "race", "session"]
        )
        
        # =========================
        # 🔧 進站策略模組
        # =========================
        
        # Function 3: 進站分析
        self.register_module(
            module_id=3,
            name="進站分析",
            description="分析進站策略和時間",
            category="strategy",
            module_file="pitstop_analysis_complete",
            class_name="PitstopAnalyzer",
            parameters=["year", "race", "session"]
        )
        
        # =========================
        # 🚨 意外分析模組
        # =========================
        
        # Function 4: 事故分析
        self.register_module(
            module_id=4,
            name="事故分析", 
            description="分析比賽中的事故和意外事件",
            category="incidents",
            module_file="accident_analysis",
            class_name="AccidentAnalyzer",
            parameters=["year", "race", "session"]
        )
        
        # =========================
        # 🏎️ 車手分析模組
        # =========================
        
        # Function 11: 單車手分析
        self.register_module(
            module_id=11,
            name="單車手分析",
            description="分析單一車手的詳細表現",
            category="driver",
            module_file="single_driver_analysis",
            class_name="SingleDriverAnalyzer",
            parameters=["year", "race", "session", "driver"]
        )
        
        # Function 12: 車手遙測分析
        self.register_module(
            module_id=12,
            name="車手遙測分析",
            description="分析車手的遙測數據",
            category="driver",
            module_file="driver_telemetry_analysis",
            class_name="DriverTelemetryAnalyzer",
            parameters=["year", "race", "session", "driver"]
        )
        
        # Function 13: 車手圈速分析
        self.register_module(
            module_id=13,
            name="車手圈速分析",
            description="分析車手的圈速表現",
            category="driver",
            module_file="driver_laptime_analysis",
            class_name="DriverLaptimeAnalyzer",
            parameters=["year", "race", "session", "driver"]
        )
        
        # =========================
        # ⚖️ 比較分析模組
        # =========================
        
        # Function 22: 距離差距分析
        self.register_module(
            module_id=22,
            name="距離差距分析",
            description="分析車手間的距離差距",
            category="comparison",
            module_file="distance_gap_analysis",
            class_name="DistanceGapAnalyzer",
            parameters=["year", "race", "session", "driver", "driver2"]
        )
        
        # =========================
        # 📊 統計分析模組
        # =========================
        
        # Function 15: 距離百分比分析
        self.register_module(
            module_id=15,
            name="距離百分比分析",
            description="基於百分比的距離統計分析",
            category="statistics",
            module_file="distance_percentage_analysis",
            class_name="DistancePercentageAnalyzer",
            parameters=["year", "race", "session"]
        )
        
        # =========================
        # 🔧 系統功能模組
        # =========================
        
        # Function 47: 數據載入
        self.register_module(
            module_id=47,
            name="數據載入",
            description="載入F1賽事數據",
            category="system",
            module_file="data_loader",
            class_name="DataLoader",
            parameters=["year", "race", "session"]
        )
        
    def register_module(self, module_id: int, name: str, description: str, 
                       category: str, module_file: str, class_name: str, 
                       parameters: List[str], **kwargs):
        """註冊分析模組"""
        self.modules[module_id] = {
            "name": name,
            "description": description,
            "category": category,
            "module_file": module_file,
            "class_name": class_name,
            "parameters": parameters,
            "is_available": True,
            "last_used": None,
            **kwargs
        }
    
    def get_module(self, module_id: int) -> Optional[Dict[str, Any]]:
        """獲取指定模組資訊"""
        return self.modules.get(module_id)
    
    def get_modules_by_category(self, category: str) -> List[Dict[str, Any]]:
        """根據類別獲取模組列表"""
        return [
            {**module, "module_id": module_id} 
            for module_id, module in self.modules.items() 
            if module.get("category") == category
        ]
    
    def get_all_modules(self) -> Dict[int, Dict[str, Any]]:
        """獲取所有模組"""
        return self.modules
    
    def load_module_class(self, module_id: int):
        """動態載入模組類"""
        module_info = self.get_module(module_id)
        if not module_info:
            raise ValueError(f"模組 ID {module_id} 不存在")
        
        try:
            # 動態導入模組
            module_name = module_info["module_file"]
            class_name = module_info["class_name"]
            
            # 確保模組路徑正確
            modules_path = os.path.join(os.path.dirname(__file__))
            if modules_path not in sys.path:
                sys.path.insert(0, modules_path)
            
            # 導入模組
            module = importlib.import_module(module_name)
            
            # 獲取類別
            module_class = getattr(module, class_name)
            return module_class
            
        except Exception as e:
            print(f"載入模組 {module_id} 失敗: {e}")
            self.modules[module_id]["is_available"] = False
            return None
    
    def execute_analysis(self, module_id: int, **kwargs) -> Dict[str, Any]:
        """執行指定模組的分析"""
        try:
            # 載入模組類
            module_class = self.load_module_class(module_id)
            if not module_class:
                return {
                    "success": False,
                    "error": f"模組 {module_id} 載入失敗"
                }
            
            # 創建實例並執行分析
            analyzer = module_class()
            
            # 驗證參數
            module_info = self.get_module(module_id)
            required_params = module_info.get("parameters", [])
            missing_params = [param for param in required_params if param not in kwargs]
            
            if missing_params:
                return {
                    "success": False,
                    "error": f"缺少必要參數: {missing_params}"
                }
            
            # 執行分析
            result = analyzer.analyze(**kwargs)
            
            # 更新最後使用時間
            from datetime import datetime
            self.modules[module_id]["last_used"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "module_id": module_id,
                "module_name": module_info["name"],
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "module_id": module_id,
                "error": str(e),
                "traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else None
            }
    
    def get_module_statistics(self) -> Dict[str, Any]:
        """獲取模組統計資訊"""
        total_modules = len(self.modules)
        available_modules = sum(1 for m in self.modules.values() if m.get("is_available", True))
        categories = {}
        
        for module in self.modules.values():
            category = module.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_modules": total_modules,
            "available_modules": available_modules,
            "unavailable_modules": total_modules - available_modules,
            "categories": categories,
            "category_descriptions": self.module_categories
        }
    
    def get_gui_modules_info(self) -> Dict[str, Any]:
        """獲取GUI模組資訊"""
        try:
            from .gui_modules import GUI_MODULE_INFO
            return GUI_MODULE_INFO
        except ImportError:
            return {
                "name": "GUI Modules",
                "location": self.gui_modules_location,
                "status": "Not Available",
                "error": "GUI modules not found"
            }
    
    def validate_module_availability(self) -> Dict[int, bool]:
        """驗證所有模組的可用性"""
        availability = {}
        for module_id in self.modules:
            try:
                module_class = self.load_module_class(module_id)
                availability[module_id] = module_class is not None
            except:
                availability[module_id] = False
        return availability

# 全域模組管理器實例
module_manager = F1AnalysisModuleManager()

# 便捷函數
def get_available_modules():
    """獲取可用的分析模組"""
    return {
        module_id: module 
        for module_id, module in module_manager.get_all_modules().items()
        if module.get("is_available", True)
    }

def execute_analysis_by_id(module_id: int, **kwargs):
    """根據模組ID執行分析"""
    return module_manager.execute_analysis(module_id, **kwargs)

def get_modules_by_category(category: str):
    """根據類別獲取模組"""
    return module_manager.get_modules_by_category(category)

if __name__ == "__main__":
    # 測試模組管理器
    print("🔧 F1 分析模組管理器")
    print("=" * 50)
    
    manager = F1AnalysisModuleManager()
    stats = manager.get_module_statistics()
    
    print(f"📊 模組統計:")
    print(f"   總模組數: {stats['total_modules']}")
    print(f"   可用模組: {stats['available_modules']}")
    print(f"   不可用模組: {stats['unavailable_modules']}")
    
    print(f"\n📋 類別分布:")
    for category, count in stats['categories'].items():
        description = stats['category_descriptions'].get(category, category)
        print(f"   {description}: {count}")
    
    print(f"\n🔍 模組可用性檢查:")
    availability = manager.validate_module_availability()
    for module_id, is_available in availability.items():
        module_info = manager.get_module(module_id)
        status = "✅" if is_available else "❌"
        print(f"   {status} 模組 {module_id}: {module_info['name']}")
