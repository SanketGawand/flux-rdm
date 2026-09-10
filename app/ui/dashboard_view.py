import socket
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QByteArray
from PyQt6.QtGui import QPixmap, QPainter, QIcon
from PyQt6.QtSvg import QSvgRenderer


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


class DashboardView(QWidget):
    import_requested = pyqtSignal()
    vault_create_requested = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()
        self.refresh_stats()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header Section
        header_box = QVBoxLayout()
        header_box.setSpacing(4)
        title = QLabel("Remote Connections Hub")
        title.setStyleSheet("color: #f0f6fc; font-size: 20px; font-weight: 700;")
        subtitle = QLabel("Manage, launch, and monitor active remote desktop sessions and credentials.")
        subtitle.setStyleSheet("color: #8b949e; font-size: 13px;")
        header_box.addWidget(title)
        header_box.addWidget(subtitle)
        layout.addLayout(header_box)

        # Telemetry Card Row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        self.card_nodes = self._create_metric_card("CONFIGURED NODES", "0", "#58a6ff")
        self.card_groups = self._create_metric_card("ACTIVE GROUPS", "0", "#3fb950")
        self.card_coverage = self._create_metric_card("VAULT COVERAGE", "0%", "#bc8cff")
        self.card_unassigned = self._create_metric_card("UNPROTECTED NODES", "0", "#f85149")

        cards_layout.addWidget(self.card_nodes)
        cards_layout.addWidget(self.card_groups)
        cards_layout.addWidget(self.card_coverage)
        cards_layout.addWidget(self.card_unassigned)
        layout.addLayout(cards_layout)

        # Quick Connect Inline Toolbar
        qc_card = QFrame()
        qc_card.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #21262d;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        qc_layout = QHBoxLayout(qc_card)
        qc_layout.setContentsMargins(4, 2, 4, 2)
        qc_layout.setSpacing(10)

        qc_label = QLabel("Ad-hoc Target:")
        qc_label.setStyleSheet("color: #8b949e; font-weight: 600; font-size: 12px;")
        
        self.qc_input = QLineEdit()
        self.qc_input.setPlaceholderText("Enter IP or hostname (e.g. 192.168.1.50:3389)...")
        self.qc_input.setFixedHeight(30)
        self.qc_input.returnPressed.connect(self._on_quick_connect_triggered)

        self.qc_btn = QPushButton("Connect Direct")
        self.qc_btn.setObjectName("PrimaryBtn")
        self.qc_btn.setFixedHeight(30)
        self.qc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.qc_btn.clicked.connect(self._on_quick_connect_triggered)

        qc_layout.addWidget(qc_label)
        qc_layout.addWidget(self.qc_input, 1)
        qc_layout.addWidget(self.qc_btn)
        layout.addWidget(qc_card)

        # Recent Sessions Table
        recent_label = QLabel("RECENT & FREQUENT NODES")
        recent_label.setStyleSheet("color: #8b949e; font-weight: 700; font-size: 11px; letter-spacing: 0.8px;")
        layout.addWidget(recent_label)

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
        layout.addWidget(self.recent_table, 1)

        layout.addStretch()

        # Vibe Coder Credit Footer
        credit_label = QLabel("Vibe coded by: Sanket Gawand")
        credit_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        credit_label.setStyleSheet("color: #484f58; font-size: 14px; font-weight: 500; background: transparent; padding-top: 4px;")
        layout.addWidget(credit_label)

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

        # Update Telemetry Counters
        self.card_nodes.findChild(QLabel, "MetricVal").setText(str(stats.get("nodes", 0)))
        self.card_groups.findChild(QLabel, "MetricVal").setText(str(stats.get("groups", 0)))
        self.card_coverage.findChild(QLabel, "MetricVal").setText(f"{audit.get('coverage_pct', 0)}%")
        self.card_unassigned.findChild(QLabel, "MetricVal").setText(str(audit.get("unassigned", 0)))

        # Update Recent Table
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

            btn = QPushButton("Connect")
            btn.setObjectName("GhostBtn")
            btn.setFixedHeight(24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            conn_id = item.get("id")
            btn.clicked.connect(lambda _, cid=conn_id: self._launch_node(cid))

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
