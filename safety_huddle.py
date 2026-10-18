#!/usr/bin/env python3
"""Weekly Safety Huddle Generator for U.S. AutoForce.

Auto-generates a branded, printable safety briefing sheet each week
with rotating topics relevant to straight truck drivers.

Usage:
  python3 safety_huddle.py              # generate this week's sheet
  python3 safety_huddle.py --week 35    # generate a specific ISO week
  python3 safety_huddle.py --list       # show all topics
  python3 safety_huddle.py --preview    # generate + open in browser

Output:
  ~/Desktop/work/safety-huddle-wkNN.html
  ~/Desktop/work/safety-huddle-wkNN.pdf

(NN = the zero-padded ISO week, e.g. safety-huddle-wk42.pdf)
"""
import argparse, datetime, os, subprocess, sys

DESKTOP = os.path.expanduser("~/Desktop/work")
LOGO_B64_FILE = os.path.expanduser("~/scripts/brand/logo-print-b64.txt")

TOPICS = [
    {"id":"accident_top5","title":"Accident Prevention — Top 5 Causes","icon":"&#9888;","color":"s-red",
     "items":["<strong>Distracted Driving</strong> — Phone, food, looking at dash. Eyes on road, always.",
              "<strong>Overhead Clearance</strong> — Know your height. Measure once, remember forever.",
              "<strong>Backing Accidents</strong> — Get out and look (GOAL). Use a spotter when possible.",
              "<strong>Rear-End Collisions</strong> — Increase following distance. No tailgating.",
              "<strong>Swing-Out on Turns</strong> — Watch your tail swing and off-tracking on tight turns."],
     "es_title":"Prevención de Accidentes — Las 5 Causas Principales",
     "es_items":['<strong>Conducir Distraído</strong> — Teléfono, comida, mirando el tablero. Siempre con los ojos en la carretera.',
              '<strong>Altura Libre Sobre la Cabeza</strong> — Conozca su altura. Mídala una vez, recuérdela siempre.',
              '<strong>Accidentes al Retroceder</strong> — Salga y revise (GOAL). Use un guía cuando sea posible.',
              '<strong>Choques por Alcance</strong> — Aumente la distancia de seguimiento. Espacio = tiempo para reaccionar.',
              '<strong>Exceso de Velocidad</strong> — Reduce su tiempo de reacción y aumenta la gravedad. Respete el límite.'],
     "es_callout":("<strong>RECUERDE:</strong> La mayoría de los accidentes son prevenibles. Respete estas 5 reglas todos los días.", "tip"),
     "callout":("<strong>REMEMBER:</strong> A loaded straight truck needs significantly more room to stop than you think. Slow down in wet/icy conditions (reduce speed by 1/3 on wet, 1/2+ on ice).","danger")},
    {"id":"pretrip","title":"Pre-Trip & Post-Trip — Non-Negotiable","icon":"&#9989;","color":"s-green",
     "checklist":["Walk-around: tires, lights, brakes, coupling, fluids",
                  "Check previous DVIR defects are marked as repaired",
                  "Log DVIR on Samsara app — select Pre-Trip or Post-Trip",
                  "Switching vehicles? Complete Post-Trip BEFORE logging into the next one",
                  "Sign &amp; submit daily logs every 24-hour cycle"],
     "es_title":"Inspección Previa al Viaje — Seguridad Primero",
     "es_items":['<strong>Frenos de Aire</strong> — Pruebe pérdida, reserva y aplicación. Sin fugas.',
              '<strong>Llantas &amp; Ruedas</strong> — Presión, desgaste, tuercas flojas o rotas.',
              '<strong>Luces &amp; Reflectores</strong> — Todos funcionando, limpios.',
              '<strong>Fluidos</strong> — Aceite, refrigerante, dirección, DEF, combustible. Busque fugas.',
              '<strong>Dirección &amp; Suspensión</strong> — Holgura excesiva, grietas o piezas sueltas.',
              '<strong>Equipo de Emergencia</strong> — Extintor, triángulos, cables, botiquín completos.'],
     "es_callout":("<strong>REGLA DE ORO:</strong> Si no está seguro, NO lo conduzca. Reporte los defectos antes de salir.", "danger"),
     "callout":("<strong>3 Points of Contact:</strong> Always use three points of contact when entering or exiting the cab — two hands and one foot, or two feet and one hand. No jumping.","tip")},
    {"id":"airbrakes","title":"Air Brake Quick-Check Numbers","icon":"&#128167;","color":"s-blue",
     "es_title":"Números Rápidos de Frenos de Aire",
     "es_items":["<strong>Corte del gobernador:</strong> 120-125 psi",
                 "<strong>Alarma de aire bajo:</strong> 60 psi",
                 "<strong>Activación de frenos de resorte:</strong> 20-45 psi",
                 "<strong>Pérdida máx. aplicado (simple):</strong> 3 psi/min",
                 "<strong>Pérdida máx. aplicado (combo):</strong> 4 psi/min",
                 "<strong>Válvula de seguridad abre:</strong> 150 psi"],
     "es_callout":("<strong>CONSEJO:</strong> Conozca estos números. Se preguntan en inspecciones.","tip"),
     "columns":[("<strong>Governor cut-out:</strong> 120-125 psi","<strong>Low air warning:</strong> 60 psi","<strong>Spring brake pop-out:</strong> 20-45 psi"),
                ("<strong>Max applied leak (single):</strong> 3 psi/min","<strong>Max applied leak (combo):</strong> 4 psi/min","<strong>Safety valve opens:</strong> 150 psi")]},
    {"id":"weight","title":"DOT Weight Limits — Know Your Numbers","icon":"&#9878;","color":"s-amber",
     "es_title":"Límites de Peso DOT",
     "es_items":["<strong>Eje delantero:</strong> 12,000 lbs",
                 "<strong>Eje sencillo:</strong> 20,000 lbs",
                 "<strong>Eje tándem:</strong> 34,000 lbs",
                 "<strong>GVWR > 10,000 lbs</strong> — Debe detenerse en básculas abiertas si no tiene bypass",
                 "Sensores WIM en el pavimento — siempre esté preparado"],
     "es_callout":("<strong>CONSEJO:</strong> Los vehículos comerciales >10,000 lbs GVWR deben detenerse en básculas abiertas a menos que tengan señal de bypass.","tip"),
     "stat_cards":[("12K","Steer Axle (lbs)"),("20K","Single Axle (lbs)"),("34K","Tandem Axle (lbs)")],
     "callout":("<strong>Scale Smart:</strong> WIM sensors are in the pavement. All vehicles over 10,000 lbs GVWR must stop at open weigh stations unless you get a bypass signal.","tip")},
    {"id":"defensive","title":"Defensive Driving — Stay Sharp","icon":"&#128737;","color":"s-purple",
     "es_title":"Conducción Defensiva — Siempre Alerta",
     "es_items":["<strong>Revise intersecciones</strong> — izquierda, derecha, izquierda antes de entrar",
                 "<strong>Mantenga espacio</strong> — mínimo 4 segundos de distancia",
                 "<strong>Cuidado con peatones</strong> en estacionamientos y entregas",
                 "<strong>Revise espejos</strong> cada 5-8 segundos",
                 "<strong>Luz amarilla = detenerse</strong> si es seguro",
                 "<strong>De noche:</strong> reduzca velocidad, aumente distancia"],
     "es_callout":("<strong>RECUERDE:</strong> Llegar tarde es mejor que no llegar. Ninguna carga vale su vida.","danger"),
     "items":["<strong>Scan intersections</strong> — left, right, left again before entering",
              "<strong>Keep space</strong> — at least 4 seconds of following distance",
              "<strong>Watch for pedestrians</strong> in parking lots and at delivery sites",
              "<strong>Check mirrors</strong> every 5-8 seconds while driving",
              "<strong>Yellow light means stop</strong> if you can safely do so",
              "<strong>Night driving:</strong> reduce speed, increase following distance"],
     "callout":("<strong>REMEMBER:</strong> Arriving late is always better than not arriving at all. No load is worth your life.","danger")},
    {"id":"hos","title":"Hours of Service — Stay Compliant","icon":"&#128337;","color":"s-slate",
     "es_title":"Horas de Servicio — Cumpla la Ley",
     "es_items":["<strong>10 horas consecutivas fuera de servicio</strong> para reinicio diario",
                 "Inicie sesión en Samsara con SUS credenciales — nunca comparta",
                 "Acepte/rechace tiempo de manejo no asignado inmediatamente",
                 "Conducción adversa? Puede aplicar extensión de 2 horas — llame a despacho",
                 "Certifique y firme sus registros diariamente — sin firmar = citación DOT"],
     "es_callout":("<strong>RECUERDE:</strong> Verifique sus registros antes de firmar. Cuando tenga dudas, comuníquese con despacho.","danger"),
     "items":["<strong>10 consecutive hours off-duty</strong> required for a daily restart",
              "Sign in to Samsara with YOUR credentials — never share logins",
              "Claim or decline any unassigned driving time immediately",
              "Adverse driving? 2-hour extension may apply — contact dispatch",
              "Certify and sign your logs daily — unsigned logs = DOT citation"],
     "callout":("<strong>DEF Fluid:</strong> Monitor levels daily. Running out = Limp Mode. Top off when you get back to the warehouse when possible.","tip")},
    {"id":"seatbelt","title":"Seatbelt Usage — Zero Exceptions","icon":"&#128737;","color":"s-green",
     "es_title":"Cinturón de Seguridad — Sin Excepciones",
     "es_items":["<strong>Abroche cada viaje</strong> — sin excepciones",
                 "Cinturón es la mejor defensa en vuelco/choque",
                 "Multas DOT por no usar cinturón <strong>$500+ por infracción</strong>",
                 "Dé ejemplo — otros lo seguirán",
                 "Abróchese <strong>antes</strong> de moverse"],
     "es_callout":("<strong>HECHO:</strong> Quien no usa cinturón tiene 30x más probabilidad de ser expulsado. La expulsión casi siempre es fatal.","danger"),
     "items":["<strong>Click it every time</strong> — every trip, every seat, no exceptions",
              "Seatbelts are the #1 defense in a rollover or collision",
              "DOT citations for unbelted drivers cost <strong>$500+ per offense</strong>",
              "Set the example — your habits rub off on others",
              "Buckle up <strong>before</strong> you start moving, not after"],
     "callout":("<strong>FACT:</strong> Drivers not wearing seatbelts are 30x more likely to be ejected in a crash. Ejection is almost always fatal.","danger")},
    {"id":"phones","title":"Phone & Device Rules — Zero Tolerance","icon":"&#128222;","color":"s-red",
     "es_title":"Reglas de Teléfono y Dispositivos — Cero Tolerancia",
     "es_items":["<strong>Prohibido usar celular en mano — CERO tolerancia</strong>",
                 "Solo soporte manos libres para GPS/llamadas",
                 "Prohibidos audífonos al conducir",
                 "Deténgase para usar dispositivos si es necesario",
                 "Enviar mensajes = descalificación automática en muchas flotas"],
     "es_callout":("<strong>PENA DOT:</strong> Primera infracción hasta $2,750 para conductores, $11,000 para transportistas.","danger"),
     "items":["<strong>No handheld phone use while driving — ZERO tolerance</strong>",
              "Hands-free mount only for GPS/calls",
              "No headphones while driving",
              "Pull over safely if you need to use your device",
              "Texting while driving = automatic disqualification in most fleets"],
     "callout":("<strong>DOT PENALTY:</strong> First offense fine for handheld use is up to $2,750 for drivers, $11,000 for carriers.","danger")},
    {"id":"backing","title":"Backing Safety — GOAL","icon":"&#9888;","color":"s-amber",
     "es_title":"Seguridad al Reversa — GOAL",
     "es_items":["<strong>GOAL:</strong> Salga y Mire — cada vez",
                 "Use un guía si es posible — comunique por radio o señas",
                 "Revise atrás ANTES de subir",
                 "Reversa lenta — si no ve, PARE y mire",
                 "Use espejos Y cámaras — nunca uno solo",
                 "Cuidado con peatones y obstáculos"],
     "es_callout":("<strong>CONSEJO:</strong> Muchas averías al reversar ocurren en sitios de entrega que visita a diario. Manténgase alerta.","tip"),
     "items":["<strong>GOAL:</strong> Get Out And Look — every single time",
              "Use a spotter when available — communicate via radio or hand signals",
              "Check behind BEFORE you get in the truck",
              "Back slowly — if you can't see, STOP and look",
              "Use mirrors AND cameras — never rely on just one",
              "Watch for pedestrians, carts, and other vehicles in your path"],
     "callout":("<strong>TIP:</strong> Most backing accidents happen at delivery sites and warehouses — the places you go every day. Stay sharp.","tip")},
    {"id":"post_accident","title":"If You're in an Accident — Immediate Steps","icon":"&#128680;","color":"s-red",
     "es_title":"Si Tiene un Accidente — Pasos Inmediatos",
     "es_items":["<strong>PARE</strong> — Freno estacionamiento, luces de emergencia",
                 "Revise heridos — llame al 911 si es necesario",
                 "Proteja la escena — señales en 10 minutos",
                 "Fotos de TODOS los vehículos, placas, carretera",
                 "Testigos — nombres y teléfonos",
                 "Llame a despacho/supervisor inmediatamente"],
     "es_callout":("<strong>Pruebas de drogas:</strong> Obligatorias si hay muerte, o citación + remolque, o citación + tratamiento médico. Alcohol en 2 horas, drogas en 32 horas.","danger"),
     "items":["<strong>STOP</strong> — Set parking brakes, turn on hazards",
              "Check for injuries — call 911 if needed",
              "Protect the scene — warning devices within 10 minutes",
              "Photos of ALL vehicles, plates, road conditions",
              "Witness names &amp; phone numbers",
              "Call dispatch / supervisor immediately"],
     "callout":("<strong>Drug Testing:</strong> Mandatory if fatality, OR citation + tow, OR citation + medical treatment away from scene. Alcohol test within 2 hours, drug screen within 32 hours.","danger")},
    {"id":"weather","title":"Adverse Weather Driving","icon":"&#9729;","color":"s-blue",
     "es_title":"Conducción en Clima Adverso",
     "es_items":["<strong>Reduzca velocidad</strong> — 1/3 en mojado, 1/2+ en nieve/hielo",
                 "<strong>Aumente distancia</strong> a 6-8 segundos",
                 "<strong>Luces encendidas</strong> si visibilidad baja",
                 "<strong>Evite maniobras bruscas</strong> — sin frenados duros",
                 "<strong>Hielo negro</strong> es invisible — puentes y sombras se congelan primero",
                 "Si visibilidad es peligrosa, <strong>deténgase y espere</strong>"],
     "es_callout":("<strong>RECUERDE:</strong> Siempre puede reemplazar una entrega. No puede reemplazar a un conductor.","danger"),
     "items":["<strong>Reduce speed</strong> — 1/3 on wet roads, 1/2+ on snow/ice",
              "<strong>Increase following distance</strong> to 6-8 seconds",
              "<strong>Headlights on</strong> anytime visibility is reduced",
              "<strong>Avoid sudden moves</strong> — no hard braking or sharp turns",
              "<strong>Black ice</strong> is invisible — bridges and shaded areas freeze first",
              "If visibility drops below safe levels, <strong>pull over and wait it out</strong>"],
     "callout":("<strong>REMEMBER:</strong> You can always replace a delivery. You can't replace a driver.","danger")},
    {"id":"cargo","title":"Cargo Securement — Before Every Trip","icon":"&#128230;","color":"s-amber",
     "es_title":"Aseguramiento de Carga — Antes de Cada Viaje",
     "es_items":["Revise correas, barras y amarres antes de salir",
                 "Vuelva a revisar a las 50 millas y en cada parada",
                 "La carga no debe moverse, caerse ni gotear",
                 "Use suficientes amarres para el peso",
                 "Asegure objetos sueltos — nada se sale volando",
                 "Conozca peso y distribución de su carga"],
     "es_callout":("<strong>VIOLACIÓN DOT:</strong> Carga sin asegurar puede generar multas, fuera de servicio y puntos en CSA.","danger"),
     "items":["Check all straps, bars, and tie-downs before driving",
              "Re-check after 50 miles and at every stop",
              "Cargo must not shift, fall, or leak onto the road",
              "Use the right number of tie-downs for the weight",
              "Cover and secure loose items — nothing flies out",
              "Know your load weight and distribution"],
     "callout":("<strong>DOT VIOLATION:</strong> Unsecured cargo can result in fines, out-of-service orders, and points on your CSA score.","danger")},
    {"id":"delivery","title":"Delivery Site & Parking Lot Safety","icon":"&#128663;","color":"s-green",
     "es_title":"Seguridad en Entregas y Estacionamientos",
     "es_items":["Busque peatones — clientes, empleados, niños",
                 "Cuidado con carritos y obstáculos",
                 "Use direccionales temprano — avise sus intenciones",
                 "Ceda a peatones — siempre, sin excepciones",
                 "Estacione solo en áreas designadas para camiones",
                 "Velocidad máxima 10 mph en estacionamientos"],
     "es_callout":("<strong>CONSEJO:</strong> Los sitios de entrega son donde ocurren los accidentes a baja velocidad. Reduzca velocidad y manténgase alerta.","tip"),
     "items":["Scan for pedestrians — customers, employees, children",
              "Watch for shopping carts and obstacles in your path",
              "Use turn signals early — let others know your intentions",
              "Yield to pedestrians — always, no exceptions",
              "Park in designated truck areas only",
              "Keep speed under 10 mph in parking lots"],
     "callout":("<strong>TIP:</strong> Delivery sites are where most low-speed accidents happen. Slow down and stay alert.","tip")},
    {"id":"roadrage","title":"Road Rage & Aggressive Drivers","icon":"&#128545;","color":"s-red",
     "es_title":"Enojo al Volante y Conductores Agresivos",
     "es_items":["<strong>No se enfrente</strong> — déles paso, mantenga calma",
                 "<strong>No haga contacto visual</strong> con conductores agresivos",
                 "Use bocina con moderación — escala situaciones",
                 "Mantenga distancia de vehículos agresivos",
                 "Reporte conducción peligrosa a despacho",
                 "Usted es más grande — usted pierde siempre"],
     "es_callout":("<strong>RECUERDE:</strong> Su ego no vale un choque. Déjelos ir. Manténgase profesional.","danger"),
     "items":["<strong>Don't engage</strong> — let them pass, stay calm",
              "<strong>Don't make eye contact</strong> with aggressive drivers",
              "Use your horn sparingly — it escalates situations",
              "Keep safe distance from aggressive vehicles",
              "Report dangerous driving to dispatch",
              "Your vehicle is bigger — you always lose in a confrontation"],
     "callout":("<strong>REMEMBER:</strong> Your ego isn't worth a collision. Let them go. Stay professional.","danger")},
    {"id":"fatigue","title":"Fatigue Management — Don't Push It","icon":"&#128564;","color":"s-slate",
     "items":["<strong>Get your 10 hours</strong> of off-duty rest — no shortcuts",
              "Watch for signs: yawning, heavy eyelids, drifting lanes",
              "<strong>Pull over immediately</strong> if you feel drowsy",
              "Caffeine helps short-term but isn't a substitute for sleep",
              "Keep your cab cool and well-ventilated",
              "Avoid heavy meals before driving"],
     "es_title":"Manejo de Fatiga — No Se Exija Demasiado",
     "es_items":['<strong>10 horas de descanso</strong> — Respeto total a su tiempo fuera de servicio.',
              'Señales: bostezos, párpados pesados, carrilando.',
              '<strong>Deténgase inmediatamente</strong> si se siente somnoliento.',
              'Cafeína ayuda poco tiempo, NO sustituye el sueño.',
              'Mantenga cabina fresca y ventilada.',
              'Evite comidas pesadas antes de conducir.'],
     "es_callout":("<strong>HECHO:</strong> Conducir somnoliento es tan peligroso como conducir ebrio. Tras 17h despierto = 0.05% BAC.", "danger"),
     "callout":("<strong>FACT:</strong> Drowsy driving is as dangerous as drunk driving. After 17 hours awake, impairment equals a BAC of 0.05%.","danger")},
    {"id":"fuel","title":"Fuel Management & Emissions","icon":"&#9981;","color":"s-amber",
     "items":["<strong>On-Road Diesel only</strong> — clear/light amber fuel for commercial trucks",
              "<strong>Red dyed fuel is ILLEGAL</strong> in on-road vehicles — massive fines",
              "<strong>DEF Fluid:</strong> Monitor daily. Running out = Limp Mode",
              "Idle reduction — avoid extended idling in restricted zones",
              "Report any fuel or fluid leaks immediately",
              "Keep fuel receipts for IFTA reporting"],
     "es_title":"Combustible &amp; Emisiones",
     "es_items":['<strong>Diesel solo para carretera</strong> — Color ámbar claro.',
              '<strong>Diesel rojo es ILEGAL</strong> en vehículos de carretera — multas enormes.',
              '<strong>DEF</strong> — Revise diario. Quedarse sin él = Modo de Limitación.',
              'Reduzca ralentí — Evite ralentí prolongado en zonas restringidas.',
              'Reporte fugas de combustible/fluidos inmediatamente.',
              'Guarde recibos para reporte IFTA.'],
     "es_callout":("<strong>ADVERTENCIA LEGAL:</strong> Usar diesel rojo en carretera es evasión fiscal federal. Multas > $10/gal + impuestos atrasados.", "danger"),
     "callout":("<strong>LEGAL WARNING:</strong> Using red dyed off-road fuel in an on-road vehicle is federal tax evasion. Fines can exceed $10 per gallon + back taxes.","danger")},
    {"id":"cameras","title":"Samsara Dash Cameras","icon":"&#128247;","color":"s-slate",
     "items":["Cameras record continuously — assume you're always on camera",
              "Hard braking, sharp turns, and speeding trigger event recordings",
              "Keep your dash cam lens clean at all times",
              "Never obstruct the camera's view",
              "Events are reviewed by safety team — don't give them reasons",
              "Good driving = no events = positive reviews"],
     "es_title":"Cámaras Dash Samsara",
     "es_items":['Graban continuamente — Asuma que siempre está grabando.',
              'Frenado brusco, giros bruscos, exceso velocidad generan eventos.',
              'Limpie lente de la cámara siempre.',
              'Nunca obstruya la vista de la cámara.',
              'Eventos revisados por seguridad — No dé motivos.',
              'Buena conducción = sin eventos = revisión positiva.'],
     "es_callout":("<strong>CONSEJO:</strong> La cámara es su mejor testigo en un accidente. Lo protege cuando NO es culpable.", "tip"),
     "callout":("<strong>TIP:</strong> The camera is your best witness in an accident. It protects YOU when it's not your fault.","tip")},
    {"id":"workzones","title":"Work Zone Safety — Slow Down","icon":"&#128679;","color":"s-amber",
     "items":["<strong>Slow down</strong> — fines are doubled in work zones",
              "Watch for flaggers and follow their directions",
              "Merge early — don't wait until the last second",
              "Watch for workers near the road — they're close to traffic",
              "Expect the unexpected — lane shifts, stopped traffic, equipment",
              "Increase following distance — stop &amp; go traffic"],
     "es_title":"Zonas de Trabajo — Reduzca Velocidad",
     "es_items":['<strong>Reduzca velocidad</strong> — Multas duplicadas en zonas de trabajo.',
              'Observe bandereros, siga sus indicaciones.',
              'Únase a carril temprano — No espere al último momento.',
              'Cuidado con trabajadores cerca de carretera.',
              'Espere lo inesperado — cambios de carril, tráfico detenido, equipos.',
              'Aumente distancia de seguimiento — Tráfico parado/arranca.'],
     "es_callout":("<strong>HECHO:</strong> Choques en zonas de trabajo matan a cientos de trabajadores y conductores cada año. Mayoría: alcance + distracción/velocidad.", "danger"),
     "callout":("<strong>FACT:</strong> Work zone crashes kill hundreds of workers and drivers every year. Most are rear-end collisions from distracted or speeding drivers.","danger")},
    {"id":"csa","title":"CSA Program — Your Score Matters","icon":"&#128200;","color":"s-purple",
     "items":["CSA (Compliance, Safety, Accountability) tracks your driving record",
              "Violations, crashes, and inspections all affect your score",
              "Higher CSA score = more inspections, higher insurance costs",
              "Keep your record clean — it follows you",
              "Address violations immediately — don't ignore citations",
              "Good CSA = better job opportunities"],
     "es_title":"Programa CSA — Su Puntuación Importa",
     "es_items":['CSA (Cumplimiento, Seguridad, Responsabilidad) registra su historial.',
              'Infracciones, choques, inspecciones afectan su puntaje.',
              'Puntaje alto = más inspecciones, mayor seguro.',
              'Mantenga récord limpio — Lo sigue a lo largo de su carrera.',
              'Corrija infracciones inmediatamente — No las ignore.',
              'Buen CSA = mejores oportunidades laborales.'],
     "es_callout":("<strong>RECUERDE:</strong> Su puntaje CSA es su reputación profesional. Protégalo conduciendo con seguridad.", "tip"),
     "callout":("<strong>REMEMBER:</strong> Your CSA score is your professional reputation. Protect it by driving safely every day.","tip")},
    {"id":"wellness","title":"Driver Wellness — Take Care of Yourself","icon":"&#129657;","color":"s-green",
     "items":["Stay hydrated — water is better than energy drinks",
              "Pack healthy snacks — avoid fast food every meal",
              "Stretch at every stop — back, neck, shoulders",
              "Get moving on your 10-hour break — walk, stretch, move",
              "Watch your blood pressure — DOT physical requires it",
              "Report any health concerns to your supervisor"],
     "es_title":"Bienestar del Conductor — Cuídese",
     "es_items":['Hidrátese — Agua mejor que bebidas energéticas.',
              'Lleve snacks saludables — Evite comida rápida a diario.',
              'Estírese en cada parada — Espalda, cuello, hombros.',
              'Muévase en sus 10h de descanso — Camine, estírese.',
              'Cuide presión arterial — Requisito examen médico DOT.',
              'Reporte problemas de salud a su supervisor.'],
     "es_callout":("<strong>CONSEJO:</strong> Su cuerpo es su equipo más importante. Cuídelo y él lo cuidará.", "tip"),
     "callout":("<strong>TIP:</strong> Your body is your most important piece of equipment. Take care of it and it'll take care of you.","tip")},
    {"id":"intersections","title":"Intersection Safety — Look Twice","icon":"&#128308;","color":"s-red",
     "items":["<strong>Left-Right-Left:</strong> Scan every intersection before entering",
              "Be prepared for red-light runners",
              "Don't block the intersection — wait until you can clear it",
              "Watch for vehicles turning left in front of you",
              "Cover the brake as you approach — be ready to stop",
              "Right on red? Come to a complete stop first, then check"],
     "es_title":"Intersecciones — Revise Dos Veces",
     "es_items":['<strong>Izquierda-Derecha-Izquierda</strong> — Revise cada intersección antes de entrar.',
              'Espere corredores de rojo.',
              'No bloquee intersección — Espere poder cruzar completo.',
              'Cuidado con vehículos girando a izquierda frente a usted.',
              'Cubra freno al acercarse — Siempre listo a frenar.',
              '¿Giro a derecha en rojo? Alto completo, luego verifique.'],
     "es_callout":("<strong>HECHO:</strong> Choques en intersecciones son muy graves. Causados por ceder mal o distracción.", "danger"),
     "callout":("<strong>FACT:</strong> Intersection crashes are among the most deadly. Most are caused by failure to yield or distraction.","danger")},
    {"id":"railroad","title":"Railroad Crossings — Stop, Look, Listen","icon":"&#128646;","color":"s-amber",
     "items":["<strong>STOP</strong> at every railroad crossing — no exceptions for commercial vehicles",
              "Look both ways — trains can come from either direction",
              "Never stop ON the tracks — leave room on the other side",
              "If the gate is down, <strong>WAIT</strong> — don't go around it",
              "Listen for horns — trains are quieter than you think",
              "Know your route — avoid crossings when possible"],
     "es_title":"Cruces Ferroviarios — Pare, Mire, Escuche",
     "es_items":['<strong>PARE</strong> en todo cruce ferroviario — Obligatorio para vehículos comerciales.',
              'Mire ambos lados — Tren puede venir de cualquier dirección.',
              'Nunca pare SOBRE las vías — Deje espacio al otro lado.',
              'Puerta baja = <strong>ESPERE</strong> — No la rodee.',
              'Escuche bocina — Trenes son más silenciosos de lo que cree.',
              'Conozca su ruta — Evite cruces difíciles cuando pueda.'],
     "es_callout":("<strong>LEY:</strong> Ley federal exige alto completo en todo cruce público para camiones. Sin excepciones. Multas hasta $10,000.", "danger"),
     "callout":("<strong>LAW:</strong> Federal law requires commercial vehicles to stop at all public railroad crossings. No exceptions. Fines up to $10,000.","danger")},
    {"id":"three_points","title":"3 Points of Contact — Every Time","icon":"&#128694;","color":"s-green",
     "items":["<strong>Two hands, one foot</strong> OR <strong>two feet, one hand</strong>",
              "Face the truck when climbing in or out",
              "<strong>Never jump</strong> — step down carefully",
              "Use grab handles — they're there for a reason",
              "Wet or icy steps? Take extra care — wipe them off",
              "Carrying something? Set it down and use both hands"],
     "es_title":"3 Puntos de Contacto — Siempre",
     "es_items":['<strong>2 manos, 1 pie</strong> O <strong>2 pies, 1 mano</strong>.',
              'Enfrente el camión al subir/bajar.',
              '<strong>Nunca salte</strong> — Baje con cuidado, paso a paso.',
              'Use agarraderas — Están ahí por seguridad.',
              'Escalones mojados/hielo — Extra cuidado, límpielos.',
              'Lleva algo? Déjelo, use ambas manos.'],
     "es_callout":("<strong>HECHO:</strong> Caídas/subidas son la #1 causa de lesiones con tiempo perdido. Ocurren al entrar/salir de cabina.", "danger"),
     "callout":("<strong>FACT:</strong> Slip, trip, and fall injuries are the #1 cause of lost-time injuries for truck drivers. Most happen getting in/out of the cab.","danger")},
    {"id":"roadside","title":"Roadside Inspections — Be Ready","icon":"&#128269;","color":"s-purple",
     "items":["Pull over safely and turn on hazard lights",
              "Stay in the cab unless told otherwise",
              "Have your CDL, medical card, registration, and insurance ready",
              "Be polite and professional — attitude matters",
              "Don't volunteer information — answer only what's asked",
              "Fix any violations immediately or within the timeframe given"],
     "es_title":"Inspecciones en Carretera — Prepárese",
     "es_items":['Deténgase con seguridad, encienda luces de emergencia.',
              'Permanezca en cabina a menos que le indiquen.',
              'Tenga CDL, tarjeta médica, registro, seguro a mano.',
              'Sea cortés y profesional — Actitud importa.',
              'No ofrezca información extra — Responda lo preguntado.',
              'Corrija violaciones inmediatamente o en plazo dado.'],
     "es_callout":("<strong>CONSEJO:</strong> Mejor inspección = lo despiden rápido. Mantenga unidad limpia y bien mantenida.", "tip"),
     "callout":("<strong>TIP:</strong> The best roadside inspection is the one where they wave you through. Keep your truck clean and well-maintained.","tip")},
]

