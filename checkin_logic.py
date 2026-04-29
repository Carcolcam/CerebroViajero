import json
import os
import requests
import urllib.parse
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════
#  CEREBROVIAJERO - Motor v5.3 (PILOTO AUTOMÁTICO)
#  Sincronizado con Tiempo Real y Cobertura Total
# ═══════════════════════════════════════════════════════════

CITY_NAMES = {
    "MAD": "Madrid 🇪🇸", "DOH": "Doha 🇶🇦", "HKT": "Phuket 🇹🇭", 
    "WNI": "Wakatobi 🇮🇩", "KDI": "Kendari 🇮🇩", "UPG": "Makassar 🇮🇩",
    "MDC": "Manado 🇮🇩", "CGK": "Yakarta 🇮🇩", "SIN": "Singapur 🇸🇬"
}

def get_maps_link(query):
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(query)

def send_telegram(text, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=15)
        return True
    except: return False

def get_current_status(itinerary, target_date_str):
    target_dt = datetime.strptime(target_date_str, "%Y-%m-%d")
    status = {"flights": [], "hotel": None}
    for item in itinerary:
        if not item.get("date"): continue
        if item.get("type") == "Vuelo" and item["date"] == target_date_str:
            status["flights"].append(item)
        if item.get("type") == "Alojamiento":
            ci = datetime.strptime(item["date"], "%Y-%m-%d")
            co = datetime.strptime(item["checkout"], "%Y-%m-%d")
            if ci <= target_dt < co: status["hotel"] = item
    return status

def run_alerts():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id: return

    with open("itinerario_maestro.json", "r", encoding="utf-8") as f:
        itinerary = json.load(f).get("itinerary", [])
    with open("travel_intel.json", "r", encoding="utf-8") as f:
        intel = json.load(f)

    # 🕒 TIEMPO REAL ACTIVADO
    today_dt = datetime.now() 
    today_str = today_dt.strftime("%Y-%m-%d")
    tomorrow_str = (today_dt + timedelta(days=1)).strftime("%Y-%m-%d")

    status = get_current_status(itinerary, today_str)
    
    city_key = None
    if status["hotel"]:
        loc_low = status["hotel"]["location"].lower()
        for k in intel.keys():
            if k in loc_low: city_key = k
    
    # Si no hay hotel hoy, buscar ciudad por el destino del último vuelo de hoy
    if not city_key and status["flights"]:
        dest_code = status["flights"][-1].get("to", "")
        # Podríamos mapear aquí códigos IATA a city_keys
        if dest_code == "DOH": city_key = "doha"
        elif dest_code == "MAD": city_key = "madrid"
        elif dest_code == "SIN": city_key = "singapur"

    msg = [
        f"⚡️ *CEREBRO VIAJERO - BRIEIFNG DIARIO*",
        f"📅 {today_str}\n",
        "━━━━━━━━━━━━━━━━━━━━"
    ]

    has_content = False

    if status["flights"]:
        has_content = True
        msg.append("✈️ *MOVIMIENTOS HOY:*")
        for f in status["flights"]:
            orig = CITY_NAMES.get(f['from'], f['from'])
            dest = CITY_NAMES.get(f['to'], f['to'])
            msg.append(f"• `{f['flight_num']}`: {orig} ➔ {dest} ({f['dep_time']})")
        msg.append("")

    if status["hotel"]:
        has_content = True
        h = status["hotel"]
        msg.append(f"🏨 *TU BASE:* [{h['hotel']}]({get_maps_link(h['hotel'] + ' ' + h['location'])})")
    
    if city_key in intel:
        has_content = True
        c_data = intel[city_key]
        idx = (today_dt.day) % len(c_data["gastronomy"]) # Rotación simple por día del mes
        
        food = c_data["gastronomy"][idx % len(c_data["gastronomy"])]
        gem = c_data["hidden_gems"][idx % len(c_data["hidden_gems"])]
        drone = c_data["drone_suggestions"][idx % len(c_data["drone_suggestions"])]
        phrase = c_data["essential_phrases"][idx % len(c_data["essential_phrases"])]

        msg.append(f"\n🍜 *GASTRONOMÍA:* _{food['name']}_")
        msg.append(f"📝 {food['description']}")
        msg.append(f"🍳 *Receta:* {food['recipe_quick']}")

        msg.append(f"\n💎 *GEMA OCULTA:* [{gem['name']}]({get_maps_link(gem['map_query'])})")
        msg.append(f"\n🚁 *DRONE PILOT:* [{drone['name']}]({get_maps_link(drone['map_query'])})")
        msg.append(f"🗣️ *IDIOMA:* {phrase['phrase']} (`{phrase['pronunciation']}`)")

    # Alerta de Check-in para mañana
    for item in itinerary:
        if item.get("type") == "Vuelo" and item.get("date") == tomorrow_str:
            has_content = True
            msg.append(f"\n🎫 *ALERTA CHECK-IN MAÑANA:* {item['flight_num']} ({item['from']} ➡️ {item['to']})")

    if has_content:
        send_telegram("\n".join(msg), bot_token, chat_id)

if __name__ == "__main__":
    run_alerts()
