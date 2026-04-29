import msal
import imaplib
import base64
import os
import email
from email.header import decode_header
import json
import re
from pathlib import Path
from dotenv import load_dotenv
import hashlib
import PyPDF2
from io import BytesIO

# --- CONFIGURACIÓN SENTINEL ELITE ---
load_dotenv()
CLIENT_ID = os.getenv('HOTMAIL_CLIENT_ID')
CLIENT_SECRET = os.getenv('HOTMAIL_CLIENT_SECRET')
EMAIL = os.getenv('HOTMAIL_EMAIL', "carlos.collado@hotmail.com")
TOKEN_PATH = os.getenv('HOTMAIL_TOKEN_PATH', 'hotmail_token.txt')
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["https://outlook.office.com/IMAP.AccessAsUser.All"]

BUSQUEDA_KEYWORDS = ["2026", "Booking", "Gotogate", "Reserva", "Confirmation", "Itinerary", "Sudeste", "Hotel", "Vuelo", "Qatar", "Iberia", "AirAsia"]
CARPETAS_MS = ["INBOX", '"Sent Items"']

BASE_DIR = Path(r"c:\Users\Pc1\.gemini\antigravity\scratch\CerebroViajero")
RESERVA_DIR = BASE_DIR / "Reserva"
CONVERSACIONES_DIR = BASE_DIR / "Conversaciones"
for d in ["Vuelos", "Hoteles"]: (RESERVA_DIR / d).mkdir(parents=True, exist_ok=True)
CONVERSACIONES_DIR.mkdir(parents=True, exist_ok=True)

def conectar_hotmail():
    print(f"[*] Autenticando en Azure para {EMAIL}...")
    if not os.path.exists(TOKEN_PATH): 
        print(f"[!] Error: No existe {TOKEN_PATH}")
        return None
    with open(TOKEN_PATH, "r") as f: refresh_token = f.read().strip()
    
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
    result = app.acquire_token_by_refresh_token(refresh_token, scopes=SCOPES)
    
    if "access_token" in result:
        token = result["access_token"]
        auth_string = f"user={EMAIL}\x01auth=Bearer {token}\x01\x01"
        auth_base64 = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
        
        mail = imaplib.IMAP4_SSL("outlook.office365.com")
        tag = mail._new_tag().decode('ascii')
        cmd = f"{tag} AUTHENTICATE XOAUTH2 {auth_base64}\r\n"
        mail.send(cmd.encode('ascii'))
        
        while True:
            line = mail.readline().decode('ascii')
            print(f"   [SERVER]: {line.strip()}") # Debug vital
            if line.startswith(tag):
                if "OK" in line: 
                    print("[+] Autenticacion Exitosa.")
                    mail.state = 'AUTH' # Forzamos el estado para que imaplib nos deje continuar
                    return mail
                else:
                    print(f"[!] Autenticacion Fallida: {line}")
                    break
            elif line.startswith("+ "): # Error codificado de MS
                print(f"[!] Error XOAUTH2: {base64.b64decode(line[2:]).decode()}")
                mail.send(b"\r\n") # Cancelar auth
    else:
        print(f"[!] Error MSAL: {result.get('error_description')}")
    return None

def deducir_metadatos(nombre_archivo, payload_bytes):
    texto = nombre_archivo.upper() + " "
    if nombre_archivo.lower().endswith('.pdf'):
        try:
            lector = PyPDF2.PdfReader(BytesIO(payload_bytes))
            for pagina in lector.pages[:2]: # Solo primeras 2 paginas para velocidad
                texto += (pagina.extract_text() or "") + " "
        except: pass
    
    # Lógica de detección Sentinel
    metadatos = {"fecha": "2026-08-22", "tipo": "Vuelo", "proveedor": "Agencia", "pnr": "N/A"}
    match_fecha = re.search(r'([0-3][0-9])[-/](0[1-9]|1[0-2])[-/](2026|26)', texto)
    if match_fecha: metadatos["fecha"] = f"2026-{match_fecha.group(2)}-{match_fecha.group(1)}"
    
    for prov in ["Booking", "Traveloka", "Qatar", "AirAsia", "Iberia", "Gotogate"]:
        if prov.upper() in texto: metadatos["proveedor"] = prov; break
        
    match_pnr = re.search(r'\b[A-Z0-9]{6}\b', texto)
    metadatos["pnr"] = match_pnr.group(0) if match_pnr and not match_pnr.group(0).isnumeric() else hashlib.md5(payload_bytes).hexdigest()[:6].upper()
    if "HOTEL" in texto or "BOOKING" in texto or "ALOJAMIENTO" in texto: metadatos["tipo"] = "Alojamiento"
    
    return metadatos

