import os
import socket
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QLineEdit, QMenu, QGraphicsOpacityEffect, QDialog, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty, QThread, QByteArray, QTimer, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QPoint, QRect, QRectF, QUrl
from PyQt6.QtGui import QPixmap, QPainter, QIcon, QAction, QColor, QImage, QLinearGradient, QDesktopServices
from PyQt6.QtSvg import QSvgRenderer

from app.ui.theme import LOGO_SVG


def load_changelog_text() -> str:
    """Reads the separate changelog content from disk relative to this file or root."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(current_dir, "../../../CHANGELOG.md"),
        os.path.join(current_dir, "../../CHANGELOG.md"),
        os.path.join(current_dir, "../CHANGELOG.md"),
        os.path.join(current_dir, "CHANGELOG.md"),
        "CHANGELOG.md",
        "docs/CHANGELOG.md"
    ]
    
    check_dir = current_dir
    for _ in range(4):
        candidate = os.path.join(check_dir, "CHANGELOG.md")
        if os.path.exists(candidate):
            possible_paths.insert(0, candidate)
        check_dir = os.path.dirname(check_dir)

    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
    return ""


class ChangelogDialog(QDialog):
    """A clean, modal-independent dialog that can be dragged freely around the screen."""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Release Notes & Changelog")
        self.setFixedSize(560, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 1px solid #21262d;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Release Notes")
        header.setStyleSheet("color: #f0f6fc; font-size: 16px; font-weight: 700; background: transparent;")
        layout.addWidget(header)

        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #090d13;
                color: #c9d1d9;
                border: 1px solid #21262d;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
            }
        """)
        self.text_browser.setOpenExternalLinks(False)
        self.text_browser.anchorClicked.connect(self._handle_link_clicked)
        layout.addWidget(self.text_browser)

        # Bottom Action Bar with Direct Repo/Release Links & Close Button
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 0, 0, 0)
        bottom_bar.setSpacing(10)

        links_label = QLabel(
            "<a href='https://github.com/Sanket-Gawand/rdm-dashboard' style='color: #58a6ff; text-decoration: none;'>GitHub Repo</a> &nbsp;|&nbsp; "
            "<a href='https://github.com/Sanket-Gawand/rdm-dashboard/releases' style='color: #58a6ff; text-decoration: none;'>Release Updates</a>"
        )
        links_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        links_label.setOpenExternalLinks(False)
        links_label.linkActivated.connect(self._handle_link_clicked)
        links_label.setStyleSheet("background: transparent; font-size: 13px;")
        bottom_bar.addWidget(links_label)
        bottom_bar.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setObjectName("PrimaryBtn")
        close_btn.setFixedHeight(30)
        close_btn.setFixedWidth(90)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(close_btn)
        
        layout.addLayout(bottom_bar)

        self._load_changelog_content()

    def _handle_link_clicked(self, url: QUrl):
        if isinstance(url, str):
            url = QUrl(url)
        QDesktopServices.openUrl(url)

    def _load_changelog_content(self):
        content = load_changelog_text()
        if content:
            html_content = self._markdown_to_html(content)
            self.text_browser.setHtml(html_content)
        else:
            self.text_browser.setPlainText("Changelog file (CHANGELOG.md) could not be located in the project root.")

    def _markdown_to_html(self, md_text: str) -> str:
        lines = md_text.split("\n")
        html = ["<div style='font-family: -apple-system, BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;'>"]
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("## "):
                html.append(f"<h2 style='color: #58a6ff; border-bottom: 1px solid #21262d; padding-bottom: 4px; margin-top: 16px;'>{line_str[3:]}</h2>")
            elif line_str.startswith("### "):
                html.append(f"<h3 style='color: #8b949e; margin-top: 12px; margin-bottom: 4px;'>{line_str[4:]}</h3>")
            elif line_str.startswith("- "):
                html.append(f"<div style='color: #c9d1d9; margin: 2px 0 2px 0;'>• &nbsp;{line_str[2:]}</div>")
            elif line_str:
                html.append(f"<p style='color: #8b949e; margin: 4px 0;'>{line_str}</p>")
        html.append("</div>")
        return "".join(html)


