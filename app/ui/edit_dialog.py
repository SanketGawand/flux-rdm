from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFormLayout, QTextEdit, QWidget, QCheckBox
)
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt


def render_svg_icon(svg_str: str, width: int = 16, height: int = 16) -> QIcon:
    renderer = QSvgRenderer(svg_str.encode('utf-8'))
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


class EditConnectionDialog(QDialog):
    def __init__(self, conn: dict, vault_creds: list, available_folders: list = None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.vault_creds = vault_creds
        self.available_folders = available_folders or []
        
        self.setWindowTitle("Edit Connection" if conn.get("id") else "New Connection")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.CustomizeWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.resize(460, 440)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(12)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Name Input
        self.name_input = QLineEdit(self.conn.get("name", ""))
        self.name_input.setPlaceholderText("e.g. Production Database 01")
        self.name_input.setFixedHeight(30)
        self.form_layout.addRow(QLabel("Connection Name:"), self.name_input)

        # Common ComboBox stylesheet with embedded SVG down-arrow
        combo_stylesheet = """
            QComboBox {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding-left: 8px;
                padding-right: 28px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left-width: 0px;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QComboBox::down-arrow {
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%238b949e' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='6 9 12 15 18 9'/></svg>");
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                selection-background-color: #1f6feb;
            }
        """

        # Folder / Group Path ComboBox
        self.folder_combo = QComboBox()
        self.folder_combo.setEditable(False)
        self.folder_combo.setFixedHeight(30)
        self.folder_combo.setStyleSheet(combo_stylesheet)
        
        self.folder_combo.addItem("Select from folders...", "")
        unique_folders = sorted(list(set(self.available_folders)))
        for f in unique_folders:
            if f:
                self.folder_combo.addItem(f, f)
                
        current_group = self.conn.get("group_path", "")
        if current_group:
            idx = self.folder_combo.findData(current_group)
            if idx != -1:
                self.folder_combo.setCurrentIndex(idx)
            else:
                self.folder_combo.setCurrentIndex(0)
        else:
            self.folder_combo.setCurrentIndex(0)

        self.form_layout.addRow(QLabel("Folder Path:"), self.folder_combo)

        # Host Input
        self.host_input = QLineEdit(self.conn.get("host", ""))
        self.host_input.setPlaceholderText("e.g. 10.204.2.140")
        self.host_input.setFixedHeight(30)
        self.form_layout.addRow(QLabel("Host / IP:"), self.host_input)

        # Port Input
        self.port_input = QLineEdit(str(self.conn.get("port", 3389)))
        self.port_input.setPlaceholderText("3389")
        self.port_input.setFixedHeight(30)
        self.form_layout.addRow(QLabel("Port:"), self.port_input)

        # Credential Vault Link ComboBox
        self.vault_combo = QComboBox()
        self.vault_combo.setEditable(False)
        self.vault_combo.setFixedHeight(30)
        self.vault_combo.setStyleSheet(combo_stylesheet)
        
        self.vault_combo.addItem("-- Direct / Unlinked --", None)
        for vc in self.vault_creds:
            dom = f"{vc['domain']}\\" if vc.get('domain') else ""
            display_str = f"{vc['name']} ({dom}{vc['username']})"
            self.vault_combo.addItem(display_str, vc["id"])
            
        current_cred_id = self.conn.get("credential_id")
        if current_cred_id:
            for i in range(self.vault_combo.count()):
                if self.vault_combo.itemData(i) == current_cred_id:
                    self.vault_combo.setCurrentIndex(i)
                    break
                
        self.vault_combo.currentIndexChanged.connect(self._on_vault_changed)
        self.form_layout.addRow(QLabel("Credential Vault:"), self.vault_combo)

        # Custom Credential / Domain Fields
        self.domain_label = QLabel("Domain:")
        
        domain_container = QWidget()
        domain_layout = QHBoxLayout(domain_container)
        domain_layout.setContentsMargins(0, 0, 0, 0)
        domain_layout.setSpacing(10)

        self.override_domain_chk = QCheckBox("Custom Domain")
        self.override_domain_chk.setFixedHeight(30)
        self.override_domain_chk.setStyleSheet("""
            QCheckBox {
                color: #e6edf3;
                font-size: 13px;
                spacing: 8px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 4px;
            }
            QCheckBox::indicator:hover {
                border-color: #8b949e;
            }
            QCheckBox::indicator:checked {
                background-color: #1f6feb;
                border-color: #1f6feb;
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'><polyline points='20 6 9 17 4 12'/></svg>");
            }
        """)
        self.override_domain_chk.toggled.connect(self._on_override_domain_toggled)

        self.domain_input = QLineEdit(self.conn.get("domain", ""))
        self.domain_input.setPlaceholderText("Optional domain")
        self.domain_input.setFixedHeight(30)

        domain_layout.addWidget(self.override_domain_chk)
        domain_layout.addWidget(self.domain_input, 1)

        if self.conn.get("credential_id") and self.conn.get("domain"):
            self.override_domain_chk.setChecked(True)
        else:
            self.override_domain_chk.setChecked(False)

        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit(self.conn.get("username", ""))
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedHeight(30)

        self.password_label = QLabel("Password:")
        
        # Password layout with programmatically rendered vector icons
        pass_container = QWidget()
        pass_layout = QHBoxLayout(pass_container)
        pass_layout.setContentsMargins(0, 0, 0, 0)
        pass_layout.setSpacing(0)

        self.password_input = QLineEdit(self.conn.get("password", ""))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setFixedHeight(30)
        self.password_input.setStyleSheet("border-top-right-radius: 0px; border-bottom-right-radius: 0px; border-right: none;")

        self.toggle_pass_btn = QPushButton()
        self.toggle_pass_btn.setFixedSize(38, 30)
        self.toggle_pass_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_pass_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QPushButton:hover {
                background-color: #30363d;
            }
        """)
        
        # NOTE: Standard "#" color codes restored here for proper QSvgRenderer loading
        svg_eye_open = "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='#8b949e' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z'/><circle cx='12' cy='12' r='3'/></svg>"
        svg_eye_closed = "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='#8b949e' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24'/><line x1='1' y1='1' x2='23' y2='23'/></svg>"

        self.icon_eye_open = render_svg_icon(svg_eye_open)
        self.icon_eye_closed = render_svg_icon(svg_eye_closed)

        self.toggle_pass_btn.setIcon(self.icon_eye_open)
        self.toggle_pass_btn.clicked.connect(self._toggle_connection_password_visibility)

        pass_layout.addWidget(self.password_input)
        pass_layout.addWidget(self.toggle_pass_btn)

        self.form_layout.addRow(self.domain_label, domain_container)
        self.form_layout.addRow(self.username_label, self.username_input)
        self.form_layout.addRow(self.password_label, pass_container)

        layout.addLayout(self.form_layout)
        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("GhostBtn")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        self._on_vault_changed()

    def _toggle_connection_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_pass_btn.setIcon(self.icon_eye_closed)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_pass_btn.setIcon(self.icon_eye_open)

    def _on_vault_changed(self):
        is_direct = self.vault_combo.currentData() is None
        self.username_label.setVisible(is_direct)
        self.username_input.setVisible(is_direct)
        self.password_label.setVisible(is_direct)
        self.password_input.parentWidget().setVisible(is_direct)
        
        self.override_domain_chk.setVisible(not is_direct)
        if is_direct:
            self.domain_input.setVisible(True)
            self.resize(460, 440)
        else:
            is_override = self.override_domain_chk.isChecked()
            self.domain_input.setVisible(is_override)
            self.resize(460, 360 if not is_override else 400)

    def _on_override_domain_toggled(self, checked: bool):
        is_direct = self.vault_combo.currentData() is None
        if not is_direct:
            self.domain_input.setVisible(checked)

    def get_data(self) -> dict:
        try:
            port_val = int(self.port_input.text().strip())
        except ValueError:
            port_val = 3389

        updated = dict(self.conn)
        updated["name"] = self.name_input.text().strip()
        updated["host"] = self.host_input.text().strip()
        updated["port"] = port_val
        
        folder_data = self.folder_combo.currentData()
        updated["group_path"] = folder_data if folder_data is not None else ""
        
        updated["credential_id"] = self.vault_combo.currentData()
        
        if updated["credential_id"] is None:
            updated["domain"] = self.domain_input.text().strip()
            updated["username"] = self.username_input.text().strip()
            updated["password"] = self.password_input.text()
        else:
            if self.override_domain_chk.isChecked():
                updated["domain"] = self.domain_input.text().strip()
            else:
                updated["domain"] = ""
            updated["username"] = ""
            updated["password"] = ""
            
        return updated


class VaultEntryDialog(QDialog):
    def __init__(self, cred: dict = None, available_folders: list = None, parent=None):
        super().__init__(parent)
        self.cred = cred or {}
        self.available_folders = available_folders or []
        
        self.setWindowTitle("Edit Vault Credential" if self.cred.get("id") else "New Vault Credential")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.CustomizeWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.resize(440, 380)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.name_input = QLineEdit(self.cred.get("name", ""))
        self.name_input.setPlaceholderText("e.g. Domain Admin Credentials")
        self.name_input.setFixedHeight(30)
        form_layout.addRow(QLabel("Credential Name:"), self.name_input)

        self.domain_input = QLineEdit(self.cred.get("domain", ""))
        self.domain_input.setPlaceholderText("e.g. CEXCORP (Optional)")
        self.domain_input.setFixedHeight(30)
        form_layout.addRow(QLabel("Domain:"), self.domain_input)

        self.user_input = QLineEdit(self.cred.get("username", ""))
        self.user_input.setPlaceholderText("e.g. administrator")
        self.user_input.setFixedHeight(30)
        form_layout.addRow(QLabel("Username:"), self.user_input)

        # Password layout with programmatically rendered vector icons for Vault entries
        pass_container = QWidget()
        pass_layout = QHBoxLayout(pass_container)
        pass_layout.setContentsMargins(0, 0, 0, 0)
        pass_layout.setSpacing(0)

        self.pass_input = QLineEdit(self.cred.get("password", ""))
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Enter password")
        self.pass_input.setFixedHeight(30)
        self.pass_input.setStyleSheet("border-top-right-radius: 0px; border-bottom-right-radius: 0px; border-right: none;")

        self.toggle_vault_pass_btn = QPushButton()
        self.toggle_vault_pass_btn.setFixedSize(38, 30)
        self.toggle_vault_pass_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_vault_pass_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QPushButton:hover {
                background-color: #30363d;
            }
        """)
        
        # NOTE: Standard "#" color codes restored here for proper QSvgRenderer loading
        svg_eye_open = "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='#8b949e' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z'/><circle cx='12' cy='12' r='3'/></svg>"
        svg_eye_closed = "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='#8b949e' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24'/><line x1='1' y1='1' x2='23' y2='23'/></svg>"

        self.vault_icon_open = render_svg_icon(svg_eye_open)
        self.vault_icon_closed = render_svg_icon(svg_eye_closed)

        self.toggle_vault_pass_btn.setIcon(self.vault_icon_open)
        self.toggle_vault_pass_btn.clicked.connect(self._toggle_vault_password_visibility)

        pass_layout.addWidget(self.pass_input)
        pass_layout.addWidget(self.toggle_vault_pass_btn)

        form_layout.addRow(QLabel("Password:"), pass_container)

        self.scope_combo = QComboBox()
        self.scope_combo.setFixedHeight(30)
        self.scope_combo.addItem("Save only (Do not apply automatically)", "none")
        self.scope_combo.addItem("Apply to ALL configured connections", "all")
        self.scope_combo.addItem("Apply to a specific folder...", "folder")
        self.scope_combo.currentIndexChanged.connect(self._on_scope_changed)
        form_layout.addRow(QLabel("Bulk Assignment:"), self.scope_combo)

        self.target_folder_combo = QComboBox()
        self.target_folder_combo.setFixedHeight(30)
        for f in sorted(list(set(self.available_folders))):
            if f:
                self.target_folder_combo.addItem(f)
        self.target_folder_combo.setVisible(False)
        form_layout.addRow(self.target_folder_combo)

        layout.addLayout(form_layout)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("GhostBtn")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _toggle_vault_password_visibility(self):
        if self.pass_input.echoMode() == QLineEdit.EchoMode.Password:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_vault_pass_btn.setIcon(self.vault_icon_closed)
        else:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_vault_pass_btn.setIcon(self.vault_icon_open)

    def _on_scope_changed(self, index: int):
        scope = self.scope_combo.currentData()
        self.target_folder_combo.setVisible(scope == "folder")

    def get_data(self) -> dict:
        import uuid
        updated = dict(self.cred)
        if not updated.get("id"):
            updated["id"] = str(uuid.uuid4())
        updated["name"] = self.name_input.text().strip()
        updated["domain"] = self.domain_input.text().strip()
        updated["username"] = self.user_input.text().strip()
        updated["password"] = self.pass_input.text()
        return updated

    def get_apply_scope(self) -> tuple:
        scope = self.scope_combo.currentData()
        folder = self.target_folder_combo.currentText() if scope == "folder" else ""
        return scope, folder


class AssignFolderVaultDialog(QDialog):
    def __init__(self, folder_path: str, vault_creds: list, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.vault_creds = vault_creds

        self.setWindowTitle(f"Assign Vault to Folder: {folder_path}")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.CustomizeWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.resize(380, 200)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        label = QLabel(f"Select a Credential Vault to assign to all connections inside '{self.folder_path}':")
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 13px; color: #e6edf3;")
        layout.addWidget(label)

        self.vault_combo = QComboBox()
        self.vault_combo.setFixedHeight(30)
        for vc in self.vault_creds:
            dom = f"{vc['domain']}\\" if vc.get('domain') else ""
            display_str = f"{vc['name']} ({dom}{vc['username']})"
            self.vault_combo.addItem(display_str, vc["id"])
        layout.addWidget(self.vault_combo)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("GhostBtn")
        cancel_btn.clicked.connect(self.reject)

        assign_btn = QPushButton("Assign")
        assign_btn.setObjectName("PrimaryBtn")
        assign_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(assign_btn)
        layout.addLayout(btn_layout)

    def get_selected_cred_id(self) -> str:
        return self.vault_combo.currentData()