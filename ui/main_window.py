"""
ui/main_window.py
─────────────────
Ventana principal de la aplicación.
Solo orquesta la UI y se comunica con el worker mediante señales Qt.
No contiene lógica de negocio ni acceso directo a archivos.
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QProgressBar, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor

from core.worker import ProcesadorWorker
from ui.widgets import PathSelector


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Procesador de Facturas DGI")
        self.setMinimumSize(680, 540)
        self.resize(720, 580)
        self._worker: ProcesadorWorker | None = None

        self._build_ui()
        self._apply_stylesheet()

    # ══════════════════════════════════════════
    #  Construcción de la interfaz
    # ══════════════════════════════════════════

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        layout.addLayout(self._build_header())
        layout.addWidget(self._build_divider())
        layout.addWidget(self._build_xml_selector())
        layout.addWidget(self._build_csv_selector())
        layout.addWidget(self._build_progress_bar())
        layout.addWidget(self._build_log_label())
        layout.addWidget(self._build_log_area(), stretch=1)
        layout.addLayout(self._build_bottom_bar())

    def _build_header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        header.setSpacing(2)

        title = QLabel("Procesador de Facturas")
        title.setObjectName("Title")

        subtitle = QLabel("Conversión de XML DGI-FEP a hoja de cálculo CSV")
        subtitle.setObjectName("Subtitle")

        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _build_divider(self) -> QFrame:
        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        return divider

    def _build_xml_selector(self) -> PathSelector:
        self.xml_selector = PathSelector(
            label       = "Carpeta de facturas XML",
            placeholder = "Seleccione la carpeta que contiene los archivos .xml",
            folder      = True,
        )
        return self.xml_selector

    def _build_csv_selector(self) -> PathSelector:
        self.csv_selector = PathSelector(
            label       = "Archivo de salida CSV",
            placeholder = "Ruta donde se guardará el archivo .csv generado",
            folder      = False,
        )
        return self.csv_selector

    def _build_progress_bar(self) -> QProgressBar:
        self.progress = QProgressBar()
        self.progress.setObjectName("Progress")
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        return self.progress

    def _build_log_label(self) -> QLabel:
        lbl = QLabel("Registro de actividad")
        lbl.setObjectName("FieldLabel")
        return lbl

    def _build_log_area(self) -> QTextEdit:
        self.log = QTextEdit()
        self.log.setObjectName("Log")
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        return self.log

    def _build_bottom_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)

        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusLabel")
        row.addWidget(self.status_label, stretch=1)

        self.clear_btn = QPushButton("Limpiar")
        self.clear_btn.setObjectName("SecondaryBtn")
        self.clear_btn.setFixedWidth(90)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self._on_limpiar)
        row.addWidget(self.clear_btn)

        self.run_btn = QPushButton("Procesar facturas")
        self.run_btn.setObjectName("PrimaryBtn")
        self.run_btn.setFixedWidth(150)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self._on_procesar)
        row.addWidget(self.run_btn)

        return row

    # ══════════════════════════════════════════
    #  Manejadores de eventos (slots)
    # ══════════════════════════════════════════

    def _on_limpiar(self) -> None:
        self.log.clear()
        self.progress.setValue(0)
        self.status_label.setText("")

    def _on_procesar(self) -> None:
        carpeta = self.xml_selector.path()
        csv_out = self.csv_selector.path()

        if not carpeta or not os.path.isdir(carpeta):
            self._log("Por favor seleccione una carpeta válida de XML.", "error")
            return
        if not csv_out:
            self._log("Por favor especifique la ruta del archivo CSV de salida.", "error")
            return

        self._set_processing(True)
        self.progress.setValue(0)
        self.status_label.setText("Procesando…")
        self._log(f"Iniciando procesamiento en: {carpeta}", "info")

        self._worker = ProcesadorWorker(carpeta, csv_out)
        self._worker.progreso.connect(self.progress.setValue)
        self._worker.mensaje.connect(self._log)
        self._worker.terminado.connect(self._on_terminado)
        self._worker.start()

    def _on_terminado(self, procesados: int, errores: int) -> None:
        self._set_processing(False)
        nivel   = "ok" if errores == 0 else "error"
        resumen = f"Finalizado — {procesados} procesados, {errores} errores."
        self._log(resumen, nivel)
        self.status_label.setText(resumen)
        self.progress.setValue(100)

    # ══════════════════════════════════════════
    #  Helpers privados
    # ══════════════════════════════════════════

    def _set_processing(self, active: bool) -> None:
        """Activa/desactiva controles durante el procesamiento."""
        self.run_btn.setEnabled(not active)
        self.xml_selector.setEnabled(not active)
        self.csv_selector.setEnabled(not active)

    def _log(self, texto: str, nivel: str = "info") -> None:
        colors = {"info": "#94a3b8", "ok": "#4ade80", "error": "#f87171"}
        color  = colors.get(nivel, "#94a3b8")
        self.log.append(
            f'<span style="color:{color}; font-family: monospace;">{texto}</span>'
        )
        self.log.moveCursor(QTextCursor.MoveOperation.End)

    # ══════════════════════════════════════════
    #  Estilos
    # ══════════════════════════════════════════

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            QLabel#Title {
                font-size: 20px;
                font-weight: 700;
                color: #f1f5f9;
                letter-spacing: -0.5px;
            }
            QLabel#Subtitle {
                font-size: 12px;
                color: #64748b;
            }
            QLabel#FieldLabel {
                font-size: 11px;
                font-weight: 600;
                color: #94a3b8;
                letter-spacing: 0.8px;
            }
            QLabel#StatusLabel {
                font-size: 11px;
                color: #64748b;
            }
            QFrame#Divider {
                background-color: #1e293b;
                border: none;
            }
            QLineEdit#PathEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 12px;
                color: #cbd5e1;
            }
            QLineEdit#PathEdit:focus {
                border-color: #3b82f6;
                background-color: #1e3a5f;
            }
            QPushButton#BrowseBtn {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 12px;
                color: #94a3b8;
            }
            QPushButton#BrowseBtn:hover {
                background-color: #334155;
                color: #e2e8f0;
            }
            QPushButton#PrimaryBtn {
                background-color: #2563eb;
                border: none;
                border-radius: 6px;
                padding: 9px 16px;
                font-size: 13px;
                font-weight: 600;
                color: #ffffff;
            }
            QPushButton#PrimaryBtn:hover      { background-color: #3b82f6; }
            QPushButton#PrimaryBtn:disabled   { background-color: #1e3a5f; color: #475569; }
            QPushButton#SecondaryBtn {
                background-color: transparent;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                color: #64748b;
            }
            QPushButton#SecondaryBtn:hover {
                border-color: #475569;
                color: #94a3b8;
            }
            QProgressBar#Progress {
                background-color: #1e293b;
                border: none;
                border-radius: 3px;
            }
            QProgressBar#Progress::chunk {
                background-color: #2563eb;
                border-radius: 3px;
            }
            QTextEdit#Log {
                background-color: #0a0f1e;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 10px;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 12px;
                color: #94a3b8;
            }
            QScrollBar:vertical              { background: #0f172a; width: 8px; }
            QScrollBar::handle:vertical      { background: #334155; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical    { height: 0px; }
        """)