TOPIC_BY_ID = {t["id"]: t for t in TOPICS}

CSS = """
@page{size:letter;margin:0.45in}
@media print{body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;color:#1a1a2e;background:#fff;line-height:1.35;font-size:11.5px}
.header{background:linear-gradient(135deg,#0b1120 0%,#1b2b4a 100%);color:#fff;padding:8px 16px;display:flex;align-items:center;gap:12px;border-radius:7px;margin-bottom:6px}
.header img{height:40px;width:auto;border-radius:5px}
.header-text h1{font-size:16px;font-weight:700;letter-spacing:0.5px}
.header-text .subtitle{font-size:10px;opacity:0.8;margin-top:1px}
.header .date-box{margin-left:auto;text-align:right;font-size:10px;opacity:0.85}
.header .date-box .date{font-size:15px;font-weight:600}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.section{margin-bottom:3px;border:1.5px solid #e2e8f0;border-radius:5px;overflow:hidden}
.section-header{padding:2.5px 7px;font-weight:700;font-size:10.5px;text-transform:uppercase;letter-spacing:0.8px;display:flex;align-items:center;gap:6px}
.section-body{padding:2.5px 7px 3.5px}
.s-blue .section-header{background:#dbeafe;color:#1e40af;border-bottom:1.5px solid #bfdbfe}
.s-red .section-header{background:#fee2e2;color:#991b1b;border-bottom:1.5px solid #fecaca}
.s-green .section-header{background:#dcfce7;color:#166534;border-bottom:1.5px solid #bbf7d0}
.s-amber .section-header{background:#fef3c7;color:#92400e;border-bottom:1.5px solid #fde68a}
.s-purple .section-header{background:#f3e8ff;color:#6b21a8;border-bottom:1.5px solid #e9d5ff}
.s-slate .section-header{background:#f1f5f9;color:#334155;border-bottom:1.5px solid #cbd5e1}
ul{padding-left:15px}li{margin-bottom:0.5px}
.stat-row{display:flex;gap:6px;margin-top:3px}
.stat-card{flex:1;background:#f8fafc;border:1px solid #e2e8f0;border-radius:4px;padding:4px 8px;text-align:center}
.stat-card .num{font-size:16px;font-weight:800;color:#0b1120}
.stat-card .label{font-size:8px;text-transform:uppercase;letter-spacing:0.5px;color:#64748b;margin-top:0}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:0 18px}
.checklist{list-style:none;padding:0}.checklist li{padding:2px 0 2px 21px;position:relative}
.checklist li::before{content:'';position:absolute;left:0;top:3.5px;width:13px;height:13px;border:1.5px solid #94a3b8;border-radius:3px;background:#fff}
.tip-box{background:#fffbeb;border-left:3px solid #f59e0b;padding:2.5px 7px;border-radius:0 4px 4px 0;margin-top:2.5px;font-size:10px}
.tip-box strong{color:#92400e}
.danger-box{background:#fef2f2;border-left:3px solid #dc2626;padding:2.5px 7px;border-radius:0 4px 4px 0;margin-top:2.5px;font-size:10px}
.danger-box strong{color:#991b1b}
.bottom-strip{display:flex;gap:5px;margin-top:2px}
.bottom-strip>div{flex:1;border-radius:5px;padding:2.5px 7px}
.bottom-strip strong{font-size:9px;text-transform:uppercase;letter-spacing:0.5px}
.footer{margin-top:1px;padding:2px 8px;background:#f1f5f9;border-radius:5px;text-align:center;font-size:9.5px;color:#64748b}
.footer strong{color:#1e40af}
"""


