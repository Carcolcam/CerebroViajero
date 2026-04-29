# 🛰️ Sentinel: Logistics Automation System

Sentinel es un ecosistema autónomo diseñado para la gestión de crisis y optimización logística de viajes internacionales. Transforma documentos dispersos en un itinerario maestro inteligente con detección de huecos, seguimiento en vivo y sincronización nativa.

## 🚀 Funcionalidades Core

- **🧠 Master Itinerary Engine**: Procesa PDFs y Emails para construir una línea de tiempo coherente.
- **🚨 Gap Detection Engine**: Identifica automáticamente noches sin hotel o discontinuidades geográficas entre vuelos.
- **📱 Tactical Dashboard**: Interfaz móvil premium en español con alertas de integridad y visualización de "Efecto Dominó".
- **☁️ Cloud Sync (Drive)**: Ingesta automática de documentos desde la nube mediante la carpeta `01_ZONA_INGESTA`.
- **📅 Native Calendar**: Sincronización bidireccional con Google Calendar (Calendario "Sentinel: Viajes").
- **📧 Thread Hunter**: Escaneo de hilos de correo para detección de nuevas reservas vía PNR.

## 🛠️ Instalación y Configuración

1. **Requisitos**: Python 3.10+
2. **Dependencias**:
   ```bash
   pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 requests python-dotenv
   ```
3. **Credenciales**: Requiere un archivo `credentials.json` de Google Cloud Console con acceso a Drive, Calendar y Gmail.

## 📁 Estructura del Proyecto

- `tejedor_itinerario.py`: El motor principal (El cerebro).
- `centro_de_mando.html`: El Dashboard táctico.
- `vigilante_drive.py`: Automatización de ingesta desde la nube.
- `procesar_emails.py`: Escaneo de reservas en bandeja de entrada.
- `Reserva/`: Carpeta local de almacenamiento clasificado.

## 🛡️ Seguridad
El sistema utiliza un archivo `.gitignore` estricto que impide la subida de tokens, credenciales y documentos personales a repositorios públicos.

---
**Sentinel v1.0** - *Pair-programmed with Antigravity* 🌌
