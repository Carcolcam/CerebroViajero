# Arquitectura de Gestión Logística: CerebroViajero Sentinel

Este documento define la hoja de ruta y la estructura lógica para la evolución del sistema de monitorización de alertas y gestión de crisis del CerebroViajero.

## FASE 1: Estructuración Universal de Datos
1. **Modelo de Datos Agnóstico:** En el `itinerario_maestro.json`, todo (vuelos, hoteles, taxis, ferris) se tratará como un "Eslabón Logístico" con una estructura común. Todo se rige por un Identificador Único (`PNR` o `BookingID`).
2. **Jerarquía de Escalas:** Los vuelos no son eventos planos. Una "Reserva" (`Booking`) contiene uno o varios "Tramos" (`Legs`).
   * Si es la misma reserva (mismo PNR), el sistema sabe que el proveedor te protege ante pérdidas de enlace.
   * Si son reservas distintas ("Self-Transfer", distinto PNR), el sistema sabe que el riesgo logístico es tuyo y debe vigilarlo estrechamente.

## FASE 2: Motor de Ingesta IMAP (El Cazador de Hilos)
Para garantizar una reconstrucción impecable desde cero, sin ruido publicitario y sin perder conversaciones directas, la conexión a correos no buscará simples palabras clave, sino que implementará un **Filtro de Embudo de 4 Fases**:
3. **White-listing de Dominios:** Escaneo exclusivo de correos provenientes de dominios de proveedores logísticos validados (ej. `@booking.com`, `@traveloka.com`, etc.) y hoteles específicos, ignorando el resto instantáneamente.
4. **Detección de Hilos por Cabeceras (In-Reply-To):** Rastreo de las cabeceras invisibles `Message-ID` e `In-Reply-To` para cazar automáticamente las respuestas y conversaciones manuales de soporte o incidencias derivadas de una reserva base.
5. **Filtro Anti-Ruido (Regex Subjects):** Descarte automático de correos de marketing basados en un diccionario de exclusión de asuntos ("oferta", "newsletter", "promoción").
6. **Triaje Triangulado (NLP + PNR):** El payload de los correos que superan el embudo es analizado para extraer PNRs exactos. Si no hay PNR, se aplica *Triangulación por Huellas (Proveedor + Ruta + Fecha)*. El modelo deduce si es Confirmación, Modificación, Cancelación o Chat.

## FASE 3: El Tejedor y el Algoritmo de Fricción (Cálculo Espacio-Temporal)
Una vez extraídos los sucesos, el archivo `itinerario_maestro.json` se teje dinámicamente. Aquí el sistema calcula la viabilidad del solapamiento logístico usando el **Diccionario de Fricción**:
7. **Deducción de Hora de Check-in en Hotel:** La hora de entrada al hotel NO es la oficial (ej. 14:00). Es el resultado de: `Hora Prevista de Aterrizaje del Vuelo + Inmigración + Maletas + Tráfico local`.
8. **Regla de Inmigración Inteligente:** El sistema evalúa la ruta completa. Si `País_Origen = País_Destino` (Vuelo Doméstico), se asume un buffer de inmigración de `0`. Si es internacional, suma la penalización del aeropuerto correspondiente.
9. **La Fuente de Verdad Dual:** Los correos dictan el estado oficial (Confirmado/Cancelado). Sin embargo, el Tejedor cruza el PNR del vuelo con una **API de Vuelos en Vivo (Live Tracking)** para actualizar horas reales, solucionando el problema de los "Retrasos Silenciosos" (cuando la aerolínea retrasa el vuelo en la terminal pero no manda correo).

