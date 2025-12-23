"""
F1T Load Workspace Dialog
載入 Workspace 配置對話框

版本: 1.0
創建日期: 2025-10-21
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTextEdit,
    QGroupBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from typing import List, Dict, Optional
import json
from datetime import datetime
from core.gui_i18n import tr


class LoadWorkspaceDialog(QDialog):
    """載入 Workspace 對話框"""
    
    workspace_selected = pyqtSignal(int, dict)  # (workspace_id, config)
    
    def __init__(self, workspace_database, parent=None):
        """
        初始化對話框
        
        Args:
            workspace_database: WorkspaceDatabase 實例
            parent: 父視窗
        """
        super().__init__(parent)
        self.database = workspace_database
        self.workspaces = []  # 所有 workspace 列表
        self.selected_workspace = None  # 選中的 workspace
        
        self.setWindowTitle(tr('load_workspace_title'))
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        self._init_ui()
        self._load_workspaces()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        
        # 標題
        title_label = QLabel(tr('load_workspace_title'))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 搜尋區
        search_layout = self._create_search_layout()
        layout.addLayout(search_layout)
        
        # Workspace 列表
        list_group = self._create_workspace_list_group()
        layout.addWidget(list_group)
        
        # 預覽區
        preview_group = self._create_preview_group()
        layout.addWidget(preview_group)
        
        # 按鈕區
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_search_layout(self) -> QHBoxLayout:
        """創建搜尋區"""
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel(tr('workspace_search')))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr('search_placeholder'))
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton(tr('refresh'))
        refresh_btn.clicked.connect(self._load_workspaces)
        layout.addWidget(refresh_btn)
        
        return layout
    
    def _create_workspace_list_group(self) -> QGroupBox:
        """創建 Workspace 列表區"""
        group = QGroupBox(tr('available_workspaces'))
        layout = QVBoxLayout()
        
        # 創建表格
        self.workspace_table = QTableWidget()
        self.workspace_table.setColumnCount(6)
        self.workspace_table.setHorizontalHeaderLabels([
            tr('workspace_id'), tr('workspace_name'), tr('tab_count'), 
            tr('window_count'), tr('created_time'), tr('description')
        ])
        
        # 設定表格屬性
        self.workspace_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.workspace_table.setSelectionMode(QAbstractItemView.ExtendedSelection)  # 支援 Ctrl/Shift 多選
        self.workspace_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.workspace_table.setAlternatingRowColors(True)
        
        # 設定欄位寬度
        header = self.workspace_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 名稱
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 分頁數
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 視窗數
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 建立時間
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # 描述
        
        # 連接選擇事件
        self.workspace_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.workspace_table.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        layout.addWidget(self.workspace_table)
        
        group.setLayout(layout)
        return group
    
    def _create_preview_group(self) -> QGroupBox:
        """創建預覽區"""
        group = QGroupBox(tr('workspace_details'))
        layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setPlaceholderText(tr('preview_placeholder'))
        layout.addWidget(self.preview_text)
        
        group.setLayout(layout)
        return group
    
    def _create_button_layout(self) -> QHBoxLayout:
        """創建按鈕區"""
        layout = QHBoxLayout()
        
        # 刪除按鈕
        self.delete_btn = QPushButton(tr('delete'))
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        layout.addWidget(self.delete_btn)
        
        layout.addStretch()
        
        # 取消按鈕
        cancel_btn = QPushButton(tr('cancel'))
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # 載入按鈕
        self.load_btn = QPushButton(tr('load_workspace_btn'))
        self.load_btn.setEnabled(False)
        self.load_btn.clicked.connect(self._on_load_clicked)
        layout.addWidget(self.load_btn)
        
        return layout
    
    def _load_workspaces(self):
        """載入所有 Workspace"""
        try:
            # 獲取所有 workspace（按修改時間降序）
            self.workspaces = self.database.list_workspaces(
                order_by="modified_at",
                ascending=False
            )
            
            self._populate_table(self.workspaces)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                tr('load_failed'),
                tr('load_workspaces_error').format(error=str(e))
            )
            import traceback
            traceback.print_exc()
    
    def _populate_table(self, workspaces: List[Dict]):
        """填充表格"""
        self.workspace_table.setRowCount(0)
        
        for workspace in workspaces:
            row = self.workspace_table.rowCount()
            self.workspace_table.insertRow(row)
            
            # 解析 config_json 獲取統計
            try:
                config = json.loads(workspace['config_json'])
                total_tabs = len(config.get('tabs', []))
                total_windows = sum(len(tab.get('mdi_windows', [])) for tab in config.get('tabs', []))
            except:
                total_tabs = 0
                total_windows = 0
            
            # ID
            id_item = QTableWidgetItem(str(workspace['id']))
            id_item.setData(Qt.UserRole, workspace)  # 儲存完整數據
            self.workspace_table.setItem(row, 0, id_item)
            
            # 名稱
            self.workspace_table.setItem(row, 1, QTableWidgetItem(workspace['name']))
            
            # 分頁數
            self.workspace_table.setItem(row, 2, QTableWidgetItem(str(total_tabs)))
            
            # 視窗數
            self.workspace_table.setItem(row, 3, QTableWidgetItem(str(total_windows)))
            
            # 建立時間
            created_at = datetime.fromisoformat(workspace['created_at'])
            time_str = created_at.strftime("%Y-%m-%d %H:%M")
            self.workspace_table.setItem(row, 4, QTableWidgetItem(time_str))
            
            # 描述
            description = workspace.get('description', '') or ''
            # 限制描述長度
            if len(description) > 50:
                description = description[:50] + "..."
            self.workspace_table.setItem(row, 5, QTableWidgetItem(description))
    
    def _on_search_changed(self, text: str):
        """搜尋文字變更事件"""
        if not text.strip():
            # 顯示所有
            self._populate_table(self.workspaces)
            return
        
        try:
            # 執行搜尋
            results = self.database.search_workspaces(keyword=text.strip())
            self._populate_table(results)
            
        except Exception as e:
            pass
    
    def _on_selection_changed(self):
        """選擇變更事件 - 支援多選"""
        selected_rows = self.workspace_table.selectionModel().selectedRows()
        
        if not selected_rows:
            self.selected_workspace = None
            self.load_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.preview_text.clear()
            return
        
        # 獲取第一個選中的 workspace（用於載入和預覽）
        first_row = selected_rows[0].row()
        id_item = self.workspace_table.item(first_row, 0)
        self.selected_workspace = id_item.data(Qt.UserRole)
        
        # 啟用按鈕
        self.load_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        
        # 更新預覽（顯示第一個選中的項目）
        self._update_preview()
    
    def _update_preview(self):
        """更新預覽"""
        if not self.selected_workspace:
            return
        
        try:
            workspace = self.selected_workspace
            config = json.loads(workspace['config_json'])
            
            # 構建預覽文字
            preview_lines = []
            preview_lines.append(tr('preview_name').format(name=workspace['name']))
            preview_lines.append(tr('preview_id').format(id=workspace['id']))
            preview_lines.append(tr('preview_created').format(time=workspace['created_at']))
            preview_lines.append(tr('preview_modified').format(time=workspace['modified_at']))
            
            if workspace.get('description'):
                preview_lines.append(f"\n{tr('description')}:\n{workspace['description']}")
            
            if workspace.get('tags'):
                preview_lines.append(tr('preview_tags').format(tags=workspace['tags']))
            
            # 統計資訊
            total_tabs = len(config.get('tabs', []))
            total_windows = sum(len(tab.get('mdi_windows', [])) for tab in config.get('tabs', []))
            
            preview_lines.append(f"\n{tr('preview_statistics')}")
            preview_lines.append(tr('preview_total_tabs').format(count=total_tabs))
            preview_lines.append(tr('preview_total_windows').format(count=total_windows))
            
            # 分頁詳情
            if config.get('tabs'):
                preview_lines.append(f"\n{tr('preview_tab_details')}")
                for i, tab in enumerate(config['tabs'], 1):
                    tab_name = tab.get('tab_name', f'Tab {i}')
                    window_count = len(tab.get('mdi_windows', []))
                    is_popped = tab.get('is_popped_out', False)
                    status = tr('preview_popped_out') if is_popped else ""
                    preview_lines.append(tr('preview_tab_entry').format(
                        index=i, name=tab_name, status=status, count=window_count
                    ))
            
            self.preview_text.setPlainText('\n'.join(preview_lines))
            
        except Exception as e:
            self.preview_text.setPlainText(f"預覽失敗: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _on_item_double_clicked(self, item):
        """項目雙擊事件 - 直接載入"""
        self._on_load_clicked()
    
    def _on_load_clicked(self):
        """載入按鈕點擊事件"""
        if not self.selected_workspace:
            return
        
        try:
            workspace = self.selected_workspace
            config = json.loads(workspace['config_json'])
            
            # 顯示確認對話框
            total_tabs = len(config.get('tabs', []))
            total_windows = sum(len(tab.get('mdi_windows', [])) for tab in config.get('tabs', []))
            
            reply = QMessageBox.question(
                self,
                tr('load_workspace_title'),
                tr('confirm_load_workspace').format(
                    name=workspace['name'],
                    tabs=total_tabs,
                    windows=total_windows
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 發送信號
                self.workspace_selected.emit(workspace['id'], config)
                
                # 關閉對話框
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                tr('load_failed'),
                tr('load_workspace_error').format(error=str(e))
            )
            import traceback
            traceback.print_exc()
    
    def _on_delete_clicked(self):
        """刪除按鈕點擊事件 - 支援批量刪除"""
        # 獲取所有選中的行
        selected_rows = self.workspace_table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
        
        # 收集所有選中的 workspace
        selected_workspaces = []
        for row_index in selected_rows:
            row = row_index.row()
            id_item = self.workspace_table.item(row, 0)
            workspace = id_item.data(Qt.UserRole)
            selected_workspaces.append(workspace)
        
        # 構建確認訊息
        count = len(selected_workspaces)
        if count == 1:
            # 單個刪除
            workspace = selected_workspaces[0]
            message = tr('confirm_delete_workspace').format(name=workspace['name'])
        else:
            # 批量刪除
            workspace_names = [ws['name'] for ws in selected_workspaces]
            names_list = '\n  • '.join(workspace_names)
            message = tr('confirm_delete_multiple_workspaces').format(
                count=count,
                names=names_list
            )
        
        reply = QMessageBox.question(
            self,
            tr('delete'),
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 刪除所有選中的 workspace
                success_count = 0
                failed_count = 0
                
                for workspace in selected_workspaces:
                    try:
                        self.database.delete_workspace(workspace['id'])
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                
                # 顯示結果
                if failed_count == 0:
                    # 全部成功
                    if count == 1:
                        message = tr('workspace_deleted').format(name=selected_workspaces[0]['name'])
                    else:
                        message = tr('workspaces_deleted_success').format(count=success_count)
                    
                    QMessageBox.information(
                        self,
                        tr('delete_success'),
                        message
                    )
                else:
                    # 部分失敗
                    message = tr('workspaces_deleted_partial').format(
                        success=success_count,
                        failed=failed_count
                    )
                    QMessageBox.warning(
                        self,
                        tr('delete_success'),
                        message
                    )
                
                # 重新載入列表
                self._load_workspaces()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr('delete_failed'),
                    tr('delete_workspace_error').format(error=str(e))
                )
                import traceback
                traceback.print_exc()


# ============================================================================
# 測試代碼
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("LoadWorkspaceDialog 測試")
    print("=" * 60)
    print("\n⚠️ 注意：完整測試需要在 GUI 環境中執行")
    print("此測試僅驗證類別可以被導入")
    
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    print("\n[測試] 類別導入成功")
    print(f"[測試] LoadWorkspaceDialog 類別: {LoadWorkspaceDialog}")
    print(f"[測試] 信號定義: {LoadWorkspaceDialog.workspace_selected}")
    
    print("\n" + "=" * 60)
    print("基本測試完成！")
    print("=" * 60)