def procesar_mensaje(msg, buzon):
    asunto = str(decode_header(msg.get("Subject", ""))[0][0])
    if isinstance(asunto, bytes): asunto = asunto.decode(errors='ignore')
    remitente = msg.get("From")
    
    print(f"   [SEARCH] Analizando: {asunto[:50]}...")
    
    # 1. Guardar Hilo de Texto
    cuerpo = ""
    for part in msg.walk():
        if part.get_content_type() in ["text/plain", "text/html"]:
            cuerpo = part.get_payload(decode=True).decode(errors='ignore')
            break
            
    email_data = {
        "id": msg.get("Message-ID"), "ref": msg.get("In-Reply-To"), "folder": buzon,
        "from": remitente, "to": msg.get("To"), "subject": asunto, "date": msg.get("Date"), "body": cuerpo
    }
    
    # 2. Extraer PDFs
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart': continue
        if part.get('Content-Disposition') is None: continue
        filename = part.get_filename()
        if filename and filename.lower().endswith('.pdf'):
            payload = part.get_payload(decode=True)
            meta = deducir_metadatos(filename, payload)
            # Formato esperado por el Tejedor: [DD-MM-AA]_Tipo_Ruta_Proveedor_PNR.pdf
            fecha_compacta = f"{meta['fecha'][8:10]}-{meta['fecha'][5:7]}-{meta['fecha'][2:4]}"
            ext = os.path.splitext(filename)[1]
            nuevo_nombre = f"[{fecha_compacta}]_{meta['tipo']}_Real_{meta['proveedor']}_{meta['pnr']}{ext}"
            carpeta = "Hoteles" if meta['tipo'] == "Alojamiento" else "Vuelos"
            with open(RESERVA_DIR / carpeta / nuevo_nombre, "wb") as f: f.write(payload)
            print(f"      [FILE] PDF Real Guardado: {nuevo_nombre}")
            
    return email_data

def ejecutar_mision():
    mail = conectar_hotmail()
    if not mail: print("[!] Error de Conexion Azure."); return
    
    todos_los_emails = []
    for buzon in CARPETAS_MS:
        print(f"[*] Escaneando {buzon}...")
        res, data = mail.select(buzon)
        if res != "OK":
            print(f"   [!] No se pudo seleccionar {buzon}. Reintentando con Inbox...")
            res, data = mail.select("Inbox") # Backup por si acaso
            if res != "OK": continue
            
        status, mensajes = mail.search(None, 'ALL')
        if status != "OK": continue
        
        ids = mensajes[0].split()
        for num in ids[-50:]: # Analizamos los últimos 50 de cada carpeta
            _, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            
            asunto = str(msg.get("Subject", "")).upper()
            remitente = str(msg.get("From", "")).upper()
            
            if any(kw.upper() in asunto for kw in BUSQUEDA_KEYWORDS) or any(kw.upper() in remitente for kw in BUSQUEDA_KEYWORDS):
                data_email = procesar_mensaje(msg, buzon)
                todos_los_emails.append(data_email)
                
    # Agrupar y guardar hilos
    hilos = {}
    indice_hilos = []
    for em in todos_los_emails:
        key = em["ref"] if em["ref"] else em["id"]
        if key not in hilos: hilos[key] = []
        hilos[key].append(em)
        
    for key, posts in hilos.items():
        safe_subject = re.sub(r'[^a-zA-Z0-9]', '_', posts[0]["subject"][:30])
        filename = f"hilo_{safe_subject}.json"
        with open(CONVERSACIONES_DIR / filename, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=4, ensure_ascii=False)
        indice_hilos.append({"archivo": filename, "titulo": posts[0]["subject"], "mensajes": len(posts)})
            
    # Guardar índice para la UI
    with open(CONVERSACIONES_DIR / "index_hilos.json", "w", encoding="utf-8") as f:
        json.dump(indice_hilos, f, indent=4, ensure_ascii=False)
            
    print(f"\n[DONE] MISION COMPLETADA. Hilos: {len(hilos)}")
    mail.logout()

if __name__ == "__main__":
    ejecutar_mision()
