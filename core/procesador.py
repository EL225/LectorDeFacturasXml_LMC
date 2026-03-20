
# core/procesador.py
# ──────────────────
# Lógica pura de negocio: parseo de XML y escritura de CSV.
# No depende de Qt — se puede importar y testear de forma independiente.


import csv
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional


NS = {"fe": "http://dgi-fep.mef.gob.pa"}

CSV_HEADERS = [
    "RUC",
    "DV",
    "Nombre",
    "Num de Factura",
    "Fecha",
    "Total Neto",
    "ITBMS",
    "ISC",
    "Descuentos",
    "Total",
]


@dataclass
class Factura:
    #Representa los campos extraídos de una factura XML.
    ruc:        Optional[str]
    dv:         Optional[str]
    nombre:     Optional[str]
    num_fac:    Optional[str]
    fecha:      Optional[str]
    total_neto: Optional[str]
    itbms:      Optional[str]
    isc:        Optional[str]
    descuentos: Optional[str]
    total:      Optional[str]

    def as_row(self) -> list:
        return [
            self.ruc,
            self.dv,
            self.nombre,
            self.num_fac,
            self.fecha,
            self.total_neto,
            self.itbms,
            self.isc,
            self.descuentos,
            self.total,
        ]


def obtener_archivos_xml(carpeta: str) -> list[str]:
    #Retorna la lista de rutas de archivos .xml dentro de una carpeta.
    return [
        os.path.join(carpeta, f)
        for f in os.listdir(carpeta)
        if f.lower().endswith(".xml")
    ]


def parsear_factura(ruta_xml: str) -> Factura:
    
    # Parsea un archivo XML de factura DGI-FEP y retorna un objeto Factura.
    # Lanza una excepción si el archivo no se puede procesar.
    
    tree = ET.parse(ruta_xml)
    root = tree.getroot()

    fecha_raw = root.findtext(".//fe:dFechaEm", namespaces=NS)

    return Factura(
        ruc        = root.findtext(".//fe:gEmis/fe:gRucEmi/fe:dRuc",  namespaces=NS),
        dv         = root.findtext(".//fe:gEmis/fe:gRucEmi/fe:dDV",   namespaces=NS),
        nombre     = root.findtext(".//fe:gEmis/fe:dNombEm",           namespaces=NS),
        num_fac    = root.findtext(".//fe:dNroDF",                     namespaces=NS),
        fecha      = fecha_raw.split("T")[0] if fecha_raw else None,
        total_neto = root.findtext(".//fe:gTot/fe:dTotNeto",           namespaces=NS),
        itbms      = root.findtext(".//fe:gTot/fe:dTotITBMS",          namespaces=NS),
        isc        = root.findtext(".//fe:gTot/fe:dTotISC",            namespaces=NS),
        descuentos = root.findtext(".//fe:gTot/fe:dTotDesc",           namespaces=NS),
        total      = root.findtext(".//fe:gTot/fe:dTotRec",            namespaces=NS),
    )


def inicializar_csv(ruta_csv: str) -> None:
    #Crea (o sobreescribe) el CSV con los encabezados.
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(CSV_HEADERS)


def escribir_fila(ruta_csv: str, factura: Factura) -> None:
    #Agrega una fila al CSV existente.
    with open(ruta_csv, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(factura.as_row())
