"""
F1T Save Workspace Dialog
儲存 Workspace 配置對話框

版本: 2.0
創建日期: 2025-10-21
更新日期: 2025-10-22 - 多國語言化，移除客製化按鈕樣式
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QGroupBox, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from typing import Optional, Dict
import re
from core.gui_i18n import tr


class SaveWorkspaceDialog(QDialog):
    """儲存 Workspace 對話框"""
    
    workspace_saved = pyqtSignal(int, str)  # (workspace_id, workspace_name)
    
    def __init__(self, workspace_serializer, workspace_database, parent=None):
        """
        初始化對話框
        
        Args:
            workspace_serializer: WorkspaceSerializer 實例
            workspace_database: WorkspaceDatabase 實例
            parent: 父視窗
        """
        super().__init__(parent)
        self.serializer = workspace_serializer
        self.database = workspace_database
        self.config = None  # 序列化後的配置
        self.statistics = None  # 統計資訊
        
        self.setWindowTitle(tr('save_workspace_title', 'Save Workspace'))
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self._init_ui()
        self._load_workspace_data()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        
        # 標題
        title_label = QLabel(tr('save_workspace_dialog_title', 'Save Current Workspace'))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 基本資訊輸入區
        basic_group = self._create_basic_info_group()
        layout.addWidget(basic_group)
        
        # 統計資訊顯示區
        stats_group = self._create_statistics_group()
        layout.addWidget(stats_group)
        
        # 預覽區
        preview_group = self._create_preview_group()
        layout.addWidget(preview_group)
        
        # 按鈕區
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_basic_info_group(self) -> QGroupBox:
        """創建基本資訊輸入區"""
        group = QGroupBox(tr('workspace_basic_info', 'Basic Information'))
        layout = QFormLayout()
        
        # 名稱輸入
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(tr('workspace_name_placeholder', 'Enter workspace name (required)'))
        self.name_input.textChanged.connect(self._on_name_changed)
        layout.addRow(tr('workspace_name_required', 'Name *') + ":", self.name_input)
        
        # 名稱提示標籤
        self.name_hint = QLabel("")
        self.name_hint.setStyleSheet("color: #888; font-size: 10px;")
        layout.addRow("", self.name_hint)
        
        # 描述輸入
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(tr('workspace_description_placeholder', 'Enter workspace description (optional)'))
        self.description_input.setMaximumHeight(80)
        layout.addRow(tr('workspace_description_label', 'Description') + ":", self.description_input)
        
        # 標籤輸入
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText(tr('workspace_tags_placeholder', 'Enter tags, separated by commas'))
        layout.addRow(tr('workspace_tags_label', 'Tags') + ":", self.tags_input)
        
        group.setLayout(layout)
        return group
    
    def _create_statistics_group(self) -> QGroupBox:
        """創建統計資訊顯示區"""
        group = QGroupBox(tr('workspace_statistics', 'Workspace Statistics'))
        layout = QVBoxLayout()
        
        self.stats_label = QLabel(tr('workspace_loading_stats', 'Loading statistics...'))
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        layout.addWidget(self.stats_label)
        
        group.setLayout(layout)
        return group
    
    def _create_preview_group(self) -> QGroupBox:
        """創建預覽區"""
        group = QGroupBox(tr('workspace_preview', 'Save Preview'))
        layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setPlaceholderText(tr('workspace_preview_placeholder', 'Configuration preview will be displayed here...'))
        layout.addWidget(self.preview_text)
        
        group.setLayout(layout)
        return group
    
    def _create_button_layout(self) -> QHBoxLayout:
        """創建按鈕區"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        # 取消按鈕
        cancel_btn = QPushButton(tr('workspace_cancel', 'Cancel'))
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # 儲存按鈕（基本款，無客製化樣式）
        self.save_btn = QPushButton(tr('workspace_save_button', 'Save Workspace'))
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._on_save_clicked)
        layout.addWidget(self.save_btn)
        
        return layout
    
    def _load_workspace_data(self):
        """載入 Workspace 數據"""
        try:
            # 序列化當前 GUI 狀態
            self.config = self.serializer.serialize_workspace()
            
            if not self.config or not self.config.get("tabs"):
                QMessageBox.warning(
                    self,
                    tr('workspace_cannot_save', 'Cannot Save'),
                    tr('workspace_no_tabs_message', 'No tabs or windows to save.\nPlease open some analysis modules first.')
                )
                self.reject()
                return
            
            # 提取統計資訊
            self.statistics = self.serializer.extract_statistics(self.config)
            self._update_statistics_display()
            
            # 更新預覽
            self._update_preview()
            
            # 生成建議名稱
            suggested_name = self._generate_suggested_name()
            self.name_input.setText(suggested_name)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                tr('workspace_load_error', 'Error'),
                tr('workspace_load_data_failed', 'Failed to load workspace data: {error}').format(error=str(e))
            )
            import traceback
            traceback.print_exc()
            self.reject()
    
    def _generate_suggested_name(self) -> str:
        """生成建議的 Workspace 名稱"""
        from datetime import datetime
        
        # 從統計資訊中提取參數
        params = self.statistics.get("parameters", {})
        
        # 嘗試構建有意義的名稱
        parts = []
        
        # 年份
        if "year" in params and params["year"]:
            years = params["year"]
            if len(years) == 1:
                parts.append(str(years[0]))
        
        # 賽事
        if "race" in params and params["race"]:
            races = params["race"]
            if len(races) == 1:
                parts.append(races[0])
            elif len(races) <= 3:
                parts.append("_".join(races))
        
        # 會話
        if "session" in params and params["session"]:
            sessions = params["session"]
            if len(sessions) == 1:
                parts.append(sessions[0])
        
        # 如果沒有足夠資訊，使用日期
        if not parts:
            parts.append(datetime.now().strftime("%Y%m%d"))
        
        base_name = "_".join(parts)
        
        # 檢查名稱是否重複，自動附加序號
        return self._get_unique_name(base_name)
    
    def _get_unique_name(self, base_name: str) -> str:
        """
        獲取唯一名稱，如果重複則自動附加序號
        
        Args:
            base_name: 基礎名稱
            
        Returns:
            唯一名稱
        """
        # 檢查基礎名稱是否存在
        existing = self.database.get_workspace_by_name(base_name)
        if not existing:
            return base_name
        
        # 尋找可用的序號
        counter = 2
        while True:
            new_name = f"{base_name} ({counter})"
            existing = self.database.get_workspace_by_name(new_name)
            if not existing:
                return new_name
            counter += 1
            
            # 防止無限循環
            if counter > 100:
                import time
                return f"{base_name}_{int(time.time())}"
    
    def _update_statistics_display(self):
        """更新統計資訊顯示"""
        if not self.statistics:
            return
        
        total_tabs = self.statistics.get("total_tabs", 0)
        total_windows = self.statistics.get("total_windows", 0)
        window_types = self.statistics.get("window_types", {})
        parameters = self.statistics.get("parameters", {})
        
        # 構建顯示文字
        stats_text = f"{tr('workspace_total_tabs', 'Total Tabs')}: {total_tabs}\n"
        stats_text += f"{tr('workspace_total_windows', 'Total Windows')}: {total_windows}\n\n"
        
        # 視窗類型分布
        if window_types:
            stats_text += f"{tr('workspace_window_types', 'Window Type Distribution')}:\n"
            for window_type, count in sorted(window_types.items(), key=lambda x: x[1], reverse=True):
                type_name = self._translate_window_type(window_type)
                stats_text += f"  • {type_name}: {count}\n"
        
        # 參數資訊
        if parameters:
            stats_text += f"\n{tr('workspace_parameters', 'Parameter Information')}:\n"
            if "year" in parameters:
                stats_text += f"  • {tr('workspace_year', 'Year')}: {', '.join(map(str, parameters['year']))}\n"
            if "race" in parameters:
                stats_text += f"  • {tr('workspace_race', 'Race')}: {', '.join(parameters['race'])}\n"
            if "session" in parameters:
                stats_text += f"  • {tr('workspace_session', 'Session')}: {', '.join(parameters['session'])}\n"
        
        self.stats_label.setText(stats_text)
    
    def _translate_window_type(self, window_type: str) -> str:
        """翻譯視窗類型為中文"""
        translations = {
            "rain_analysis": "降雨分析",
            "tire_strategy": "輪胎策略",
            "track_analysis": "賽道分析",
            "accident_analysis": "事故分析",
            "pitstop_analysis": "進站分析",
            "season_progress": "賽季進度",
            "calendar": "賽程日曆",
            "ranking_table": "排名表",
            "lap_analysis": "單圈分析",
            "speed_acceleration": "速度加速度",
            "brake_analysis": "煞車分析",
            "throttle_analysis": "油門分析",
            "throttle_line_chart": "油門折線圖",
            "unknown": "未知類型"
        }
        return translations.get(window_type, window_type)
    
    def _update_preview(self):
        """更新預覽"""
        if not self.config:
            return
        
        import json
        preview_text = json.dumps(self.config, indent=2, ensure_ascii=False)
        
        # 限制預覽長度
        max_lines = 50
        lines = preview_text.split('\n')
        if len(lines) > max_lines:
            preview_text = '\n'.join(lines[:max_lines]) + f"\n\n... (省略 {len(lines) - max_lines} 行)"
        
        self.preview_text.setPlainText(preview_text)
    
    def _on_name_changed(self, text: str):
        """名稱輸入變更事件"""
        # 檢查名稱是否有效
        is_valid = bool(text.strip())
        self.save_btn.setEnabled(is_valid)
        
        # 檢查名稱是否重複
        if text.strip():
            existing = self.database.get_workspace_by_name(text.strip())
            if existing:
                self.name_hint.setText(tr('workspace_name_hint_exists', 'Name already exists, a number will be appended when saving'))
                self.name_hint.setStyleSheet("color: #ff9800; font-size: 10px;")
            else:
                self.name_hint.setText(tr('workspace_name_hint_available', 'Name available'))
                self.name_hint.setStyleSheet("color: #4CAF50; font-size: 10px;")
        else:
            self.name_hint.setText("")
    
    def _on_save_clicked(self):
        """儲存按鈕點擊事件"""
        try:
            # 獲取輸入值
            name = self.name_input.text().strip()
            description = self.description_input.toPlainText().strip()
            tags_text = self.tags_input.text().strip()
            
            if not name:
                QMessageBox.warning(
                    self, 
                    tr('workspace_validation_failed', 'Validation Failed'), 
                    tr('workspace_name_required_message', 'Please enter workspace name')
                )
                return
            
            # 確保名稱唯一
            final_name = self._get_unique_name(name)
            if final_name != name:
                reply = QMessageBox.question(
                    self,
                    tr('workspace_name_duplicate', 'Duplicate Name'),
                    tr('workspace_name_duplicate_message', "Name '{old_name}' already exists.\nUse '{new_name}' instead?").format(
                        old_name=name,
                        new_name=final_name
                    ),
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # 解析標籤
            tags = []
            if tags_text:
                tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            
            # 儲存到資料庫
            import json
            workspace_id = self.database.create_workspace(
                name=final_name,
                config_json=self.config,  # 傳入 dict，由 create_workspace 內部轉換
                description=description or "",
                tags=", ".join(tags) if tags else "",  # 將 list 轉換為逗號分隔的字串
                active_tab_index=self.config.get("active_tab_index", 0),
                total_tabs=self.statistics.get("total_tabs", 0),
                total_windows=self.statistics.get("total_windows", 0)
            )
            
            # 儲存元數據
            window_types = self.statistics.get("window_types", {})
            if window_types:
                self.database.set_window_types(workspace_id, window_types)
            
            parameters = self.statistics.get("parameters", {})
            if parameters:
                self.database.set_parameters(workspace_id, parameters)
            
            print(f"[WORKSPACE] Workspace saved: ID={workspace_id}, Name={final_name}")
            
            # 顯示成功訊息
            QMessageBox.information(
                self,
                tr('workspace_save_success', 'Save Successful'),
                tr('workspace_save_success_message', "Workspace '{name}' saved successfully!\n\n• Tabs: {tabs}\n• Windows: {windows}").format(
                    name=final_name,
                    tabs=self.statistics['total_tabs'],
                    windows=self.statistics['total_windows']
                )
            )
            
            # 發送信號
            self.workspace_saved.emit(workspace_id, final_name)
            
            # 關閉對話框
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                tr('workspace_save_failed', 'Save Failed'),
                tr('workspace_save_failed_message', 'Failed to save workspace: {error}').format(error=str(e))
            )
            import traceback
            traceback.print_exc()


# ============================================================================
# 測試代碼
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("SaveWorkspaceDialog 測試")
    print("=" * 60)
    print("\n⚠️ 注意：完整測試需要在 GUI 環境中執行")
    print("此測試僅驗證類別可以被導入")
    
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    print("\n[測試] 類別導入成功")
    print(f"[測試] SaveWorkspaceDialog 類別: {SaveWorkspaceDialog}")
    print(f"[測試] 信號定義: {SaveWorkspaceDialog.workspace_saved}")
    
    print("\n" + "=" * 60)
    print("基本測試完成！")
    print("=" * 60)
