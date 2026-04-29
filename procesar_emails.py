import os
import base64
import json
import re
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuración de Scopes (Necesitamos lectura de Gmail)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def obtener_servicio_gmail():
    creds = None
    if os.path.exists('token_gmail.json'):
        creds = Credentials.from_authorized_user_file('token_gmail.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Reusamos credentials.json del proyecto
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_gmail.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def extraer_datos_vuelo(texto):
    """Lógica de extracción básica mediante Regex (IA Ligera)"""
    # Buscar PNR de 6 caracteres
    pnr_match = re.search(r'\b([A-Z0-9]{2,5}[0-9][A-Z0-9]{0,3}|[0-9][A-Z0-9]{5})\b', texto.upper())
    pnr = pnr_match.group(1) if pnr_match else None
    
    # Buscar Ciudades (Simplificado para el test)
    # En un sistema real, usaríamos un modelo de lenguaje o una lista de aeropuertos
    ciudades = re.findall(r'\b(MADRID|BARCELONA|NEW YORK|NYC|JFK|LONDON|PARIS|TOKYO|LOS ANGELES|LAX)\b', texto.upper())
    
    # Buscar Fechas (YYYY-MM-DD o DD/MM/YYYY)
    fechas = re.findall(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', texto)
    
    return {
        "pnr": pnr,
        "ciudades": list(set(ciudades)),
        "fechas": fechas
    }

def procesar_recientes():
    print("Sentinel: Escaneando hilos de correo en busca de nuevas reservas...")
    service = obtener_servicio_gmail()
    
    # Buscamos correos de las últimas 24 horas con palabras clave
    query = "subject:(Confirmacion OR Reserva OR Booking OR Itinerary OR Vuelo OR Hotel)"
    results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
    messages = results.get('messages', [])

    nuevos_sucesos = []
    
    if not messages:
        print("   [-] No se han encontrado nuevos hilos de reserva.")
        return

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = msg_data['payload']['headers']
        asunto = next(h['value'] for h in headers if h['name'] == 'Subject')
        preview = msg_data.get('snippet', '')
        
        print(f"   [+] Analizando: {asunto[:50]}...")
        
        datos = extraer_datos_vuelo(asunto + " " + preview)
        
        if datos["pnr"]:
            # Clasificar tipo
            tipo = "hotel" if any(kw in asunto.upper() for kw in ["HOTEL", "ALOJAMIENTO", "ESTANCIA"]) else "flight"
            
            suceso = {
                "id": f"EMAIL_{msg['id'][:8]}",
                "asunto": asunto,
                "preview": preview,
                "type": tipo,
                "date": datos["fechas"][0] if datos["fechas"] else datetime.now().strftime("%Y-%m-%d"),
                "pnr": datos["pnr"],
                "source": "GMAIL_AUTO_SCAN"
            }
            
            # Si es vuelo, intentamos sacar ciudades
            if tipo == "flight" and len(datos["ciudades"]) >= 2:
                suceso["from_city"] = datos["ciudades"][0].title()
                suceso["to_city"] = datos["ciudades"][1].title()
            
            nuevos_sucesos.append(suceso)
            print(f"      [!] PNR {datos['pnr']} detectado y extraido.")

    if nuevos_sucesos:
        # Actualizar sucesos_email.json
        path = "sucesos_email.json"
        existentes = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existentes = json.load(f)
        
        # Evitar duplicados por PNR
        pnr_existentes = [s.get("pnr") for s in existentes]
        for n in nuevos_sucesos:
            if n["pnr"] not in pnr_existentes:
                existentes.append(n)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existentes, f, indent=4, ensure_ascii=False)
            
        print(f"\n[OK] Se han añadido {len(nuevos_sucesos)} nuevos eventos al motor de Sentinel.")
        
        # Disparar el Tejedor automáticamente
        import subprocess
        print("[+] Sincronizando Itinerario Maestro...")
        subprocess.run(["python", "tejedor_itinerario.py"])

if __name__ == "__main__":
    try:
        procesar_recientes()
    except Exception as e:
        print(f"   [!] Error en el Cazador de Hilos: {e}")
