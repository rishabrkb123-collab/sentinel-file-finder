from __future__ import annotations

import csv
import os
import subprocess
from datetime import datetime, time

from PySide6.QtCore import QDate, QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .models import SearchFilters


class WorkerSignals(QObject):
    finished = Signal(object)
    errored = Signal(str)
    progress = Signal(str)


class Worker(QRunnable):
    def __init__(self, fn, *args, with_progress: bool = False, **kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.with_progress = with_progress
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            if self.with_progress:
                result = self.fn(*self.args, progress=self.signals.progress.emit, **self.kwargs)
            else:
                result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.errored.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, db, indexer, search_engine, app_paths) -> None:
        super().__init__()
        self.db = db
        self.indexer = indexer
        self.search_engine = search_engine
        self.app_paths = app_paths
        self.thread_pool = QThreadPool.globalInstance()
        self.results: list[dict] = []
        self.active_search_id = 0
        self._build_ui()
        self._load_roots()
        self.statusBar().showMessage("Ready")

    def _build_ui(self) -> None:
        self.setWindowTitle("Sentinel File Finder")
        self.resize(1500, 900)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        sidebar = QVBoxLayout()
        layout.addLayout(sidebar, 1)
        layout.addLayout(self._build_results_panel(), 3)

        sidebar.addWidget(self._build_roots_group())
        sidebar.addWidget(self._build_search_group())
        sidebar.addWidget(self._build_filter_group())
        sidebar.addWidget(self._build_actions_group())
        sidebar.addStretch()

        status = QStatusBar()
        self.setStatusBar(status)
        docs_action = QAction("Open Docs Folder", self)
        docs_action.triggered.connect(self._open_docs_folder)
        self.menuBar().addAction(docs_action)

    def _build_roots_group(self) -> QGroupBox:
        group = QGroupBox("Indexed Locations")
        layout = QVBoxLayout(group)
        self.roots_list = QListWidget()
        layout.addWidget(self.roots_list)

        row = QHBoxLayout()
        add_root = QPushButton("Add Folder")
        add_root.clicked.connect(self._add_root)
        remove_root = QPushButton("Remove Selected")
        remove_root.clicked.connect(self._remove_root)
        row.addWidget(add_root)
        row.addWidget(remove_root)
        layout.addLayout(row)

        self.index_button = QPushButton("Rebuild Index")
        self.index_button.clicked.connect(self._rebuild_index)
        layout.addWidget(self.index_button)
        return group

    def _build_search_group(self) -> QGroupBox:
        group = QGroupBox("AI Search")
        layout = QVBoxLayout(group)
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Describe file or use patterns like **sample, sample**, **sample**, **sample**.pdf")
        self.query_input.returnPressed.connect(self._run_search)
        layout.addWidget(self.query_input)
        layout.addWidget(QLabel("Wildcard filename patterns: **sample = ends with, sample** = starts with, **sample** = contains"))

        row = QHBoxLayout()
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._run_search)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_filters)
        row.addWidget(self.search_button)
        row.addWidget(self.clear_button)
        layout.addLayout(row)
        return group

    def _build_filter_group(self) -> QGroupBox:
        group = QGroupBox("Filters")
        form = QFormLayout(group)

        self.extension_input = QLineEdit()
        self.extension_input.setPlaceholderText(".pdf or pdf")
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(
            ["Any", "Document", "Spreadsheet", "Code", "Data", "Image", "Audio", "Video", "Other"]
        )
        self.path_input = QLineEdit()
        self.min_size = QLineEdit()
        self.min_size.setPlaceholderText("0")
        self.max_size = QLineEdit()
        self.max_size.setPlaceholderText("100")
        self.content_only = QCheckBox("Only files with extracted content")
        self.use_modified_after = QCheckBox("Enable")
        self.use_modified_before = QCheckBox("Enable")
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(10, 1000)
        self.limit_spin.setValue(200)

        self.modified_after = QDateEdit()
        self.modified_after.setCalendarPopup(True)
        self.modified_after.setDisplayFormat("yyyy-MM-dd")
        self.modified_after.setDate(QDate(2000, 1, 1))

        self.modified_before = QDateEdit()
        self.modified_before.setCalendarPopup(True)
        self.modified_before.setDisplayFormat("yyyy-MM-dd")
        self.modified_before.setDate(QDate.currentDate())

        form.addRow("Extension", self.extension_input)
        form.addRow("Type", self.file_type_combo)
        form.addRow("Path Contains", self.path_input)
        form.addRow("Min Size (MB)", self.min_size)
        form.addRow("Max Size (MB)", self.max_size)
        after_row = QHBoxLayout()
        after_row.addWidget(self.use_modified_after)
        after_row.addWidget(self.modified_after)
        before_row = QHBoxLayout()
        before_row.addWidget(self.use_modified_before)
        before_row.addWidget(self.modified_before)
        form.addRow("Modified After", after_row)
        form.addRow("Modified Before", before_row)
        form.addRow("Result Limit", self.limit_spin)
        form.addRow("", self.content_only)
        return group

    def _build_actions_group(self) -> QGroupBox:
        group = QGroupBox("Actions")
        layout = QVBoxLayout(group)
        open_file = QPushButton("Open File")
        open_file.clicked.connect(self._open_selected_file)
        open_folder = QPushButton("Open Containing Folder")
        open_folder.clicked.connect(self._open_selected_folder)
        export_csv = QPushButton("Export Results CSV")
        export_csv.clicked.connect(self._export_csv)
        layout.addWidget(open_file)
        layout.addWidget(open_folder)
        layout.addWidget(export_csv)
        return group

    def _build_results_panel(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        self.results_table = QTableWidget(0, 7)
        self.results_table.setHorizontalHeaderLabels(
            ["Score", "Name", "Extension", "Type", "Size (MB)", "Modified", "Path"]
        )
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.results_table.itemSelectionChanged.connect(self._update_preview)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Result preview will appear here.")

        layout.addWidget(QLabel("Results"))
        layout.addWidget(self.results_table)
        layout.addWidget(QLabel("Preview"))
        layout.addWidget(self.preview)
        return layout

    def _load_roots(self) -> None:
        self.roots_list.clear()
        for root in self.db.load_roots():
            self.roots_list.addItem(root)

    def _add_root(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose Folder to Index")
        if not directory:
            return
        existing = [self.roots_list.item(index).text() for index in range(self.roots_list.count())]
        if directory not in existing:
            self.roots_list.addItem(directory)

    def _remove_root(self) -> None:
        for item in self.roots_list.selectedItems():
            self.roots_list.takeItem(self.roots_list.row(item))

    def _rebuild_index(self) -> None:
        roots = [self.roots_list.item(index).text() for index in range(self.roots_list.count())]
        if not roots:
            QMessageBox.warning(self, "No folders", "Add at least one folder before indexing.")
            return
        self.index_button.setEnabled(False)
        worker = Worker(self.indexer.rebuild_index, roots, with_progress=True)
        worker.signals.progress.connect(self.statusBar().showMessage)
        worker.signals.finished.connect(self._handle_index_complete)
        worker.signals.errored.connect(self._handle_error)
        self.thread_pool.start(worker)
        self.statusBar().showMessage("Indexing started...")

    def _handle_index_complete(self, result) -> None:
        self.index_button.setEnabled(True)
        self.search_engine.invalidate_model_cache()
        scanned, indexed = result
        self.statusBar().showMessage(f"Index complete. Scanned {scanned} files and indexed {indexed}.")
        QMessageBox.information(self, "Index complete", f"Scanned {scanned} files and indexed {indexed}.")

    def _handle_error(self, message: str) -> None:
        self.index_button.setEnabled(True)
        if hasattr(self, "search_button"):
            self.search_button.setEnabled(True)
        QMessageBox.critical(self, "Operation failed", message)
        self.statusBar().showMessage(message)

    def _run_search(self) -> None:
        try:
            filters = self._collect_filters()
        except ValueError as exc:
            self._handle_error(str(exc))
            return
        self.active_search_id += 1
        search_id = self.active_search_id
        self.search_button.setEnabled(False)
        self.results_table.setRowCount(0)
        self.preview.clear()
        self.statusBar().showMessage("Searching...")
        worker = Worker(self.search_engine.search, filters)
        worker.signals.finished.connect(lambda results, current_id=search_id: self._handle_search_complete(current_id, results))
        worker.signals.errored.connect(self._handle_error)
        self.thread_pool.start(worker)

    def _handle_search_complete(self, search_id: int, results: list[dict]) -> None:
        if search_id != self.active_search_id:
            return
        self.search_button.setEnabled(True)
        self.results = results
        self._render_results()
        self.statusBar().showMessage(f"Found {len(self.results)} results.")

    def _collect_filters(self) -> SearchFilters:
        def parse_float(widget: QLineEdit):
            text = widget.text().strip()
            return float(text) if text else None

        min_size = parse_float(self.min_size)
        max_size = parse_float(self.max_size)
        after_date = self.modified_after.date().toPython() if self.use_modified_after.isChecked() else None
        before_date = self.modified_before.date().toPython() if self.use_modified_before.isChecked() else None
        if min_size is not None and max_size is not None and min_size > max_size:
            raise ValueError("Min Size (MB) cannot be greater than Max Size (MB).")
        if after_date and before_date and after_date > before_date:
            raise ValueError("Modified After cannot be later than Modified Before.")

        return SearchFilters(
            query=self.query_input.text().strip(),
            extension=self.extension_input.text().strip(),
            file_type=self.file_type_combo.currentText(),
            path_contains=self.path_input.text().strip(),
            min_size_mb=min_size,
            max_size_mb=max_size,
            modified_after=datetime.combine(after_date, time.min) if after_date else None,
            modified_before=datetime.combine(before_date, time.max) if before_date else None,
            content_only=self.content_only.isChecked(),
            limit=self.limit_spin.value(),
        )

    def _render_results(self) -> None:
        self.results_table.setRowCount(len(self.results))
        for row_index, result in enumerate(self.results):
            values = [
                f"{result['score']:.3f}",
                result["name"],
                result["extension"],
                result["file_type"],
                f"{result['size_bytes'] / (1024 * 1024):.2f}",
                datetime.fromtimestamp(result["modified_ts"]).strftime("%Y-%m-%d %H:%M"),
                result["path"],
            ]
            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col_index == 0:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.results_table.setItem(row_index, col_index, item)
        self.preview.clear()

    def _selected_result(self) -> dict | None:
        rows = self.results_table.selectionModel().selectedRows()
        if not rows:
            return None
        return self.results[rows[0].row()]

    def _update_preview(self) -> None:
        selected = self._selected_result()
        if not selected:
            self.preview.clear()
            return
        preview = [
            f"Name: {selected['name']}",
            f"Path: {selected['path']}",
            f"Type: {selected['file_type']} {selected['extension']}",
            f"Score: {selected['score']}",
            "",
            selected.get("content_excerpt", "") or "(No extracted preview available)",
        ]
        self.preview.setPlainText("\n".join(preview))

    def _open_selected_file(self) -> None:
        selected = self._selected_result()
        if selected:
            os.startfile(selected["path"])

    def _open_selected_folder(self) -> None:
        selected = self._selected_result()
        if selected:
            subprocess.run(["explorer.exe", "/select,", selected["path"]], check=False)

    def _export_csv(self) -> None:
        if not self.results:
            QMessageBox.information(self, "No results", "Run a search before exporting.")
            return
        target, _ = QFileDialog.getSaveFileName(self, "Save Results CSV", "sentinel_results.csv", "CSV Files (*.csv)")
        if not target:
            return
        with open(target, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["score", "name", "extension", "file_type", "size_bytes", "modified_ts", "path", "content_excerpt"],
            )
            writer.writeheader()
            writer.writerows(self.results)
        self.statusBar().showMessage(f"Exported results to {target}")

    def _clear_filters(self) -> None:
        self.query_input.clear()
        self.extension_input.clear()
        self.file_type_combo.setCurrentIndex(0)
        self.path_input.clear()
        self.min_size.clear()
        self.max_size.clear()
        self.content_only.setChecked(False)
        self.use_modified_after.setChecked(False)
        self.use_modified_before.setChecked(False)
        self.limit_spin.setValue(200)
        self.results_table.setRowCount(0)
        self.preview.clear()
        self.statusBar().showMessage("Filters cleared.")

    def _open_docs_folder(self) -> None:
        if not self.app_paths.docs_path.exists():
            QMessageBox.warning(self, "Docs missing", f"Documentation folder not found:\n{self.app_paths.docs_path}")
            return
        os.startfile(str(self.app_paths.docs_path))


def create_app_window(db, indexer, search_engine, app_paths) -> MainWindow:
    QApplication.setOrganizationName("Sentinel")
    QApplication.setApplicationName("Sentinel File Finder")
    return MainWindow(db, indexer, search_engine, app_paths)