def select_topics(week_num):
    n = len(TOPICS)
    start = (week_num * 3) % n
    indices = [(start + i) % n for i in range(6)]
    left = [TOPICS[indices[i]] for i in range(3)]
    right = [TOPICS[indices[i]] for i in range(3, 6)]
    bottom_ids = ["cameras", "phones", "three_points"]
    bottom = [TOPIC_BY_ID[bid] for bid in bottom_ids]
    return left, right, bottom


def _lang_get(topic, key, lang):
    """Get translated field based on language."""
    if lang == "es":
        es_key = f"es_{key}"
        return topic.get(es_key, topic.get(key))
    return topic.get(key)


def render_section(topic, lang="en"):
    c = topic.get("color","s-blue")
    ic = topic.get("icon","&#9679;")
    t = _lang_get(topic, "title", lang)
    lines = [f'<div class="section {c}">',f'  <div class="section-header">{ic} {t}</div>',
             f'  <div class="section-body">']
    if "checklist" in topic:
        lines.append('    <ul class="checklist">')
        for i in topic["checklist"]: lines.append(f'      <li>{i}</li>')
        lines.append('    </ul>')
    elif "items" in topic:
        lines.append('    <ul>')
        items = _lang_get(topic, "items", lang) or topic.get("items", [])
        for i in items: lines.append(f'      <li>{i}</li>')
        lines.append('    </ul>')
    if "stat_cards" in topic:
        lines.append('    <div class="stat-row">')
        for num,label in topic["stat_cards"]:
            lines.append(f'      <div class="stat-card"><div class="num">{num}</div><div class="label">{label}</div></div>')
        lines.append('    </div>')
    if "columns" in topic:
        lines.append('    <div class="two-col">')
        for col in topic["columns"]:
            lines.append('      <div><ul>')
            for i in col: lines.append(f'        <li>{i}</li>')
            lines.append('      </ul></div>')
        lines.append('    </div>')
    if "callout" in topic:
        callout = _lang_get(topic, "callout", lang)
        if callout:
            txt,bt = callout
            cls = "tip-box" if bt=="tip" else "danger-box"
            lines.append(f'    <div class="{cls}">{txt}</div>')
    lines += ['  </div>','</div>']
    return "\n".join(lines)


