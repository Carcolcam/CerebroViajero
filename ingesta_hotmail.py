import imaplib
import email
from email.header import decode_header
import re
import os
import hashlib
from pathlib import Path
import PyPDF2

# FASE 1: White-listing de Dominios Logísticos
DOMINIOS_AUTORIZADOS = [
    "@booking.com", "@traveloka.com", "@agoda.com", 
    "@qatarairways.com", "@airasia.com", "@flyjava.com", "@lionair.co.id"
]

# FASE 3: Filtro Anti-Ruido (Subjects)
PALABRAS_PROHIBIDAS = ["oferta", "newsletter", "promoción", "deals", "descubre", "10%", "anuncio"]

# Directorios de destino
BASE_DIR = Path(r"C:\Users\Pc1\.gemini\antigravity\scratch\CerebroViajero\Reserva")
(BASE_DIR / "Vuelos").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "Hoteles").mkdir(parents=True, exist_ok=True)

def deducir_metadatos_desde_bytes(nombre_archivo, payload_bytes):
    """Analiza los bytes del adjunto (PDF o TXT) en memoria para sacar Huellas."""
    texto = nombre_archivo.upper() + " "
    
    # Intentar leer PDF en memoria
    if nombre_archivo.lower().endswith('.pdf'):
        from io import BytesIO
        try:
            lector = PyPDF2.PdfReader(BytesIO(payload_bytes))
            for pagina in lector.pages:
                ext = pagina.extract_text()
                if ext: texto += ext + " "
        except:
            pass
    elif nombre_archivo.lower().endswith('.txt'):
        try:
            texto += payload_bytes.decode('utf-8')
        except:
            pass

    # Aplicar Lógica Triangulada
    metadatos = {"fecha": "00-00-00", "tipo": "Vuelo", "ruta": "Desconocida", "proveedor": "Agencia"}
    
    # Detectar Fecha DD/MM/YYYY o YYYY-MM-DD
    match_fecha = re.search(r'([0-3][0-9])[-/](0[1-9]|1[0-2])[-/](2026|26)', texto)
    if match_fecha:
        metadatos["fecha"] = f"{match_fecha.group(1)}-{match_fecha.group(2)}-26"

    # Detectar Proveedor
    for prov in ["Booking", "Traveloka", "Qatar", "AirAsia"]:
        if prov.upper() in texto:
            metadatos["proveedor"] = prov
            break

    # PNR
    match_pnr = re.search(r'\b[A-Z0-9]{6}\b', texto)
    if match_pnr and not match_pnr.group(0).isnumeric():
        metadatos["pnr"] = match_pnr.group(0)
    else:
        metadatos["pnr"] = f"H-{hashlib.md5(payload_bytes).hexdigest()[:6].upper()}"

    # Tipo
    if "HOTEL" in texto or "BOOKING" in texto:
        metadatos["tipo"] = "Alojamiento"

    return metadatos

def procesar_adjuntos(mensaje, remitente):
    """Busca y extrae PDFs o TXTs del correo validado."""
    adjuntos_guardados = 0
    for part in mensaje.walk():
        if part.get_content_maintype() == 'multipart': continue
        if part.get('Content-Disposition') is None: continue
        
        nombre_archivo = part.get_filename()
        if not nombre_archivo: continue
        
        # Filtrar solo documentos logísticos
        if not nombre_archivo.lower().endswith(('.pdf', '.txt')): continue
        
        # Descargar payload
        payload_bytes = part.get_payload(decode=True)
        if not payload_bytes: continue
        
        # Mágia: Analizar y Renombrar antes de guardar
        datos = deducir_metadatos_desde_bytes(nombre_archivo, payload_bytes)
        
        # Extensión
        ext = os.path.splitext(nombre_archivo)[1].lower()
        nuevo_nombre = f"[{datos['fecha']}]_{datos['tipo']}_{datos['ruta']}_{datos['proveedor']}_{datos['pnr']}{ext}"
        
        # Guardar en su carpeta
        carpeta = "Hoteles" if datos['tipo'] == "Alojamiento" else "Vuelos"
        ruta_final = BASE_DIR / carpeta / nuevo_nombre
        
        with open(ruta_final, "wb") as f:
            f.write(payload_bytes)
            
        print(f"   💾 Adjunto guardado: {nuevo_nombre}")
        adjuntos_guardados += 1
        
    return adjuntos_guardados

