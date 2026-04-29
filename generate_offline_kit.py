import json
import os

def generate_kit():
    # Cargar datos
    with open('itinerario_maestro.json', 'r', encoding='utf-8') as f:
        itinerary_data = json.load(f)
    
    with open('snorkel_planner.json', 'r', encoding='utf-8') as f:
        snorkel_data = json.load(f)

    # Template HTML (Escaping curly braces for .format())
    html_template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CerebroViajero - KIT OFFLINE</title>
    <style>
        :root {{
            --bg: #0b0e14;
            --card-bg: #161b22;
            --text: #c9d1d9;
            --accent: #ff4757;
            --vuelo: #58a6ff;
            --hotel: #3fb950;
            --emergency: #f85149;
        }}
        body {{ font-family: -apple-system, sans-serif; background: var(--bg); color: var(--text); padding: 15px; margin: 0; line-height: 1.4; }}
        h1 {{ color: #fff; font-size: 22px; margin-bottom: 5px; }}
        h2 {{ color: var(--accent); font-size: 16px; margin-top: 25px; border-bottom: 1px solid #30363d; padding-bottom: 5px; }}
        .card {{ background: var(--card-bg); border-radius: 8px; padding: 12px; margin-bottom: 12px; border: 1px solid #30363d; }}
        .vuelo {{ border-left: 4px solid var(--vuelo); }}
        .hotel {{ border-left: 4px solid var(--hotel); }}
        .emergency-card {{ border-left: 4px solid var(--emergency); background: #2a1215; }}
        .title {{ font-weight: bold; display: block; color: #fff; font-size: 15px; }}
        .meta {{ font-size: 12px; color: #8b949e; margin-top: 4px; }}
        .tag {{ font-size: 10px; padding: 2px 6px; border-radius: 10px; background: #30363d; margin-right: 5px; }}
        .pnr {{ font-family: monospace; color: var(--vuelo); font-weight: bold; }}
        .print-btn {{ background: var(--accent); color: #fff; border: none; padding: 12px; width: 100%; border-radius: 8px; font-weight: bold; margin-bottom: 20px; }}
        @media print {{ .print-btn {{ display: none; }} }}
    </style>
</head>
<body>
    <h1>🛰️ KIT OFFLINE</h1>
    <p class="meta">Generado el: {date_gen}</p>
    <button class="print-btn" onclick="window.print()">📥 GUARDAR PDF / IMPRIMIR</button>

    <h2>🆘 CONTACTOS DE EMERGENCIA</h2>
    <div class="card emergency-card">
        <span class="title">Seguro IATI (24h)</span>
        <span class="meta">📞 +34 93 485 77 35 | Póliza: 17263544</span>
    </div>

    <h2>✈️ CRONOGRAMA DE VIAJE</h2>
    {itinerary_html}

    <h2>🤿 SNORKEL INTEL (PUNTOS CLAVE)</h2>
    {snorkel_html}

    <script>
        console.log("Kit Offline Cargado Correctamente");
    </script>
</body>
</html>
"""

    # Procesar Itinerario
    itinerary_html = ""
    current_month = ""
    month_names = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
    
    for item in itinerary_data['itinerary']:
        m = int(item['date'].split('-')[1])
        month = month_names[m-1]
        if month != current_month:
            current_month = month
            itinerary_html += f"<h3>{month}</h3>"
        
        c_type = "vuelo" if item['type'] == "Vuelo" else "hotel"
        title = item.get('desc', item.get('hotel', item.get('flight_num')))
        time_info = f"{item.get('dep_time', '')}" if c_type == "vuelo" else "Check-in"
        
        # Uso de booking_id unificado
        bid = item.get('booking_id') or item.get('pnr') or item.get('ref') or "N/A"
        extra = f"ID: <span class='pnr'>{bid}</span>"
        
        itinerary_html += f"""
        <div class="card {c_type}">
            <span class="meta">{item['date']}</span>
            <span class="title">{title}</span>
            <span class="meta">🕒 {time_info} • {extra}</span>
        </div>
        """

    # Emergencias Detalladas
    emergency_contacts = """
    <div class="card emergency-card">
        <span class="title">🏥 HOSPITALES (Siloam / Regional)</span>
        <div class="meta"><b>Manado:</b> Siloam Hospitals Manado (+62 431 7290900)</div>
        <div class="meta"><b>Kendari:</b> Siloam Hospitals Kendari (+62 401 3089000)</div>
        <div class="meta"><b>Phuket:</b> Bangkok Hospital Phuket (+66 76 254 425)</div>
        <div class="meta"><b>Kuala Lumpur:</b> Prince Court (+60 3-2160 0000)</div>
    </div>
    <div class="card emergency-card">
        <span class="title">🛡️ SEGURO IATI (24h)</span>
        <span class="meta">📞 +34 93 485 77 35 | Póliza: 17263544</span>
    </div>
    """

    # Procesar Snorkel
    snorkel_html = ""
    for spot in snorkel_data['spots']:
        snorkel_html += f"""
        <div class="card">
            <span class="title">📍 {spot['name']}</span>
            <div class="meta">Visibilidad: {spot['visibility']} | Peligro: {spot['danger_level']}</div>
            <div class="meta" style="margin-top:5px; font-style: italic;">"{spot['tide_tip']}"</div>
        </div>
        """

    # Guardar
    from datetime import datetime
    final_html = html_template.format(
        date_gen=datetime.now().strftime("%d/%m/%Y %H:%M"),
        itinerary_html=itinerary_html,
        snorkel_html=snorkel_html
    ).replace('<h2>🆘 CONTACTOS DE EMERGENCIA</h2>', '<h2>🆘 CONTACTOS DE EMERGENCIA</h2>' + emergency_contacts)

    with open('survival_kit.html', 'w', encoding='utf-8') as f:
        f.write(final_html)
    print("Survival Kit generado con éxito.")

if __name__ == "__main__":
    generate_kit()
