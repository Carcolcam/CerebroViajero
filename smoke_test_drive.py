import os
import json
from centinela_drive import get_drive_service, subir_archivo, archivar_por_pnr

def run_smoke_test():
    print("🔥 Iniciando Smoke Test de la Fase 4 (Drive Automation)...")
    service = get_drive_service()
    
    # Cargar configuración de carpetas
    with open("config_drive.json", "r") as f:
        config = json.load(f)
    
    # 1. Crear documento de prueba local
    pnr_test = "666X"
    filename = f"Billete_Iberia_PNR_{pnr_test}.txt"
    with open(filename, "w") as f:
        f.write(f"Contenido de prueba para el PNR {pnr_test}.\nEste archivo deberia moverse a la carpeta de reembolsos.")
    
    try:
        # 2. Subir a PLAN_ACTIVO
        print("\n[Paso 1] Subiendo billete a PLAN_ACTIVO...")
        folder_activo = config["operaciones"]["sub"]["plan_activo"]
        subir_archivo(service, filename, folder_activo)
        
        # 3. Mover a REEMBOLSOS
        print("\n[Paso 2] ¡Alerta de Cancelacion! Ejecutando movimiento táctico...")
        archivar_por_pnr(service, pnr_test)
        
        print("\n✅ TEST COMPLETADO: El archivo ha sido movido en la nube.")
        
    finally:
        # Limpieza local
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    run_smoke_test()
