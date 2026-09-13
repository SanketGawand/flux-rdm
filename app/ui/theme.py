import sys
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QImage
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty

ICON_DIR = Path("/tmp/flux_icons")
ICON_DIR.mkdir(parents=True, exist_ok=True)

CHEVRON_RIGHT = ICON_DIR / "chevron-right.svg"
CHEVRON_DOWN = ICON_DIR / "chevron-down.svg"
KEY_ICON = ICON_DIR / "key-icon.svg"
EYE_ICON = ICON_DIR / "eye.svg"
EYE_OFF_ICON = ICON_DIR / "eye-off.svg"
CLOSE_ICON = ICON_DIR / "close.svg"
CLOSE_HOVER_ICON = ICON_DIR / "close-hover.svg"
LOGO_SVG = ICON_DIR / "flux-logo.svg"
CEX_LOGO_SVG = ICON_DIR / "cex-logo.svg"
TERMINAL_ICON = ICON_DIR / "terminal.svg"

if not CHEVRON_RIGHT.exists():
    CHEVRON_RIGHT.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" '
        'stroke="#8b949e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="9 18 15 12 9 6"></polyline></svg>'
    )

if not CHEVRON_DOWN.exists():
    CHEVRON_DOWN.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" '
        'stroke="#58a6ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="6 9 12 15 18 9"></polyline></svg>'
    )

if not KEY_ICON.exists():
    KEY_ICON.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" '
        'stroke="#58a6ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="7.5" cy="15.5" r="5.5"></circle>'
        '<path d="m21 2-9.6 9.6"></path>'
        '<path d="m15.5 7.5 2.5 2.5"></path>'
        '<path d="m18 5 2 2"></path>'
        '</svg>'
    )

if not EYE_ICON.exists():
    EYE_ICON.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" '
        'stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>'
        '<circle cx="12" cy="12" r="3"/>'
        '</svg>'
    )

if not EYE_OFF_ICON.exists():
    EYE_OFF_ICON.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" '
        'stroke="#58a6ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/>'
        '<path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/>'
        '<path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/>'
        '<line x1="2" x2="22" y1="2" y2="22"/>'
        '</svg>'
    )

if not CLOSE_ICON.exists():
    CLOSE_ICON.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 16 16" fill="none" '
        'stroke="#8b949e" stroke-width="2" stroke-linecap="round">'
        '<line x1="4" y1="4" x2="12" y2="12"/>'
        '<line x1="12" y1="4" x2="4" y2="12"/>'
        '</svg>'
    )

if not CLOSE_HOVER_ICON.exists():
    CLOSE_HOVER_ICON.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 16 16" fill="none" '
        'stroke="#f85149" stroke-width="2" stroke-linecap="round">'
        '<line x1="4" y1="4" x2="12" y2="12"/>'
        '<line x1="12" y1="4" x2="4" y2="12"/>'
        '</svg>'
    )

if not TERMINAL_ICON.exists():
    TERMINAL_ICON.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" '
        'stroke="#1f6feb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="4 17 10 11 4 5"/>'
        '<line x1="12" y1="19" x2="20" y2="19"/>'
        '</svg>'
    )

if not LOGO_SVG.exists():
    LOGO_SVG.write_text("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 64" fill="none">
  <defs>
    <linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#06B6D4"/>
      <stop offset="100%" stop-color="#3B82F6"/>
    </linearGradient>
    <linearGradient id="fluxVector" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#94A3B8"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="3" flood-color="#000" flood-opacity="0.3"/>
    </filter>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  
  <!-- Scaled Independent Floating Monitor -->
  <g transform="translate(4, 4) scale(0.56)" filter="url(#shadow)">
    <rect x="10" y="15" width="80" height="55" rx="8" fill="none" stroke="#94A3B8" stroke-width="8"/>
    <path d="M50 70 V85 M35 85 H65" fill="none" stroke="#94A3B8" stroke-width="8" stroke-linecap="round"/>
    <path d="M -5 42 Q 30 10, 50 42 T 105 42" fill="none" stroke="url(#waveGrad)" stroke-width="10" stroke-linecap="round"/>
    <circle cx="50" cy="42" r="8" fill="#3B82F6"/>
  </g>
  
  <!-- Custom Vector Drawn "FLUX" -->
  <path d="M74 38 V16 H88 M74 26 H84 M96 16 V38 H110 M118 16 V30 A8 8 0 0 0 134 30 V16 M142 16 L158 38 M158 16 L142 38" 
        fill="none" stroke="url(#fluxVector)" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
  
  <!-- Glowing Slash Separator -->
  <path d="M174 16 L164 40" fill="none" stroke="#06B6D4" stroke-width="4" stroke-linecap="round" filter="url(#glow)"/>
  
  <!-- Custom Vector Drawn "RDM" -->
  <path d="M184 38 V16 H194 A6 6 0 0 1 194 28 H184 M190 28 L198 38 M208 16 V38 M208 16 H214 A11 11 0 0 1 214 38 H208 M232 38 V16 L242 26 L252 16 V38" 
        fill="none" stroke="#06B6D4" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
  
  <text x="70" y="58" fill="#64748B" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="13" font-weight="700" letter-spacing="2.5">REMOTE DESKTOP STUDIO</text>
</svg>""")

RAW_STYLE = """
QMainWindow {
    background-color: #090d13;
}

QWidget {
    color: #e6edf3;
    font-family: "DejaVu Sans", "Liberation Sans", -apple-system, sans-serif;
    font-size: 13px;
    outline: none;
}

QSplitter::handle {
    background-color: #21262d;
    width: 1px;
    height: 1px;
}

QSplitter::handle:hover {
    background-color: #58a6ff;
}

QFrame#Sidebar, QWidget#Sidebar {
    background-color: #0d1117;
    border-right: 1px solid #21262d;
}

