import os
import pickle
from googleapiclient.discovery import build

def cleanup():
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            service = build('drive', 'v3', credentials=creds)
            # Buscar carpeta Vuelos
            res = service.files().list(q="name = 'Vuelos' and mimeType = 'application/vnd.google-apps.folder'", fields="files(id)").execute()
            folders = res.get('files', [])
            if folders:
                folder_id = folders[0]['id']
                # Listar y borrar archivos
                res = service.files().list(q=f"'{folder_id}' in parents", fields="files(id, name)").execute()
                for f in res.get('files', []):
                    print(f"Borrando {f['name']}...")
                    service.files().delete(fileId=f['id']).execute()
                print("Drive limpio.")
            else:
                print("Carpeta Vuelos no encontrada.")
    else:
        print("Token no encontrado.")

if __name__ == "__main__":
    cleanup()