## FASE 4: El Botón "Procesar Baja" (El Gatillo)
Al hacer clic en "Procesar Baja" en una alerta crítica:
10. **Actualización de Estado:** El sistema localiza el eslabón roto en `itinerario_maestro.json`, cambia su estado a `"status": "CANCELLED"` y activa `"refund_status": "PENDING"`.
11. **Limpieza de Alertas (Cascade Archive):** El sistema localiza *todas* las alertas del Dashboard relacionadas con ese mismo PNR (Informativas, Precaución, Críticas, Resueltas) y las archiva simultáneamente para limpiar la vista.
12. **Gestión de Documentos (Drive):** El sistema mueve automáticamente los PDFs originales (billetes o vouchers cancelados) en Google Drive a una carpeta de archivo legal (ej. `7. Cancelados y Reembolsos`) renombrándolos (ej: `[CANCELADO]_Vuelo.pdf`) para mantener la limpieza sin perder la prueba legal de cara al banco.

## FASE 5: Reacción Logística (El Dashboard)
Al detectar un estado `"CANCELLED"` o un retraso severo:
13. **Aviso de Hueco Logístico:** El Dashboard detecta "agujeros espacio-temporales" (ej: te quedas tirado en una ciudad o sin hotel). Genera una tarjeta estática de Alta Prioridad en la interfaz avisando del riesgo exacto y recomendando la compra urgente de una alternativa.
14. **Previsión de Efecto Dominó:** Ante un retraso (no cancelación) de un Tramo 1, el sistema cruza la nueva hora de llegada con la hora de salida del Tramo 2 (conexión). Si el margen de tiempo es inviable, genera una Alerta Crítica inmediata.

## FASE 6: Seguimiento Económico (El Dinero)
15. **Lista Negra de Reembolsos:** Toda reserva marcada con `"refund_status": "PENDING"` entra en vigilancia por el script de revisión diaria.
16. **Recordatorio Proactivo:** Cada X días, el sistema envía un aviso recordando: *"Tienes pendiente de cobro X euros de Y proveedor"*. El ciclo no se cierra en la base de datos hasta que el usuario confirma la recepción de los fondos cambiando el estado a `"REFUNDED"`.

## FASE 7: Casos Extremos (Edge Cases a vigilar)
17. **El "Falso Positivo" del Cambio de Horario (Madrugones):** Un adelanto de vuelo (ej. de 14:00 a 06:00 AM) puede no romper ninguna conexión logística, pero destroza la planificación de descanso o traslados. El sistema deberá marcar como `WARNING` (Nivel de Precaución - Ámbar Neón) cualquier ajuste horario que desplace la salida a la franja nocturna (00:00 - 07:00), advirtiendo del impacto en transporte terrestre y hoteles.
18. **La Trampa del Aeropuerto Múltiple:** En escalas manuales ("Self-Transfers") en grandes ciudades (ej. Yakarta `CGK`/`HLP`, Tokio `HND`/`NRT`), el sistema debe verificar explícitamente el código IATA. Si la llegada es en un aeropuerto y la salida en otro distinto, el margen de conexión mínima exigida internamente pasará de 2 horas a un mínimo de 5-6 horas para generar alerta de viabilidad.
19. **El Retraso Silencioso:** Vuelos retrasados horas en panel del aeropuerto sin notificación por correo de la aerolínea. Se soluciona obligando al Tejedor a contrastar la hora de salida con una API de Vuelos en Vivo (ej. AviationStack) dentro de la ventana de las últimas 24 horas antes del despegue.
20. **Tráfico Predictivo Georreferenciado:** El Algoritmo de Fricción no usará tiempos de tráfico estáticos. El Tejedor consultará una API de Mapas (ej. Google Maps Distance Matrix) enviando el punto de origen (extraído del eslabón anterior, ej. Hotel) y el aeropuerto de destino, usando el parámetro de predicción temporal (`arrival_time` / `departure_time`) para obtener el atasco exacto a esa hora de ese día.
21. **Navegación Visual (Dashboard & Telegram):** Las recomendaciones de salida/llegada (ej. *"Un taxi debería recogerte a las 11:30"*) vendrán siempre acompañadas de una miniatura interactiva de Google Maps (Static API) incrustada en la tarjeta del Dashboard. Esta misma tarjeta visual con el mapa será disparada proactivamente por el **Bot de Telegram** para asegurar que el usuario la vea en el móvil sin necesidad de abrir la web.
