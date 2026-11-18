"""PDF Studio Pro — Phase 1 desktop PDF viewer."""
import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QLabel, QMainWindow, QMessageBox,
    QScrollArea, QToolBar
)
from .pdf_engine import PDFDocument


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.document = PDFDocument()
        self.page_index = 0
        self.zoom = 1.0
        self.setWindowTitle("PDF Studio Pro")
        self.resize(1100, 800)
        self.page_label = QLabel("Open a PDF to begin")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.page_label)
        self.setCentralWidget(self.scroll)
        self.setStyleSheet("""
            QMainWindow { background: #15171c; }
            QToolBar { background: #20232a; border: none; spacing: 8px; padding: 8px; }
            QToolButton { color: white; padding: 7px; }
            QToolButton:hover { background: #b91c1c; border-radius: 5px; }
            QScrollArea { background: #15171c; border: none; }
            QLabel { color: #d1d5db; }
        """)
        toolbar = QToolBar("Document")
        self.addToolBar(toolbar)
        for label, handler in (
            ("Open PDF", self.open_file),
            ("Previous", self.previous_page),
            ("Next", self.next_page),
            ("Zoom −", self.zoom_out),
            ("Zoom +", self.zoom_in),
        ):
            action = QAction(label, self)
            action.triggered.connect(handler)
            toolbar.addAction(action)
        self.statusBar().showMessage("Ready")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            self.document.open(path)
            self.page_index = 0
            self.zoom = 1.0
            self.show_page()
            self.setWindowTitle(f"PDF Studio Pro — {Path(path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "Cannot open PDF", str(exc))

    def show_page(self):
        if not self.document.page_count:
            return
        pix = self.document.render(self.page_index, self.zoom)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy()
        self.page_label.setPixmap(QPixmap.fromImage(image))
        self.page_label.resize(image.size())
        self.statusBar().showMessage(
            f"Page {self.page_index + 1} / {self.document.page_count}   |   Zoom {self.zoom:.0%}"
        )

    def previous_page(self):
        if self.page_index > 0:
            self.page_index -= 1
            self.show_page()

    def next_page(self):
        if self.page_index + 1 < self.document.page_count:
            self.page_index += 1
            self.show_page()

    def zoom_in(self):
        if self.document.page_count:
            self.zoom = min(4.0, round(self.zoom + 0.25, 2))
            self.show_page()

    def zoom_out(self):
        if self.document.page_count:
            self.zoom = max(0.25, round(self.zoom - 0.25, 2))
            self.show_page()

    def closeEvent(self, event):
        self.document.close()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
