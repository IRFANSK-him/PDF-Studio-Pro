"""PDF Studio Pro — Phase 1 desktop PDF viewer."""
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QImage, QPixmap, QIcon
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QLabel, QMainWindow, QMessageBox,
    QScrollArea, QToolBar, QInputDialog, QListWidget, QDockWidget, QAbstractItemView, QListWidgetItem, QLineEdit
)
import fitz
from .production_tools import export_page_images, watermark_pdf, insert_image, set_metadata
from .editing import add_text, highlight_text, redact_text, encrypt_pdf
from .history import PageOrderHistory
from .search import find_text
from .pdf_engine import PDFDocument
from .page_tools import merge_pdfs, split_pdf, extract_pages, rotate_pages, delete_pages, reorder_pages


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.document = PDFDocument()
        self.page_index = 0
        self.zoom = 1.0
        self.history = PageOrderHistory()
        self.search_results = []
        self.search_position = -1
        self._restoring_order = False
        self.setWindowTitle("PDF Studio Pro")
        self.resize(1100, 800)
        self.page_label = QLabel("Open a PDF to begin")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.page_label)
        self.setCentralWidget(self.scroll)
        self.thumbnails = QListWidget()
        self.thumbnails.setIconSize(QSize(100, 140))
        self.thumbnails.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.thumbnails.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.thumbnails.itemClicked.connect(self.thumbnail_selected)
        self.thumbnails.model().rowsMoved.connect(self.on_pages_moved)
        self.thumbnail_dock = QDockWidget("Pages — drag to reorder", self)
        self.thumbnail_dock.setWidget(self.thumbnails)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.thumbnail_dock)
        self.setStyleSheet("""
            QMainWindow { background: #15171c; }
            QToolBar { background: #20232a; border: none; spacing: 8px; padding: 8px; }
            QToolButton { color: white; padding: 7px; }
            QToolButton:hover { background: #b91c1c; border-radius: 5px; }
            QScrollArea { background: #15171c; border: none; }
            QLabel { color: #d1d5db; }
            QListWidget { background: #1b1d24; color: #f3f4f6; border: none; selection-background-color: #991b1b; padding: 8px; }
            QDockWidget { color: #f3f4f6; font-weight: 600; }
            QStatusBar { background: #20232a; color: #f3f4f6; }
        """)
        toolbar = QToolBar("Document")
        self.addToolBar(toolbar)
        for label, handler in (
            ("Open PDF", self.open_file),
            ("Previous", self.previous_page),
            ("Next", self.next_page),
            ("Zoom −", self.zoom_out),
            ("Zoom +", self.zoom_in),
            ("Merge", self.merge_files),
            ("Split", self.split_file),
            ("Extract", self.extract_file),
            ("Rotate 90°", self.rotate_file),
            ("Delete pages", self.delete_file),
            ("Save page order", self.save_page_order),
            ("Undo order", self.undo_order),
            ("Redo order", self.redo_order),
            ("Find text", self.find_in_document),
            ("Next match", self.next_match),
            ("Add text", self.add_text_to_page),
            ("Highlight", self.highlight_on_page),
            ("Redact", self.redact_on_page),
            ("Protect PDF", self.protect_pdf),
            ("Export PNG", self.export_png),
            ("Watermark", self.add_watermark),
            ("Insert image", self.add_image),
            ("Metadata", self.edit_metadata),
        ):
            action = QAction(label, self)
            action.triggered.connect(handler)
            toolbar.addAction(action)
            shortcuts = {"Open PDF": "Ctrl+O", "Find text": "Ctrl+F", "Undo order": "Ctrl+Z", "Redo order": "Ctrl+Y", "Next match": "F3"}
            if label in shortcuts:
                action.setShortcut(shortcuts[label])
        self.statusBar().showMessage("Ready")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            self.document.open(path)
            self.page_index = 0
            self.zoom = 1.0
            self.populate_thumbnails()
            self.search_results = []
            self.search_position = -1
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


    def _require_document(self):
        if not self.document.path:
            QMessageBox.information(self, "Open PDF", "Open a PDF first.")
            return False
        return True

    def _choose_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save new PDF", "", "PDF Files (*.pdf)")
        return path

    def _pages_prompt(self):
        if not self._require_document():
            return None
        raw, ok = QInputDialog.getText(
            self, "Select pages", "Page numbers (e.g. 1,3-5):"
        )
        if not ok:
            return None
        try:
            indices = []
            for part in raw.replace(" ", "").split(","):
                if "-" in part:
                    first, last = map(int, part.split("-"))
                    if first > last:
                        raise ValueError("Page ranges must be ascending")
                    indices.extend(range(first - 1, last))
                else:
                    indices.append(int(part) - 1)
            if not indices or any(i < 0 or i >= self.document.page_count for i in indices):
                raise ValueError("Page number outside document range")
            return indices
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Invalid pages", "Use page numbers such as 1,3-5.")
            return None

    def _perform(self, operation):
        try:
            result = operation()
            QMessageBox.information(self, "PDF saved", f"Created: {result}")
        except Exception as exc:
            QMessageBox.critical(self, "Operation failed", str(exc))

    def merge_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select PDFs in merge order", "", "PDF Files (*.pdf)")
        if len(paths) < 2:
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: merge_pdfs(paths, output))

    def split_file(self):
        if not self._require_document():
            return
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self._perform(lambda: f"{len(split_pdf(self.document.path, folder))} files in {folder}")

    def extract_file(self):
        pages = self._pages_prompt()
        if pages is None:
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: extract_pages(self.document.path, pages, output))

    def rotate_file(self):
        pages = self._pages_prompt()
        if pages is None:
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: rotate_pages(self.document.path, pages, 90, output))

    def delete_file(self):
        pages = self._pages_prompt()
        if pages is None:
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: delete_pages(self.document.path, pages, output))


    def populate_thumbnails(self):
        self.thumbnails.clear()
        if not self.document.path:
            return
        with fitz.open(str(self.document.path)) as doc:
            for index, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2), alpha=False)
                image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy()
                item = QListWidgetItem(QIcon(QPixmap.fromImage(image)), f"Page {index + 1}")
                item.setData(Qt.ItemDataRole.UserRole, index)
                self.thumbnails.addItem(item)
        self.history.reset(list(range(self.thumbnails.count())))

    def thumbnail_selected(self, item):
        self.page_index = item.data(Qt.ItemDataRole.UserRole)
        self.show_page()

    def save_page_order(self):
        if not self._require_document():
            return
        order = [self.thumbnails.item(i).data(Qt.ItemDataRole.UserRole)
                 for i in range(self.thumbnails.count())]
        if order == list(range(self.document.page_count)):
            QMessageBox.information(self, "Page order", "Pages are already in their original order.")
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: reorder_pages(self.document.path, order, output))


    def current_page_order(self):
        return [self.thumbnails.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.thumbnails.count())]

    def on_pages_moved(self, *args):
        if not self._restoring_order:
            self.history.record(self.current_page_order())

    def restore_page_order(self, order):
        self._restoring_order = True
        try:
            items = {}
            while self.thumbnails.count():
                item = self.thumbnails.takeItem(0)
                items[item.data(Qt.ItemDataRole.UserRole)] = item
            for index in order:
                self.thumbnails.addItem(items[index])
        finally:
            self._restoring_order = False

    def undo_order(self):
        if self.history.can_undo:
            self.restore_page_order(self.history.undo())

    def redo_order(self):
        if self.history.can_redo:
            self.restore_page_order(self.history.redo())

    def find_in_document(self):
        if not self._require_document():
            return
        query, ok = QInputDialog.getText(self, "Find in PDF", "Search text:")
        if not ok or not query.strip():
            return
        try:
            self.search_results = find_text(self.document.path, query)
            self.search_position = -1
            if self.search_results:
                self.next_match()
            else:
                QMessageBox.information(self, "Search", "No matching text found.")
        except Exception as exc:
            QMessageBox.critical(self, "Search failed", str(exc))

    def next_match(self):
        if not self.search_results:
            return
        self.search_position = (self.search_position + 1) % len(self.search_results)
        self.page_index = self.search_results[self.search_position][0]
        self.show_page()
        self.statusBar().showMessage(
            f"Match {self.search_position + 1} of {len(self.search_results)} | Page {self.page_index + 1}"
        )


    def add_text_to_page(self):
        if not self._require_document():
            return
        text, ok = QInputDialog.getText(self, "Add text", "Text to insert:")
        if not ok or not text.strip():
            return
        x, ok = QInputDialog.getDouble(self, "Text position", "X (PDF points):", 72, 0, 10000, 1)
        if not ok:
            return
        y, ok = QInputDialog.getDouble(self, "Text position", "Y (PDF points):", 120, 0, 10000, 1)
        if not ok:
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: add_text(self.document.path, self.page_index, text, x, y, output))

    def highlight_on_page(self):
        if not self._require_document():
            return
        query, ok = QInputDialog.getText(self, "Highlight text", "Text on current page:")
        if not ok or not query.strip():
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: highlight_text(self.document.path, self.page_index, query, output))

    def redact_on_page(self):
        if not self._require_document():
            return
        query, ok = QInputDialog.getText(self, "Permanent redaction", "Text to permanently remove:")
        if not ok or not query.strip():
            return
        confirmation = QMessageBox.warning(
            self, "Permanent redaction",
            "This permanently removes matching content from the new PDF. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: redact_text(self.document.path, self.page_index, query, output))

    def protect_pdf(self):
        if not self._require_document():
            return
        user_pw, ok = QInputDialog.getText(
            self, "PDF password", "Reader password:", QLineEdit.EchoMode.Password
        )
        if not ok or not user_pw:
            return
        owner_pw, ok = QInputDialog.getText(
            self, "PDF owner password", "Owner password:", QLineEdit.EchoMode.Password
        )
        if not ok or not owner_pw:
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: encrypt_pdf(self.document.path, output, user_pw, owner_pw))


    def export_png(self):
        if not self._require_document():
            return
        folder = QFileDialog.getExistingDirectory(self, "Select PNG export folder")
        if folder:
            self._perform(lambda: f"{len(export_page_images(self.document.path, folder))} PNG files in {folder}")

    def add_watermark(self):
        if not self._require_document():
            return
        value, ok = QInputDialog.getText(self, "Watermark", "Watermark text:")
        if not ok or not value.strip():
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: watermark_pdf(self.document.path, output, value))

    def add_image(self):
        if not self._require_document():
            return
        image, _ = QFileDialog.getOpenFileName(self, "Select image", "", "Images (*.png *.jpg *.jpeg)")
        if not image:
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: insert_image(self.document.path, self.page_index, image, output))

    def edit_metadata(self):
        if not self._require_document():
            return
        title, ok = QInputDialog.getText(self, "PDF metadata", "Document title:")
        if not ok:
            return
        author, ok = QInputDialog.getText(self, "PDF metadata", "Author:")
        if not ok:
            return
        output = self._choose_output()
        if output:
            self._perform(lambda: set_metadata(self.document.path, output, title, author))

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