def render_bottom_card(topic, lang="en"):
    cmap = {"s-blue":("#1e40af","#eff6ff","#bfdbfe"),"s-red":("#991b1b","#fef2f2","#fecaca"),
            "s-green":("#166534","#f0fdf4","#bbf7d0"),"s-amber":("#92400e","#fefce8","#fde68a"),
            "s-purple":("#6b21a8","#faf5ff","#e9d5ff"),"s-slate":("#334155","#f1f5f9","#cbd5e1")}
    tc,bg,bd = cmap.get(topic.get("color","s-slate"),("#334155","#f1f5f9","#cbd5e1"))
    ic = topic.get("icon","&#9679;")
    t = _lang_get(topic, "title", lang)
    lines = [f'<div style="flex:1;background:{bg};border:1.5px solid {bd};border-radius:5px;padding:4px 8px">',
             f'  <strong style="color:{tc};font-size:10.5px;text-transform:uppercase;letter-spacing:0.5px;">{ic} {t}</strong>',
             '  <ul style="margin-top:2px">']
    items = _lang_get(topic, "items", lang) or topic.get("checklist", [])
    for i in items: lines.append(f'    <li>{i}</li>')
    if "callout" in topic:
        callout = _lang_get(topic, "callout", lang)
        if callout:
            txt,bt = callout
            cls = "tip-box" if bt=="tip" else "danger-box"
            lines.append(f'    <div class="{cls}" style="margin-top:3px">{txt}</div>')
    lines += ['  </ul>','</div>']
    return "\n".join(lines)


