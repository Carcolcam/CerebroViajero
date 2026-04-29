import json
import datetime

# --- CONFIGURACIÓN DE LA API (AviationStack) ---
# En el mundo real, aquí iría tu clave secreta de la API.
API_KEY = "tu_clave_de_aviationstack_aqui"
BASE_URL = "http://api.aviationstack.com/v1/flights"

def consultar_vuelo(flight_iata):
    """
    Simula una consulta a la API de AviationStack para un número de vuelo específico.
    """
    print(f"[API] Iniciando rastreo satelital para el vuelo: {flight_iata}")
    
    # Simulación de respuesta HTTP de la API
    # Imagina que esto es lo que nos devuelve la API tras hacer requests.get()
    mock_response = {
        "data": [
            {
                "flight_date": "2026-03-22",
                "flight_status": "active",
                "departure": {
                    "airport": "Adolfo Suarez Barajas",
                    "timezone": "Europe/Madrid",
                    "iata": "MAD",
                    "scheduled": "2026-03-22T15:00:00+00:00",
                    "estimated": "2026-03-22T15:00:00+00:00", # Salida en hora
                    "actual": None
                },
                "arrival": {
                    "airport": "Doha International",
                    "timezone": "Asia/Qatar",
                    "iata": "DOH",
                    "scheduled": "2026-03-22T23:30:00+00:00",
                    "estimated": "2026-03-23T01:15:00+00:00", # ALERTA: Retraso estimado de casi 2h
                    "actual": None
                },
                "airline": {
                    "name": "Qatar Airways",
                    "iata": "QR"
                },
                "flight": {
                    "number": "832",
                    "iata": "QR832"
                }
            }
        ]
    }
    
    return mock_response

def analizar_retraso_silencioso(vuelo_data):
    """
    Extrae las horas y determina si hay un retraso sin notificar.
    """
    vuelo_info = vuelo_data['data'][0]
    
    salida_prevista = vuelo_info['departure']['scheduled']
    salida_estimada = vuelo_info['departure']['estimated']
    
    llegada_prevista = vuelo_info['arrival']['scheduled']
    llegada_estimada = vuelo_info['arrival']['estimated']
    
    # Formateo rápido para la consola
    print("\n--- INFORME DE RASTREO ---")
    print(f"[Aerolinea]: {vuelo_info['airline']['name']} ({vuelo_info['flight']['iata']})")
    print(f"[Ruta]: {vuelo_info['departure']['iata']} -> {vuelo_info['arrival']['iata']}")
    print(f"[Prevista]: Llegada original en billete: {llegada_prevista}")
    print(f"[ESTIMADA]: Llegada real segun Radar API: {llegada_estimada}")
    
    # Detección matemática
    if llegada_prevista != llegada_estimada:
        print("\n[CRITICO] RETRASO SILENCIOSO DETECTADO.")
        print("El radar muestra una discrepancia respecto al horario oficial.")
        print("El Tejedor actualizara el itinerario_maestro.json con la nueva hora y recalculara la friccion de llegada.")
    else:
        print("\n[OK] Vuelo en hora. No se requiere recalculo.")

if __name__ == "__main__":
    print("Iniciando Laboratorio de API (AviationStack)...")
    # Simulamos que leemos 'QR832' de uno de los nombres de tus PDFs
    respuesta = consultar_vuelo("QR832")
    analizar_retraso_silencioso(respuesta)