def conectar_hotmail(usuario, contraseña):
    """Establece conexión segura IMAP con Hotmail/Outlook."""
    print("📡 Conectando a Hotmail...")
    try:
        mail = imaplib.IMAP4_SSL("imap-mail.outlook.com")
        mail.login(usuario, contraseña)
        mail.select("inbox")
        print("✅ Conexión establecida.")
        return mail
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def es_remitente_autorizado(remitente):
    """Comprueba si el correo viene de una agencia u hotel autorizado."""
    remitente = remitente.lower()
    return any(dominio in remitente for dominio in DOMINIOS_AUTORIZADOS)

def es_marketing(asunto):
    """Comprueba si el asunto parece publicidad."""
    if not asunto: return False
    asunto = asunto.lower()
    return any(palabra in asunto for palabra in PALABRAS_PROHIBIDAS)

def cazar_hilos_nuevos(mail):
    """
    Escanea la bandeja de entrada aplicando el Embudo de 4 Fases.
    Retorna una lista de identificadores de correos validados.
    """
    print("\n🔍 Iniciando Escaneo de Sucesos (Embudo de 4 Fases)...")
    correos_validos = []
    
    # Buscar todos los correos
    status, mensajes = mail.search(None, "ALL")
    
    if status == "OK":
        lista_ids = mensajes[0].split()
        # Para evitar saturar, leemos solo los últimos 10 en este prototipo
        for num in lista_ids[-10:]:
            _, msg_data = mail.fetch(num, "(RFC822)")
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    mensaje = email.message_from_bytes(response_part[1])
                    
                    remitente = str(mensaje.get("From"))
                    asunto, encoding = decode_header(mensaje.get("Subject"))[0]
                    if isinstance(asunto, bytes):
                        # Evitar errores si el asunto es nulo o está mal codificado
                        try:
                            asunto = asunto.decode(encoding if encoding else "utf-8")
                        except:
                            asunto = str(asunto)
                            
                    msg_id = mensaje.get("Message-ID")
                    in_reply_to = mensaje.get("In-Reply-To")
                    
                    # --- EL EMBUDO ---
                    
                    # FASE 1: White-listing
                    if not es_remitente_autorizado(remitente):
                        # FASE 2: Detección de Hilos (Si no es Booking, ¿es respuesta a un hotel?)
                        # Aquí guardaríamos los Message-ID válidos en BD y comprobaríamos el In-Reply-To
                        if not in_reply_to: 
                            continue # Ignorado (Ruido)
                    
                    # FASE 3: Filtro Anti-Ruido
                    if es_marketing(asunto):
                        continue # Ignorado (Marketing)
                        
                    # FASE 4: Supera el Embudo - Triaje y Extracción de Adjuntos
                    print(f"🎯 SUCESO CAZADO!")
                    print(f"   Remitente: {remitente}")
                    print(f"   Asunto: {asunto}")
                    if in_reply_to:
                        print(f"   [!] Es una respuesta/hilo (In-Reply-To detectado)")
                        
                    # <-- AQUI SUCEDE LA MAGIA DE LA DESCARGA -->
                    adjuntos = procesar_adjuntos(mensaje, remitente)
                    if adjuntos == 0:
                        print("   [i] No contiene PDFs ni TXTs, se procesará solo el texto del correo.")
                    
                    print("-" * 50)
                    correos_validos.append(num)
                    
    return correos_validos

if __name__ == "__main__":
    print("🚧 Módulo de Ingesta IMAP Sentinel - Inicializado")
    # Para probarlo en real, sustituir por credenciales generadas de aplicación
    # mail = conectar_hotmail("tu_correo@hotmail.com", "TU_CONTRASEÑA_DE_APLICACION")
    # if mail:
    #     cazar_hilos_nuevos(mail)
    #     mail.logout()