def generate(week_num=None, preview=False, lang="en"):
    if week_num is None:
        week_num = datetime.date.today().isocalendar()[1]
    year = datetime.date.today().year
    jan4 = datetime.date(year, 1, 4)
    start_w1 = jan4 - datetime.timedelta(days=jan4.weekday())
    monday = start_w1 + datetime.timedelta(weeks=week_num-1)
    friday = monday + datetime.timedelta(days=4)
    left, right, bottom = select_topics(week_num)

    logo_b64 = open(LOGO_B64_FILE).read().strip()

    lang_es = (lang == "es")
    if lang_es:
        month_fmt = lambda d: d.strftime('%d').lstrip('0') + ' de ' + {1:'enero',2:'febrero',3:'marzo',4:'abril',5:'mayo',6:'junio',7:'julio',8:'agosto',9:'septiembre',10:'octubre',11:'noviembre',12:'diciembre'}[d.month]
        date_range = f"{month_fmt(monday)} — {month_fmt(friday)}, {friday.year}"
        week_label = f"Semana {week_num}"
    else:
        date_range = f"{monday.strftime('%B %d')} — {friday.strftime('%B %d, %Y')}"
        week_label = f"Week {week_num}"
    sections_html = "\n".join(render_section(t, lang) for t in left)
    sections_html_r = "\n".join(render_section(t, lang) for t in right)
    bottom_html = "\n".join(render_bottom_card(t, lang) for t in bottom)

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>U.S. AutoForce — Safety Huddle Week {week_num}</title>
<style>{CSS}</style></head><body>
<div class="header">
  <img src="data:image/jpeg;base64,{logo_b64}" alt="U.S. AutoForce">
  <div class="header-text">
    <h1>{'Reunión Semanal de Seguridad' if lang_es else 'Weekly Safety Huddle'}</h1>
    <div class="subtitle">{'Resumen de Seguridad del Conductor' if lang_es else 'Driver Safety Briefing'}</div>
  </div>
  <div class="date-box">
    <div class="date">{week_label}</div>
    <div>{date_range}</div>
  </div>
