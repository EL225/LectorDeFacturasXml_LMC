"""
app_streamlit.py
────────────────
Demo web del Procesador de Facturas LMC.
Reutiliza la lógica de core/procesador.py sin modificaciones.

Ejecución local:  streamlit run app_streamlit.py
"""

import io
import csv
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd
import streamlit as st

from core.procesador import Factura, CSV_HEADERS, NS


# ─────────────────────────────────────────────────────────
# Adaptador: parsear desde bytes en memoria (no desde disco)
# Replica la lógica de core.procesador.parsear_factura
# pero acepta un objeto file-like en lugar de una ruta.
# ─────────────────────────────────────────────────────────
def parsear_factura_desde_bytes(contenido: bytes) -> Factura:
    tree = ET.parse(io.BytesIO(contenido))
    root = tree.getroot()
    fecha_raw = root.findtext(".//fe:dFechaEm", namespaces=NS)

    return Factura(
        ruc          = root.findtext(".//fe:gEmis/fe:gRucEmi/fe:dRuc",  namespaces=NS),
        dv           = root.findtext(".//fe:gEmis/fe:gRucEmi/fe:dDV",   namespaces=NS),
        nombre       = root.findtext(".//fe:gEmis/fe:dNombEm",          namespaces=NS),
        num_fac      = root.findtext(".//fe:dNroDF",                    namespaces=NS),
        fecha        = fecha_raw.split("T")[0] if fecha_raw else None,
        item         = root.findtext(".//fe:gItem/fe:dSecItem",         namespaces=NS),
        codigo       = root.findtext(".//fe:gItem/fe:dCodProd",         namespaces=NS),
        descripcion  = root.findtext(".//fe:gItem/fe:dDescProd",        namespaces=NS),
        cantidad     = root.findtext(".//fe:gItem/fe:dCantCodInt",      namespaces=NS),
        unidad       = root.findtext(".//fe:gItem/fe:cUnidad",          namespaces=NS),
        precioUnidad = root.findtext(".//fe:gPrecios/fe:dPrUnit",       namespaces=NS),
        total_neto   = root.findtext(".//fe:gTot/fe:dTotNeto",          namespaces=NS),
        itbms        = root.findtext(".//fe:gTot/fe:dTotITBMS",         namespaces=NS),
        isc          = root.findtext(".//fe:gTot/fe:dTotISC",           namespaces=NS),
        descuentos   = root.findtext(".//fe:gTot/fe:dTotDesc",          namespaces=NS),
        total        = root.findtext(".//fe:gTot/fe:dTotRec",           namespaces=NS),
    )


def generar_csv_en_memoria(facturas: list[Factura]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADERS)
    for f in facturas:
        writer.writerow(f.as_row())
    return buffer.getvalue()


# ─────────────────────────────────────────────────────────
# Configuración de la página
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Procesador de Facturas LMC — Demo",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Procesador de Facturas LMC")
st.caption(
    "Demo web del procesador de facturas electrónicas DGI-FEP (Panamá). "
    "Extrae datos de XML de facturas y genera un reporte consolidado en CSV."
)

with st.expander("ℹ️ Sobre este proyecto"):
    st.markdown(
        """
        Esta aplicación procesa facturas electrónicas en formato **DGI-FEP** 
        (Dirección General de Ingresos de Panamá) y extrae automáticamente:

        - Datos del emisor (RUC, DV, nombre)
        - Número y fecha de factura
        - Detalle de ítems (código, descripción, cantidad, precio)
        - Totales (neto, ITBMS, ISC, descuentos, total)

        **Versión original:** aplicación de escritorio en Python + PyQt6, 
        empaquetada como ejecutable Windows.  
        **Este demo:** misma lógica de negocio expuesta vía web con Streamlit.

        🔒 **Privacidad:** los archivos se procesan en memoria durante tu sesión 
        y no se almacenan en ningún servidor.
        """
    )

st.divider()

# ─────────────────────────────────────────────────────────
# Selector de fuente de datos
# ─────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("1. Carga tus facturas XML")

with col2:
    usar_ejemplos = st.button("📂 Usar facturas de ejemplo", use_container_width=True)

archivos_subidos = st.file_uploader(
    "Arrastra uno o más archivos XML de facturas DGI-FEP",
    type=["xml"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

# Resolver la fuente de archivos
fuente_archivos = []  # lista de tuplas (nombre, bytes)

if usar_ejemplos:
    ejemplos_dir = Path(__file__).parent / "ejemplos"
    if ejemplos_dir.exists():
        for xml_path in sorted(ejemplos_dir.glob("*.xml")):
            fuente_archivos.append((xml_path.name, xml_path.read_bytes()))
        if fuente_archivos:
            st.success(f"✓ Cargados {len(fuente_archivos)} archivos de ejemplo")
    else:
        st.warning("No hay facturas de ejemplo disponibles")

elif archivos_subidos:
    for archivo in archivos_subidos:
        fuente_archivos.append((archivo.name, archivo.read()))

# ─────────────────────────────────────────────────────────
# Procesamiento
# ─────────────────────────────────────────────────────────
if fuente_archivos:
    st.divider()
    st.subheader("2. Resultado del procesamiento")

    facturas_ok: list[Factura] = []
    errores: list[tuple[str, str]] = []

    progreso = st.progress(0, text="Procesando...")
    total = len(fuente_archivos)

    for i, (nombre, contenido) in enumerate(fuente_archivos):
        try:
            factura = parsear_factura_desde_bytes(contenido)
            facturas_ok.append(factura)
        except Exception as e:
            errores.append((nombre, str(e)))
        progreso.progress((i + 1) / total, text=f"Procesando {nombre}...")

    progreso.empty()

    # Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Archivos totales", total)
    m2.metric("Procesados OK", len(facturas_ok))
    m3.metric("Con error", len(errores))

    # Errores (si hay)
    if errores:
        with st.expander(f"⚠️ Ver {len(errores)} archivo(s) con error"):
            for nombre, err in errores:
                st.error(f"**{nombre}** — {err}")

    # Tabla de resultados
    if facturas_ok:
        df = pd.DataFrame(
            [f.as_row() for f in facturas_ok],
            columns=CSV_HEADERS,
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Botón de descarga del CSV
        csv_texto = generar_csv_en_memoria(facturas_ok)
        st.download_button(
            label="⬇️ Descargar CSV consolidado",
            data=csv_texto,
            file_name="facturas_consolidadas.csv",
            mime="text/csv",
            use_container_width=True,
        )
else:
    st.info("👆 Sube archivos XML o prueba con facturas de ejemplo para comenzar")

# ─────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────
st.divider()
st.caption(
    "💻 Código fuente disponible en GitHub · "
    "Aplicación de escritorio original hecha con PyQt6"
)