def create_vault_status_widget(text: str, is_linked: bool) -> QWidget:
    """Creates a table cell widget containing a crisp programmatically rendered SVG icon and text label."""
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    layout = QHBoxLayout(container)
    layout.setContentsMargins(6, 2, 6, 2)
    layout.setSpacing(8)
    layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    icon_label = QLabel()
    icon_label.setFixedSize(18, 18)
    icon_label.setStyleSheet("background: transparent;")

    svg_check = "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='#3fb950' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='20 6 9 17 4 12'/></svg>"
    svg_alert = "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='#d29922' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><path d='M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z'/><line x1='12' y1='9' x2='12' y2='13'/><line x1='12' y1='17' x2='12.01' y2='17'/></svg>"

    pixmap_svg = svg_check if is_linked else svg_alert
    renderer = QSvgRenderer(QByteArray(pixmap_svg.encode('utf-8')))
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    icon_label.setPixmap(pixmap)

    text_label = QLabel(text)
    color = "#3fb950" if is_linked else "#d29922"
    text_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 500; background: transparent;")

    layout.addWidget(icon_label)
    layout.addWidget(text_label)
    layout.addStretch()

    return container


class PortProbeWorker(QThread):
    result_ready = pyqtSignal(str, bool, float)

    def __init__(self, host: str, port: int = 3389, timeout: float = 1.2):
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout

    def run(self):
        import time
        start = time.time()
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout):
                latency = (time.time() - start) * 1000
                self.result_ready.emit(self.host, True, latency)
        except Exception:
            self.result_ready.emit(self.host, False, 0.0)


class LogoOverlayWidget(QWidget):
    """Custom full-viewport overlay featuring a feathered wipe and a continuous, sub-pixel smooth scale animation."""
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #090d13;")
        
        renderer = QSvgRenderer(svg_path)
        self.logo_pixmap = QPixmap(420, 95)
        self.logo_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self.logo_pixmap)
        renderer.render(painter)
        painter.end()

        self._progress = 0.0
        self._scale_progress = 0.0

    def get_progress(self):
        return self._progress

    def set_progress(self, p):
        self._progress = max(0.0, min(2.0, p))
        self.update()

    progress = pyqtProperty(float, get_progress, set_progress)

    def get_scale_progress(self):
        return self._scale_progress

    def set_scale_progress(self, sp):
        self._scale_progress = max(0.0, min(1.0, sp))
        self.update()

    scale_progress = pyqtProperty(float, get_scale_progress, set_scale_progress)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        painter.fillRect(self.rect(), QColor("#090d13"))

        if self._progress <= 0.0:
            return

        lw = self.logo_pixmap.width()
        lh = self.logo_pixmap.height()

        # Continuous scale factor
        scale_factor = 0.8 + (0.40 * self._scale_progress)

        # Floating-point dimensions for sub-pixel accuracy and buttery-smooth interpolation
        scaled_w = lw * scale_factor
        scaled_h = lh * scale_factor
        x = (self.width() - scaled_w) / 2.0
        y = (self.height() - scaled_h) / 2.0

        if self._progress >= 2.0:
            return

        alpha_img = QImage(lw, lh, QImage.Format.Format_ARGB32_Premultiplied)
        alpha_img.fill(Qt.GlobalColor.transparent)

        img_painter = QPainter(alpha_img)
        img_painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        img_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        img_painter.drawPixmap(0, 0, lw, lh, self.logo_pixmap)
        img_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)

        feather = 80
        total_span = lw + feather

        if self._progress <= 1.0:
            # WIPE IN (0.0 to 1.0): reveals from left to right
            edge = total_span * self._progress
            gradient = QLinearGradient(edge - feather, 0, edge, 0)
            gradient.setColorAt(0.0, QColor(0, 0, 0, 255))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        else:
            # WIPE OUT (1.0 to 2.0): hides from left to right
            out_progress = self._progress - 1.0
            edge = total_span * out_progress
            gradient = QLinearGradient(edge - feather, 0, edge, 0)
            gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 255))

        img_painter.fillRect(0, 0, lw, lh, gradient)
        img_painter.end()

        # Render using QRectF for smooth hardware-accelerated transformation without step-choppiness
        target_rect = QRectF(x, y, scaled_w, scaled_h)
        painter.drawImage(target_rect, alpha_img, QRectF(alpha_img.rect()))


