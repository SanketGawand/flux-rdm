import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTreeView, QTabWidget, QTabBar, QMessageBox,
    QSplitter, QStatusBar, QMenu, QListWidget, QListWidgetItem, QLabel,
    QFileDialog, QDialog, QGraphicsOpacityEffect, QSizePolicy
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction, QKeySequence, QShortcut, QIcon
from PyQt6.QtCore import Qt, QModelIndex, QProcess, QTimeLine
from PyQt6.QtSvgWidgets import QSvgWidget

from app.storage.database import Database
from app.parser import parse_rdm_file
from app.exporter import export_to_csv, export_to_rdm, export_to_rdp_bundle
from app.ui.rdp_viewer import RDPViewerWidget
from app.ui.edit_dialog import EditConnectionDialog, VaultEntryDialog, AssignFolderVaultDialog
from app.ui.dashboard_view import DashboardView
from app.ui.theme import KEY_ICON, LOGO_SVG


def show_independent_question(title: str, message: str) -> bool:
    """Helper creating a native, movable confirmation dialog."""
    dialog = QDialog(None)
    dialog.setWindowTitle(title)
    dialog.setWindowFlags(
        Qt.WindowType.Window |
        Qt.WindowType.WindowTitleHint |
        Qt.WindowType.WindowCloseButtonHint |
        Qt.WindowType.CustomizeWindowHint
    )
    dialog.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
    dialog.resize(400, 160)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(14)

    body = QLabel(message)
    body.setWordWrap(True)
    body.setStyleSheet("font-size: 13px; color: #e6edf3;")
    layout.addWidget(body)

    layout.addStretch()

    btn_layout = QHBoxLayout()
    btn_layout.addStretch()

    no_btn = QPushButton("No")
    no_btn.setObjectName("GhostBtn")
    no_btn.clicked.connect(dialog.reject)

    yes_btn = QPushButton("Yes")
    yes_btn.setObjectName("PrimaryBtn")
    yes_btn.clicked.connect(dialog.accept)

    btn_layout.addWidget(no_btn)
    btn_layout.addWidget(yes_btn)
    layout.addLayout(btn_layout)

    return dialog.exec() == QDialog.DialogCode.Accepted


def show_independent_info(title: str, message: str):
    """Helper creating a native, movable information dialog."""
    dialog = QDialog(None)
    dialog.setWindowTitle(title)
    dialog.setWindowFlags(
        Qt.WindowType.Window |
        Qt.WindowType.WindowTitleHint |
        Qt.WindowType.WindowCloseButtonHint |
        Qt.WindowType.CustomizeWindowHint
    )
    dialog.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
    dialog.resize(380, 150)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(14)

    body = QLabel(message)
    body.setWordWrap(True)
    body.setStyleSheet("font-size: 13px; color: #e6edf3;")
    layout.addWidget(body)

    layout.addStretch()

    btn_layout = QHBoxLayout()
    btn_layout.addStretch()

    ok_btn = QPushButton("OK")
    ok_btn.setObjectName("PrimaryBtn")
    ok_btn.clicked.connect(dialog.accept)

    btn_layout.addWidget(ok_btn)
    layout.addLayout(btn_layout)

    dialog.exec()


