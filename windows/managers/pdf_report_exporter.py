"""
PDF Report Exporter - 分頁截圖 PDF 導出器

將所有分頁內容截圖並生成 PDF 報告。

功能：
- 專業封面頁（年份、賽事、Session、模組列表）
- 遍歷所有 Tab（跳過 Home）
- 截圖每個 Tab 的內容
- 生成帶有 PitWall Logo 和時間戳記的 PDF
- 自動儲存至 report/ 資料夾

Author: F1T Development Team
Date: 2026-01-12
Updated: 2026-01-15 - Added cover page with professional layout
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple, Optional

from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QBuffer, QIODevice

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QMainWindow, QTabWidget

logger = logging.getLogger(__name__)


def tr(key: str, default: str = '') -> str:
    """Multi-language translation function"""
    try:
        from core.gui_i18n import tr as gui_tr
        return gui_tr(key, default)
    except ImportError:
        return default


class PDFReportExporter:
    """
    PDF Report Exporter
    
    Export all tab contents as a PDF report with:
    - Professional cover page with race info
    - PitWall Logo header
    - Timestamp
    - Tab name as page title
    """
    
    # Session display names mapping
    SESSION_NAMES = {
        'FP1': 'Free Practice 1',
        'FP2': 'Free Practice 2', 
        'FP3': 'Free Practice 3',
        'SQ': 'Sprint Qualifying',
        'S': 'Sprint Race',
        'Q': 'Qualifying',
        'R': 'Race'
    }
    
    def __init__(self, main_window: 'QMainWindow'):
        """
        Initialize PDF Report Exporter
        
        Args:
            main_window: Main window instance (StyleHMainWindow)
        """
        self.main_window = main_window
        self._register_fonts()
        logger.debug("[PDFReportExporter] Initialized")
    
    def _register_fonts(self) -> None:
        """Register custom fonts for PDF generation"""
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # Try to register Inter font (if available)
            font_paths = [
                Path.cwd() / 'fonts' / 'Inter-Bold.ttf',
                Path.cwd() / 'fonts' / 'Inter-Regular.ttf',
                Path.cwd() / 'fonts' / 'RobotoMono-Regular.ttf',
            ]
            
            import sys
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                meipass = Path(sys._MEIPASS)
                font_paths.extend([
                    meipass / 'fonts' / 'Inter-Bold.ttf',
                    meipass / 'fonts' / 'Inter-Regular.ttf', 
                    meipass / 'fonts' / 'RobotoMono-Regular.ttf',
                ])
            
            # Register fonts if they exist
            for font_path in font_paths:
                if font_path.exists():
                    font_name = font_path.stem.replace('-', '')
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                        logger.debug(f"[PDFReportExporter] Registered font: {font_name}")
                    except Exception as e:
                        logger.debug(f"[PDFReportExporter] Could not register {font_name}: {e}")
                        
        except Exception as e:
            logger.debug(f"[PDFReportExporter] Font registration skipped: {e}")
    
    def export_all_tabs_to_pdf(self) -> Optional[str]:
        """
        Export all tabs to a single PDF file
        
        Returns:
            str: Path to the generated PDF file, or None if failed
        """
        try:
            # Check if reportlab is available
            try:
                from reportlab.lib.pagesizes import A4, landscape
                from reportlab.lib.units import mm
                from reportlab.pdfgen import canvas
                from reportlab.lib.utils import ImageReader
            except ImportError:
                QMessageBox.critical(
                    self.main_window,
                    tr('pdf_export_error', 'PDF Export Error'),
                    tr('pdf_reportlab_missing', 
                       'reportlab library is not installed.\n\n'
                       'Please install it with:\npip install reportlab')
                )
                logger.error("[PDFReportExporter] reportlab not installed")
                return None
            
            # Get tab widget
            tab_widget = getattr(self.main_window, 'tab_widget', None)
            if tab_widget is None:
                logger.error("[PDFReportExporter] tab_widget not found")
                return None
            
            # Collect screenshots from all tabs (skip Home at index 0)
            screenshots: List[Tuple[str, QPixmap]] = []
            tab_count = tab_widget.count()
            
            if tab_count <= 1:
                QMessageBox.information(
                    self.main_window,
                    tr('pdf_export_info', 'PDF Export'),
                    tr('pdf_no_tabs', 'No tabs to export (Home tab is skipped).')
                )
                return None
            
            for i in range(1, tab_count):  # Skip Home (index 0)
                tab_name = tab_widget.tabText(i)
                tab_content = tab_widget.widget(i)
                
                if tab_content is None:
                    logger.debug(f"[PDFReportExporter] Tab {i} '{tab_name}' has no content, skipping")
                    continue
                
                # Check if tab has any visible content
                if not self._has_visible_content(tab_content):
                    logger.debug(f"[PDFReportExporter] Tab {i} '{tab_name}' is empty, skipping")
                    continue
                
                # Take screenshot of entire MDI area including all subwindows
                pixmap = self._capture_full_mdi_area(tab_content)
                if pixmap is None or pixmap.isNull():
                    logger.debug(f"[PDFReportExporter] Tab {i} '{tab_name}' screenshot failed, skipping")
                    continue
                
                screenshots.append((tab_name, pixmap))
                logger.debug(f"[PDFReportExporter] Captured tab {i}: '{tab_name}' ({pixmap.width()}x{pixmap.height()})")
            
            if not screenshots:
                QMessageBox.information(
                    self.main_window,
                    tr('pdf_export_info', 'PDF Export'),
                    tr('pdf_no_content', 'No tabs with content to export.')
                )
                return None
            
            # Create report directory
            report_dir = self._get_report_directory()
            report_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
            pdf_filename = f"PitWall_report_{timestamp}.pdf"
            pdf_path = report_dir / pdf_filename
            
            # Get logo path
            logo_path = self._get_logo_path()
            
            # Get session info from main window
            session_info = self._get_session_info()
            
            # Collect module names from tabs
            module_names = [tab_name for tab_name, _ in screenshots]
            
            # Generate PDF with cover page
            self._generate_pdf(
                pdf_path=str(pdf_path),
                screenshots=screenshots,
                logo_path=logo_path,
                timestamp=timestamp,
                session_info=session_info,
                module_names=module_names
            )
            
            # Show success message
            QMessageBox.information(
                self.main_window,
                tr('pdf_export_success', 'PDF Export Successful'),
                tr('pdf_export_saved', 'Report saved to:\n{path}').format(path=str(pdf_path))
            )
            
            logger.info(f"[PDFReportExporter] PDF exported: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"[PDFReportExporter] Export failed: {e}", exc_info=True)
            QMessageBox.critical(
                self.main_window,
                tr('pdf_export_error', 'PDF Export Error'),
                tr('pdf_export_failed', 'Failed to export PDF:\n{error}').format(error=str(e))
            )
            return None
    
    def _capture_full_mdi_area(self, mdi_widget: QWidget) -> Optional[QPixmap]:
        """
        Capture the full MDI area including all subwindows,
        even those that extend beyond the visible area.
        
        Args:
            mdi_widget: The MDI area widget (CustomMdiArea)
            
        Returns:
            QPixmap: Screenshot of the entire MDI area with all subwindows
        """
        from PyQt5.QtGui import QPainter
        from PyQt5.QtCore import QRect
        
        # Check if it's an MDI area with subwindows
        if not hasattr(mdi_widget, 'subWindowList'):
            # Not an MDI area, just grab the visible area
            return mdi_widget.grab()
        
        subwindows = mdi_widget.subWindowList()
        if not subwindows:
            return mdi_widget.grab()
        
        # Calculate the bounding box of all subwindows
        min_x = float('inf')
        min_y = float('inf')
        max_x = 0
        max_y = 0
        
        for subwindow in subwindows:
            if not subwindow.isVisible():
                continue
            geom = subwindow.geometry()
            min_x = min(min_x, geom.x())
            min_y = min(min_y, geom.y())
            max_x = max(max_x, geom.x() + geom.width())
            max_y = max(max_y, geom.y() + geom.height())
        
        # Handle case where no visible subwindows
        if min_x == float('inf'):
            return mdi_widget.grab()
        
        # Add some padding
        padding = 10
        min_x = max(0, min_x - padding)
        min_y = max(0, min_y - padding)
        max_x = max_x + padding
        max_y = max_y + padding
        
        # Calculate total size needed
        total_width = max(max_x, mdi_widget.width())
        total_height = max(max_y, mdi_widget.height())
        
        # Create a pixmap large enough for all content
        from PyQt5.QtGui import QPixmap as QPixmapClass
        full_pixmap = QPixmapClass(int(total_width), int(total_height))
        full_pixmap.fill(mdi_widget.palette().color(mdi_widget.backgroundRole()))
        
        # Render the MDI area onto the pixmap
        painter = QPainter(full_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Render each subwindow's CONTENT (without window frame)
        for subwindow in subwindows:
            if not subwindow.isVisible():
                continue
            
            geom = subwindow.geometry()
            
            # Try to grab only the widget content (without MDI window frame)
            inner_widget = subwindow.widget()
            if inner_widget:
                subwindow_pixmap = inner_widget.grab()
            else:
                subwindow_pixmap = subwindow.grab()
            
            # Draw it at the correct position
            painter.drawPixmap(geom.x(), geom.y(), subwindow_pixmap)
        
        painter.end()
        
        logger.debug(f"[PDFReportExporter] Full MDI capture: {total_width}x{total_height} with {len(subwindows)} subwindows")
        return full_pixmap
    
    def _has_visible_content(self, widget: QWidget) -> bool:
        """
        Check if a widget has visible content
        
        Args:
            widget: Widget to check
            
        Returns:
            bool: True if widget has visible content
        """
        # Check if it's a CustomMdiArea with subwindows
        if hasattr(widget, 'subWindowList'):
            subwindows = widget.subWindowList()
            return len(subwindows) > 0
        
        # Check if widget has children
        if widget.children():
            return True
        
        return widget.isVisible() and widget.width() > 0 and widget.height() > 0
    
    def _get_report_directory(self) -> Path:
        """
        Get or create the report directory
        
        Returns:
            Path: Path to the report directory
        """
        # Get project root directory
        if hasattr(self.main_window, 'get_resource_path'):
            base_path = Path(self.main_window.get_resource_path(''))
        else:
            base_path = Path.cwd()
        
        return base_path / 'report'
    
    def _get_logo_path(self) -> Optional[str]:
        """
        Get the PitWall logo path (純白底版本)
        
        Returns:
            str: Path to logo file, or None if not found
        """
        # Try multiple possible locations - 優先使用純白底 logo
        possible_paths = [
            Path.cwd() / 'image' / 'logo_pure_bw.png',
            Path.cwd() / 'image' / 'logo.png',
            Path.cwd() / 'image' / 'logo.ico',
        ]
        
        # Check for EXE mode
        import sys
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            meipass = Path(sys._MEIPASS)
            possible_paths.insert(0, meipass / 'image' / 'logo_pure_bw.png')
            possible_paths.insert(1, meipass / 'image' / 'logo.png')
            possible_paths.insert(2, meipass / 'image' / 'logo.ico')
        
        for path in possible_paths:
            if path.exists():
                logger.debug(f"[PDFReportExporter] Logo found: {path}")
                return str(path)
        
        logger.warning("[PDFReportExporter] Logo not found")
        return None
    
    def _get_session_info(self) -> dict:
        """
        Get current session information from main window
        
        Returns:
            dict: Session info with year, race, session keys
        """
        info = {
            'year': '2025',
            'race': 'Grand Prix',
            'session': 'R',
            'session_full': 'Race'
        }
        
        try:
            # Get from main window combo boxes
            if hasattr(self.main_window, 'year_combo'):
                info['year'] = self.main_window.year_combo.currentText()
                print(f"[PDFReportExporter] Year: {info['year']}")
            
            if hasattr(self.main_window, 'race_combo'):
                race_text = self.main_window.race_combo.currentText()
                # Extract race name (remove round number if present)
                if ' - ' in race_text:
                    info['race'] = race_text.split(' - ', 1)[1]
                else:
                    info['race'] = race_text
                print(f"[PDFReportExporter] Race: {info['race']}")
            
            if hasattr(self.main_window, 'session_combo'):
                session_code = self.main_window.session_combo.currentText()
                info['session'] = session_code
                info['session_full'] = self.SESSION_NAMES.get(session_code, session_code)
                print(f"[PDFReportExporter] Session: {session_code} -> {info['session_full']}")
            else:
                print("[PDFReportExporter] WARNING: session_combo not found on main_window")
                print(f"[PDFReportExporter] main_window type: {type(self.main_window)}")
                print(f"[PDFReportExporter] main_window attrs: {[a for a in dir(self.main_window) if 'combo' in a.lower()]}")
                
        except Exception as e:
            print(f"[PDFReportExporter] ERROR: Could not get session info: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[PDFReportExporter] Final session info: {info}")
        return info
    
    def _generate_pdf(
        self,
        pdf_path: str,
        screenshots: List[Tuple[str, QPixmap]],
        logo_path: Optional[str],
        timestamp: str,
        session_info: Optional[dict] = None,
        module_names: Optional[List[str]] = None
    ) -> None:
        """
        Generate the PDF file with cover page
        
        Args:
            pdf_path: Output PDF file path
            screenshots: List of (tab_name, pixmap) tuples
            logo_path: Path to logo file
            timestamp: Timestamp string
            session_info: Session information dict
            module_names: List of module names for cover page
        """
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        from io import BytesIO
        
        # Use landscape A4 for better display of wide content
        page_width, page_height = landscape(A4)
        
        # Create PDF
        c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
        
        # Margins - 減少邊距讓內容更大
        margin = 8 * mm
        header_height = 18 * mm
        
        # ===== COVER PAGE =====
        self._draw_cover_page(
            c, page_width, page_height,
            logo_path, timestamp,
            session_info or {},
            module_names or []
        )
        c.showPage()
        
        # ===== CONTENT PAGES =====
        for tab_name, pixmap in screenshots:
            # Draw header
            self._draw_page_header(
                c, page_width, page_height, 
                logo_path, tab_name, timestamp, 
                margin, header_height
            )
            
            # Calculate available space for image
            content_top = page_height - margin - header_height
            content_width = page_width - 2 * margin
            content_height = content_top - margin
            
            # Convert QPixmap to bytes for reportlab
            img_bytes = self._pixmap_to_bytes(pixmap)
            if img_bytes:
                img_reader = ImageReader(BytesIO(img_bytes))
                
                # Calculate scaled dimensions to fit content area
                img_width = pixmap.width()
                img_height = pixmap.height()
                
                # Scale to fit - allow scaling up to fill the available space
                scale_x = content_width / img_width
                scale_y = content_height / img_height
                scale = min(scale_x, scale_y)  # Fit within bounds, allow upscale
                
                final_width = img_width * scale
                final_height = img_height * scale
                
                # Center the image
                x = margin + (content_width - final_width) / 2
                y = margin + (content_height - final_height) / 2
                
                c.drawImage(img_reader, x, y, final_width, final_height)
            
            # Add new page for next screenshot
            c.showPage()
        
        c.save()
        logger.info(f"[PDFReportExporter] PDF saved: {pdf_path}")
    
    def _draw_page_header(
        self,
        c,
        page_width: float,
        page_height: float,
        logo_path: Optional[str],
        tab_name: str,
        timestamp: str,
        margin: float,
        header_height: float
    ) -> None:
        """
        Draw the page header with logo and title
        """
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from reportlab.lib.colors import HexColor
        
        # Header background - 純白色背景
        header_y = page_height - margin - header_height
        c.setFillColor(HexColor('#ffffff'))
        c.rect(margin, header_y, page_width - 2 * margin, header_height, fill=1, stroke=0)
        
        # Logo - 較小尺寸適應減少的 header
        logo_size = 14 * mm
        logo_x = margin + 3 * mm
        logo_y = header_y + (header_height - logo_size) / 2
        
        if logo_path and os.path.exists(logo_path):
            try:
                c.drawImage(
                    logo_path, logo_x, logo_y, 
                    logo_size, logo_size,
                    preserveAspectRatio=True, mask='auto'
                )
            except Exception as e:
                logger.warning(f"[PDFReportExporter] Failed to draw logo: {e}")
        
        # Title (Tab name) - 深色字體配合白色背景
        c.setFillColor(HexColor('#1a1a2e'))
        c.setFont("Helvetica-Bold", 14)
        title_x = logo_x + logo_size + 6 * mm
        title_y = header_y + header_height / 2 + 1 * mm
        c.drawString(title_x, title_y, f"PitWall Report - {tab_name}")
        
        # Timestamp - 深灰色字體，右側對齊
        c.setFont("Helvetica", 9)
        c.setFillColor(HexColor('#555555'))
        formatted_time = self._format_timestamp(timestamp)
        timestamp_text = f"Generated: {formatted_time}"
        timestamp_x = page_width - margin - c.stringWidth(timestamp_text, "Helvetica", 9) - 3 * mm
        timestamp_y = header_y + header_height / 2 - 2 * mm
        c.drawString(timestamp_x, timestamp_y, timestamp_text)
    
    def _draw_cover_page(
        self,
        c,
        page_width: float,
        page_height: float,
        logo_path: Optional[str],
        timestamp: str,
        session_info: dict,
        module_names: List[str]
    ) -> None:
        """
        Draw the professional cover page
        
        Layout (left-aligned, logo bottom-right):
        - Main title: {year} {race} Grand Prix
        - Subtitle: {session} Performance Debrief  
        - Separator line
        - Description text (3 lines)
        - Module list
        - Logo (bottom-right)
        """
        from reportlab.lib.units import mm
        from reportlab.lib.colors import HexColor
        
        # Extract session info
        year = session_info.get('year', '2025')
        race = session_info.get('race', 'Grand Prix')
        session_full = session_info.get('session_full', 'Race')
        
        # Clean race name - remove "Grand Prix" if already present to avoid duplication
        race_display = race.replace(' Grand Prix', '').replace('Grand Prix', '').strip()
        if not race_display:
            race_display = 'Grand Prix'
        
        # Margins - 減少左邊和上方空白
        margin_left = 15 * mm
        margin_top = 20 * mm
        
        # ===== WHITE BACKGROUND =====
        c.setFillColor(HexColor('#ffffff'))
        c.rect(0, 0, page_width, page_height, fill=1, stroke=0)
        
        # ===== MAIN TITLE =====
        # Use Helvetica-Bold as fallback (Inter-Bold if registered)
        try:
            c.setFont("InterBold", 36)
        except:
            c.setFont("Helvetica-Bold", 36)
        
        c.setFillColor(HexColor('#1a1a1a'))
        title_y = page_height - margin_top
        main_title = f"{year} {race_display} Grand Prix"
        c.drawString(margin_left, title_y, main_title)
        
        # ===== SUBTITLE =====
        try:
            c.setFont("InterBold", 24)
        except:
            c.setFont("Helvetica-Bold", 24)
        
        c.setFillColor(HexColor('#333333'))
        subtitle_y = title_y - 35
        subtitle = f"{session_full} Performance Debrief"
        c.drawString(margin_left, subtitle_y, subtitle)
        
        # ===== SEPARATOR LINE =====
        line_y = subtitle_y - 20
        c.setStrokeColor(HexColor('#cccccc'))
        c.setLineWidth(0.5)
        c.line(margin_left, line_y, page_width - 100 * mm, line_y)
        
        # ===== DESCRIPTION TEXT (Roboto Mono style) =====
        try:
            c.setFont("RobotoMonoRegular", 11)
        except:
            c.setFont("Courier", 11)
        
        c.setFillColor(HexColor('#555555'))
        desc_y = line_y - 25
        
        # 只顯示一行說明
        c.drawString(margin_left, desc_y, "PitWall Telemetry Analysis // Session Report")
        
        # ===== TAB LIST =====
        if module_names:
            module_y = desc_y - 35
            
            try:
                c.setFont("RobotoMonoRegular", 11)
            except:
                c.setFont("Courier", 11)
            
            c.setFillColor(HexColor('#333333'))
            c.drawString(margin_left, module_y, "Tabs:")
            
            c.setFillColor(HexColor('#555555'))
            for i, module_name in enumerate(module_names[:10]):  # Limit to 10 tabs
                bullet_y = module_y - 18 - (i * 16)
                c.drawString(margin_left + 10, bullet_y, f"  - {module_name}")
        
        # ===== LOGO (Right side, vertically centered) =====
        if logo_path and os.path.exists(logo_path):
            try:
                logo_width = 70 * mm
                logo_height = 70 * mm
                logo_x = page_width - 50 * mm - logo_width  # 從右邊留 50mm
                logo_y = (page_height - logo_height) / 2 - 20 * mm  # 垂直居中偏下
                
                c.drawImage(
                    logo_path, logo_x, logo_y,
                    logo_width, logo_height,
                    preserveAspectRatio=True, mask='auto'
                )
            except Exception as e:
                logger.warning(f"[PDFReportExporter] Failed to draw cover logo: {e}")
        
        # ===== TIMESTAMP (Bottom-Left) =====
        try:
            c.setFont("RobotoMonoRegular", 9)
        except:
            c.setFont("Courier", 9)
        
        c.setFillColor(HexColor('#888888'))
        formatted_time = self._format_timestamp(timestamp)
        c.drawString(margin_left, 30 * mm, f"Generated: {formatted_time}")
        
        logger.debug("[PDFReportExporter] Cover page drawn")
    
    def _format_timestamp(self, timestamp: str) -> str:
        """
        Format timestamp string for display
        
        Args:
            timestamp: Timestamp in format 'YYYY-MM-DD-HHMMSS'
            
        Returns:
            str: Formatted timestamp
        """
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d-%H%M%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return timestamp
    
    def _pixmap_to_bytes(self, pixmap: QPixmap) -> Optional[bytes]:
        """
        Convert QPixmap to PNG bytes
        
        Args:
            pixmap: QPixmap to convert
            
        Returns:
            bytes: PNG image data, or None if failed
        """
        try:
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            pixmap.save(buffer, "PNG")
            return bytes(buffer.data())
        except Exception as e:
            logger.error(f"[PDFReportExporter] Failed to convert pixmap: {e}")
            return None
