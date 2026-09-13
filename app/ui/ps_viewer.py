import subprocess
import shutil
import shlex
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from app.ui.rdp_viewer import ProcessWorker, IndependentErrorDialog, ConfirmCloseDialog


class PSViewerWidget(QWidget):
    request_close = pyqtSignal(QWidget)

    def __init__(self, session_data: dict, parent=None):
        super().__init__(parent)
        self.session_data = session_data
        self.worker = None
        self._connected = False
        self._window_poll_timer = None
        self._is_closing = False

        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(16)

        header = QHBoxLayout()
        display_name = self.session_data.get("name", "Host")
        host = self.session_data.get("host", "")

        self.status_label = QLabel(
            f"Active PS Session: <b style='color: #60a5fa;'>{display_name}</b> "
            f"(<span style='color: #94a3b8;'>{host}</span>)",
            self
        )
        self.status_label.setTextFormat(Qt.TextFormat.RichText)

        self.toggle_log_btn = QPushButton("Show Log", self)
        self.toggle_log_btn.setObjectName("GhostBtn")
        self.toggle_log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_log_btn.clicked.connect(self._toggle_logs)

        self.reconnect_btn = QPushButton("↻ Relaunch Terminal", self)
        self.reconnect_btn.setObjectName("GhostBtn")
        self.reconnect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reconnect_btn.clicked.connect(self.launch_windowed)

        header.addWidget(self.status_label)
        header.addStretch()
        header.addWidget(self.toggle_log_btn)
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

        self.status_badge = QLabel("● CONNECTING...")
        self.status_badge.setStyleSheet("color: #d29922; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;")

        self.session_title = QLabel(f"Connecting to {display_name}...")
        self.session_title.setStyleSheet("color: #f0f6fc; font-size: 18px; font-weight: 600;")

        self.instructions = QLabel("Establishing WinRM handshake and opening terminal...")
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
            self.status_badge.setText("● TERMINAL RUNNING")
            self.status_badge.setStyleSheet("color: #3fb950; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;")
            self.session_title.setText(f"Connected to {display_name}")
            self.session_title.setStyleSheet("color: #f0f6fc; font-size: 18px; font-weight: 600;")
            self.instructions.setText(
                "The PowerShell session is running in an independent terminal window.<br><br>"
                "• <b>Commands:</b> You have direct WinRM access to the remote host.<br>"
                "• <b>Window Tracking:</b> Closing the external terminal will mark this session as disconnected."
            )

    def _mark_as_failed(self):
        if self._window_poll_timer and self._window_poll_timer.isActive():
            self._window_poll_timer.stop()

        self.status_badge.setText("● CONNECTION FAILED")
        self.status_badge.setStyleSheet("color: #f85149; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;")
        
        self.session_title.setText("Terminal connection failed")
        self.session_title.setStyleSheet("color: #f85149; font-size: 18px; font-weight: 600;")
        
        self.instructions.setText("The server is unreachable or credentials were rejected.<br>Review the error in the terminal window before it closes.")

    def _check_window_presence(self):
        if not self.worker or not self.worker.process or self.worker.process.poll() is not None:
            return

        host = self.session_data.get('host', '')
        target_title = f"PS Session: {host}"
        failed_title = f"Failed: {host}"

        if shutil.which("wmctrl"):
            try:
                res = subprocess.run(
                    ["wmctrl", "-l"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=1
                )
                output = res.stdout.lower()
                if target_title.lower() in output:
                    self._mark_as_connected()
                    return
                if failed_title.lower() in output:
                    self._mark_as_failed()
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
                    
                res_fail = subprocess.run(
                    ["xdotool", "search", "--name", failed_title],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=1
                )
                if res_fail.returncode == 0 and res_fail.stdout.strip():
                    self._mark_as_failed()
                    return
            except Exception:
                pass

    def log(self, message: str):
        self.log_output.append(message)

    def launch_windowed(self):
        self.start_session()

    def start_session(self):
        display_name = self.session_data.get("name", "Host")
        self._connected = False
        self._is_closing = False

        if self._window_poll_timer and self._window_poll_timer.isActive():
            self._window_poll_timer.stop()

        self.status_badge.setText("● CONNECTING...")
        self.session_title.setText(f"Connecting to {display_name}...")
        self.instructions.setText("Establishing WinRM handshake and opening terminal...")
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

        binary = shutil.which("xterm")
        if not binary:
            self.show_error_dialog("Terminal Missing", "Could not find 'xterm' in PATH.")
            return

        cmd = self._build_xterm_command()
        
        sanitized = []
        for c in cmd:
            if "ConvertTo-SecureString" in c:
                sanitized.append("<redacted_secure_payload>")
            else:
                sanitized.append(c)

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

        if exit_code == 1:
            return "WinRM Connection Failed", f"Code 1: The remote host {host} refused the WinRM connection, or the credentials provided were rejected."
        elif exit_code == 127:
            return "Terminal Emulator Missing", "Code 127: The 'xterm' executable was not found. Ensure it is installed on the host system."
        else:
            return "Terminal Exited Unexpectedly", f"Code {exit_code}: An unexpected error caused the PowerShell terminal process to terminate."

    def _on_process_finished(self, exit_code: int):
        if getattr(self, '_is_closing', False):
            return

        self.log(f"\n[*] Process exited with code: {exit_code}")
        self._connected = False

        if self._window_poll_timer and self._window_poll_timer.isActive():
            self._window_poll_timer.stop()

        USER_DISCONNECT_CODES = {0, 15, 130, 143}

        if exit_code in USER_DISCONNECT_CODES:
            self.request_close.emit(self)
            return

        error_title, error_desc = self._get_error_details(exit_code)
        display_desc = error_desc.split(': ', 1)[-1]

        self.status_badge.setText("● CONNECTION FAILED")
        self.status_badge.setStyleSheet("color: #f85149; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;")
        
        self.session_title.setText(f"Error {exit_code}: {error_title} — {display_desc}")
        self.session_title.setStyleSheet("color: #f85149; font-size: 16px; font-weight: 600;")
        
        self.instructions.setText("Click <b>Relaunch Terminal</b> to retry or click <b>Show Log</b> above to inspect detailed debug output.")

        self.show_error_dialog(error_title, error_desc)

    def show_error_dialog(self, title: str, description: str):
        dialog = IndependentErrorDialog(title, description)
        dialog.exec()

        if dialog.user_choice == "retry":
            self.start_session()
        elif dialog.user_choice == "close":
            self.request_close.emit(self)

    def _build_xterm_command(self) -> list:
        domain = self.session_data.get("domain", "")
        username = self.session_data.get("username", "")
        password = self.session_data.get("password", "")
        host = self.session_data.get("host", "")
        full_user = f"{domain}\\{username}" if domain else username
        
        ps_cmd = (
            f"$secpasswd = ConvertTo-SecureString '{password}' -AsPlainText -Force; "
            f"$cred = New-Object System.Management.Automation.PSCredential ('{full_user}', $secpasswd); "
            f"try {{ "
            f"  $t = New-Object System.Net.Sockets.TcpClient; "
            f"  $c = $t.ConnectAsync('{host}', 5985); "
            f"  if (-not $c.Wait(15000)) {{ throw 'Network timeout (15s). Ensure your VPN is connected.' }}; "
            f"  if ($c.IsFaulted) {{ throw $c.Exception.InnerException.Message }}; "
            f"  $t.Close(); "
            f"  $s = New-PSSession -ComputerName {host} -Credential $cred -Authentication Negotiate -ErrorAction Stop; "
            f"}} catch {{ "
            f"  $e = [char]27; $bel = [char]7; Write-Host -NoNewline \"$e]0;Failed: {host}$bel\"; "
            f"  Write-Host \"`n[!] Connection Failed: $($_.Exception.Message)`n\" -ForegroundColor Red; "
            f"  Start-Sleep -Seconds 10; "
            f"  exit 1; "
            f"}} "
            f"Invoke-Command -Session $s -ScriptBlock {{ "
            f"  function global:Clear-Host {{ $e = [char]27; Write-Host -NoNewline \"$e[2J$e[H\" }}; "
            f"  $ProgressPreference = 'SilentlyContinue'; "
            f"}}; "
            f"$e = [char]27; $bel = [char]7; Write-Host -NoNewline \"$e]0;PS Session: {host}$bel\"; "
            f"Enter-PSSession -Session $s"
        )

        return [
            "env",
            "POWERSHELL_TELEMETRY_OPTOUT=1",
            "XMODIFIERS=@im=none",
            "xterm",
            "-class", "flux-rdm",
            "-name", "flux-rdm",
            "-geometry", "110x30",
            "-fa", "DejaVu Sans Mono",
            "-fs", "11",
            "-xrm", "XTerm*fastScroll: true",
            "-xrm", "XTerm*jumpScroll: true",
            "-xrm", "XTerm*cursorBlink: false",  
            "+bc",                               
            "-bg", "#0d1117",
            "-fg", "#f0f6fc",
            "-sl", "10000",
            "-title", f"Connecting to {host}...",
            "-e",
            "pwsh", "-NoProfile", "-NoExit", "-Command", ps_cmd
        ]

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            dialog = ConfirmCloseDialog(
                "Close Active Terminal", 
                "Are you sure you want to close this session? This will terminate the WinRM connection."
            )
            dialog.exec()
            
            if not dialog.user_choice:
                event.ignore()
                return
                
        self._is_closing = True
        
        if self._window_poll_timer and self._window_poll_timer.isActive():
            self._window_poll_timer.stop()
            
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
                
        super().closeEvent(event)