import json
import os
import sys
from datetime import datetime

def integrar_hotel(alert_id):
    alerts_path = 'alertas_sentinel.json'
    itin_path = 'itinerario_maestro.json'

    if not os.path.exists(alerts_path) or not os.path.exists(itin_path):
        print("❌ Error: Archivos no encontrados.")
        return

    # 1. Cargar Alertas y buscar la seleccionada
    with open(alerts_path, 'r', encoding='utf-8') as f:
        alerts_data = json.load(f)
    
    alert = next((a for a in alerts_data.get('alerts', []) if a['id'] == alert_id), None)
    if not alert:
        print(f"❌ Error: Alerta {alert_id} no encontrada.")
        return

    # 2. Cargar Itinerario
    with open(itin_path, 'r', encoding='utf-8') as f:
        itin_data = json.load(f)

    # 3. Lógica de Extracción de Datos (Simulada para The Pulisan)
    # En una versión más avanzada, aquí llamaríamos a la API de Gmail para extraer fechas exactas
    # Por ahora, usamos el conocimiento del hueco logístico si es The Pulisan
    hotel_name = "The Pulisan"
    if "Pulisan" in alert['title'] or "Pulisan" in alert['description']:
        # Fechas detectadas para el hueco en Manado (Basado en el análisis de las cancelaciones)
        new_hotel = {
            "id": f"H_AUTO_{datetime.now().strftime('%M%S')}",
            "type": "Alojamiento",
            "date": "2026-09-08",
            "checkout": "2026-09-11", # Matiz: solo hasta el 11 para probar el Gap
            "hotel": "The Pulisan (Eco Resort)",
            "location": "Pulisan, Manado",
            "desc": "Integrado automáticamente vía Sentinel",
            "booking_id": "PENDING_CONF",
            "provider": "The Pulisan",
            "status": "CONFIRMED",
            "refund_status": "NONE"
        }
        
        # Insertar y ordenar por fecha
        itin_data['itinerary'].append(new_hotel)
        itin_data['itinerary'].sort(key=lambda x: x.get('date', '9999-99-99'))
        itin_data['ultima_sincronizacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 4. Guardar Itinerario
        with open(itin_path, 'w', encoding='utf-8') as f:
            json.dump(itin_data, f, indent=2, ensure_ascii=False)

        # 5. Limpieza Inteligente: Archivar todas las alertas relacionadas con este hotel
        hotel_keyword = "Pulisan" # Podríamos extraerlo dinámicamente
        count_cleaned = 0
        for a in alerts_data.get('alerts', []):
            if hotel_keyword.lower() in a['title'].lower() or hotel_keyword.lower() in a['description'].lower():
                if not a.get('archived'):
                    a['archived'] = True
                    count_cleaned += 1
        
        with open(alerts_path, 'w', encoding='utf-8') as f:
            json.dump(alerts_data, f, indent=2, ensure_ascii=False)

        print(f"✅ ÉXITO: {hotel_name} integrado. Se han archivado {count_cleaned} alertas relacionadas.")
    else:
        print("❌ Error: Este tipo de alerta requiere extracción manual por ahora.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python integrar_hotel.py <alert_id>")
    else:
        integrar_hotel(sys.argv[1])
