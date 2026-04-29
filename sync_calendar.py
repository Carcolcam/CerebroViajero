import os
import json
import datetime
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Forzar UTF-8 en la salida de terminal para evitar errores con emojis en Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuración de rutas (Basado en la estructura del proyecto)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Usamos las credenciales existentes en la habilidad de Gmail
CRED_DIR = os.path.join(os.path.dirname(BASE_DIR), '.agent', 'skills', 'gmail-travel-sync', 'scripts')
CREDENTIALS_PATH = os.path.join(CRED_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(CRED_DIR, 'token_calendar.json') # Token separado para calendario
ITINERARY_PATH = os.path.join(BASE_DIR, 'itinerario_maestro.json')

# Scope para el calendario
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(f"No se encontró credentials.json en {CREDENTIALS_PATH}")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def sync_itinerary():
    print("Iniciando sincronización con Google Calendar...")
    
    if not os.path.exists(ITINERARY_PATH):
        print(f"Error: No se encontró {ITINERARY_PATH}")
        return

    with open(ITINERARY_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    service = get_calendar_service()
    
    for item in data.get('itinerary', []):
        event = {}
        summary = ""
        description = item.get('desc', '')
        
        if item['type'] == 'Vuelo':
            summary = f"✈️ {item['airline']} {item['flight_num']}: {item['from']} ➔ {item['to']}"
            date = item['date']
            start_time = f"{date}T{item['dep_time']}:00Z"
            end_time = f"{date}T{item['arr_time']}:00Z"
            # Ajuste básico: si la hora de llegada es menor que la de salida, es el día siguiente
            if item['arr_time'] < item['dep_time']:
                d = datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(days=1)
                end_time = f"{d.strftime('%Y-%m-%d')}T{item['arr_time']}:00Z"
            
            event = {
                'summary': summary,
                'description': f"PNR: {item.get('pnr', 'N/A')}\n{description}",
                'start': {'dateTime': start_time},
                'end': {'dateTime': end_time},
                'colorId': '1' # Lavanda (Vuelos)
            }
            
        elif item['type'] == 'Alojamiento':
            summary = f"🏨 Stay: {item['hotel']}"
            event = {
                'summary': summary,
                'description': f"Ref: {item.get('booking_ref', 'N/A')}\n{description}",
                'start': {'date': item['date']},
                'end': {'date': item['checkout']},
                'colorId': '2' # Verde (Hoteles)
            }

        if event:
            try:
                # Check for duplicates on the same day
                start_date = item['date']
                t_min = f"{start_date}T00:00:00Z"
                t_max = f"{start_date}T23:59:59Z"
                
                existing = service.events().list(
                    calendarId='primary', 
                    timeMin=t_min, 
                    timeMax=t_max, 
                    q=summary
                ).execute()
                
                if existing.get('items'):
                    print(f"Omitido (Ya existe): {summary}")
                    continue

                res = service.events().insert(
                    calendarId='primary', 
                    body=event,
                    sendUpdates='none'
                ).execute()
                print(f"Creado: {summary}")
            except Exception as e:
                print(f"Error creando {summary}: {e}")

if __name__ == "__main__":
    sync_itinerary()