class DashboardView(QWidget):
    import_requested = pyqtSignal()
    vault_create_requested = pyqtSignal()
    ps_launch_requested = pyqtSignal(str)  # Emits conn_id for powershell launch

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.cascade_animations = []
        self._init_ui()
        self.refresh_stats()
        
        # Initial delay before starting the boot sequence
        QTimer.singleShot(600, self._start_logo_boot_sequence)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header Section
        self.header_container = QWidget()
        header_box = QHBoxLayout(self.header_container)
        header_box.setContentsMargins(0, 0, 0, 0)
        header_box.setSpacing(10)
        
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        title = QLabel("Remote Connections Hub")
        title.setStyleSheet("color: #f0f6fc; font-size: 20px; font-weight: 700;")
        subtitle = QLabel("Manage, launch, and monitor active remote desktop sessions and credentials.")
        subtitle.setStyleSheet("color: #8b949e; font-size: 13px;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        header_box.addWidget(title_widget, 1)

        # Changelog Button in Header
        self.changelog_btn = QPushButton("v1.1.0 Changelog")
        self.changelog_btn.setObjectName("GhostBtn")
        self.changelog_btn.setFixedHeight(28)
        self.changelog_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.changelog_btn.clicked.connect(self._show_changelog_dialog)
        header_box.addWidget(self.changelog_btn, 0, Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self.header_container)

        # Telemetry Card Row
        self.cards_container = QWidget()
        cards_layout = QHBoxLayout(self.cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(14)

        self.card_nodes = self._create_metric_card("CONFIGURED NODES", "0", "#58a6ff")
        self.card_groups = self._create_metric_card("ACTIVE GROUPS", "0", "#3fb950")
        self.card_coverage = self._create_metric_card("VAULT COVERAGE", "0%", "#bc8cff")
        self.card_unassigned = self._create_metric_card("UNPROTECTED NODES", "0", "#f85149")

        cards_layout.addWidget(self.card_nodes)
        cards_layout.addWidget(self.card_groups)
        cards_layout.addWidget(self.card_coverage)
        cards_layout.addWidget(self.card_unassigned)
        layout.addWidget(self.cards_container)

        # Quick Connect Inline Toolbar
        self.qc_card = QFrame()
        self.qc_card.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #21262d;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        qc_layout = QHBoxLayout(self.qc_card)
        qc_layout.setContentsMargins(4, 2, 4, 2)
        qc_layout.setSpacing(10)

        qc_label = QLabel("Ad-hoc Target:")
        qc_label.setStyleSheet("color: #8b949e; font-weight: 600; font-size: 12px;")
        
        self.qc_input = QLineEdit()
        self.qc_input.setPlaceholderText("Enter IP or hostname (e.g. 192.168.1.50:3389)...")
        self.qc_input.setFixedHeight(30)
        self.qc_input.returnPressed.connect(self._on_quick_connect_triggered)

        self.qc_btn = QPushButton("Connect RDP ▾")
        self.qc_btn.setObjectName("PrimaryBtn")
        self.qc_btn.setFixedHeight(30)
        self.qc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        qc_menu = QMenu(self)
        act_rdp = QAction("Connect via RDP", self)
        act_ps = QAction("Connect via PowerShell", self)
        act_rdp.triggered.connect(self._on_quick_connect_triggered)
        act_ps.triggered.connect(self._on_quick_connect_ps_triggered)
        qc_menu.addAction(act_rdp)
        qc_menu.addAction(act_ps)
        self.qc_btn.setMenu(qc_menu)

        qc_layout.addWidget(qc_label)
        qc_layout.addWidget(self.qc_input, 1)
        qc_layout.addWidget(self.qc_btn)
        layout.addWidget(self.qc_card)

        # Recent Sessions Table
        recent_label = QLabel("RECENT & FREQUENT NODES")
        recent_label.setStyleSheet("color: #8b949e; font-weight: 700; font-size: 11px; letter-spacing: 0.8px;")
        
        self.recent_container = QWidget()
        rc_layout = QVBoxLayout(self.recent_container)
        rc_layout.setContentsMargins(0, 0, 0, 0)
        rc_layout.addWidget(recent_label)
        
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(5)
        self.recent_table.setHorizontalHeaderLabels(["Node Name", "Endpoint", "Group", "Vault Status", "Action"])
        self.recent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.recent_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.recent_table.setColumnWidth(3, 160)
        self.recent_table.setColumnWidth(4, 110)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.recent_table.setStyleSheet("""
            QTableWidget {
                background-color: #0d1117;
                border: 1px solid #21262d;
                border-radius: 8px;
            }
        """)
        rc_layout.addWidget(self.recent_table, 1)
        layout.addWidget(self.recent_container, 1)

        layout.addStretch()

        # Vibe Coder Credit Footer
        self.credit_label = QLabel("Vibe coded by: Sanket Gawand")
        self.credit_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.credit_label.setStyleSheet("color: #484f58; font-size: 14px; font-weight: 500; background: transparent; padding-top: 4px;")
        layout.addWidget(self.credit_label)

        # -------------------------------------------------------------
        # DASHBOARD CASCADE ELEMENTS SETUP (HIDDEN INITIALLY)
        # -------------------------------------------------------------
        self.cascade_elements = [
            self.header_container,
            self.cards_container,
            self.qc_card,
            self.recent_container,
            self.credit_label
        ]
        
        for el in self.cascade_elements:
            el.hide()
            eff = QGraphicsOpacityEffect(el)
            eff.setOpacity(0.0)
            el.setGraphicsEffect(eff)

        # -------------------------------------------------------------
        # FULL-VIEWPORT FEATHERED WIPE OVERLAY (HIDDEN INITIALLY)
        # -------------------------------------------------------------
        self.logo_overlay = LogoOverlayWidget(LOGO_SVG.as_posix(), self)
        self.logo_overlay.hide()
        self.logo_overlay.setGeometry(self.rect())
        self.logo_overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'logo_overlay') and self.logo_overlay:
            self.logo_overlay.setGeometry(self.rect())

    def _show_changelog_dialog(self):
        if not hasattr(self, 'changelog_dlg') or self.changelog_dlg is None:
            self.changelog_dlg = ChangelogDialog(self)
        self.changelog_dlg.show()
        self.changelog_dlg.raise_()
        self.changelog_dlg.activateWindow()

    # --- CINEMATIC WIPE ANIMATION CONTROLLERS ---

    def _start_logo_boot_sequence(self):
        self.logo_overlay.show()
        
        # Continuous independent scale animation spanning the entire sequence with smooth ease-in/ease-out
        self.scale_anim = QPropertyAnimation(self.logo_overlay, b"scale_progress", self)
        self.scale_anim.setDuration(2000)
        self.scale_anim.setStartValue(0.0)
        self.scale_anim.setEndValue(1.0)
        self.scale_anim.setEasingCurve(QEasingCurve.Type.OutInCubic)
        self.scale_anim.start()

        self.anim_in = QPropertyAnimation(self.logo_overlay, b"progress", self)
        self.anim_in.setDuration(900)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0)
        self.anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        def on_wipe_in_finished():
            QTimer.singleShot(200, self._start_wipe_out)

        self.anim_in.finished.connect(on_wipe_in_finished)
        self.anim_in.start()

    def _start_wipe_out(self):
        if not hasattr(self, 'logo_overlay') or not self.logo_overlay:
            return

        self.anim_out = QPropertyAnimation(self.logo_overlay, b"progress", self)
        self.anim_out.setDuration(900)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(2.0)
        self.anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        
        def on_wipe_out_finished():
            if self.logo_overlay:
                self.logo_overlay.hide()
                self.logo_overlay.deleteLater()
                self.logo_overlay = None
            for el in self.cascade_elements:
                el.show()
            self._start_dashboard_cascade()

        self.anim_out.finished.connect(on_wipe_out_finished)
        self.anim_out.start()

    def _start_dashboard_cascade(self):
        delay = 0
        for el in self.cascade_elements:
            eff = el.graphicsEffect()
            
            anim_op = QPropertyAnimation(eff, b"opacity")
            anim_op.setDuration(600)
            anim_op.setStartValue(0.0)
            anim_op.setEndValue(1.0)
            anim_op.setEasingCurve(QEasingCurve.Type.InOutSine)
            
            orig_pos = el.pos()
            anim_pos = QPropertyAnimation(el, b"pos")
            anim_pos.setDuration(600)
            anim_pos.setStartValue(orig_pos + QPoint(0, 15))
            anim_pos.setEndValue(orig_pos)
            anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            group = QParallelAnimationGroup(self)
            group.addAnimation(anim_op)
            group.addAnimation(anim_pos)
            
            self.cascade_animations.append(group)
            QTimer.singleShot(delay, group.start)
            delay += 90

    # -------------------------------------------------------------

    def _create_metric_card(self, label: str, default_val: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #21262d;
                border-radius: 8px;
                padding: 14px 18px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(6)
        card_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(label)
        title.setStyleSheet("color: #8b949e; font-size: 11px; font-weight: 600; letter-spacing: 0.8px;")

        val = QLabel(default_val)
        val.setObjectName("MetricVal")
        val.setStyleSheet(f"color: {accent_color}; font-size: 26px; font-weight: 700; padding: 2px 0;")

        card_layout.addWidget(title)
        card_layout.addWidget(val)
        return card

    def refresh_stats(self):
        stats = self.db.get_stats()
        audit = self.db.get_security_audit()

        self.card_nodes.findChild(QLabel, "MetricVal").setText(str(stats.get("nodes", 0)))
        self.card_groups.findChild(QLabel, "MetricVal").setText(str(stats.get("groups", 0)))
        self.card_coverage.findChild(QLabel, "MetricVal").setText(f"{audit.get('coverage_pct', 0)}%")
        self.card_unassigned.findChild(QLabel, "MetricVal").setText(str(audit.get('unassigned', 0)))

        recent = self.db.fetch_recent_connections(6)
        self.recent_table.setRowCount(len(recent))

        for row, item in enumerate(recent):
            name_item = QTableWidgetItem(item.get("name", "Unknown"))
            name_item.setForeground(Qt.GlobalColor.white)

            endpoint_item = QTableWidgetItem(f"{item.get('host')}:{item.get('port', 3389)}")
            endpoint_item.setForeground(Qt.GlobalColor.gray)

            group_item = QTableWidgetItem(item.get("group_path") or "Root")
            
            vault_name = item.get("vault_name")
            if vault_name:
                status_widget = create_vault_status_widget(vault_name, is_linked=True)
            else:
                status_widget = create_vault_status_widget("Direct / Unlinked", is_linked=False)

            btn = QPushButton("Launch")
            btn.setObjectName("GhostBtn")
            btn.setFixedHeight(24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            conn_id = item.get("id")
            
            row_menu = QMenu(self)
            row_rdp = QAction("Connect RDP", self)
            row_ps = QAction("Connect PowerShell", self)
            row_rdp.triggered.connect(lambda _, cid=conn_id: self._launch_node(cid))
            row_ps.triggered.connect(lambda _, cid=conn_id: self.ps_launch_requested.emit(cid))
            row_menu.addAction(row_rdp)
            row_menu.addAction(row_ps)
            btn.setMenu(row_menu)

            self.recent_table.setItem(row, 0, name_item)
            self.recent_table.setItem(row, 1, endpoint_item)
            self.recent_table.setItem(row, 2, group_item)
            self.recent_table.setCellWidget(row, 3, status_widget)
            self.recent_table.setCellWidget(row, 4, btn)

    def _launch_node(self, conn_id: str):
        self.db.record_session_launch(conn_id)
        parent_window = self.window()
        if hasattr(parent_window, "_launch_session"):
            parent_window._launch_session(conn_id, fullscreen=False)
        self.refresh_stats()

    def _on_quick_connect_triggered(self):
        text = self.qc_input.text().strip()
        if not text:
            return

        parts = text.split(":")
        host = parts[0].strip()
        port = int(parts[1].strip()) if len(parts) > 1 and parts[1].isdigit() else 3389

        adhoc_conn = {
            "id": "adhoc_temp",
            "name": f"Ad-hoc ({host})",
            "host": host,
            "port": port,
            "username": "",
            "password": "",
            "domain": ""
        }
        parent_window = self.window()
        if hasattr(parent_window, "_launch_adhoc_session"):
            parent_window._launch_adhoc_session(adhoc_conn)

    def _on_quick_connect_ps_triggered(self):
        text = self.qc_input.text().strip()
        if not text:
            return
            
        parts = text.split(":")
        host = parts[0].strip()
        
        adhoc_id = f"adhoc_ps_{host}"
        
        parent_window = self.window()
        if hasattr(parent_window, "status_bar"):
            parent_window.status_bar.showMessage("Ad-hoc PowerShell requires saved credentials. Please create a node.")