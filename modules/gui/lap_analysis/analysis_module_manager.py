#!/usr/bin/env python3
"""
F1T 圈速分析模組管理器
管理多個圈速分析模組（速度、RPM、油門）的統計面板顯示
當開啟3個或以上模組時，自動隱藏詳細統計信息以節省界面空間
"""

from typing import Dict, List, Set
from PyQt5.QtCore import QObject, pyqtSignal

class AnalysisModuleManager(QObject):
    """圈速分析模組管理器 - 單例模式"""
    
    # 信號定義
    statistics_visibility_changed = pyqtSignal(bool)  # 統計面板顯示狀態變更
    module_count_changed = pyqtSignal(int)           # 活躍模組數量變更
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            super().__init__()
            
            # 活躍模組追蹤
            self._active_modules: Dict[str, object] = {}  # 模組ID -> 模組實例
            self._module_types: Set[str] = set()          # 活躍的模組類型
            
            # 配置
            self.HIDE_STATISTICS_THRESHOLD = 3  # 隱藏統計信息的模組數量閾值
            
            # 統計面板顯示狀態
            self._statistics_visible = True
            
            # 註冊的圖表組件（用於控制統計面板顯示）
            self._registered_chart_widgets: List[object] = []
            
            AnalysisModuleManager._initialized = True
            
            print(f"[ANALYSIS_MANAGER] Lap analysis module manager initialized")
    
    def register_module(self, module_id: str, module_instance: object, module_type: str = None):
        """註冊分析模組"""
        try:
            print(f"[ANALYSIS_MANAGER] Registering module: {module_id} (type: {module_type})")
            
            # 檢查是否為圈速分析模組
            if not self._is_lap_analysis_module(module_instance, module_type):
                print(f"[ANALYSIS_MANAGER] ⚠️ Not a lap analysis module, skipping: {module_id}")
                return False
            
            # 註冊模組
            self._active_modules[module_id] = module_instance
            if module_type:
                self._module_types.add(module_type)
            
            # 更新統計面板顯示狀態
            self._update_statistics_visibility()
            
            # 發送信號
            self.module_count_changed.emit(len(self._active_modules))
            
            print(f"[ANALYSIS_MANAGER] ✅ Module registered successfully: {module_id}")
            print(f"[ANALYSIS_MANAGER] 📊 Current active modules: {len(self._active_modules)}")
            print(f"[ANALYSIS_MANAGER] 📈 Active module types: {list(self._module_types)}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] [ANALYSIS_MANAGER] Module registration failed: {e}")
            return False
    
    def unregister_module(self, module_id: str):
        """解除註冊分析模組"""
        try:
            if module_id in self._active_modules:
                print(f"[ANALYSIS_MANAGER] Unregistering module: {module_id}")
                
                # 移除模組
                del self._active_modules[module_id]
                
                # 重新計算活躍模組類型
                self._module_types.clear()
                for module_instance in self._active_modules.values():
                    module_type = self._get_module_type(module_instance)
                    if module_type:
                        self._module_types.add(module_type)
                
                # 更新統計面板顯示狀態
                self._update_statistics_visibility()
                
                # 發送信號
                self.module_count_changed.emit(len(self._active_modules))
                
                print(f"[ANALYSIS_MANAGER] ✅ Module unregistered successfully: {module_id}")
                print(f"[ANALYSIS_MANAGER] 📊 Current active modules: {len(self._active_modules)}")
                
                return True
            else:
                print(f"[ANALYSIS_MANAGER] ⚠️ Module not registered, cannot unregister: {module_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] [ANALYSIS_MANAGER] Module unregistration failed: {e}")
            return False
    
    def register_chart_widget(self, chart_widget: object):
        """註冊圖表組件（用於控制統計面板）"""
        try:
            if chart_widget not in self._registered_chart_widgets:
                self._registered_chart_widgets.append(chart_widget)
                print(f"[ANALYSIS_MANAGER] Registered chart widget: {type(chart_widget).__name__}")
                
                # 立即應用當前的統計面板顯示狀態
                if hasattr(chart_widget, 'set_statistics_visibility'):
                    chart_widget.set_statistics_visibility(self._statistics_visible)
                
                return True
        except Exception as e:
            print(f"[ERROR] [ANALYSIS_MANAGER] Chart widget registration failed: {e}")
            return False
    
    def unregister_chart_widget(self, chart_widget: object):
        """解除註冊圖表組件"""
        try:
            if chart_widget in self._registered_chart_widgets:
                self._registered_chart_widgets.remove(chart_widget)
                print(f"[ANALYSIS_MANAGER] Unregistered chart widget: {type(chart_widget).__name__}")
                return True
        except Exception as e:
            print(f"[ERROR] [ANALYSIS_MANAGER] Chart widget unregistration failed: {e}")
            return False
    
    def _is_lap_analysis_module(self, module_instance: object, module_type: str = None) -> bool:
        """判斷是否為圈速分析模組"""
        try:
            # 方法1: 根據模組類型判斷
            if module_type:
                lap_analysis_types = [
                    'telemetry_speed', 'speed_analysis',
                    'telemetry_rpm', 'rpm_analysis',
                    'telemetry_throttle', 'throttle_analysis',
                    'telemetry_acceleration', 'acceleration_analysis'
                ]
                if any(analysis_type in module_type.lower() for analysis_type in lap_analysis_types):
                    return True
            
            # 方法2: 根據類名判斷
            class_name = type(module_instance).__name__.lower()
            if any(keyword in class_name for keyword in ['speed', 'rpm', 'throttle', 'acceleration']):
                if any(keyword in class_name for keyword in ['analysis', 'module']):
                    return True
            
            # 方法3: 根據模組路徑判斷
            module_path = str(type(module_instance).__module__)
            if 'lap_analysis' in module_path:
                return True
            
            return False
            
        except Exception as e:
            print(f"[ERROR] [ANALYSIS_MANAGER] 判斷模組類型失敗: {e}")
            return False
    
    def _get_module_type(self, module_instance: object) -> str:
        """獲取模組類型"""
        try:
            class_name = type(module_instance).__name__.lower()
            
            if 'speed' in class_name:
                return 'speed_analysis'
            elif 'rpm' in class_name:
                return 'rpm_analysis'  
            elif 'throttle' in class_name:
                return 'throttle_analysis'
            elif 'acceleration' in class_name:
                return 'acceleration_analysis'
            else:
                return 'unknown'
                
        except Exception as e:
            print(f"[ERROR] [ANALYSIS_MANAGER] 獲取模組類型失敗: {e}")
            return 'unknown'
    
    def _update_statistics_visibility(self):
        """更新統計面板顯示狀態"""
        try:
            active_count = len(self._active_modules)
            should_show_statistics = active_count < self.HIDE_STATISTICS_THRESHOLD
            
            if self._statistics_visible != should_show_statistics:
                print(f"[ANALYSIS_MANAGER] 📊 統計面板顯示狀態變更:")
                print(f"[ANALYSIS_MANAGER]   活躍模組數: {active_count}")
                print(f"[ANALYSIS_MANAGER]   閾值: {self.HIDE_STATISTICS_THRESHOLD}")
                print(f"[ANALYSIS_MANAGER]   {self._statistics_visible} → {should_show_statistics}")
                
                self._statistics_visible = should_show_statistics
                
                # 通知所有註冊的圖表組件
                self._notify_chart_widgets_visibility_change(should_show_statistics)
                
                # 發送信號
                self.statistics_visibility_changed.emit(should_show_statistics)
        
        except Exception as e:
            print(f"[ERROR] [ANALYSIS_MANAGER] 更新統計面板顯示狀態失敗: {e}")
    
    def _notify_chart_widgets_visibility_change(self, visible: bool):
        """通知所有圖表組件統計面板顯示狀態變更"""
        try:
            action_text = "顯示" if visible else "隱藏"
            print(f"[ANALYSIS_MANAGER] 📢 通知 {len(self._registered_chart_widgets)} 個圖表組件{action_text}統計面板")
            
            for chart_widget in self._registered_chart_widgets:
                try:
                    if hasattr(chart_widget, 'set_statistics_visibility'):
                        chart_widget.set_statistics_visibility(visible)
                        print(f"[ANALYSIS_MANAGER] ✅ {type(chart_widget).__name__} 統計面板{action_text}完成")
                    else:
                        print(f"[ANALYSIS_MANAGER] ⚠️ {type(chart_widget).__name__} 不支援統計面板控制")
                except Exception as e:
                    print(f"[ERROR] [ANALYSIS_MANAGER] 通知圖表組件失敗: {e}")
                    
        except Exception as e:
            print(f"[ERROR] [ANALYSIS_MANAGER] 通知圖表組件統計面板變更失敗: {e}")
    
    # 公共屬性和方法
    @property
    def active_module_count(self) -> int:
        """獲取活躍模組數量"""
        return len(self._active_modules)
    
    @property
    def statistics_visible(self) -> bool:
        """獲取統計面板顯示狀態"""
        return self._statistics_visible
    
    @property
    def active_module_types(self) -> List[str]:
        """獲取活躍模組類型列表"""
        return list(self._module_types)
    
    def get_module_info(self) -> Dict:
        """獲取模組管理信息"""
        return {
            'active_count': len(self._active_modules),
            'active_types': list(self._module_types),
            'statistics_visible': self._statistics_visible,
            'threshold': self.HIDE_STATISTICS_THRESHOLD,
            'registered_chart_widgets': len(self._registered_chart_widgets)
        }
    
    def force_update_visibility(self, visible: bool = None):
        """強制更新統計面板顯示狀態"""
        try:
            if visible is not None:
                self._statistics_visible = visible
            else:
                self._update_statistics_visibility()
                return
            
            # 通知所有圖表組件
            self._notify_chart_widgets_visibility_change(self._statistics_visible)
            
            # 發送信號
            self.statistics_visibility_changed.emit(self._statistics_visible)
            
            print(f"[ANALYSIS_MANAGER] 🔧 強制更新統計面板顯示狀態: {'顯示' if self._statistics_visible else '隱藏'}")
            
        except Exception as e:
            print(f"[ERROR] [ANALYSIS_MANAGER] 強制更新統計面板顯示狀態失敗: {e}")

# 全域管理器實例
analysis_module_manager = AnalysisModuleManager()

def get_analysis_module_manager() -> AnalysisModuleManager:
    """獲取圈速分析模組管理器實例"""
    return analysis_module_manager
