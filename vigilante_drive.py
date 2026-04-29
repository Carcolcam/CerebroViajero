import os
import json
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Configuración de Drive
SCOPES = ['https://www.googleapis.com/auth/drive']
CONFIG_DRIVE_PATH = 'config_drive.json'

def obtener_servicio_drive():
    creds = None
    if os.path.exists('token_drive.json'):
        creds = Credentials.from_authorized_user_file('token_drive.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_drive.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def procesar_zona_ingesta():
    print("Sentinel: Vigilando Zona de Ingesta en Google Drive...")
    
    # Cargar IDs de carpetas
    if not os.path.exists(CONFIG_DRIVE_PATH):
        print("   [!] Error: No se encuentra config_drive.json")
        return
        
    with open(CONFIG_DRIVE_PATH, "r") as f:
        config = json.load(f)
        id_ingesta = config.get("01_ZONA_INGESTA")
        id_vuelos = config.get("Vuelos")
        id_hoteles = config.get("Hoteles")

    service = obtener_servicio_drive()
    
    # Buscar archivos en la zona de ingesta
    query = f"'{id_ingesta}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = results.get('files', [])

    if not files:
        print("   [-] Zona de Ingesta vacía. No hay nuevos documentos.")
        return

    for f in files:
        nombre = f['name']
        file_id = f['id']
        
        print(f"   [+] Nuevo documento detectado: {nombre}")
        
        # Clasificación básica por nombre
        tipo = "Hoteles" if "HOTEL" in nombre.upper() or "HOSPEDAJE" in nombre.upper() else "Vuelos"
        target_folder_id = id_vuelos if tipo == "Vuelos" else id_hoteles
        
        # 1. Descargar Localmente (Para que el Tejedor lo vea)
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        ruta_local = os.path.join("Reserva", tipo, nombre)
        os.makedirs(os.path.dirname(ruta_local), exist_ok=True)
        
        with open(ruta_local, "wb") as local_file:
            local_file.write(fh.getvalue())
            
        print(f"      [OK] Descargado en: {ruta_local}")

        # 2. Mover en Drive (De Ingesta a su carpeta definitiva)
        file = service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))
        service.files().update(fileId=file_id, 
                             removeParents=previous_parents, 
                             addParents=target_folder_id, 
                             fields='id, parents').execute()
                             
        print(f"      [OK] Movido en Drive a carpeta de {tipo}.")

    # 3. Disparar actualización de Itinerario
    import subprocess
    print("\n[+] Sincronizando Itinerario Maestro...")
    subprocess.run(["python", "tejedor_itinerario.py"])
    print("[OK] Dashboard actualizado.")

if __name__ == "__main__":
    try:
        procesar_zona_ingesta()
    except Exception as e:
        print(f"   [!] Error en el Vigilante de Drive: {e}")
