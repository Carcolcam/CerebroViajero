import json
import os
import sys

def archivar_alertas(alert_ids):
    path = 'alertas_sentinel.json'
    if not os.path.exists(path):
        print(f"❌ Error: No se encuentra {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    for alert in data.get('alerts', []):
        if alert['id'] in alert_ids:
            alert['archived'] = True
            count += 1
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Sincronización completada: {count} alertas archivadas en el servidor.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python archivar_alerta.py id1 id2 ...")
    else:
        ids = sys.argv[1:]
        archivar_alertas(ids)
