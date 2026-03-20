"""
ui/widgets.py
─────────────
Widgets reutilizables independientes de la lógica de negocio.
Pueden importarse en cualquier ventana sin modificación.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog,
)
from PyQt6.QtCore import Qt


class PathSelector(QFrame):
    """
    Fila compuesta: etiqueta + campo de texto + botón "Examinar".
    
    Parámetros:
        label       — texto de la etiqueta superior
        placeholder — texto gris dentro del campo
        folder      — True  → abre diálogo de carpeta
                      False → abre diálogo de guardar archivo CSV
    """

    def __init__(
        self,
        label: str,
        placeholder: str,
        folder: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._is_folder = folder
        self.setObjectName("PathSelector")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Etiqueta
        lbl = QLabel(label)
        lbl.setObjectName("FieldLabel")
        layout.addWidget(lbl)

        # Fila: campo + botón
        row = QHBoxLayout()
        row.setSpacing(6)

        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setObjectName("PathEdit")
        row.addWidget(self.edit, 1)

        self.btn = QPushButton("Examinar")
        self.btn.setObjectName("BrowseBtn")
        self.btn.setFixedWidth(90)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(self._browse)
        row.addWidget(self.btn)

        layout.addLayout(row)

    # ── Diálogos nativos del SO ──────────────
    def _browse(self) -> None:
        if self._is_folder:
            path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Guardar CSV como", "", "CSV (*.csv)"
            )
        if path:
            self.edit.setText(path)

    # ── Interfaz pública ─────────────────────
    def path(self) -> str:
        """Retorna la ruta ingresada (sin espacios al inicio/final)."""
        return self.edit.text().strip()

    def set_path(self, path: str) -> None:
        """Establece la ruta desde código."""
        self.edit.setText(path)
