import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
import PyPDF2

# Directorio raíz donde están las reservas
BASE_DIR = Path(r"C:\Users\Pc1\.gemini\antigravity\scratch\CerebroViajero\Reserva")

# Diccionarios de apoyo para el NLP básico
PROVEEDORES_CONOCIDOS = ["Booking", "Traveloka", "Qatar", "AirAsia", "Gotogate", "LionAir", "FlyJava"]
RUTAS_CONOCIDAS = ["MAD-DOH", "HKT", "CGK-KDI", "KDI-WNI", "MDC-KUL", "KUL-HKT", "MAD", "DOH", "CGK", "KDI", "WNI", "MDC", "KUL"]

def extraer_texto_archivo(ruta_archivo):
    """Extrae texto de un archivo TXT o PDF real usando PyPDF2."""
    texto = ruta_archivo.name + " "
    if ruta_archivo.suffix.lower() == '.txt':
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                texto += f.read()
        except:
            pass
    elif ruta_archivo.suffix.lower() == '.pdf':
        try:
            with open(ruta_archivo, 'rb') as f:
                lector = PyPDF2.PdfReader(f)
                for pagina in lector.pages:
                    extracto = pagina.extract_text()
                    if extracto:
                        texto += extracto + " "
        except Exception as e:
            print(f"[!] Error leyendo PDF {ruta_archivo.name}: {e}")
    return texto

def deducir_metadatos(texto, ruta_original):
    """Algoritmo Nivel 2: Busca huellas (fecha, tipo, ruta, proveedor, pnr) en el texto."""
    metadatos = {
        "fecha": "00-00-00", # DD-MM-AA por defecto
        "tipo": "Doc",
        "ruta": "Desconocida",
        "proveedor": "Agencia",
        "pnr": "SinPNR"
    }

    # 1. Deducir Tipo basado en la carpeta de origen o palabras clave
    texto_upper = texto.upper()
    if "VUELO" in texto_upper or "Vuelos" in ruta_original.parts:
        metadatos["tipo"] = "Vuelo"
    elif "HOTEL" in texto_upper or "Alojamientos" in ruta_original.parts or "Hoteles" in ruta_original.parts:
        metadatos["tipo"] = "Alojamiento"

    # 2. Buscar Proveedor
    for prov in PROVEEDORES_CONOCIDOS:
        if prov.upper() in texto_upper:
            metadatos["proveedor"] = prov
            break

    # 3. Buscar Fecha (Patrones como DD/MM/YYYY, YYYY-MM-DD, DD-MM-AA)
    match_fecha = re.search(r'([0-3][0-9])[-/](0[1-9]|1[0-2])[-/](2026|26)', texto)
    if match_fecha:
        dia = match_fecha.group(1)
        mes = match_fecha.group(2)
        metadatos["fecha"] = f"{dia}-{mes}-26"
    else:
        # Intento secundario: formato YYYY-MM-DD
        match_fecha2 = re.search(r'2026[-/](0[1-9]|1[0-2])[-/]([0-3][0-9])', texto)
        if match_fecha2:
            mes = match_fecha2.group(1)
            dia = match_fecha2.group(2)
            metadatos["fecha"] = f"{dia}-{mes}-26"

    # 4. Buscar PNR (6 caracteres alfanuméricos en mayúsculas) o crear Hash
    match_pnr = re.search(r'\b[A-Z0-9]{6}\b', texto)
    if match_pnr and not match_pnr.group(0).isnumeric(): 
        metadatos["pnr"] = match_pnr.group(0)
    else:
        # Si no hay PNR, creamos un hash corto del nombre original como identificador único
        hash_corto = hashlib.md5(ruta_original.name.encode()).hexdigest()[:6].upper()
        metadatos["pnr"] = f"H-{hash_corto}"

    return metadatos

def limpiar_y_renombrar(dry_run=True):
    print("CerebroViajero: Iniciando Estandarizacion de Documentos...")
    print("-" * 60)
    
    archivos_procesados = 0
    
    # Recorrer Vuelos y Hoteles
    for subdir in ["Vuelos", "Hoteles"]:
        ruta_subdir = BASE_DIR / subdir
        if not ruta_subdir.exists():
            continue
            
        for archivo in ruta_subdir.glob("*.*"):
            if archivo.is_dir() or archivo.suffix.lower() not in ['.pdf', '.txt']:
                continue
                
            # Extraer huellas
            texto = extraer_texto_archivo(archivo)
            datos = deducir_metadatos(texto, archivo)
            
            # Construir Nuevo Nombre: [DD-MM-AA]_[Tipo]_[Ruta]_[Proveedor]_[Hash_o_PNR].extension
            nuevo_nombre = f"[{datos['fecha']}]_{datos['tipo']}_{datos['ruta']}_{datos['proveedor']}_{datos['pnr']}{archivo.suffix}"
            nueva_ruta = ruta_subdir / nuevo_nombre
            
            # Evitar renombrar si ya cumple el estándar
            if archivo.name.startswith("["):
                continue

            archivos_procesados += 1
            print(f"Original : {archivo.name}")
            print(f"Renombrado: {nuevo_nombre}")
            
            if not dry_run:
                # Mover / Renombrar físicamente de forma segura
                if nueva_ruta.exists():
                    nueva_ruta = nueva_ruta.with_name(nueva_ruta.stem + "_dup" + nueva_ruta.suffix)
                archivo.rename(nueva_ruta)
            print("-" * 60)
            
    if dry_run:
        print("\nMODO DRY-RUN: No se han modificado los archivos fisicos.")
        print("Para aplicar los cambios reales, cambiar dry_run=False")
    else:
        print(f"\nProceso Completado: {archivos_procesados} archivos estandarizados en disco.")

if __name__ == "__main__":
    # Cambia dry_run a False cuando quieras modificar los archivos reales
    limpiar_y_renombrar(dry_run=False)
