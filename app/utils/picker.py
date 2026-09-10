import sys
from PyQt6.QtWidgets import QApplication, QFileDialog
from app.ui.theme import MODERN_STYLE

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_STYLE)

    title = sys.argv[1] if len(sys.argv) > 1 else "Select File"
    start_dir = sys.argv[2] if len(sys.argv) > 2 else "/"
    file_filter = sys.argv[3] if len(sys.argv) > 3 else "All Files (*)"

    file_path, _ = QFileDialog.getOpenFileName(
        None,
        title,
        start_dir,
        file_filter,
        options=QFileDialog.Option.DontUseNativeDialog
    )

    if file_path:
        print(file_path)
        sys.exit(0)
    sys.exit(1)

if __name__ == "__main__":
    main()
