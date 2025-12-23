#!/usr/bin/env python3
"""
F1TV 登入對話框

用途: 提供 F1TV 帳號登入/管理介面
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.gui_i18n import tr


class F1TVAuthDialog(QDialog):
    """F1TV 帳號登入對話框"""
    
    auth_state_changed = pyqtSignal(bool)  # True = 已登入, False = 未登入
    
    def __init__(self, auth_manager, parent=None):
        """
        初始化對話框
        
        Args:
            auth_manager: F1TVAuthManager 實例
            parent: 父視窗
        """
        super().__init__(parent)
        self.auth_manager = auth_manager
        self._setup_ui()
        self._update_status_display()
        
        # 連接認證信號
        self.auth_manager.auth_success.connect(self._on_auth_success)
        self.auth_manager.auth_failed.connect(self._on_auth_failed)
        self.auth_manager.auth_status.connect(self._on_auth_status)
    
    def _setup_ui(self):
        """設置 UI"""
        self.setWindowTitle(tr('f1tv_login_title', 'F1TV Account'))
        self.setMinimumWidth(450)
        self.setMinimumHeight(300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 標題
        title_label = QLabel("F1TV Account")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 分隔線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 說明區域
        info_group = QGroupBox(tr('f1tv_info', 'Information'))
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel(tr(
            'f1tv_realtime_info',
            'Realtime Live Timing requires an active F1TV Pro subscription.\n'
            'Click "Login" to authenticate with your F1TV account.'
        ))
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666; padding: 5px;")
        info_layout.addWidget(info_label)
        layout.addWidget(info_group)
        
        # 狀態區域
        status_group = QGroupBox(tr('f1tv_status', 'Status'))
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(8)
        
        # 狀態標籤
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Status:"))
        self.lbl_status = QLabel()
        self.lbl_status.setStyleSheet("font-weight: bold;")
        status_row.addWidget(self.lbl_status)
        status_row.addStretch()
        status_layout.addLayout(status_row)
        
        # 訂閱標籤
        sub_row = QHBoxLayout()
        sub_row.addWidget(QLabel(tr('f1tv_subscription', 'Subscription') + ":"))
        self.lbl_subscription = QLabel("N/A")
        sub_row.addWidget(self.lbl_subscription)
        sub_row.addStretch()
        status_layout.addLayout(sub_row)
        
        # 到期時間標籤
        exp_row = QHBoxLayout()
        exp_row.addWidget(QLabel(tr('f1tv_expires', 'Expires') + ":"))
        self.lbl_expires = QLabel("N/A")
        exp_row.addWidget(self.lbl_expires)
        exp_row.addStretch()
        status_layout.addLayout(exp_row)
        
        layout.addWidget(status_group)
        
        # 狀態訊息 (登入中使用)
        self.lbl_auth_status = QLabel("")
        self.lbl_auth_status.setAlignment(Qt.AlignCenter)
        self.lbl_auth_status.setStyleSheet("color: #3498db; font-style: italic;")
        layout.addWidget(self.lbl_auth_status)
        
        # 按鈕區域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_login = QPushButton(tr('f1tv_login', 'Login'))
        self.btn_login.setMinimumWidth(100)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #e10600;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b30500;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.btn_login.clicked.connect(self._on_login_clicked)
        btn_layout.addWidget(self.btn_login)
        
        self.btn_logout = QPushButton(tr('f1tv_logout', 'Logout'))
        self.btn_logout.setMinimumWidth(100)
        self.btn_logout.clicked.connect(self._on_logout_clicked)
        btn_layout.addWidget(self.btn_logout)
        
        btn_layout.addStretch()
        
        self.btn_close = QPushButton(tr('close', 'Close'))
        self.btn_close.setMinimumWidth(80)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
        
        # 幫助連結
        help_label = QLabel(
            f'<a href="https://www.formula1.com/en/subscribe-to-f1-tv">'
            f'{tr("f1tv_how_to_subscribe", "How to subscribe to F1TV?")}</a>'
        )
        help_label.setOpenExternalLinks(True)
        help_label.setAlignment(Qt.AlignCenter)
        help_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(help_label)
    
    def _update_status_display(self):
        """更新狀態顯示"""
        token_info = self.auth_manager.get_token_info()
        
        if token_info is None:
            self.lbl_status.setText(tr('f1tv_not_logged_in', 'Not Logged In'))
            self.lbl_status.setStyleSheet("color: #888888; font-weight: bold;")
            self.lbl_subscription.setText("N/A")
            self.lbl_expires.setText("N/A")
            self.btn_login.setEnabled(True)
            self.btn_logout.setEnabled(False)
        elif token_info.get('expired'):
            self.lbl_status.setText(tr('f1tv_expired', 'Expired'))
            self.lbl_status.setStyleSheet("color: #f1c40f; font-weight: bold;")
            self.lbl_subscription.setText(token_info.get('product', 'N/A'))
            self.lbl_expires.setText(f"{token_info.get('exp_str', 'N/A')} (Expired)")
            self.btn_login.setEnabled(True)
            self.btn_logout.setEnabled(True)
        else:
            self.lbl_status.setText(tr('f1tv_logged_in', 'Logged In'))
            self.lbl_status.setStyleSheet("color: #2ecc71; font-weight: bold;")
            self.lbl_subscription.setText(token_info.get('product', 'F1TV'))
            self.lbl_expires.setText(token_info.get('exp_str', 'Unknown'))
            self.btn_login.setEnabled(False)
            self.btn_logout.setEnabled(True)
        
        self.lbl_auth_status.setText("")
    
    def _on_login_clicked(self):
        """開始登入流程"""
        self.btn_login.setEnabled(False)
        self.btn_login.setText(tr('f1tv_logging_in', 'Logging in...'))
        self.lbl_auth_status.setText(tr('f1tv_logging_in', 'Logging in...'))
        
        # 傳遞 self 作為 parent widget，讓 WebEngine 對話框可以正確顯示
        self.auth_manager.start_auth_flow(parent_widget=self)
    
    def _on_logout_clicked(self):
        """登出"""
        reply = QMessageBox.question(
            self,
            tr('confirm', 'Confirm'),
            tr('f1tv_logout_confirm', 'Are you sure you want to logout from F1TV?'),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.auth_manager.clear_token()
            self._update_status_display()
            self.auth_state_changed.emit(False)
    
    def _on_auth_success(self, token: str):
        """認證成功"""
        self.btn_login.setText(tr('f1tv_login', 'Login'))
        self._update_status_display()
        self.auth_state_changed.emit(True)
        QMessageBox.information(
            self,
            tr('success', 'Success'),
            tr('f1tv_login_success', 'Successfully logged in to F1TV!')
        )
    
    def _on_auth_failed(self, error: str):
        """認證失敗"""
        self.btn_login.setEnabled(True)
        self.btn_login.setText(tr('f1tv_login', 'Login'))
        self.lbl_auth_status.setText("")
        QMessageBox.warning(
            self,
            tr('error', 'Error'),
            tr('f1tv_login_failed', 'Login failed: {error}').format(error=error)
        )
    
    def _on_auth_status(self, status: str):
        """認證狀態更新"""
        self.lbl_auth_status.setText(status)
    
    def closeEvent(self, event):
        """關閉事件 - 取消正在進行的認證"""
        if hasattr(self.auth_manager, 'cancel_auth'):
            self.auth_manager.cancel_auth()
        super().closeEvent(event)