</div>
<div class="grid-2">
<div>
{sections_html}
</div>
<div>
{sections_html_r}
</div>
</div>
<div class="bottom-strip">
{bottom_html}
</div>
<div class="footer">
  <strong>U.S. AutoForce</strong> &middot; Field Operations &middot; {'La Seguridad No Es una Prioridad — Es un Prerequisito' if lang_es else "Safety is Not a Priority — It's a Prerequisite"}<br>
  {'¿Preguntas? Consulte a su Líder de Operaciones o Cumplimiento DOT.' if lang_es else 'Questions? See your Operations Leader or DOT Compliance.'}
</div>
</body></html>"""

    os.makedirs(DESKTOP, exist_ok=True)
    html_path = os.path.join(DESKTOP, f"safety-huddle-wk{week_num:02d}.html")
    pdf_path = os.path.join(DESKTOP, f"safety-huddle-wk{week_num:02d}.pdf")
    with open(html_path, "w") as f:
        f.write(html)
    print(f"HTML: {html_path}")

    r = subprocess.run(["google-chrome","--headless","--no-sandbox","--disable-gpu",
                        f"--print-to-pdf={pdf_path}","--no-pdf-header-footer",
                        f"file://{html_path}"], capture_output=True, text=True, timeout=30)
    if os.path.exists(pdf_path):
        print(f"PDF:  {pdf_path}")
    else:
        print(f"PDF generation failed: {r.stderr[:200]}")

    if preview:
        import webbrowser
        webbrowser.open(f"file://{html_path}")

    print(f"\nTopics for Week {week_num}:")
    for i,t in enumerate(left+right,1):
        print(f"  {i}. {t['title']}")
    return html_path, pdf_path


def cmd_list(args):
    print(f"Topic Pool ({len(TOPICS)} topics):\n")
    for i,t in enumerate(TOPICS,1):
        print(f"  {i:2d}. {t['title']}")
    print(f"\nRotation: 6 topics per week (3 left + 3 right) + cameras/phones/3-points always in bottom strip")
    print(f"Covers {len(TOPICS)} unique weeks before repeating.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--week","-w",type=int,help="ISO week number (default: this week)")
    p.add_argument("--list","-l",action="store_true",help="list all topics")
    p.add_argument("--preview",action="store_true",help="open in browser after generating")
    p.add_argument("--lang","-L",choices=["en","es"],default="en",help="language: en (default) or es (Spanish)")
    args = p.parse_args()
    if args.list:
        cmd_list(args)
    else:
        generate(args.week, args.preview, lang=args.lang)


if __name__ == "__main__":
    main()
