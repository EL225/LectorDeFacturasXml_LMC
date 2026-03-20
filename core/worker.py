
# core/worker.py
# ──────────────
# QThread que ejecuta el procesamiento en segundo plano.
# Usa exclusivamente funciones de core/procesador.py — no contiene lógica de negocio propia.


import os
from PyQt6.QtCore import QThread, pyqtSignal

from core.procesador import (
    obtener_archivos_xml,
    parsear_factura,
    inicializar_csv,
    escribir_fila,
)


class ProcesadorWorker(QThread):
   
    # Señales emitidas hacia la UI:
    #     progreso  (int)       — porcentaje 0–100
    #     mensaje   (str, str)  — texto, nivel: 'info' | 'ok' | 'error'
    #     terminado (int, int)  — archivos procesados, archivos con error
   

    progreso  = pyqtSignal(int)
    mensaje   = pyqtSignal(str, str)
    terminado = pyqtSignal(int, int)

    def __init__(self, carpeta_xml: str, archivo_csv: str):
        super().__init__()
        self.carpeta_xml  = carpeta_xml
        self.archivo_csv  = archivo_csv

    def run(self) -> None:
        archivos = obtener_archivos_xml(self.carpeta_xml)
        total    = len(archivos)

        if total == 0:
            self.mensaje.emit("No se encontraron archivos XML en la carpeta.", "error")
            self.terminado.emit(0, 0)
            return

        self.mensaje.emit(f"Encontrados {total} archivos XML.", "info")
        inicializar_csv(self.archivo_csv)

        procesados = 0
        errores    = 0

        for i, ruta in enumerate(archivos):
            nombre_archivo = os.path.basename(ruta)
            try:
                factura = parsear_factura(ruta)
                escribir_fila(self.archivo_csv, factura)
                self.mensaje.emit(f"✔  {nombre_archivo}", "ok")
                procesados += 1

            except Exception as e:
                self.mensaje.emit(f"✘  {nombre_archivo}: {e}", "error")
                errores += 1

            self.progreso.emit(int((i + 1) / total * 100))

        self.terminado.emit(procesados, errores)
