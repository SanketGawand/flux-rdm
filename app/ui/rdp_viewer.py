import subprocess
import shutil
import shlex
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLabel, QPushButton, QDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer


class ProcessWorker(QThread):
    output_received = pyqtSignal(str)
    process_finished = pyqtSignal(int)

    def __init__(self, cmd: list):
        super().__init__()
        self.cmd = cmd
        self.process = None

    def run(self):
        try:
            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_received.emit(line.rstrip("\r\n"))
            self.process.stdout.close()
            return_code = self.process.wait()
            self.process_finished.emit(return_code)
        except Exception as e:
            self.output_received.emit(f"[-] Execution Error: {str(e)}")
            self.process_finished.emit(-1)

    def stop(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass


class ConfirmCloseDialog(QDialog):
    """Independently movable dialog to confirm closing an active session."""
    def __init__(self, title: str, description: str):
        super().__init__(None)
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.CustomizeWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.resize(420, 160)
        self.user_choice = False

        self._init_ui(title, description)

    def _init_ui(self, title: str, description: str):
        self.setStyleSheet("""
            QDialog { background-color: #0d1117; }
            QPushButton#DangerBtn { background-color: #da3633; color: white; border-radius: 6px; padding: 6px 16px; font-weight: 600; }
            QPushButton#GhostBtn { background-color: transparent; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; padding: 6px 16px; font-weight: 600; }
            QPushButton#GhostBtn:hover { background-color: #21262d; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)

        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 28px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)

        heading = QLabel(title)
        heading.setStyleSheet("font-size: 15px; font-weight: 700; color: #e6edf3; background: transparent;")

        body = QLabel(description)
        body.setStyleSheet("font-size: 13px; color: #8b949e; line-height: 1.4; background: transparent;")
        body.setWordWrap(True)

        text_layout.addWidget(heading)
        text_layout.addWidget(body)

        content_layout.addWidget(icon_label)
        content_layout.addLayout(text_layout, 1)
        layout.addLayout(content_layout)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("GhostBtn")
        cancel_btn.clicked.connect(self._on_cancel)

        confirm_btn = QPushButton("Close Session")
        confirm_btn.setObjectName("DangerBtn")
        confirm_btn.clicked.connect(self._on_confirm)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)

    def _on_cancel(self):
        self.user_choice = False
        self.reject()

    def _on_confirm(self):
        self.user_choice = True
        self.accept()


class IndependentErrorDialog(QDialog):
    """Independently movable dialog for session alerts and errors."""
    def __init__(self, title: str, description: str):
        super().__init__(None)
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.CustomizeWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.resize(440, 180)
        self.user_choice = "dismiss"

        self._init_ui(title, description)

    def _init_ui(self, title: str, description: str):
        self.setStyleSheet("""
            QDialog { background-color: #0d1117; }
            QPushButton#PrimaryBtn { background-color: #238636; color: white; border-radius: 6px; padding: 6px 16px; font-weight: 600; }
            QPushButton#GhostBtn { background-color: transparent; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; padding: 6px 16px; font-weight: 600; }
            QPushButton#GhostBtn:hover { background-color: #21262d; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)

        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 28px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)

        heading = QLabel(title)
        heading.setStyleSheet("font-size: 15px; font-weight: 700; color: #f85149; background: transparent;")

        body = QLabel(description)
        body.setStyleSheet("font-size: 13px; color: #c9d1d9; line-height: 1.4; background: transparent;")
        body.setWordWrap(True)

        text_layout.addWidget(heading)
        text_layout.addWidget(body)

        content_layout.addWidget(icon_label)
        content_layout.addLayout(text_layout, 1)
        layout.addLayout(content_layout)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.setObjectName("GhostBtn")
        dismiss_btn.clicked.connect(self._on_dismiss)

        retry_btn = QPushButton("Retry")
        retry_btn.setObjectName("PrimaryBtn")
        retry_btn.clicked.connect(self._on_retry)

        close_btn = QPushButton("Close Tab")
        close_btn.setObjectName("GhostBtn")
        close_btn.clicked.connect(self._on_close)

        btn_layout.addWidget(dismiss_btn)
        btn_layout.addWidget(retry_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _on_dismiss(self):
        self.user_choice = "dismiss"
        self.accept()

    def _on_retry(self):
        self.user_choice = "retry"
        self.accept()

    def _on_close(self):
        self.user_choice = "close"
        self.accept()


class RDPViewerWidget(QWidget):
    request_close = pyqtSignal(QWidget)

    def __init__(self, session_data: dict, fullscreen: bool = False, parent=None):
        super().__init__(parent)
        self.session_data = session_data
        self.fullscreen = fullscreen
        self.worker = None
        self._connected = False
        self._window_poll_timer = None
        self._expected_exit = False
        self._is_closing = False

        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(16)

        header = QHBoxLayout()
        display_name = self.session_data.get("name", "Host")
        host = self.session_data.get("host", "")
        port = self.session_data.get("port", 3389)

        self.status_label = QLabel(
            f"Active Session: <b style='color: #60a5fa;'>{display_name}</b> "
            f"(<span style='color: #94a3b8;'>{host}:{port}</span>)",
            self
        )
        self.status_label.setTextFormat(Qt.TextFormat.RichText)

        self.toggle_log_btn = QPushButton("Show Log", self)
        self.toggle_log_btn.setObjectName("GhostBtn")
        self.toggle_log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_log_btn.clicked.connect(self._toggle_logs)

        self.fs_btn = QPushButton("Launch Fullscreen", self)
        self.fs_btn.setObjectName("GhostBtn")
        self.fs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fs_btn.clicked.connect(self.launch_fullscreen)

        self.reconnect_btn = QPushButton("↻ Relaunch Window", self)
        self.reconnect_btn.setObjectName("GhostBtn")
        self.reconnect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reconnect_btn.clicked.connect(self.launch_windowed)

        header.addWidget(self.status_label)
        header.addStretch()
        header.addWidget(self.toggle_log_btn)
        header.addWidget(self.fs_btn)
        header.addWidget(self.reconnect_btn)
        self.main_layout.addLayout(header)

        self.info_card = QFrame(self)
        self.info_card.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #21262d;
                border-radius: 8px;
                padding: 24px;
            }
        """)
        card_layout = QVBoxLayout(self.info_card)
        card_layout.setSpacing(12)

        badge_text = "● CONNECTING (FULLSCREEN)..." if self.fullscreen else "● CONNECTING..."
        title_text = f"Connecting to {display_name} (Fullscreen Mode)..." if self.fullscreen else f"Connecting to {display_name}..."

        self.status_badge = QLabel(badge_text)
        self.status_badge.setStyleSheet("color: #d29922; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;")

        self.session_title = QLabel(title_text)
        self.session_title.setStyleSheet("color: #f0f6fc; font-size: 18px; font-weight: 600;")

        self.instructions = QLabel("Establishing network handshake and verifying credentials...")
        self.instructions.setStyleSheet("color: #8b949e; font-size: 13px; line-height: 1.6;")
        self.instructions.setTextFormat(Qt.TextFormat.RichText)

        card_layout.addWidget(self.status_badge)
        card_layout.addWidget(self.session_title)
        card_layout.addWidget(self.instructions)
        self.main_layout.addWidget(self.info_card)

        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #0b0d11;
                color: #58a6ff;
                font-family: monospace;
                font-size: 12px;
                border: 1px solid #232730;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        self.log_output.hide()
        self.main_layout.addWidget(self.log_output)

        self.main_layout.addStretch()

    def _toggle_logs(self):
        if self.log_output.isVisible():
            self.log_output.hide()
            self.info_card.show()
            self.toggle_log_btn.setText("Show Log")
        else:
            self.info_card.hide()
            self.log_output.show()
            self.toggle_log_btn.setText("Hide Log")

    def _mark_as_connected(self):
        if not self._connected:
            self._connected = True
            if self._window_poll_timer and self._window_poll_timer.isActive():
                self._window_poll_timer.stop()

            display_name = self.session_data.get("name", "Host")

            if self.fullscreen:
                self.status_badge.setText("● FULLSCREEN SESSION RUNNING")
                self.status_badge.setStyleSheet("color: #3fb950; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;")
                self.session_title.setText(f"Connected to {display_name} (Fullscreen Mode)")
                self.session_title.setStyleSheet("color: #f0f6fc; font-size: 18px; font-weight: 600;")
                self.instructions.setText(
                    "The remote desktop session is active in <b>Fullscreen Mode</b>.<br><br>"
                    "• <b>Controls:</b> Move the cursor to the top edge to reveal the dropdown navigation bar.<br>"
                    "• <b>Keyboard:</b> All input events are currently captured and directed to the remote system."
                )
            else:
                self.status_badge.setText("● SESSION RUNNING")
                self.status_badge.setStyleSheet("color: #3fb950; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;")
                self.session_title.setText(f"Connected to {display_name}")
                self.session_title.setStyleSheet("color: #f0f6fc; font-size: 18px; font-weight: 600;")
                self.instructions.setText(
                    "The remote desktop session is running in an independent window.<br><br>"
                    "• <b>Floatbar:</b> Move the cursor to the top edge of the window to access session controls.<br>"
                    "• <b>Dynamic Scaling:</b> Resizing the remote window automatically adjusts resolution.<br>"
                    "• <b>File Transfer:</b> Use the 'FluxShared' drive in This PC to move files to your mapped host folder."
                )

    def _check_window_presence(self):
        if not self.worker or not self.worker.process or self.worker.process.poll() is not None:
            return

        target_title = f"{self.session_data.get('name', 'Remote Session')} - Flux RDM"

        if shutil.which("wmctrl"):
            try:
                res = subprocess.run(
                    ["wmctrl", "-l"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=1
                )
                if target_title.lower() in res.stdout.lower():
                    self._mark_as_connected()
                    return
            except Exception:
                pass

        if shutil.which("xdotool"):
            try:
                res = subprocess.run(
                    ["xdotool", "search", "--name", target_title],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=1
                )
                if res.returncode == 0 and res.stdout.strip():
                    self._mark_as_connected()
                    return
            except Exception:
                pass

    def log(self, message: str):
        self.log_output.append(message)

    def launch_windowed(self):
        self.fullscreen = False
        self.start_session()

    def launch_fullscreen(self):
        self.fullscreen = True
        self.start_session()

    def start_session(self):
        display_name = self.session_data.get("name", "Host")
        self._connected = False
        self._expected_exit = False
        self._is_closing = False

        if self._window_poll_timer and self._window_poll_timer.isActive():
            self._window_poll_timer.stop()

        if self.fullscreen:
            self.status_badge.setText("● CONNECTING (FULLSCREEN)...")
            self.session_title.setText(f"Connecting to {display_name} in Fullscreen Mode...")
            self.instructions.setText("Negotiating fullscreen display parameters and establishing handshake...")
        else:
            self.status_badge.setText("● CONNECTING...")
            self.session_title.setText(f"Connecting to {display_name}...")
            self.instructions.setText("Establishing network handshake and verifying credentials...")

        self.status_badge.setStyleSheet("color: #d29922; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;")
        self.session_title.setStyleSheet("color: #f0f6fc; font-size: 18px; font-weight: 600;")

        if self.worker:
            try:
                self.worker.output_received.disconnect()
                self.worker.process_finished.disconnect()
            except Exception:
                pass

            if self.worker.isRunning():
                self.log("[*] Terminating previous session before relaunch...")
                self.worker.stop()
                self.worker.wait(1500)

        binary = shutil.which("xfreerdp3") or shutil.which("xfreerdp")
        if not binary:
            self.show_error_dialog("FreeRDP Missing", "FreeRDP binary not found in PATH.")
            return

        cmd = self._build_freerdp_command(binary)
        sanitized = [arg if not arg.startswith("/p:") else "/p:******" for arg in cmd]
        self.log(f"[*] Executing: {shlex.join(sanitized)}\n")

        self.worker = ProcessWorker(cmd)
        self.worker.output_received.connect(self.log)
        self.worker.process_finished.connect(self._on_process_finished)
        self.worker.start()

        self._window_poll_timer = QTimer(self)
        self._window_poll_timer.timeout.connect(self._check_window_presence)
        self._window_poll_timer.start(250)

    def _get_error_details(self, exit_code: int) -> tuple[str, str]:
        host = self.session_data.get('host', 'Unknown')
        port = self.session_data.get('port', 3389)

        if exit_code == 131:
            return "Authentication Failed", f"Code 131: The credentials provided for {host} were rejected by the server."
        elif exit_code == 141:
            return "Connection Refused", f"Code 141: Host {host} refused the connection on port {port}."
        elif exit_code == 132:
            return "Certificate Error", f"Code 132: Network Level Authentication (NLA) or certificate negotiation failed for {host}."
        elif exit_code == 119:
            return "Protocol Error", f"Code 119: RDP protocol negotiation failed. The server might not support the requested graphics pipeline."
        else:
            return "Connection Failed", f"Code {exit_code}: An unexpected network or protocol error occurred while connecting to {host}."

    def _on_process_finished(self, exit_code: int):
        # Ignore process exits that we triggered intentionally by closing the tab
        if getattr(self, '_is_closing', False):
            return

        self.log(f"\n[*] Process exited with code: {exit_code}")
        self._connected = False

        if self._window_poll_timer and self._window_poll_timer.isActive():
            self._window_poll_timer.stop()

        USER_DISCONNECT_CODES = {0, 11, 12, 15, 130, 143}

        if exit_code in USER_DISCONNECT_CODES:
            self._expected_exit = True
            self.request_close.emit(self)
            return

        error_title, error_desc = self._get_error_details(exit_code)
        display_desc = error_desc.split(': ', 1)[-1]

        self.status_badge.setText("● CONNECTION FAILED")
        self.status_badge.setStyleSheet("color: #f85149; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;")
        
        self.session_title.setText(f"Error {exit_code}: {error_title} — {display_desc}")
        self.session_title.setStyleSheet("color: #f85149; font-size: 16px; font-weight: 600;")
        
        self.instructions.setText("Click <b>Relaunch Window</b> to retry or click <b>Show Log</b> above to inspect detailed debug output.")

        self.show_error_dialog(error_title, error_desc)

    def show_error_dialog(self, title: str, description: str):
        dialog = IndependentErrorDialog(title, description)
        dialog.exec()

        if dialog.user_choice == "retry":
            self.start_session()
        elif dialog.user_choice == "close":
            self.request_close.emit(self)

    def _build_freerdp_command(self, binary: str) -> list:
        s = self.session_data
        local_share = "/app/shared"
        
        try:
            if not os.path.exists(local_share):
                os.makedirs(local_share, exist_ok=True)
        except Exception:
            pass

        args = [
            binary,
            f"/v:{s['host']}:{s['port']}",
            "/cert:ignore",
            "+clipboard",
            f"/drive:FluxShared,{local_share}",
            "+auto-reconnect",
            "/audio-mode:0",
            "/network:auto",
            "/compression",
            "-themes",
            "-wallpaper",
            f"/t:{s.get('name', 'Remote Session')} - Flux RDM",
            "/floatbar:sticky:off,default:visible,show:always",
            "+toggle-fullscreen",
            "/wm-class:flux-rdm",
        ]

        user = s.get("username", "").strip()
        domain = s.get("domain", "").strip()

        if user.lower() == "administrator" and not domain and ("\\" not in user and "@" not in user):
            domain = "."

        if user:
            args.append(f"/u:{user}")
        if domain:
            args.append(f"/d:{domain}")
        if s.get("password"):
            args.append(f"/p:{s['password']}")

        if self.fullscreen:
            args.extend([
                "/f",
                "+grab-keyboard",
                "/scale:180",
                "/scale-device:180",
                "+dynamic-resolution"
            ])
        else:
            args.extend([
                "/size:1600x900",
                "/scale:180",
                "/scale-desktop:180",
                "/scale-device:180",
                "+dynamic-resolution"
            ])

        return args

    def closeEvent(self, event):
        # 1. Ask for confirmation ONLY if the session is actively running
        if self.worker and self.worker.isRunning():
            dialog = ConfirmCloseDialog(
                "Close Active Session", 
                "Are you sure you want to close this session? This will immediately disconnect the remote host."
            )
            dialog.exec()
            
            if not dialog.user_choice:
                # User canceled, keep the tab open
                event.ignore()
                return
                
        # 2. Proceed with closing silently
        self._is_closing = True
        
        if self._window_poll_timer and self._window_poll_timer.isActive():
            self._window_poll_timer.stop()
            
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
                
        super().closeEvent(event)