/**
 * SCANNER TOTAL DE HILOS V4 - SOPORTE PARA OTAs (GOTOGATE/BOOKING)
 */
const fs = require('fs');

const ITINERARIO_PATH = 'itinerario_maestro.json';
const NOTIFICACIONES_PATH = 'notificaciones.json';
const OUTPUT_PATH = 'hilos_reservas.json';

const itinerary = JSON.parse(fs.readFileSync(ITINERARIO_PATH, 'utf8')).itinerary;
const notifications = JSON.parse(fs.readFileSync(NOTIFICACIONES_PATH, 'utf8'));

const allThreads = [];

itinerary.forEach(item => {
    const ref = item.pnr || item.booking_ref || item.booking_id;
    const provider = item.airline || item.hotel;
    
    if (!ref) return;

    // Buscar emails reales que contengan la referencia o el proveedor
    // Ampliamos búsqueda para detectar OTAs como Gotogate o Booking
    const matchingEmails = notifications.filter(n => {
        const content = (n.asunto + " " + (n.asunto_es || "") + " " + (n.cuerpo || "") + " " + (n.cuerpo_es || "")).toUpperCase();
        return content.includes(ref.toUpperCase());
    });

    let emails = [];
    if (matchingEmails.length > 0) {
        emails = matchingEmails.map(n => {
            // Si el correo es de Gotogate pero la reserva es de AirAsia, lo marcamos
            const senderDisplay = n.asunto.toUpperCase().includes('GOTOGATE') ? 'Gotogate (Booking.com)' : provider;
            return {
                type: 'in',
                sender: senderDisplay,
                subject: n.asunto_es || n.asunto,
                body: n.cuerpo_es || n.cuerpo,
                body_es: n.cuerpo_es || null,
                date: n.fecha,
                threadId: n.threadId || n.id || null,
                is_ota: n.asunto.toUpperCase().includes('GOTOGATE')
            };
        });
    } else {
        emails = [{
            type: 'in',
            sender: provider,
            body: `No matching emails found for reference ${ref}.`,
            body_es: `No se han encontrado correos específicos para la referencia ${ref}.`
        }];
    }

    allThreads.push({
        reserva: ref,
        proveedor: provider,
        fecha_viaje: item.date,
        descripcion: item.desc,
        emails: emails
    });
});

fs.writeFileSync(OUTPUT_PATH, JSON.stringify(allThreads, null, 2));
console.log(`[CerebroViajero] Hilos sincronizados (OTAs incluidas).`);
