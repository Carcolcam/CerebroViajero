import json
import sys
import os
from centinela_drive import get_drive_service, archivar_por_pnr

if len(sys.argv) < 3:
    print("Uso: python procesar_baja.py <booking_id> <nombre_proveedor>")
    sys.exit(1)

booking_id = sys.argv[1]
proveedor = sys.argv[2].lower()

itinerario_path = 'itinerario_maestro.json'
alertas_path = 'alertas_sentinel.json'

print(f">>> Procesando baja para Reserva: {booking_id} ({proveedor})")

# 1. ACTUALIZAR ITINERARIO MAESTRO
try:
    with open(itinerario_path, 'r', encoding='utf-8') as f:
        itin_data = json.load(f)
        
    actualizado_itin = False
    pnr_a_archivar = None
    
    for item in itin_data.get('itinerary', []):
        if item.get('id') == booking_id or item.get('booking_id') == booking_id:
            item['status'] = "CANCELLED"
            item['refund_status'] = "PENDING"
            # Capturamos el PNR o referencia para Drive
            pnr_a_archivar = item.get('pnr') or item.get('booking_ref') or booking_id
            actualizado_itin = True
            
    if actualizado_itin:
        with open(itinerario_path, 'w', encoding='utf-8') as f:
            json.dump(itin_data, f, indent=2, ensure_ascii=False)
        print("✅ Itinerario Maestro actualizado: CANCELLED & PENDING REFUND")
        
        # --- INTEGRACIÓN FASE 4: DRIVE ---
        if pnr_a_archivar:
            try:
                service = get_drive_service()
                archivar_por_pnr(service, pnr_a_archivar)
            except Exception as drive_err:
                print(f"⚠️ Error al mover documentos en Drive: {drive_err}")
        # ---------------------------------
        
    else:
        print("⚠️ No se encontró el booking_id en el Itinerario Maestro.")
except Exception as e:
    print(f"Error procesando itinerario: {e}")


# 2. ARCHIVAR ALERTAS EN CASCADA
try:
    with open(alertas_path, 'r', encoding='utf-8') as f:
        alertas_data = json.load(f)
        
    archividas_count = 0
    for alerta in alertas_data.get('alerts', []):
        titulo_desc = (alerta.get('title', '') + " " + alerta.get('description', '')).lower()
        
        # Archivar si coincide el booking_id explícito o el nombre de la aerolínea/hotel
        if booking_id.lower() in titulo_desc or proveedor in titulo_desc:
            if not alerta.get('archived', False):
                alerta['archived'] = True
                archividas_count += 1
                
    if archividas_count > 0:
        with open(alertas_path, 'w', encoding='utf-8') as f:
            json.dump(alertas_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Limpieza de alertas: {archividas_count} notificaciones relacionadas archivadas en cascada.")
    else:
        print("ℹ️ No había alertas activas que archivar para este proveedor.")
        
except Exception as e:
    print(f"Error limpiando alertas: {e}")

print(">>> Baja procesada correctamente.")
