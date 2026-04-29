import os
import json
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Forzar UTF-8 en la salida de terminal para evitar errores con emojis en Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Configuración de Scopes: Necesitamos acceso total a Drive para gestionar carpetas y archivos
SCOPES = ['https://www.googleapis.com/auth/drive']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token_drive.json')
CONFIG_PATH = os.path.join(BASE_DIR, 'config_drive.json')

def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(f"No se encontró credentials.json en {CREDENTIALS_PATH}")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def crear_carpeta(service, nombre, parent_id=None):
    """Crea una carpeta en Drive y devuelve su ID."""
    file_metadata = {
        'name': nombre,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    # Verificar si ya existe para no duplicar
    query = f"name = '{nombre}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    
    if items:
        print(f"   [Drive] Carpeta existente: {nombre}")
        return items[0]['id']
    
    file = service.files().create(body=file_metadata, fields='id').execute()
    print(f"   [Drive] Carpeta creada: {nombre}")
    return file.get('id')

def inicializar_boveda():
    print("🚀 Sentinel iniciando despliegue de bóveda en Google Drive...")
    try:
        service = get_drive_service()
        
        # 1. Carpeta Raíz
        root_id = crear_carpeta(service, "CerebroViajero_Sentinel")
        
        estructura = {
            "root": root_id,
            "operaciones": {
                "id": crear_carpeta(service, "📦 01_OPERACIONES", root_id),
                "sub": {}
            },
            "exploracion": {
                "id": crear_carpeta(service, "🗺️ 02_EXPLORACION", root_id),
                "sub": {}
            }
        }
        
        # 2. Subcarpetas de Operaciones
        op_id = estructura["operaciones"]["id"]
        estructura["operaciones"]["sub"]["plan_activo"] = crear_carpeta(service, "🟢 PLAN_ACTIVO", op_id)
        
        zona_crisis_id = crear_carpeta(service, "🔴 ZONA_CRISIS", op_id)
        estructura["operaciones"]["sub"]["zona_crisis"] = {
            "id": zona_crisis_id,
            "pendiente": crear_carpeta(service, "⏳ PENDIENTE_REEMBOLSO", zona_crisis_id),
            "reembolsado": crear_carpeta(service, "✅ REEMBOLSADO", zona_crisis_id)
        }
        
        estructura["operaciones"]["sub"]["legal"] = crear_carpeta(service, "📜 LEGAL_Y_VISADOS", op_id)
        
        # 3. Subcarpetas de Exploración
        ex_id = estructura["exploracion"]["id"]
        estructura["exploracion"]["sub"]["drone"] = crear_carpeta(service, "🚁 DRONE_RADAR", ex_id)
        estructura["exploracion"]["sub"]["snorkel"] = crear_carpeta(service, "🤿 SNORKEL_SPOTS", ex_id)
        estructura["exploracion"]["sub"]["multimedia"] = crear_carpeta(service, "📸 MULTIMEDIA_INTEL", ex_id)
        estructura["exploracion"]["sub"]["gastronomia"] = crear_carpeta(service, "🍴 GASTRONOMIA", ex_id)
        estructura["exploracion"]["sub"]["cultura"] = crear_carpeta(service, "🗿 CULTURA_LOCAL", ex_id)
        
        # Guardar configuración
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(estructura, f, indent=4)
            
        print("\n✅ ¡Bóveda Sentinel desplegada con éxito!")
        print(f"Configuración guardada en: {CONFIG_PATH}")
        return service
        
    except Exception as e:
        print(f"\n❌ Error en el despliegue: {str(e)}")
        return None

def subir_archivo(service, nombre_local, carpeta_id, nombre_drive=None):
    """Sube un archivo local a una carpeta de Drive."""
    if not nombre_drive:
        nombre_drive = os.path.basename(nombre_local)
        
    file_metadata = {'name': nombre_drive, 'parents': [carpeta_id]}
    media = MediaFileUpload(nombre_local, resumable=True)
    
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"   [Drive] Archivo subido: {nombre_drive} (ID: {file.get('id')})")
    return file.get('id')

def archivar_por_pnr(service, pnr):
    """Busca archivos que contengan el PNR y los mueve a la zona de crisis."""
    print(f"\n🚨 Sentinel activando protocolo de crisis para PNR: {pnr}")
    
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    
    destino_id = config["operaciones"]["sub"]["zona_crisis"]["pendiente"]
    
    # Buscar archivos con el PNR en el nombre
    query = f"name contains '{pnr}' and trashed = false"
    results = service.files().list(q=query, fields='files(id, name, parents)').execute()
    items = results.get('files', [])
    
    if not items:
        print(f"   [Drive] No se encontraron documentos para el PNR {pnr}")
        return
    
    for file in items:
        file_id = file['id']
        nombre = file['name']
        print(f"   [Drive] Localizado: {nombre}. Moviendo a PENDIENTE_REEMBOLSO...")
        
        # Mover archivo (quitar padres actuales y añadir el de destino)
        prev_parents = ",".join(file.get('parents', []))
        service.files().update(
            fileId=file_id,
            addParents=destino_id,
            removeParents=prev_parents,
            fields='id, parents'
        ).execute()
        
    print(f"✅ Protocolo finalizado. Documentos a buen recaudo.")

if __name__ == "__main__":
    service = inicializar_boveda()
    
    # --- BLOQUE DE TEST (Descomentar para probar) ---
    # if service:
    #     # 1. Crear dummy
    #     with open("test_vuelo_ABC123.txt", "w") as f: f.write("Billete de prueba para PNR ABC123")
    #     
    #     with open(CONFIG_PATH, "r") as f: config = json.load(f)
    #     
    #     # 2. Subir a Plan Activo
    #     subir_archivo(service, "test_vuelo_ABC123.txt", config["operaciones"]["sub"]["plan_activo"])
    #     
    #     # 3. Simular crisis
    #     archivar_por_pnr(service, "ABC123")
    #     
    #     os.remove("test_vuelo_ABC123.txt")