QTreeView {
    background-color: #0d1117;
    border: none;
    outline: 0;
    padding: 4px;
    show-decoration-selected: 1;
}

QTreeView::item {
    height: 30px;
    border-radius: 6px;
    padding-left: 4px;
    color: #8b949e;
    border: none;
}

QTreeView::item:hover {
    background-color: #161b22;
    color: #f0f6fc;
}

QTreeView::item:selected {
    background-color: #1f293d;
    color: #58a6ff;
    font-weight: 600;
}

QTreeView::branch {
    background-color: transparent;
}

QTreeView::branch:selected {
    background-color: #1f293d;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: url("__CHEVRON_RIGHT__");
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {
    image: url("__CHEVRON_DOWN__");
}

QListView, QTableView {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 6px;
    color: #e6edf3;
    gridline-color: #21262d;
    selection-background-color: #1f293d;
    selection-color: #58a6ff;
    padding: 4px;
}

QListView::item, QTableView::item {
    height: 28px;
    border-radius: 4px;
    padding: 4px;
}

QListView::item:hover, QTableView::item:hover {
    background-color: #161b22;
    color: #f0f6fc;
}

QListView::item:selected, QTableView::item:selected {
    background-color: #1f293d;
    color: #58a6ff;
}

QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    padding: 6px 10px;
    border: none;
    border-right: 1px solid #21262d;
    border-bottom: 1px solid #21262d;
    font-weight: 600;
    font-size: 11px;
}

QListWidget {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 6px;
    outline: none;
}

QListWidget::item {
    height: 32px;
    color: #8b949e;
    border-radius: 6px;
    padding-left: 6px;
    margin: 1px 0;
}

QListWidget::item:hover {
    background-color: #161b22;
    color: #f0f6fc;
}

QListWidget::item:selected {
    background-color: #1f293d;
    color: #58a6ff;
    font-weight: 500;
}

QLineEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f0f6fc;
    selection-background-color: #1f6feb;
}

QLineEdit:focus {
    border: 1px solid #58a6ff;
    background-color: #161b22;
}

QPushButton#EyeToggleBtn {
    background-color: transparent;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 0;
}

QPushButton#EyeToggleBtn:hover {
    background-color: #21262d;
    border-color: #58a6ff;
}

QComboBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 5px 12px;
    color: #e6edf3;
    min-height: 26px;
    combobox-popup: 0;
}

QComboBox:hover {
    border-color: #58a6ff;
}

QComboBox:focus {
    border: 1px solid #58a6ff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border-left: 1px solid #30363d;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox QAbstractItemView,
QComboBox QListView,
QComboBoxPrivateContainer {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #e6edf3;
    selection-background-color: #1f293d;
    selection-color: #58a6ff;
    padding: 2px;
    outline: none;
}

QComboBox QAbstractItemView::item,
QComboBox QListView::item {
    min-height: 28px;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: transparent;
}

QComboBox QAbstractItemView::item:selected,
QComboBox QListView::item:selected {
    background-color: #1f293d;
    color: #58a6ff;
}

QComboBox QAbstractItemView QScrollBar:vertical,
QComboBox QListView QScrollBar:vertical {
    border: none;
    background: #161b22;
    width: 6px;
    margin: 0;
}

QComboBox QAbstractItemView QScrollBar::handle:vertical,
QComboBox QListView QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 20px;
    border-radius: 3px;
}

QComboBox QAbstractItemView QScrollBar::handle:vertical:hover,
QComboBox QListView QScrollBar::handle:vertical:hover {
    background: #58a6ff;
}

