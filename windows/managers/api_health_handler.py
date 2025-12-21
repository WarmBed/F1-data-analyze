# -*- coding: utf-8 -*-
"""
ApiHealthHandler - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.logger import get_logger
from core.api_runtime_state import update_health_state

logger = get_logger(__name__)


class ApiHealthHandler:
    """從 f1t_gui_main.py 提取的 on_api_health_result 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def on_api_health_result(self, result: dict) -> None:
        """Handle health check result coming back from the worker thread."""
        try:
            state = result.get('state', 'offline')
            manual = result.get('manual', False)
            base_url = result.get('base_url', self.main_window.api_base_url)
            details = [str(item) for item in result.get('details', [])]
            errors = [str(item) for item in result.get('errors', [])]
            latency = result.get('latency_ms')
            checked_at = result.get('checked_at')
            tooltip_lines = [f'API Base: {base_url}']
            if checked_at:
                tooltip_lines.append(f'Checked: {checked_at}')
            if latency is not None:
                tooltip_lines.append(f'Avg latency: {latency:.1f} ms')
            if details:
                tooltip_lines.extend(details)
            if errors:
                tooltip_lines.append('----')
                tooltip_lines.extend(errors)
            tooltip_text = '\n'.join(tooltip_lines)
            self.main_window._api_status_details = details
            if self.main_window.api_status_label:
                text_map = {
                    'online': '[API] ONLINE',
                    'degraded': '[API] DEGRADED',
                    'offline': '[API] OFFLINE',
                }
                color_map = {
                    'online': '#2ecc71',
                    'degraded': '#f1c40f',
                    'offline': '#e74c3c',
                }
                self.main_window.api_status_label.setText(text_map.get(state, '[API] UNKNOWN'))
                self.main_window.api_status_label.setStyleSheet(f"color: {color_map.get(state, '#95a5a6')}; font-weight: bold;")
                self.main_window.api_status_label.setToolTip(tooltip_text)
            if self.main_window.ready_label:
                if state == 'online':
                    self.main_window.ready_label.setText('[READY] API MODE')
                elif state == 'degraded':
                    self.main_window.ready_label.setText('[READY] API MODE (DEGRADED)')
                else:
                    self.main_window.ready_label.setText('[READY] LOCAL JSON MODE')
            self.main_window.api_mode_enabled = state != 'offline'
            update_health_state(state, tooltip_text)
            previous_state = getattr(self, '_api_last_state', 'unknown')
            self.main_window._api_last_state = state
            message_title = {
                'online': 'API Online',
                'degraded': 'API Degraded',
                'offline': 'API Offline',
            }.get(state, 'API Status')
            
            # ✅ 修復洩漏：只在手動觸發時顯示 QMessageBox
            # 自動輪詢（每 10 秒）只更新狀態欄，不彈窗
            if manual:
                if state == 'online':
                    QMessageBox.information(self.main_window, message_title, tooltip_text)
                elif state == 'degraded':
                    QMessageBox.warning(self.main_window, message_title, tooltip_text)
                else:
                    QMessageBox.warning(self.main_window, message_title, tooltip_text)
            # ❌ 已移除：自動輪詢時的彈窗邏輯（避免每 10 秒創建 QMessageBox 導致洩漏）
            # else:
            #     if state == 'offline' and previous_state != 'offline':
            #         QMessageBox.warning(self, message_title, tooltip_text)
            #     elif state == 'online' and previous_state in ('offline', 'degraded'):
            #         QMessageBox.information(self, 'API Restored', tooltip_text)
            #     elif state == 'degraded' and previous_state == 'online':
            #         QMessageBox.warning(self, message_title, tooltip_text)
            
            # 📊 日誌記錄（保留，用於調試和監控）
            if state == 'offline':
                logger.warning('API health check failed: %s', errors or details)
            elif state == 'degraded':
                logger.warning('API health degraded: %s', errors or details)
            else:
                logger.info('API health online (latency=%s ms)', latency)
        except Exception as exc:
            logger.error('Error processing API health result: %s', exc)
        finally:
            if self.main_window.check_api_action:
                self.main_window.check_api_action.setEnabled(True)