class MainWindow(QMainWindow):
    EXPANDED_WIDTH = 356
    COLLAPSED_WIDTH = 54
    MIN_SIDEBAR_WIDTH = 256  # 240px logo width + 16px margins to prevent logo shrinking
    MAX_SIDEBAR_WIDTH = 750

    VAULT_COLLAPSED_HEIGHT = 36
    VAULT_DEFAULT_HEIGHT = 210

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flux RDM")
        self.resize(1440, 880)
        self.db = Database()
        self.sidebar_expanded = True
        self.vault_expanded = False
        self.last_vault_height = self.VAULT_DEFAULT_HEIGHT
        self.last_sidebar_width = self.EXPANDED_WIDTH
        self._picker_process = None
        self.empty_folders = set()

        self._build_ui()
        self._load_connections_to_tree()
        self._load_vault_list()

    def _build_ui(self):
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.main_splitter.setHandleWidth(4)
        self.main_splitter.setChildrenCollapsible(False)

        # ----------------- SIDEBAR -----------------
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setMinimumWidth(self.MIN_SIDEBAR_WIDTH)
        self.sidebar.setMaximumWidth(self.MAX_SIDEBAR_WIDTH)

        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(8, 12, 8, 12)
        self.sidebar_layout.setSpacing(10)
        self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Logo container with safe size policy preventing layout width panic
        self.logo_container = QWidget()
        self.logo_container.setFixedSize(240, 52)
        self.logo_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        logo_layout = QHBoxLayout(self.logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.logo_widget = QSvgWidget(LOGO_SVG.as_posix())
        self.logo_widget.setFixedSize(240, 52)
        self.logo_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.logo_widget.setStyleSheet("background: transparent;")
        
        self.logo_opacity = QGraphicsOpacityEffect(self.logo_widget)
        self.logo_widget.setGraphicsEffect(self.logo_opacity)
        self.logo_opacity.setOpacity(1.0)
        
        logo_layout.addWidget(self.logo_widget)
        self.sidebar_layout.addWidget(self.logo_container)

        # Placeholder spacer matching logo height for collapsed state layout stability
        self.logo_placeholder = QWidget()
        self.logo_placeholder.setFixedHeight(52)
        self.logo_placeholder.setVisible(False)
        self.sidebar_layout.addWidget(self.logo_placeholder)

        # Header Row containing Hamburger Button and Import/Export Controls below Logo
        self.header_row = QWidget()
        self.header_row.setFixedHeight(34)
        self.header_row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        hr_layout = QHBoxLayout(self.header_row)
        hr_layout.setContentsMargins(0, 0, 0, 0)
        hr_layout.setSpacing(6)
        hr_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.hamburger_btn = QPushButton("☰")
        self.hamburger_btn.setObjectName("GhostBtn")
        self.hamburger_btn.setFixedSize(38, 34)
        self.hamburger_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hamburger_btn.setToolTip("Toggle Sidebar (Ctrl+B)")
        self.hamburger_btn.setStyleSheet("font-size: 16px; font-weight: bold; padding: 0;")
        self.hamburger_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.hamburger_btn.clicked.connect(self.toggle_sidebar)
        hr_layout.addWidget(self.hamburger_btn)

        self.header_actions = QWidget()
        self.header_actions.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.actions_opacity = QGraphicsOpacityEffect(self.header_actions)
        self.header_actions.setGraphicsEffect(self.actions_opacity)
        self.actions_opacity.setOpacity(1.0)

        ha_layout = QHBoxLayout(self.header_actions)
        ha_layout.setContentsMargins(0, 0, 0, 0)
        ha_layout.setSpacing(4)

        self.import_btn = QPushButton("Import")
        self.import_btn.setObjectName("PrimaryBtn")
        self.import_btn.setFixedHeight(34)
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.clicked.connect(self._handle_import)

        self.export_btn = QPushButton("Export ▾")
        self.export_btn.setObjectName("GhostBtn")
        self.export_btn.setFixedHeight(34)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.export_menu = QMenu(self)
        act_export_rdm = QAction("Devolutions (.rdm)", self)
        act_export_rdp = QAction("RDP Archive (.zip)", self)
        act_export_csv = QAction("Spreadsheet (.csv)", self)

        act_export_rdm.triggered.connect(lambda: self._handle_export("rdm"))
        act_export_rdp.triggered.connect(lambda: self._handle_export("rdp"))
        act_export_csv.triggered.connect(lambda: self._handle_export("csv"))

        self.export_menu.addAction(act_export_rdm)
        self.export_menu.addAction(act_export_rdp)
        self.export_menu.addAction(act_export_csv)
        self.export_btn.setMenu(self.export_menu)

        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setObjectName("GhostBtn")
        self.refresh_btn.setToolTip("Refresh List")
        self.refresh_btn.setFixedSize(34, 34)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._refresh_all)

        ha_layout.addWidget(self.import_btn, 1)
        ha_layout.addWidget(self.export_btn, 1)
        ha_layout.addWidget(self.refresh_btn)
        
        hr_layout.addWidget(self.header_actions, 1)
        self.sidebar_layout.addWidget(self.header_row)

        self.slider_body = QWidget()
        
        self.slider_opacity = QGraphicsOpacityEffect(self.slider_body)
        self.slider_body.setGraphicsEffect(self.slider_opacity)
        self.slider_opacity.setOpacity(1.0)

        slider_layout = QVBoxLayout(self.slider_body)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        slider_layout.setSpacing(8)

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("SearchInput")
        self.search_bar.setPlaceholderText("Filter connections...")
        self.search_bar.setFixedHeight(32)
        self.search_bar.textChanged.connect(self._filter_tree)
        slider_layout.addWidget(self.search_bar)

        # --- Top Section: Sessions Header and Tree ---
        sessions_header_layout = QHBoxLayout()
        sessions_header_layout.setContentsMargins(0, 4, 0, 0)
        sessions_header_layout.setSpacing(4)

        sessions_label = QLabel("SESSIONS")
        sessions_label.setStyleSheet(
            "color: #58a6ff; font-weight: 700; font-size: 11px; letter-spacing: 0.8px;"
        )

        self.add_session_btn = QPushButton("+ New")
        self.add_session_btn.setObjectName("GhostBtn")
        self.add_session_btn.setFixedHeight(24)
        self.add_session_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_session_btn.clicked.connect(self._show_new_options_menu)

        sessions_header_layout.addWidget(sessions_label)
        sessions_header_layout.addStretch()
        sessions_header_layout.addWidget(self.add_session_btn)
        slider_layout.addLayout(sessions_header_layout)

        self.tree_view = QTreeView()
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Sessions"])
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setRootIsDecorated(True)
        self.tree_view.setAllColumnsShowFocus(True)
        self.tree_view.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.tree_view.setUniformRowHeights(True)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(18)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_tree_context_menu)
        self.tree_view.doubleClicked.connect(self._on_tree_double_clicked)
        slider_layout.addWidget(self.tree_view, 1)

        # --- Bottom Section: Collapsible Vault Container ---
        self.vault_container = QWidget()
        self.vault_container.setFixedHeight(self.VAULT_COLLAPSED_HEIGHT)
        vault_layout = QVBoxLayout(self.vault_container)
        vault_layout.setContentsMargins(0, 4, 0, 0)
        vault_layout.setSpacing(6)

        vault_header = QHBoxLayout()
        vault_header.setContentsMargins(0, 0, 0, 0)
        vault_header.setSpacing(4)

        self.vault_toggle_btn = QPushButton("▸ CREDENTIAL VAULT")
        self.vault_toggle_btn.setObjectName("GhostBtn")
        self.vault_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.vault_toggle_btn.setStyleSheet(
            "border: none; background: transparent; color: #58a6ff; "
            "font-weight: 700; font-size: 11px; letter-spacing: 0.8px; "
            "padding: 0; text-align: left;"
        )
        self.vault_toggle_btn.clicked.connect(self.toggle_vault_section)

        self.add_vault_btn = QPushButton("+ New")
        self.add_vault_btn.setObjectName("GhostBtn")
        self.add_vault_btn.setFixedHeight(24)
        self.add_vault_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_vault_btn.clicked.connect(self._create_vault_entry)

        vault_header.addWidget(self.vault_toggle_btn)
        vault_header.addStretch()
        vault_header.addWidget(self.add_vault_btn)
        vault_layout.addLayout(vault_header)

        self.vault_list = QListWidget()
        self.vault_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.vault_list.customContextMenuRequested.connect(self._show_vault_context_menu)
        self.vault_list.itemDoubleClicked.connect(self._edit_selected_vault_entry)
        self.vault_list.setVisible(False)
        vault_layout.addWidget(self.vault_list, 1)

        slider_layout.addWidget(self.vault_container)
        self.sidebar_layout.addWidget(self.slider_body, 1)

        # ----------------- WORKSPACE -----------------
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)

        self.dashboard_tab = DashboardView(self.db, self)
        self.dashboard_tab.import_requested.connect(self._handle_import)
        self.dashboard_tab.vault_create_requested.connect(self._create_vault_entry)

        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.tab_widget.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

        right_layout.addWidget(self.tab_widget)

        self.main_splitter.addWidget(self.sidebar)
        self.main_splitter.addWidget(right_container)
        self.main_splitter.setSizes([self.EXPANDED_WIDTH, 1440 - self.EXPANDED_WIDTH])
        self.main_splitter.setCollapsible(0, False)

        self.setCentralWidget(self.main_splitter)

        self.timeline = QTimeLine(220, self)
        self.timeline.setFrameRange(0, 100)
        self.timeline.frameChanged.connect(self._on_animation_step)
        self.timeline.finished.connect(self._on_animation_finished)

        self.vault_timeline = QTimeLine(200, self)
        self.vault_timeline.setFrameRange(0, 100)
        self.vault_timeline.frameChanged.connect(self._on_vault_animation_step)
        self.vault_timeline.finished.connect(self._on_vault_animation_finished)

        self.sidebar_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        self.sidebar_shortcut.activated.connect(self.toggle_sidebar)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Flux Ready")

    def toggle_vault_section(self):
        if self.vault_timeline.state() == QTimeLine.State.Running:
            self.vault_timeline.stop()

        current_h = self.vault_container.height()

        if self.vault_expanded:
            if current_h > self.VAULT_COLLAPSED_HEIGHT + 20:
                self.last_vault_height = current_h
            self.vault_anim_start_h = current_h
            self.vault_anim_end_h = self.VAULT_COLLAPSED_HEIGHT
            self.vault_toggle_btn.setText("▸ CREDENTIAL VAULT")
            self.vault_expanded = False
        else:
            self.vault_anim_start_h = current_h
            self.vault_anim_end_h = max(self.last_vault_height, 160)
            self.vault_list.setVisible(True)
            self.vault_toggle_btn.setText("▾ CREDENTIAL VAULT")
            self.vault_expanded = True

        self.vault_timeline.start()

    def _on_vault_animation_step(self, frame: int):
        progress = frame / 100.0
        ease = 1.0 - (1.0 - progress) * (1.0 - progress)
        curr_h = int(self.vault_anim_start_h + (self.vault_anim_end_h - self.vault_anim_start_h) * ease)
        self.vault_container.setFixedHeight(curr_h)

    def _on_vault_animation_finished(self):
        if not self.vault_expanded:
            self.vault_container.setFixedHeight(self.VAULT_COLLAPSED_HEIGHT)
            self.vault_list.setVisible(False)
        else:
            self.vault_container.setFixedHeight(self.vault_anim_end_h)
            self.vault_list.setVisible(True)

    def toggle_sidebar(self):
        if self.timeline.state() == QTimeLine.State.Running:
            self.timeline.stop()

        if self.sidebar_expanded:
            self.last_sidebar_width = max(self.sidebar.width(), self.MIN_SIDEBAR_WIDTH)
            self.anim_start_width = self.last_sidebar_width
            self.anim_end_width = self.COLLAPSED_WIDTH
            self.sidebar_expanded = False
            self.sidebar.setMinimumWidth(self.COLLAPSED_WIDTH)
            self.sidebar.setMaximumWidth(self.last_sidebar_width)
            
            handle = self.main_splitter.handle(1)
            if handle:
                handle.setEnabled(False)

            self.logo_container.setVisible(True)
            self.logo_widget.setVisible(True)
            self.logo_placeholder.setVisible(False)
            self.header_actions.setVisible(True)
            self.slider_body.setVisible(True)
        else:
            self.anim_start_width = self.sidebar.width()
            self.anim_end_width = self.last_sidebar_width
            self.sidebar_expanded = True
            self.sidebar.setMinimumWidth(self.MIN_SIDEBAR_WIDTH)
            self.sidebar.setMaximumWidth(self.MAX_SIDEBAR_WIDTH)
            
            handle = self.main_splitter.handle(1)
            if handle:
                handle.setEnabled(True)

            self.logo_placeholder.setVisible(False)
            self.logo_container.setVisible(True)
            self.logo_widget.setVisible(True)
            self.header_actions.setVisible(True)
            self.slider_body.setVisible(True)

        self.timeline.start()

    def _on_animation_step(self, frame: int):
        progress = frame / 100.0
        ease = 1.0 - (1.0 - progress) * (1.0 - progress)
        current_w = int(self.anim_start_width + (self.anim_end_width - self.anim_start_width) * ease)

        self.sidebar.setFixedWidth(current_w)

        if self.sidebar_expanded:
            opacity = progress
        else:
            opacity = 1.0 - progress

        self.logo_opacity.setOpacity(opacity)
        self.actions_opacity.setOpacity(opacity)
        self.slider_opacity.setOpacity(opacity)

        if not self.sidebar_expanded and current_w < 180:
            self.header_actions.setVisible(False)
            self.slider_body.setVisible(False)

    def _on_animation_finished(self):
        if self.sidebar_expanded:
            self.sidebar.setMinimumWidth(self.MIN_SIDEBAR_WIDTH)
            self.sidebar.setMaximumWidth(self.MAX_SIDEBAR_WIDTH)
            self.sidebar.setFixedWidth(self.last_sidebar_width)
            self.sidebar.setMinimumSize(self.MIN_SIDEBAR_WIDTH, 0)
            self.sidebar.setMaximumSize(self.MAX_SIDEBAR_WIDTH, 16777215)
            self.logo_opacity.setOpacity(1.0)
            self.actions_opacity.setOpacity(1.0)
            self.slider_opacity.setOpacity(1.0)
            self.logo_placeholder.setVisible(False)
            self.logo_container.setVisible(True)
            self.logo_widget.setVisible(True)
            self.header_actions.setVisible(True)
            self.slider_body.setVisible(True)
        else:
            self.sidebar.setFixedWidth(self.COLLAPSED_WIDTH)
            self.logo_opacity.setOpacity(0.0)
            self.actions_opacity.setOpacity(0.0)
            self.slider_opacity.setOpacity(0.0)
            self.logo_container.setVisible(False)
            self.logo_placeholder.setVisible(True)
            self.header_actions.setVisible(False)
            self.slider_body.setVisible(False)

    def _refresh_all(self):
        self._load_connections_to_tree()
        self._load_vault_list()
        self.dashboard_tab.refresh_stats()

    def _load_vault_list(self):
        self.vault_list.clear()
        creds = self.db.fetch_all_vault_creds()
        icon = QIcon(str(KEY_ICON))
        for c in creds:
            dom = f"{c['domain']}\\" if c.get('domain') else ""
            item = QListWidgetItem(icon, f"  {c['name']} ({dom}{c['username']})")
            item.setData(Qt.ItemDataRole.UserRole, c["id"])
            self.vault_list.addItem(item)

    def _create_vault_entry(self):
        folders = self._get_all_folders()
        dialog = VaultEntryDialog(available_folders=folders, parent=None)
        if dialog.exec():
            data = dialog.get_data()
            self.db.insert_or_update_vault_cred(data)

            scope, folder = dialog.get_apply_scope()
            if scope == "all":
                count = self.db.apply_credential_to_all(data["id"])
                self.status_bar.showMessage(f"Vault '{data['name']}' applied to {count} sessions.")
            elif scope == "folder" and folder:
                count = self.db.apply_credential_to_folder(folder, data["id"])
                self.status_bar.showMessage(f"Vault '{data['name']}' applied to {count} sessions in '{folder}'.")
            else:
                self.status_bar.showMessage(f"Added vault credential: {data['name']}")

            self._load_vault_list()
            self._load_connections_to_tree()
            self.dashboard_tab.refresh_stats()

    def _edit_selected_vault_entry(self, item: QListWidgetItem):
        cred_id = item.data(Qt.ItemDataRole.UserRole)
        cred = self.db.get_vault_cred(cred_id)
        if not cred:
            return

        folders = self._get_all_folders()
        dialog = VaultEntryDialog(cred, available_folders=folders, parent=None)
        if dialog.exec():
            data = dialog.get_data()
            self.db.insert_or_update_vault_cred(data)

            scope, folder = dialog.get_apply_scope()
            if scope == "all":
                count = self.db.apply_credential_to_all(data["id"])
                self.status_bar.showMessage(f"Vault '{data['name']}' updated and applied to {count} sessions.")
            elif scope == "folder" and folder:
                count = self.db.apply_credential_to_folder(folder, data["id"])
                self.status_bar.showMessage(f"Vault '{data['name']}' updated and applied to {count} sessions in '{folder}'.")
            else:
                self.status_bar.showMessage(f"Updated vault credential: {data['name']}")

            self._load_vault_list()
            self._load_connections_to_tree()
            self.dashboard_tab.refresh_stats()

    def _show_vault_context_menu(self, position):
        item = self.vault_list.itemAt(position)
        if not item:
            return
        cred_id = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu()
        edit_action = QAction("Edit Vault Credential...", self)
        apply_all_action = QAction("Apply to All Connections", self)
        delete_action = QAction("Delete Credential", self)

        edit_action.triggered.connect(lambda: self._edit_selected_vault_entry(item))
        apply_all_action.triggered.connect(lambda: self._apply_vault_to_all(cred_id))
        delete_action.triggered.connect(lambda: self._delete_vault_entry(cred_id))

        menu.addAction(edit_action)
        menu.addAction(apply_all_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(self.vault_list.viewport().mapToGlobal(position))

    def _apply_vault_to_all(self, cred_id: str):
        cred = self.db.get_vault_cred(cred_id)
        if not cred:
            return

        if show_independent_question(
            "Confirm Global Application",
            f"Assign '{cred['name']}' to ALL configured connections?"
        ):
            count = self.db.apply_credential_to_all(cred_id)
            self._load_connections_to_tree()
            self.status_bar.showMessage(f"Applied vault '{cred['name']}' to {count} sessions.")

    def _delete_vault_entry(self, cred_id: str):
        cred = self.db.get_vault_cred(cred_id)
        name = cred.get("name", "Credential") if cred else "Credential"
        if show_independent_question(
            "Delete Credential",
            f"Are you sure you want to delete vault credential '{name}'?"
        ):
            self.db.delete_vault_cred(cred_id)
            self._load_vault_list()
            self._load_connections_to_tree()
            self.dashboard_tab.refresh_stats()
            self.status_bar.showMessage(f"Deleted vault credential '{name}'.")

    def _show_new_options_menu(self):
        """Displays a dropdown menu for the Sessions '+ New' button giving options for Folder or Connection."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #1f6feb;
                color: #ffffff;
            }
        """)
        
        act_folder = QAction("New Folder...", self)
        act_conn = QAction("New Connection...", self)
        
        act_folder.triggered.connect(self._create_folder_dialog)
        act_conn.triggered.connect(self._create_connection_entry)
        
        menu.addAction(act_folder)
        menu.addAction(act_conn)
        
        btn_pos = self.add_session_btn.mapToGlobal(self.add_session_btn.rect().bottomLeft())
        menu.exec(btn_pos)

    def _create_folder_dialog(self):
        """Dialog to create an empty folder locally without dummy database records."""
        dialog = QDialog(self)
        dialog.setWindowTitle("New Folder")
        dialog.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.CustomizeWindowHint
        )
        dialog.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        dialog.resize(380, 150)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        label = QLabel("Enter Folder Name or Path (e.g., Production/AWS):")
        label.setStyleSheet("font-size: 13px; color: #e6edf3;")
        layout.addWidget(label)

        folder_input = QLineEdit()
        folder_input.setPlaceholderText("e.g. Database Servers")
        folder_input.setFixedHeight(30)
        layout.addWidget(folder_input)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("GhostBtn")
        cancel_btn.clicked.connect(dialog.reject)

        create_btn = QPushButton("Create")
        create_btn.setObjectName("PrimaryBtn")
        create_btn.clicked.connect(dialog.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(create_btn)
        layout.addLayout(btn_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            folder_path = folder_input.text().strip()
            if folder_path:
                self.empty_folders.add(folder_path)
                self._load_connections_to_tree()
                self.dashboard_tab.refresh_stats()
                self.status_bar.showMessage(f"Created folder: {folder_path}")

    def _get_all_folders(self) -> list:
        db_folders = self.db.get_unique_folders()
        combined = set(db_folders) | self.empty_folders
        return sorted(list(combined))

    def _create_connection_entry(self):
        vault_creds = self.db.fetch_all_vault_creds()
        existing_folders = self._get_all_folders()
        dummy_conn = {
            "id": "",
            "name": "",
            "host": "",
            "port": 3389,
            "group_path": "",
            "credential_id": None
        }
        dialog = EditConnectionDialog(dummy_conn, vault_creds, available_folders=existing_folders, parent=None)
        dialog.setWindowTitle("New Connection")
        if dialog.exec():
            updated = dialog.get_data()
            if not updated.get("id"):
                import uuid
                updated["id"] = str(uuid.uuid4())
            self.db.insert_or_update(updated)
            self._load_connections_to_tree()
            self.dashboard_tab.refresh_stats()
            self.status_bar.showMessage(f"Created connection: {updated['name']}")

    def _load_connections_to_tree(self):
        # 1. Capture currently expanded folder paths
        expanded_paths = set()
        def _capture_expanded(parent_index):
            for r in range(self.tree_model.rowCount(parent_index)):
                idx = self.tree_model.index(r, 0, parent_index)
                if self.tree_view.isExpanded(idx):
                    path = self.tree_model.data(idx, Qt.ItemDataRole.UserRole + 1)
                    if path:
                        expanded_paths.add(path)
                    _capture_expanded(idx)
                    
        _capture_expanded(QModelIndex())

        # 2. Clear and rebuild the tree
        self.tree_model.clear()
        connections = self.db.fetch_all()
        root_node = self.tree_model.invisibleRootItem()
        folder_nodes = {}

        # Collect all active group paths from DB plus user-created empty folders
        all_group_paths = set(self.empty_folders)
        for conn in connections:
            gp = conn.get("group_path", "").strip()
            if gp and not conn.get("is_placeholder", False):
                all_group_paths.add(gp)

        # Build folder nodes hierarchy
        for group_path in sorted(all_group_paths):
            group_parts = group_path.split("/")
            current_parent = root_node
            accumulated_path = ""
            for part in group_parts:
                if not part:
                    continue
                accumulated_path += f"/{part}" if accumulated_path else part
                if accumulated_path not in folder_nodes:
                    folder_item = QStandardItem(part)
                    folder_item.setData(accumulated_path, Qt.ItemDataRole.UserRole + 1)
                    folder_item.setEditable(False)
                    current_parent.appendRow(folder_item)
                    folder_nodes[accumulated_path] = folder_item
                current_parent = folder_nodes[accumulated_path]

        # Populate actual connection leaves with a bullet/server bullet indicator
        for conn in connections:
            if conn.get("is_placeholder", False):
                continue
            group_path = conn.get("group_path", "").strip()
            current_parent = folder_nodes.get(group_path, root_node)

            leaf_item = QStandardItem(f"•  {conn['name']} ({conn['host']})")
            leaf_item.setData(conn["id"], Qt.ItemDataRole.UserRole)
            leaf_item.setEditable(False)
            current_parent.appendRow(leaf_item)

        # 3. Restore the expanded states using the exact paths
        for path, folder_item in folder_nodes.items():
            if path in expanded_paths:
                self.tree_view.expand(folder_item.index())

    def _filter_tree(self, query: str):
        query = query.lower().strip()
        for i in range(self.tree_model.rowCount()):
            item = self.tree_model.item(i)
            self._filter_item_recursive(item, query)

    def _filter_item_recursive(self, item: QStandardItem, query: str) -> bool:
        text_matches = query in item.text().lower()
        child_matches = False

        for r in range(item.rowCount()):
            if self._filter_item_recursive(item.child(r), query):
                child_matches = True

        visible = text_matches or child_matches
        index = item.index()
        self.tree_view.setRowHidden(index.row(), index.parent(), not visible)
        return visible

    def _handle_import(self):
        self._picker_process = QProcess(self)
        cmd_args = [
            "-m", "app.utils.picker",
            "Import Devolutions .rdm file",
            "/home/appuser/imports",
            "RDM Files (*.rdm);;All Files (*)"
        ]

        def on_picker_finished(exit_code, exit_status):
            if exit_code != 0:
                return

            raw_output = bytes(self._picker_process.readAllStandardOutput()).decode("utf-8").strip()
            if not raw_output:
                return

            file_path = raw_output.splitlines()[-1].strip()
            if not file_path:
                return

            try:
                records = parse_rdm_file(file_path)
                for r in records:
                    self.db.insert_or_update(r)
                self._load_connections_to_tree()
                self.dashboard_tab.refresh_stats()
                show_independent_info("Import Success", f"Imported {len(records)} connections successfully.")
            except Exception as e:
                show_independent_info("Import Failed", f"Could not read .rdm file:\n{str(e)}")

        self._picker_process.finished.connect(on_picker_finished)
        self._picker_process.start(sys.executable, cmd_args)

    def _handle_export(self, export_format: str):
        connections = self.db.fetch_all()
        if not connections:
            show_independent_info("Export Empty", "No connection records available to export.")
            return

        target_dir = "/home/appuser/imports"
        if not Path(target_dir).exists():
            target_dir = str(Path.home())

        file_dialog = QFileDialog(None, "", f"{target_dir}/", "")
        file_dialog.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.CustomizeWindowHint
        )
        file_dialog.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

        if export_format == "rdm":
            file_dialog.setWindowTitle("Export to Devolutions .rdm")
            file_dialog.setNameFilter("Devolutions RDM (*.rdm);;All Files (*)")
            file_dialog.selectFile("flux_export.rdm")
            if file_dialog.exec() == QDialog.DialogCode.Accepted:
                sel = file_dialog.selectedFiles()
                if sel:
                    try:
                        content = export_to_rdm(connections)
                        Path(sel[0]).write_text(content, encoding="utf-8")
                        show_independent_info("Export Complete", f"Saved {len(connections)} sessions to:\n{sel[0]}")
                    except Exception as e:
                        show_independent_info("Export Failed", str(e))

        elif export_format == "rdp":
            file_dialog.setWindowTitle("Export RDP Files Archive")
            file_dialog.setNameFilter("ZIP Archives (*.zip);;All Files (*)")
            file_dialog.selectFile("flux_rdp_bundle.zip")
            if file_dialog.exec() == QDialog.DialogCode.Accepted:
                sel = file_dialog.selectedFiles()
                if sel:
                    try:
                        export_to_rdp_bundle(connections, sel[0])
                        show_independent_info("Export Complete", f"Bundled {len(connections)} .rdp sessions into:\n{sel[0]}")
                    except Exception as e:
                        show_independent_info("Export Failed", str(e))

        elif export_format == "csv":
            file_dialog.setWindowTitle("Export to CSV Spreadsheet")
            file_dialog.setNameFilter("CSV Files (*.csv);;All Files (*)")
            file_dialog.selectFile("flux_connections.csv")
            if file_dialog.exec() == QDialog.DialogCode.Accepted:
                sel = file_dialog.selectedFiles()
                if sel:
                    try:
                        content = export_to_csv(connections)
                        Path(sel[0]).write_text(content, encoding="utf-8")
                        show_independent_info("Export Complete", f"Saved CSV dataset to:\n{sel[0]}")
                    except Exception as e:
                        show_independent_info("Export Failed", str(e))

    def _on_tree_double_clicked(self, index: QModelIndex):
        item = self.tree_model.itemFromIndex(index)
        conn_id = item.data(Qt.ItemDataRole.UserRole)
        if conn_id:
            self._launch_session(conn_id, fullscreen=False)

    def _show_tree_context_menu(self, position):
        index = self.tree_view.indexAt(position)
        menu = QMenu()

        if not index.isValid():
            # Right-clicked on empty space
            act_new_folder = QAction("New Folder...", self)
            act_new_conn = QAction("New Connection...", self)

            act_new_folder.triggered.connect(self._create_folder_dialog)
            act_new_conn.triggered.connect(self._create_connection_entry)

            menu.addAction(act_new_folder)
            menu.addAction(act_new_conn)
            menu.exec(self.tree_view.viewport().mapToGlobal(position))
            return

        item = self.tree_model.itemFromIndex(index)
        conn_id = item.data(Qt.ItemDataRole.UserRole)
        folder_path = item.data(Qt.ItemDataRole.UserRole + 1)

        if folder_path:
            clean_name = item.text().strip()
            act_assign_vault = QAction(f"Assign Vault Credential to '{clean_name}'...", self)
            act_new_conn_in_folder = QAction(f"New Connection in '{clean_name}'...", self)
            act_delete_folder = QAction(f"Delete Folder '{clean_name}'", self)

            act_assign_vault.triggered.connect(lambda: self._assign_vault_to_folder(folder_path))
            act_new_conn_in_folder.triggered.connect(lambda: self._create_connection_in_folder(folder_path))
            act_delete_folder.triggered.connect(lambda: self._delete_folder_action(folder_path, clean_name))

            menu.addAction(act_assign_vault)
            menu.addAction(act_new_conn_in_folder)
            menu.addSeparator()
            menu.addAction(act_delete_folder)
            menu.exec(self.tree_view.viewport().mapToGlobal(position))
            return

        if not conn_id:
            return

        conn = self.db.get_by_id(conn_id)
        conn_name = conn.get("name", "Session") if conn else "Session"

        act_open = QAction("Connect (Windowed)", self)
        act_fs = QAction("Connect (Full Screen - Grab All Keys)", self)
        act_edit = QAction("Edit Connection...", self)
        act_delete_entry = QAction(f"Delete '{conn_name}'", self)

        act_open.triggered.connect(lambda: self._launch_session(conn_id, fullscreen=False))
        act_fs.triggered.connect(lambda: self._launch_session(conn_id, fullscreen=True))
        act_edit.triggered.connect(lambda: self._edit_connection(conn_id))
        act_delete_entry.triggered.connect(lambda: self._delete_connection_action(conn_id, conn_name))

        menu.addAction(act_open)
        menu.addAction(act_fs)
        menu.addSeparator()
        menu.addAction(act_edit)
        menu.addSeparator()
        menu.addAction(act_delete_entry)
        menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def _create_connection_in_folder(self, folder_path: str):
        vault_creds = self.db.fetch_all_vault_creds()
        existing_folders = self._get_all_folders()
        dummy_conn = {
            "id": "",
            "name": "",
            "host": "",
            "port": 3389,
            "group_path": folder_path,
            "credential_id": None
        }
        dialog = EditConnectionDialog(dummy_conn, vault_creds, available_folders=existing_folders, parent=None)
        dialog.setWindowTitle(f"New Connection in {folder_path}")
        if dialog.exec():
            updated = dialog.get_data()
            if not updated.get("id"):
                import uuid
                updated["id"] = str(uuid.uuid4())
            self.db.insert_or_update(updated)
            self._load_connections_to_tree()
            self.dashboard_tab.refresh_stats()
            self.status_bar.showMessage(f"Created connection: {updated['name']}")

    def _delete_folder_action(self, folder_path: str, display_name: str):
        if show_independent_question(
            "Delete Folder",
            f"Are you sure you want to delete folder '{display_name}'?\n\n"
            "This will delete all sessions and sub-folders inside it."
        ):
            if folder_path in self.empty_folders:
                self.empty_folders.remove(folder_path)
            deleted_count = self.db.delete_folder(folder_path)
            self._load_connections_to_tree()
            self.dashboard_tab.refresh_stats()
            self.status_bar.showMessage(f"Deleted folder '{display_name}' and {deleted_count} child sessions.")

    def _delete_connection_action(self, conn_id: str, display_name: str):
        if show_independent_question(
            "Delete Connection",
            f"Are you sure you want to delete '{display_name}'?"
        ):
            self.db.delete_connection(conn_id)
            self._load_connections_to_tree()
            self.dashboard_tab.refresh_stats()
            self.status_bar.showMessage(f"Deleted connection '{display_name}'.")

    def _assign_vault_to_folder(self, folder_path: str):
        vault_creds = self.db.fetch_all_vault_creds()
        if not vault_creds:
            show_independent_info("Vault Empty", "Please create a Vault credential first using the '+ New' button.")
            return

        dialog = AssignFolderVaultDialog(folder_path, vault_creds, parent=None)
        if dialog.exec():
            selected_cred_id = dialog.get_selected_cred_id()
            count = self.db.apply_credential_to_folder(folder_path, selected_cred_id)
            self._load_connections_to_tree()
            self.status_bar.showMessage(f"Assigned vault credential to {count} sessions under '{folder_path}'.")

    def _edit_connection(self, conn_id: str):
        conn = self.db.get_by_id(conn_id)
        if not conn:
            return

        vault_creds = self.db.fetch_all_vault_creds()
        existing_folders = self._get_all_folders()
        dialog = EditConnectionDialog(conn, vault_creds, available_folders=existing_folders, parent=None)
        if dialog.exec():
            updated = dialog.get_data()
            self.db.insert_or_update(updated)
            self._load_connections_to_tree()
            self.dashboard_tab.refresh_stats()
            self.status_bar.showMessage(f"Updated connection: {updated['name']}")

    def _launch_session(self, conn_id: str, fullscreen: bool = False):
        conn = self.db.get_by_id(conn_id)
        if not conn:
            return

        self.db.record_session_launch(conn_id)

        if conn.get("credential_id"):
            vault_cred = self.db.get_vault_cred(conn["credential_id"])
            if vault_cred:
                conn["username"] = vault_cred.get("username", "")
                conn["domain"] = vault_cred.get("domain", "")
                conn["password"] = vault_cred.get("password", "")

        viewer = RDPViewerWidget(conn, fullscreen=fullscreen)
        viewer.request_close.connect(self._close_viewer_tab)

        tab_index = self.tab_widget.addTab(viewer, f"{conn['name']}")
        self.tab_widget.setCurrentIndex(tab_index)
        viewer.start_session()
        self.dashboard_tab.refresh_stats()

    def _launch_adhoc_session(self, conn_data: dict):
        viewer = RDPViewerWidget(conn_data, fullscreen=False)
        viewer.request_close.connect(self._close_viewer_tab)

        tab_index = self.tab_widget.addTab(viewer, conn_data["name"])
        self.tab_widget.setCurrentIndex(tab_index)
        viewer.start_session()

    def _close_viewer_tab(self, viewer_widget: QWidget):
        index = self.tab_widget.indexOf(viewer_widget)
        if index != -1 and index != 0:
            self._close_tab(index)

    def _close_tab(self, index: int):
        if index == 0:
            return

        widget = self.tab_widget.widget(index)
        if widget:
            widget.close()
        self.tab_widget.removeTab(index)