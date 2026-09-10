import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QPixmap
from ui.theme import MODERN_STYLE
from ui.main_window import MainWindow

# Embed the SVG directly as a byte string
FLUX_ICON_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2c3e50" />
      <stop offset="100%" stop-color="#3498db" />
    </linearGradient>
  </defs>
  <rect width="100" height="100" rx="20" fill="url(#grad)"/>
  <path d="M25 35 h50 v40 h-50 z" fill="none" stroke="white" stroke-width="4" stroke-linejoin="round"/>
  <path d="M20 75 h60 M40 85 h20 M50 75 v10" stroke="white" stroke-width="4" stroke-linecap="round"/>
  <circle cx="50" cy="55" r="8" fill="white"/>
</svg>
"""

def main():
    app = QApplication(sys.argv)
    
    # 1. Force GNOME X11 window class for dock grouping
    app.setApplicationName("flux-rdm")
    app.setDesktopFileName("flux-rdm.desktop")
    
    # 2. Load the SVG from memory and apply it globally
    pixmap = QPixmap()
    pixmap.loadFromData(FLUX_ICON_SVG, "SVG")
    app.setWindowIcon(QIcon(pixmap))
    
    # 3. Apply your existing theme
    app.setStyleSheet(MODERN_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