QComboBox QAbstractItemView QScrollBar::add-line:vertical,
QComboBox QAbstractItemView QScrollBar::sub-line:vertical,
QComboBox QListView QScrollBar::add-line:vertical,
QComboBox QListView QScrollBar::sub-line:vertical {
    background: none;
    border: none;
    height: 0px;
    width: 0px;
}

QScrollBar:vertical {
    border: none;
    background: #0d1117;
    width: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #58a6ff;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #0d1117;
    height: 6px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #30363d;
    min-width: 24px;
    border-radius: 3px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QPushButton {
    background-color: #161b22;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #21262d;
    border-color: #8b949e;
    color: #ffffff;
}

QPushButton#PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1f6feb, stop:1 #238636);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton#PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #388bfd, stop:1 #2ea043);
}

QPushButton#GhostBtn {
    background-color: #161b22;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 12px;
}

QPushButton#GhostBtn:hover {
    background-color: #21262d;
    border-color: #8b949e;
    color: #ffffff;
}

QTabWidget::pane {
    border: none;
    background-color: #090d13;
}

QTabBar::tab {
    background: #0d1117;
    color: #8b949e;
    padding: 9px 18px;
    margin-right: 2px;
    border-bottom: 2px solid transparent;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background: #161b22;
    color: #58a6ff;
    border-bottom: 2px solid #58a6ff;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background: #13171f;
    color: #c9d1d9;
}

/* Modern Tab Close Button */
QTabBar::close-button {
    image: url("__CLOSE_ICON__");
    subcontrol-position: right;
    margin-left: 6px;
    padding: 2px;
    border-radius: 4px;
    background: transparent;
}

QTabBar::close-button:hover {
    image: url("__CLOSE_HOVER_ICON__");
    background-color: rgba(248, 81, 73, 0.15);
}

QTabBar::close-button:pressed {
    background-color: rgba(248, 81, 73, 0.3);
}

QMenu {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 5px;
}

QMenu::item {
    background-color: transparent;
    color: #e6edf3;
    padding: 7px 24px 7px 12px;
    border-radius: 5px;
    margin: 1px 0;
}

QMenu::item:selected {
    background-color: #1f293d;
    color: #58a6ff;
}

QMenu::separator {
    height: 1px;
    background-color: #21262d;
    margin: 4px 6px;
}

QStatusBar {
    background-color: #090d13;
    border-top: 1px solid #21262d;
    color: #7d8590;
    font-size: 11px;
}

QDialog, QMessageBox, QFileDialog {
    background-color: #0f141c;
    color: #e6edf3;
}

QDialog QLabel, QMessageBox QLabel, QFileDialog QLabel {
    color: #e6edf3;
}
"""

MODERN_STYLE = (
    RAW_STYLE
    .replace("__CHEVRON_RIGHT__", CHEVRON_RIGHT.as_posix())
    .replace("__CHEVRON_DOWN__", CHEVRON_DOWN.as_posix())
    .replace("__CLOSE_ICON__", CLOSE_ICON.as_posix())
    .replace("__CLOSE_HOVER_ICON__", CLOSE_HOVER_ICON.as_posix())
)

class ShineOverlay(QWidget):
    """A transparent overlay that paints a self-animating sweeping shine effect mapped strictly to the SVG outline."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        if parent:
            self.setFixedSize(parent.size())

        self._offset = -120.0
        
        self.anim = QPropertyAnimation(self, b"offset")
        self.anim.setDuration(4000)
        self.anim.setStartValue(-120.0)
        self.anim.setEndValue(600.0)
        self.anim.setLoopCount(-1)
        self.anim.start()

    @pyqtProperty(float)
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, val):
        self._offset = val
        self.update()

    def paintEvent(self, event):
        parent = self.parent()
        if not parent or not hasattr(parent, 'renderer'):
            return

        # 1. Create a transparent buffer image matching the widget size
        img = QImage(self.size(), QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 2. Render the actual SVG into the buffer to act as our alpha mask
        parent.renderer().render(painter)

        # 3. Switch to SourceIn mode (only keeps pixels where the SVG already drew something)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)

        # 4. Draw the sweeping shine effect
        shine_width = 45.0
        painter.translate(self._offset, 0)
        painter.shear(-0.4, 0.0) 
        
        gradient = QLinearGradient(0, 0, shine_width, 0)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.5, QColor(255, 255, 255, 120))  # Slightly brighter so it pops inside the thin vectors
        gradient.setColorAt(1.0, QColor(255, 255, 255, 0))

        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # We draw a very tall rectangle to ensure the shear angle doesn't clip the top/bottom
        painter.drawRect(0, -self.height(), int(shine_width), self.height() * 3)
        painter.end()

        # 5. Finally, draw the masked buffer directly onto the overlay widget
        widget_painter = QPainter(self)
        widget_painter.drawImage(0, 0, img)