# 🧠 CerebroViajero: Plan Maestro de Implementación

Este documento define la arquitectura y el flujo de trabajo para el Sistema Inteligente de Viaje 2026.

## 🌟 Visión del Proyecto
Un sistema dinámico, proactivo y resiliente diseñado para gestionar el viaje al Sudeste Asiático 2026, integrando información de múltiples fuentes (Gmail, Hotmail, Google Maps) y optimizando la experiencia según las preferencias personales (Snorkel, Dron, Comida Picante).

---

## 🏗️ Los 13 Pilares del Sistema

1. **Vigilancia Activa Multi-Canal**: Rastreo diario de Hotmail y Gmail para detectar cambios en vuelos y hoteles.
2. **Lógica de Variables (Offsets)**: El itinerario es elástico; si un vuelo se retrasa, todos los tiempos dependientes se recalculan automáticamente.
3. **Filtro Gastro-Local**: Búsqueda de sitios con excelente relación calidad-precio y nivel de picante auténtico, evitando "trampas turísticas".
4. **Integración con Google Maps**: Sincronización y uso prioritario de tus listas personales de lugares guardados.
5. **Inteligencia de Nodos**: Cálculo de tiempos de confort específicos para cada aeropuerto, puerto o estación (context-aware).
6. **Drone Travel Guide**: SIDOPI obligado (>250g), max 120m. Registro DJI requerido.
7. **Snorkel Planner**: Monitorización de mareas, fauna y visibilidad en puntos de buceo específicos.
8. **Asistente de Fronteras**: Recordatorios dinámicos para visados (e-VOA, SG Arrival Card) 72h antes de cada cruce.
9. **HUD de Seguridad Online**: Localización en tiempo real de hospitales y embajadas basada en GPS.
10. **Kit de Supervivencia Offline**: Generación automática de PDFs con datos críticos, mapas y frases locales para zonas sin cobertura.
11. **Estrategia de Conectividad**: Telegram Bot activo (@Cerebroviajerobot). ID: 8769374923.
12. **Dashboard de Alta Usabilidad**: PWA con modo oscuro de alto contraste, elementos táctiles grandes y diseño para uso "en el terreno".
13. **Sistema Abierto**: Preferencias dinámicas (Dron activado, Snorkel en espera).

---

## 🛠️ Stack Técnico
- **Base de Datos**: `itinerario_vuelos.json` (Local) + Google Sheets (Sincronización).
- **Frontend**: HTML5/JS (PWA) con estética Glassmorphism.
- **Backend/Scripts**: Python (Rube Sandbox) para ejecución de herramientas Composio.
- **Herramientas**:
    - `OUTLOOK` / `GMAIL`: Ingesta de datos.
    - `TELEGRAM`: Notificaciones proactivas.
    - `EXA` / `GOOGLEMAPS`: Búsqueda de "Gemas Ocultas".

### Pilar 13: Seguridad SOS y Salud 🏥
*   **Phuket (Karon):** Bangkok Hospital Phuket (Town) o Dibuk Hospital (Más cerca).
*   **Manado:** Siloam Hospitals Manado (Alta tecnología).
*   **Kendari:** Siloam Hospitals Kendari o RSUP Bahteramas.
*   **Kuala Lumpur:** Gleneagles Hospital o Prince Court (Excelencia internacional).

---

### 💰 Resumen Financiero Total (Alojamiento)
| Moneda | Total Local | **Equiv. Euros (€)** | Depósitos |
| :--- | :--- | :--- | :--- |
| **IDR** (Rupia) | 22.813.590 | **~1.383 €** | - |
| **THB** (Bath) | 6.621 | **~175 €** | 3.000 (~79€) |
| **MYR** (Ringgit)| 1.160 | **~242 €** | - |
| **TOTAL** | - | **~1.800 €** | **+ ~79 €** |

---

### 🍽️ Recomendaciones Gastronómicas (Cerca de tus Hoteles)
*   **Kendari:** *Kampung Mangrove* (Marisco a la leña sobre el agua).
*   **Manado:** *City Extra* o *Tuna House* (Atún fresco local).
*   **Phuket:** *Karon Beach Seafood* o comida local en el mercado nocturno.
*   **Kuala Lumpur:** *Nasi Ayam Chee Meng* (Pollo Hainan) o *Damascus* (Shawarma).

---

## 📍 Ruta Crítica de Conexiones (Confirmada)

1. **Tramo Wakatobi-Manado (01 SEP):** 
   - Vuelo V06: WNI ➔ KDI (Kendari)
   - Vuelo V07: KDI ➔ UPG (Macasar) - *Misma compañía, escala técnica.*
   - Vuelo V08: UPG ➔ MDC (Manado)
2. **Tramo Bangka-Manado (08 SEP):**
   - Traslado T01: Lancha + Coche (Regreso a Manado).
3. **Tramo Kuala-Phuket (15 SEP):**
   - Vuelo V11: KUL ➔ HKT (AirAsia).
4. **Tramo Vuelta a Casa (16 SEP):**
   - Vuelo V12: HKT ➔ DOH (Doha) - *Escala técnica Qatar Airways.*
   - Vuelo V13: DOH ➔ MAD (Madrid).

---

## 📅 Roadmap de Ejecución
- [x] **Fase 1**: Creación del esquema de datos e ingesta de la Matriz de Vuelos actual.
- [x] **Fase 2**: Configuración de la conexión a Hotmail para rastreo activo.
- [x] **Fase 3**: Construcción del Dashboard Visual (PWA).
- [x] **Fase 4**: Implementación de las habilidades específicas de Dron y Seguridad (Drones & SOS OK).
- [x] **Fase 6**: Interactividad avanzada (Hilos de reserva, enlaces PNR y vista expandida).
- [x] **Data Audit**: Refinado de datos críticos (Escala KUL y salida de madrugada en CGK).
- [x] **Fase 7**: Integración final con Google Calendar y validación de alertas de mareas (Snorkel Planner).
- [x] **Fase 8**: Finalización, optimización de PWA y generación de Kit de Supervivencia Offline. ✅ 100% COMPLETADO
