import os
import json
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
import msal

# --- CONFIGURACIÓN ---
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

CLIENT_ID = os.getenv("HOTMAIL_CLIENT_ID")
CLIENT_SECRET = os.getenv("HOTMAIL_CLIENT_SECRET")
EMAIL_ACCOUNT = os.getenv("HOTMAIL_EMAIL")

AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Mail.Read"]
TOKEN_CACHE_PATH = BASE_DIR / "token_cache.bin"

# Diccionarios de Filtrado (Fase 1 y Fase 3)
DOMINIOS_PERMITIDOS = ["@booking.com", "@ryanair.com", "@iberia.com", "@agoda.com", "@traveloka.com", "@airbnb.com"]
ASUNTOS_PROHIBIDOS = ["oferta", "newsletter", "promoción", "descuento", "gana", "descubre", "recomendación"]

def cargar_cache():
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE_PATH.exists():
        cache.deserialize(open(TOKEN_CACHE_PATH, "r").read())
    return cache

def guardar_cache(cache):
    if cache.has_state_changed:
        with open(TOKEN_CACHE_PATH, "w") as f:
            f.write(cache.serialize())

def obtener_token_auth():
    cache = cargar_cache()
    # Usamos ConfidentialClient porque tenemos un CLIENT_SECRET (ideal para GitHub)
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, client_credential=CLIENT_SECRET,
        authority=AUTHORITY, token_cache=cache
    )

    result = None
    accounts = app.get_accounts()
    
    # Redundancia: Si no hay cuentas en el cache pero tenemos un Refresh Token en ENV
    env_rt = os.getenv("HOTMAIL_REFRESH_TOKEN")
    if not accounts and env_rt:
        print("[*] Usando Refresh Token de respaldo (GitHub Secrets)...")
        result = app.acquire_token_by_refresh_token(env_rt, scopes=SCOPES)

    if not result and accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        # En GitHub Actions no podemos hacer login interactivo
        if os.getenv("GITHUB_ACTIONS"):
            raise Exception("Token caducado en GitHub Actions. Por favor, ejecuta el script localmente para renovar el token_cache.bin y haz commit de los cambios.")

        # Si no hay token, generamos una URL de login manual
        # Nota: Usamos localhost como redirect_uri para capturar el código
        redirect_uri = "http://localhost:8080"
        auth_url = app.get_authorization_request_url(SCOPES, redirect_uri=redirect_uri)
        
        print(f"\n=======================================================")
        print(f"CONFIGURACION PARA GITHUB ACTIONS:")
        print(f"Abre esta URL y logueate: {auth_url}")
        print(f"=======================================================\n")
        
        print("Pega aquí la URL COMPLETA a la que te redirija el navegador (la que empieza por localhost):")
        # Como no puedo abrir un servidor web aquí fácilmente, le pedimos la URL
        response_url = input("> ")
        
        # Extraer el código de la URL
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(response_url)
        code = urlparse.parse_qs(parsed.query).get('code')
        
        if not code:
            raise Exception("No se encontró el código en la URL pegada.")
            
        result = app.acquire_token_by_authorization_code(code[0], scopes=SCOPES, redirect_uri=redirect_uri)
        
    if "access_token" in result:
        guardar_cache(cache)
        return result["access_token"]
    else:
        raise Exception(f"Fallo al obtener el token: {result.get('error')}")

def es_correo_valido(remitente, asunto):
    """Embudo de Filtrado Rápido"""
    asunto_lower = asunto.lower()
    
    # Filtro Anti-Ruido
    for prohibido in ASUNTOS_PROHIBIDOS:
        if prohibido in asunto_lower:
            return False
            
    # White-listing de Dominios
    remitente_lower = remitente.lower()
    for dominio in DOMINIOS_PERMITIDOS:
        if dominio in remitente_lower:
            return True
            
    # Si no está en el whitelist de dominios logísticos, descartamos
    return False

def cazar_hilos():
    print("Iniciando Motor de Ingesta (El Cazador de Hilos)...")
    
    try:
        token = obtener_token_auth()
    except Exception as e:
        print(f"[ERROR OAUTH] {e}")
        return
        
    print("[OK] Conexión MS Graph API establecida.")
    
    # Consultar la bandeja de entrada, traer los 50 más recientes
    url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Seleccionamos solo los campos necesarios para ser ultra-rápidos
    params = {
        "$select": "subject,from,receivedDateTime,conversationId,body",
        "$top": 50,
        "$orderby": "receivedDateTime desc"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"[ERROR] Graph API: {response.text}")
        return
        
    mensajes = response.json().get("value", [])
    print(f"[*] Analizando los últimos {len(mensajes)} correos...")
    
    correos_utiles = []
    
    for msg in mensajes:
        asunto = msg.get("subject", "")
        remitente = msg.get("from", {}).get("emailAddress", {}).get("address", "")
        fecha = msg.get("receivedDateTime", "")
        cuerpo_html = msg.get("body", {}).get("content", "")
        hilo_id = msg.get("conversationId", "")
        
        # Limpieza básica de HTML para evitar falsos positivos (como colores CSS #333333)
        cuerpo = re.sub('<[^<]+?>', '', cuerpo_html)
        
        if es_correo_valido(remitente, asunto):
            # Extracción NLP Refinada (Regex) sobre texto limpio
            # 1. Buscar PNR (6 caracteres alfanuméricos) - Evitamos que coincidan con códigos de color
            pnr = re.search(r'\b(?![0-9A-Fa-f]{6}\b)[A-Z0-9]{6}\b', asunto + " " + cuerpo)
            if not pnr: # Fallback si el primero falla por ser muy estricto
                pnr = re.search(r'\b([A-Z0-9]{6})\b', asunto + " " + cuerpo)
            
            # 2. Buscar números de vuelo (Ej: EK123, VY4567)
            vuelo = re.search(r'\b([A-Z]{2,3}\s?\d{2,4})\b', asunto + " " + cuerpo)
            
            # 3. Buscar horas (Ej: 14:30)
            hora = re.search(r'\b(\d{1,2}:\d{2}(?:\s?[APM]{2})?)\b', cuerpo)

            correos_utiles.append({
                "asunto": asunto,
                "remitente": remitente,
                "fecha": fecha,
                "conversationId": hilo_id,
                "pnr_detectado": pnr.group(0) if pnr else None,
                "vuelo_detectado": vuelo.group(0).replace(" ", "") if vuelo else None,
                "hora_detectada": hora.group(0) if hora else None,
                "preview": cuerpo[:300].strip() # Snippet limpio para auditoría
            })
            
    # Guardar sucesos detectados para el Tejedor
    if correos_utiles:
        with open(BASE_DIR / "sucesos_email.json", "w", encoding="utf-8") as f:
            json.dump(correos_utiles, f, indent=4, ensure_ascii=False)
            
    print(f"\n[+] Embudo completado. Se han cazado {len(correos_utiles)} correos logísticos vitales.")
    print(f"[*] Datos exportados a sucesos_email.json para el Tejedor.")
    
    # Mostrar resultados del triaje
    for i, c in enumerate(correos_utiles, 1):
        try:
            print(f"  {i}. [{c['remitente']}] {c['asunto']} (Hilo: {c['conversationId'][:8]}...)")
        except:
            clean_asunto = c['asunto'].encode('ascii', 'ignore').decode('ascii')
            print(f"  {i}. [{c['remitente']}] {clean_asunto} (Hilo: {c['conversationId'][:8]}...)")
        
    print("\nSiguiente paso: Ejecutar tejedor_itinerario.py para asimilar estos emails.")

if __name__ == "__main__":
    cazar_hilos()
