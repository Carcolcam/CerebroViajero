import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
load_dotenv(Path(__file__).parent / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8000")
BASE_DIR = Path(__file__).parent
JSON_PATH = BASE_DIR / "itinerario_maestro.json"
ESTADO_PATH = BASE_DIR / "estado_vigilante.json"

def enviar_mensaje_telegram(mensaje):
    """Envía un mensaje formateado a través del bot de Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[ERROR] Credenciales de Telegram no configuradas en .env")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("[OK] Notificación Push enviada al móvil.")
        return True
    except Exception as e:
        print(f"[ERROR] Fallo al enviar Telegram: {e}")
        return False

def cargar_alertas_enviadas():
    if ESTADO_PATH.exists():
        with open(ESTADO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_alertas_enviadas(estado):
    with open(ESTADO_PATH, "w", encoding="utf-8") as f:
        json.dump(estado, f)

def ejecutar_vigilancia():
    print("Iniciando Vigilante Sentinel (Bot de Telegram)...")
    
    if not JSON_PATH.exists():
        print("[!] No se encuentra itinerario_maestro.json.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    itinerario = data.get("itinerary", [])
    alertas_enviadas = cargar_alertas_enviadas()
    nuevas_alertas = 0
    
    for evento in itinerario:
        pnr = evento.get("id")
        status = evento.get("status", "CONFIRMED")
        alertas = evento.get("alerts", [])
        
        # 1. Alerta por Estado (Cancelaciones)
        if status == "CANCELLED":
            alerta_id = f"{pnr}_status_cancelled"
            if alerta_id not in alertas_enviadas:
                titulo = evento.get("title", "Evento Desconocido")
                mensaje_telegram = (
                    f"<b>🛑 CEREBRO VIAJERO | CANCELACIÓN DETECTADA</b>\n\n"
                    f"<b>Reserva/PNR:</b> <code>{pnr}</code>\n"
                    f"<b>Proveedor:</b> {evento.get('provider', 'N/A')}\n"
                    f"<b>Afectado:</b> {titulo}\n\n"
                    f"<b>ACCIÓN REQUERIDA:</b> El servicio ha sido marcado como cancelado. Inicia el protocolo de reembolso o reubicación.\n\n"
                    f"🔗 <a href='{DASHBOARD_URL}/centro_de_mando.html'>Abrir Command Center</a>"
                )
                exito = enviar_mensaje_telegram(mensaje_telegram)
                if exito:
                    alertas_enviadas[alerta_id] = True
                    nuevas_alertas += 1

        # 2. Alertas por Retrasos o Problemas (Lista de alerts)
        for idx, alerta in enumerate(alertas):
            # Crear un ID único para cada alerta basado en el PNR y su índice
            alerta_id = f"{pnr}_alerta_{idx}"
            
            if alerta_id not in alertas_enviadas:
                # Es una alerta nueva, vamos a enviarla
                nivel = alerta.get("level", "INFO")
                mensaje_raw = alerta.get("message", "Alerta detectada.")
                titulo = evento.get("title", "Evento Desconocido")
                
                # Formateo estético para Telegram
                icono = "🚨" if nivel == "CRITICAL" else "⚠️"
                
                mensaje_telegram = (
                    f"<b>{icono} CEREBRO VIAJERO | SENTINEL ALERT</b>\n\n"
                    f"<b>Reserva/PNR:</b> <code>{pnr}</code>\n"
                    f"<b>Afectado:</b> {titulo}\n\n"
                    f"<b>Detalle:</b>\n"
                    f"<i>{mensaje_raw}</i>\n\n"
                    f"🔗 <a href='{DASHBOARD_URL}/centro_de_mando.html'>Abrir Command Center</a>"
                )
                
                exito = enviar_mensaje_telegram(mensaje_telegram)
                if exito:
                    alertas_enviadas[alerta_id] = True
                    nuevas_alertas += 1

    if nuevas_alertas > 0:
        guardar_alertas_enviadas(alertas_enviadas)
        print(f"[*] Vigilancia completada. {nuevas_alertas} alertas nuevas reportadas.")
    else:
        print("[*] Vigilancia completada. Sin novedades (Sector Despejado).")

if __name__ == "__main__":
    # Test inicial para confirmar que funciona
    ejecutar_vigilancia()
