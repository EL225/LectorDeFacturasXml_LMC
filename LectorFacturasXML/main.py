import csv
import xml.etree.ElementTree as ET
import os

carpetaXml = "FacturasXml"
archivoCsv = "Facturas.csv"

ns = {"fe": "http://dgi-fep.mef.gob.pa"}

def get_files_in_folder(folder_path):
    return [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(".xml")
    ]

with open(archivoCsv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "RUC",
        "DV",
        "Nombre",
        "Num de Factura",
        "Fecha",
        "Total Neto",
        "ITBMS",
        "Total"
    ])


files = get_files_in_folder(carpetaXml)

for archivoXml in files:
    try:
        tree = ET.parse(archivoXml)
        root = tree.getroot()

        # Extraer datos
        ruc = root.findtext(".//fe:gEmis/fe:gRucEmi/fe:dRuc", namespaces=ns)
        dv = root.findtext(".//fe:gEmis/fe:gRucEmi/fe:dDV", namespaces=ns)
        nombre = root.findtext(".//fe:gEmis/fe:dNombEm", namespaces=ns)

        num_factura = root.findtext(".//fe:dNroDF", namespaces=ns)

        fecha = root.findtext(".//fe:dFechaEm", namespaces=ns)
        fecha_solo = fecha.split("T")[0] if fecha else None

        total_neto = root.findtext(".//fe:gTot/fe:dTotNeto", namespaces=ns)
        itbms = root.findtext(".//fe:gTot/fe:dTotITBMS", namespaces=ns)
        total = root.findtext(".//fe:gTot/fe:dTotRec", namespaces=ns)

        
        # Escribir fila
        
        with open(archivoCsv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                ruc,
                dv,
                nombre,
                num_factura,
                fecha_solo,
                total_neto,
                itbms,
                total
            ])

        print(f"Procesado: {archivoXml}")

    except Exception as e:
        print(f"Error en {archivoXml}: {e}")

print("Proceso terminado. CSV generado correctamente.")

print("Archivo csv guardado de manera correcta")