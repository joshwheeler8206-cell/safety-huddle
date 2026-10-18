#!/usr/bin/env python3
"""Weekly Warehouse Safety Huddle Generator for U.S. AutoForce.

Generates a branded, printable one-page safety briefing sheet each ISO week
with rotating topics for WAREHOUSE / TIRE-DISTRIBUTION employees:
  forklifts, electric forklifts, pallet jacks, batteries & charging, scissor and
  aerial lifts, working at heights, loading docks & trailers, racking & tire
  storage, ergonomics & stretching, housekeeping, LOTO, PPE, emergencies.

Usage:
  python3 warehouse_huddle.py                 # generate this week's sheet
  python3 warehouse_huddle.py --week 35# generate a specific ISO week
  python3 warehouse_huddle.py --list          # show all topics
  python3 warehouse_huddle.py --preview       # generate + open in browser

Output:
  ~/Desktop/work/warehouse-safety-huddle-wk<NN>.html
  ~/Desktop/work/warehouse-safety-huddle-wk<NN>.pdf
"""
import argparse, datetime, os, subprocess, sys

DESKTOP = os.path.expanduser("~/Desktop/work")
LOGO_B64_FILE = os.path.expanduser("~/scripts/brand/logo-print-b64.txt")

SUBTITLE = "Warehouse Safety Briefing"
FOOTER_LEAD = "Questions? See your Warehouse Supervisor or Safety Team."

# Per-language chrome.  SUBTITLE / FOOTER_LEAD above stay as the English values
# so older callers keep working.
LANG = {
    "en": {"h1": "Weekly Safety Huddle", "subtitle": "Warehouse Safety Briefing",
           "week": "Week",
           "footer_lead": "Questions? See your Warehouse Supervisor or Safety Team.",
           "ops": "Warehouse Operations"},
    "es": {"h1": "Charla de Seguridad Semanal", "subtitle": "Reunión de Seguridad del Almacén",
           "week": "Semana",
           "footer_lead": "¿Preguntas? Hable con su supervisor de almacén o con el equipo de seguridad.",
           "ops": "Operaciones de Almacén"},
}
TAB_LABELS = {"en": "English", "es": "Español"}
PRINT_ORDER = ("en", "es")
# strftime('%B') is always English, so the Spanish sheet needs its own month
# names or the date box prints "April" on an otherwise Spanish page.
MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio",
           "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
}
# Rotation step is coprime with len(TOPICS) so every topic comes up once
# before any repeats (step 7 over 30 topics = a clean 30-week cycle).
ROTATION_STEP = 7
BOTTOM_IDS = ["stretch_routine", "dock_edges", "near_miss"]

TOPICS = [
    # ---------------------------------------------------------------- lifting & ergonomics
    {"id":"stretch_routine","title":"Stretch & Warm-Up — Every Shift","icon":"&#129395;","color":"s-green",
     "short":["<strong>Warm up before you lift:</strong> neck, shoulders, wrists, hips, legs",
              "<strong>Mid-shift reset:</strong> 3-5 minutes at your break",
              "Hold 15-20 sec, breathe normally, <strong>never bounce</strong>"],
     "items":["<strong>Warm up BEFORE you lift a fork:</strong> 60 seconds of neck, shoulder and wrist circles",
              "<strong>Legs & hips:</strong> body bends, hip rotations, calf raises, ankle circles",
              "<strong>Back:</strong> cat-cow, knee-to-chest, torso side bends",
              "<strong>Hands & wrists:</strong> shake out, wrist flexion, finger fans — glove hands especially",
              "<strong>Mid-shift reset:</strong> 3-5 minutes at your break, before fatigue sets in",
              "Breathe normally — <strong>never bounce</strong> through a stretch; hold 15-20 sec"],
     "callout":("<strong>REMEMBER:</strong> Stretching is a supplement, never a substitute for proper lifting technique or getting help with a heavy load. Warm muscles, warm joints, then work.","tip")},
    {"id":"manual_handling","title":"Manual Lifting — Know Your Limits","icon":"&#128230;","color":"s-amber",
     "stat_cards":[("51 lb","NIOSH recommended, ideal lift"),("4-6 in","Power zone from your spine")],
     "items":["<strong>51 lb is NIOSH's recommended start</strong> for an <em>ideal</em> lift &mdash; every real lift is less. <strong>OSHA sets no weight limit</strong>",
              "<strong>Power zone:</strong> load between mid-thigh and mid-chest, close to your body",
              "<strong>Test the load</strong> with a test-lift before you commit — shift your grip if it feels wrong",
              "<strong>Legs, not back.</strong> Push up with your legs, keep the load close",
              "<strong>NEVER twist</strong> — move your feet, turn with your whole body",
              "Heavy, bulky or unstable? <strong>Get help or grab the pallet jack</strong>"],
     "callout":("<strong>10 lb off the floor can double the load on your lower back</strong> because it moves you further from your spine. Slide it closer, then lift.","danger")},
    {"id":"ergonomics","title":"Ergonomics — Repetition Is the Enemy","icon":"&#128188;","color":"s-purple",
     "items":["<strong>MSDs build slowly</strong> — strains, tendinitis, carpal tunnel, disc injuries",
              "Reduce <strong>weight</strong> > reduce <strong>distance</strong> > reduce <strong>frequency</strong>",
              "Rotate tasks so nobody does the same motion all shift",
              "Position bins, conveyors and pallets at <strong>waist height</strong> — not the floor",
              "<strong>Push, don't pull</strong> — pushing is far safer on the body",
              "Report pain EARLY — a tingle today prevents a surgery tomorrow"],
     "callout":("<strong>NOTE:</strong> OSHA has no general ergonomics standard — but the <strong>General Duty Clause</strong> requires us to fix hazards that will cause or contribute to injury. Speak up.","tip")},
    {"id":"musculoskeletal","title":"Sprains, Strains & Musculoskeletal Injuries","icon":"&#128308;","color":"s-red",
     "items":["<strong>STOP the task</strong> the moment you feel pain — do not work through it",
              "<strong>REPORT IT TO YOUR LEADER IMMEDIATELY</strong> — right away, on the spot",
              "<strong>Not</strong> at break, <strong>not</strong> at end of shift, <strong>not</strong> &ldquo;see if it settles&rdquo;",
              "<strong>Strain:</strong> muscle/tendon pull (back, shoulder). <strong>Sprain:</strong> ligament twist (ankle, wrist)",
              "Get it looked at early — <strong>ice, heat and pills are the clinic's call</strong>, not the aisle",
              "Never lift again until pain is gone — <strong>reinjury is how people end up disabled</strong>"],
     "callout":("<strong>REPORT IMMEDIATELY.</strong> A reported injury gets you care on the spot and keeps the record honest. Waiting turns a minor strain into a chronic problem AND a lost-time claim. <strong>No report, no care.</strong>","danger")},

    # ---------------------------------------------------------------- forklifts
    {"id":"forklift_preop","title":"Forklift Pre-Op Inspection — Non-Negotiable","icon":"&#9989;","color":"s-green",
     "checklist":["<strong>Key off visual walk-around:</strong> tires, forks, mast, chains, overhead guard",
                   "<strong>Fluid leaks</strong> — hydraulic, coolant, fuel/electrolyte spots under the truck",
                   "<strong>Seat belt</strong> present, buckles, latches clean",
                   "<strong>Running check:</strong> brakes, steering, horn, lights, backup alarm, hydraulics",
                   "<strong>Forks:</strong> no bends, cracks, or twist; both at the same height",
                   "<strong>Data plate + seatbelt/overhead guard intact</strong>"],
     "callout":("<strong>OSHA requires this at least DAILY</strong> (and after every shift on round-the-clock trucks). Defect found? Tag it out and tell your supervisor — repairs are by authorized personnel only.","danger")},
    {"id":"forklift_tipping","title":"Tip-Over Prevention — The #1 Killer","icon":"&#9888;","color":"s-red",
     "items":["<strong>The stability triangle:</strong> the load, the front axle and the rear pivot wheel",
              "The higher and further out the load center, the easier the truck tips forward",
              "<strong>Travel with the load LOW</strong> and <strong>tilted BACK</strong>",
              "<strong>Lower before you turn, brake, or accelerate — never carry a raised load through a turn</strong>",
              "<strong>Drive straight up and down ramps</strong> — never cross a slope diagonally",
              "<strong>Seat belt ON.</strong> A belt keeps you in the seat and the truck pivots instead of you"],
     "callout":("<strong>FACT:</strong> Forklift overturns are the leading cause of forklift fatalities &mdash; about <strong>25% of all forklift deaths</strong>. Most happen in under 5 seconds.","danger")},
    {"id":"forklift_load","title":"Load Capacity & Stability","icon":"&#9878;","color":"s-amber",
     "stat_cards":[("Rated","Load = truck + load + riders"),("Center","Lowest & heaviest at center")],
     "items":["<strong>Read the data plate</strong> &mdash; capacity depends on load CENTER, not just weight",
              "Load capacity <strong>drops sharply as the load center moves forward</strong>",
              "<strong>Backrest extension</strong> &mdash; use it whenever a load could slide rearward",
              "Never <strong>stack or lean</strong> a load higher than the backrest",
              "Only <strong>backward tilt</strong> for stability, and only enough to stabilize",
              "<strong>Riders ride with the load, never on the forks</strong> &mdash; forks are not a ride"],
     "callout":("<strong>RULE:</strong> If the load blocks your view, travel in <strong>REVERSE</strong> (except going up a ramp). Load rating charts are on every truck and in the cab manual.","danger")},
    {"id":"forklift_pedestrian","title":"Pedestrian Safety — Forklifts Always Yield","icon":"&#128694;","color":"s-red",
     "items":["<strong>Forklifts yield to people, every time</strong> &mdash; this is the most violated rule in our building",
              "<strong>Eye contact</strong> with a pedestrian before you move, and <strong>honor it",
              "<strong>Blind corners:</strong> slow to a crawl, sound the horn, expect anyone",
              "<strong>Raised loads block sightlines</strong> &mdash; your passengers may walk in blind",
              "<strong>Establish eye contact with the operator before crossing their path</strong>",
              "Never ride a pallet jack, cart or forklift as a passenger"],
     "callout":("<strong>WALKING RULE:</strong> Walkers use marked aisles, stay alert, never assume the driver sees you &mdash; and never step out from behind a rack.","danger")},
    {"id":"forklift_attach","title":"Forks, Attachments & Trailers","icon":"&#128257;","color":"s-slate",
     "items":["<strong>Seat forks fully when parked or unattended</strong> &mdash; fully lowered",
              "<strong>Verify the load is stable and back-tilted before moving</strong>",
              "<strong>Raised forks + a raised trailer bed = load falls</strong> before you reach the top",
              "<strong>Truck height + trailer height vs. your overhead clearance</strong> &mdash; know both numbers",
              "Only trained/authorized operators use attachments or side shifters",
              "<strong>Never walk or stand under raised forks or a raised load</strong>"],
     "callout":("<strong>REMEMBER:</strong> Forks that look bent &mdash; are bent. That is how loads slide off. Report fork damage immediately.","tip")},
    {"id":"electric_forklift","title":"Electric Forklifts — Warehouse-Native","icon":"&#128267;","color":"s-green",
     "items":["<strong>No exhaust, so ours are legal indoors</strong> &mdash; and better for the product and the building",
              "<strong>Weight matters more than you'd think</strong> &mdash; a counterbalance feels lighter but can tip faster when overloaded",
              "<strong>On a grade:</strong> travel with the load uphill-forward only, or drive with the load downhill &mdash; and creep",
              "<strong>Wet or contaminated floors = traction loss</strong> &mdash; slow way down",
              "<strong>Key switch + charger plug</strong> are yours to control; report loose or damaged keys",
              "No fuel cap, but there IS a <strong>charger plug that burns</strong> &mdash; plug in straight, no arcing"],
     "callout":("<strong>TIP:</strong> Electric trucks get quiet. Quiet means people don't hear you coming. Use the horn and the backup alarm every time they aren't obvious.","tip")},
    {"id":"battery_charging","title":"Battery & Charging Area Safety","icon":"&#9881;","color":"s-amber",
     "checklist":["<strong>Park squarely on the charger</strong> &mdash; brake set, neutral/park, hood open",
                   "<strong>Confirm the correct charger for the battery group</strong> before connecting",
                   "<strong>Wear the PPE:</strong> goggles/face shield, rubber gloves, apron, safety shoes",
                   "<strong>No smoking, open flame, sparks or arcs</strong> &mdash; hydrogen gas is generated",
                   "<strong>Eyewash / flush facilities</strong> &mdash; know where they are in the charging bay",
                   "<strong>Report a hot, swollen, leaking or damaged battery IMMEDIATELY</strong>"],
     "callout":("<strong>OSHA 1910.178(g):</strong> No smoking in the charging area. No open flames, sparks or arcs. Ventilation must be adequate for gassing batteries. Hood open to dissipate heat.","danger")},
    {"id":"battery_electrolyte","title":"Electrolyte & Hydrogen Gas","icon":"&#9888;","color":"s-red",
     "items":["<strong>EYEWASH FIRST, questions later</strong> &mdash; flush 15 min and get medical attention",
              "<strong>ACID INTO WATER &mdash; NEVER water into acid.</strong> Water into acid spatters boiling acid at you",
              "<strong>Skin contact:</strong> flush with water, remove contaminated clothing",
              "<strong>Hydrogen gas</strong> is lighter than air and collects at ceiling level &mdash; it ignites easily",
              "<strong>Use a flashlight, never a lighter or an open-flame test</strong> for electrolyte level",
              "<strong>Check vent caps are working</strong> and keep the battery compartment clear of metal tools"],
     "callout":("<strong>LEAD POISONING:</strong> Wash hands before eating, drinking or leaving the charging area. Wash-out facilities and eye wash must be stocked and working &mdash; check them.","danger")},

    # ---------------------------------------------------------------- lifts & heights
    {"id":"aerial_lifts","title":"Scissor & Aerial Lifts — 1910.29","icon":"&#128205;","color":"s-purple",
     "checklist":["<strong>Pre-use inspection EVERY shift</strong> &mdash; if it fails, tag it out",
                   "<strong>Harness attached to the boom/bucket</strong> &mdash; fall RESTRAINT, not full arrest",
                   "<strong>Guardrails/gates closed</strong> and locked while elevated",
                   "<strong>NEVER drive with the platform raised</strong> (unless the maker allows it)",
                   "<strong>Never use the lift as a crane</strong> or ride forks on the platform",
                   "<strong>Outriggers</strong> on pads, level solid surface, brakes set, work zone coned"],
     "callout":("<strong>POWER LINES:</strong> Treat every line and cable as energized and stay <strong>at least 10 feet away</strong>. Never position a lift between overhead hazards if avoidable.","danger")},
    {"id":"heights","title":"Working at Heights & Falls","icon":"&#129693;","color":"s-amber",
     "stat_cards":[("4 ft","OSHA fall-protection trigger, general industry"),("6 ft","Approx. shoulder height on a ladder")],
     "items":["<strong>4 feet</strong> is the OSHA trigger for fall protection in general industry",
              "<strong>Ladders and step stools:</strong> 4:1 rule (1 ft out per 4 ft up), 3 points of contact",
              "<strong>Never stand on the top step or cap</strong> of a ladder or stool",
              "<strong>Do not climb racking.</strong> Use the correct ladder or step stool",
              "Openings &gt;4 ft need a guardrail, a cover, or a personal fall-arrest system",
              "<strong>Fall protection outranks production</strong> &mdash; every single time"],
     "callout":("<strong>FACT:</strong> Falls from ladders, stairs, platforms and loading docks are a top-5 cause of warehouse fatalities. A 6-foot fall onto concrete can end a career.","danger")},
    {"id":"dock_safety","title":"Loading Dock Safety","icon":"&#128666;","color":"s-red",
     "items":["<strong>Never stand at the dock edge while a truck is backing in or out</strong>",
              "<strong>Watch the gap between the dock and the trailer</strong> &mdash; your wheel and your foot can fall into it",
              "<strong>Use the dock leveler and secure it</strong>; stow the safety plate/lip when not in use",
              "<strong>Dock lock/restraint in place</strong> whenever a trailer is being loaded or unloaded",
              "<strong>Floor-level visibility check</strong> before committing the load into the trailer",
              "Keep the dock area <strong>clear of pallets, straps, and debris</strong> &mdash; it is a trip zone"],
     "callout":("<strong>DANGER ZONE:</strong> Truck/trailer movement at a dock has no margin for error. Stand clear until the wheels are chocked and the dock lock is set.","danger")},
    {"id":"dock_edges","title":"Docks, Trailers & Chocks","icon":"&#128251;","color":"s-blue",
     "short":["<strong>Brakes SET</strong> + <strong>chocks under the rear wheels</strong> before anyone boards",
              "<strong>Dock lock / wheel restraint in place</strong> before loading begins",
              "Never stand at the dock edge while a trailer is moving"],
     "checklist":["<strong>Brakes SET</strong> on the highway unit before anyone boards it",
                   "<strong>Wheel chocks under the rear wheels</strong> &mdash; every single time",
                   "<strong>Dock lock / wheel restraint engaged</strong> before loading begins",
                   "<strong>Fixed jack or landing gear</strong> on uncoupled trailers to prevent upending",
                   "<strong>Secure the trailer floor, doors, and any movement</strong> before driving on it",
                   "<strong>Verify the trailer is tall enough and strong enough</strong> for your load"],
     "callout":("<strong>OSHA 1910.178(k):</strong> Brakes set and chocks placed under the rear wheels <strong>before</strong> a powered industrial truck boards a highway truck. No exceptions.","danger")},

    # ---------------------------------------------------------------- storage, tires, housekeeping
    {"id":"tire_handling","title":"Tire Handling, Inflation & Mounting","icon":"&#128663;","color":"s-slate",
     "items":["<strong>ALWAYS inflate inside a guarded inflator / safety cage</strong> &mdash; never against an unconfined wheel",
              "<strong>Chock the tire BOTH directions</strong> before inflation or deflation",
              "<strong>Stand out of the blast path and sidewall line</strong> &mdash; never over the tire, never in the line of the rim",
              "<strong>Wear eye protection</strong> &mdash; inflating pressure throws parts and debris",
              "<strong>Never work on a tire you cannot verify is empty of pressure</strong>",
              "<strong>Use rated air only.</strong> Never oxygen, and never improvised fittings or adapters"],
     "callout":("<strong>WHY THE CAGE:</strong> A tire or rim that fails at inflation pressure becomes a projectile. The cage is the only thing between you and it. Company SOP governs every tire job.","danger")},
    {"id":"tire_storage","title":"Tire Storage & Stacking","icon":"&#128230;","color":"s-amber",
     "items":["<strong>Respect the stack height on the rack or stack sign</strong> &mdash; tires are not free",
              "<strong>Heavy tires on the bottom, light on top</strong> &mdash; keep stacks square and stable",
              "<strong>Never stack tires in aisles, in front of exits, or under sprinklers</strong>",
              "<strong>Rubber is fuel.</strong> A tire pile is a fire load &mdash; keep exits and aisles clear",
              "Tires lean against a wall or rack? They fall. <strong>Never store them loose like that</strong>",
              "<strong>Keep aisles clear for the sprinkler/sprinkler clearance and for access</strong>"],
     "callout":("<strong>TIP:</strong> A clean, square, correctly stacked tire bay is faster than a messy one &mdash; and it is far safer for the next person who works it.","tip")},
    {"id":"racking","title":"Racking, Beams & Storage Loads","icon":"&#127959;","color":"s-purple",
     "items":["<strong>Read the load sign on every rack</strong> &mdash; that number is the maximum, not the target",
              "<strong>Damaged, dented or rusted uprights and beams = tag out</strong> and report it",
              "<strong>Keep loads evenly distributed on the beams</strong> &mdash; don't overload the outside arms",
              "<strong>Never climb, stand on, or lean against racking</strong>",
              "<strong>Keep sprinklers, and aisle clearance clear</strong> &mdash; flanged beams are for pallets, not people",
              "<strong>Watch for falling material</strong> when picking from high or misaligned loads"],
     "callout":("<strong>REMEMBER:</strong> Rack collapse is sudden and total. Pallets go to the rack that is rated for them, with the load centered &mdash; always.","danger")},
    {"id":"pallet_jack","title":"Pallet Jacks — Manual & Electric","icon":"&#128665;","color":"s-green",
     "items":["<strong>Pull, don't push, when you can see ahead</strong> &mdash; and never ride the forks",
              "<strong>Load the forks fully, deep into the pallet</strong> &mdash; a partial insert drops the load",
              "<strong>No people under a raised pallet, ever</strong>",
              "<strong>Electric/walkie:</strong> one hand on the tiller, watch the load end AND the drive end",
              "<strong>Slow down at corners and blind spots</strong> &mdash; a pallet jack carries no load rating to save you",
              "<strong>Report damaged wheels, forks, or a leaking hydraulic lift</strong> before your next pull"],
     "callout":("<strong>Load tip:</strong> A pallet jack with <strong>forks fully engaged and tilted back</strong> is the single safest way to move product across a warehouse floor. Use it.","tip")},
    {"id":"pallet_condition","title":"Pallet & Load Integrity","icon":"&#128230;","color":"s-amber",
     "items":["<strong>Inspect before you lift:</strong> broken boards, protruding nails, missing stringers",
              "<strong>Never pick up a leaning, sagging or badly wrapped load</strong> &mdash; rebuild it",
              "<strong>Stretch wrap tight enough to carry the load</strong>, not just the pallet",
              "<strong>Watch for plastic film and strapping</strong> underfoot and on forks",
              "<strong>Never step on a pallet</strong> to reach something",
              "Label & route <strong>damaged loads to rebuild</strong> instead of passing the problem along"],
     "callout":("<strong>TIP:</strong> A stack of tires or boxes can look solid and fail halfway up. Test the bottom boards before you commit your arms to it.","tip")},
    {"id":"conveyor","title":"Conveyors & Powered Equipment","icon":"&#9881;","color":"s-slate",
     "items":["<strong>Never ride, sit on, or reach onto a moving conveyor</strong>",
              "<strong>Never cross a live conveyor</strong> &mdash; use the designated crossover or bridge",
              "<strong>Guards must stay on.</strong> A missing guard gets the machine locked out, not bypassed",
              "<strong>Lock out / tag out before clearing a jam</strong> &mdash; every time, no exceptions",
              "<strong>Long hair, loose sleeves, jewelry, lanyards</strong> &mdash; nothing loose near moving parts",
              "<strong>Report jams, tears, and running noise immediately</strong>"],
     "callout":("<strong>LOCKOUT RULE:</strong> Jam clearing is where conveyor injuries happen. Every jam is a lockout. Every time.","danger")},
    {"id":"loto","title":"Lockout / Tagout — Energy Control","icon":"&#128274;","color":"s-red",
     "items":["<strong>Shut down, isolate, lock, tag</strong> &mdash; and YOU keep the key",
              "<strong>Verify zero energy</strong> &mdash; try the start control before you touch anything",
              "<strong>Release stored energy:</strong> air, hydraulic, gravity, electrical, spring",
              "<strong>Block and bleed lines</strong> so nothing can move when you're under a raised load",
              "<strong>Only the person who applied a lock removes it</strong>",
              "<strong>Never defeat, bypass or remove someone else's lock</strong>"],
     "callout":("<strong>1910.147:</strong> Unexpected energization is the hazard that kills. If you cannot positively identify every energy source, you are not ready to work on it.","danger")},
    {"id":"housekeeping","title":"Housekeeping & Clear Aisles","icon":"&#128722;","color":"s-green",
     "items":["<strong>Aisles and passageways stay clear and unobstructed</strong> &mdash; always (OSHA 1910.176)",
              "<strong>Clear the aisle the moment you see a hazard</strong> &mdash; shrink-wrap, banding, wood, banding coils",
              "<strong>Clean spills immediately</strong> or fence the area off until it is cleaned",
              "<strong>Floor condition matters:</strong> potholes, ridges and debris catch wheels and ankles",
              "<strong>Stack nothing in egress routes</strong> &mdash; exit routes stay open at all times",
              "<strong>Good housekeeping is a team sport</strong> &mdash; if you don't own it, fix it or report it"],
     "callout":("<strong>REMEMBER:</strong> Slips, trips and falls are the most common lost-time injury in a warehouse &mdash; and almost all of them start with something left on the floor.","danger")},
    {"id":"aisle_safety","title":"Walking & Working in Aisles","icon":"&#128101;","color":"s-slate",
     "items":["<strong>Wear your high-visibility vest</strong> &mdash; required whenever equipment is operating",
              "<strong>Walk, don't run</strong> &mdash; and never take shortcuts through a live lane",
              "<strong>No headphones or phone at your ear</strong> while moving through the warehouse",
              "<strong>Phone in hand = eyes down</strong> &mdash; stop and stand in an aisle pocket first",
              "<strong>Use a spotter</strong> for tight clearances and blind approaches",
              "<strong>Proper footwear only</strong> &mdash; no sandals, no loose slippers"],
     "callout":("<strong>TIP:</strong> Warehouse sightlines are short and lanes are narrow. Anticipate that nobody can see you until they are already on top of you.","tip")},
    {"id":"ppe","title":"Personal Protective Equipment","icon":"&#128737;","color":"s-green",
     "items":["<strong>Safety glasses or safety glasses + visor</strong> in all designated areas",
              "<strong>High-visibility vest</strong> wherever powered equipment runs",
              "<strong>Safety-toe, slip-resistant footwear</strong> &mdash; the only footwear allowed on the floor",
              "<strong>Cut-resistant gloves</strong> for metal strapping, banding, and sharp edges",
              "<strong>Chock-rated gloves</strong> &mdash; not oversized loose gloves (they catch and <em>reduce</em> grip)",
              "<strong>Hard hat</strong> anywhere overhead work is happening"],
     "callout":("<strong>FACT:</strong> Wearing two or more pairs of gloves can cut your grip strength by up to <strong>60%</strong>. The wrong glove is worse than no glove.","tip")},
    {"id":"rubber_chemicals","title":"Rubber, Chemicals & SDS","icon":"&#129514;","color":"s-purple",
     "items":["<strong>Know your SDS</strong> &mdash; they're on the wall or in the app, and it takes 2 minutes to open one",
              "<strong>Carbon black &amp; rubber dust</strong> &mdash; keep the area ventilated and dusty work under control",
              "<strong>Solvents, degreasers, tire dressing:</strong> use in <strong>ventilated</strong> areas only",
              "<strong>Check the label, then check the SDS</strong> before every chemical task",
              "<strong>Wash up and wash your hands</strong> before eating or leaving the site",
              "<strong>Report unlabeled containers</strong> and spills right away"],
     "callout":("<strong>REMEMBER:</strong> A product without a legible SDS is a product you have no right to use. Ask your supervisor.","tip")},
    {"id":"heat_cold","title":"Heat, Cold & Fatigue","icon":"&#9728;","color":"s-amber",
     "items":["<strong>Heat:</strong> water, rest and shade before you feel unwell. Your call, no questions",
              "<strong>Watch each other:</strong> headache, dizziness, nausea, no sweating, confusion",
              "<strong>Heat illness is medical emergency territory</strong> &mdash; cool and call for help immediately",
              "<strong>Work-rest</strong> matters more in heat &mdash; take your breaks even when it feels like you're behind",
              "<strong>Cool storage:</strong> grip and dexterity drop fast; adjust your pace and your gloves",
              "<strong>Fatigue kills attention.</strong> If you are worn down, say so"],
     "callout":("<strong>DANGER:</strong> Heat exhaustion can become heat stroke in minutes. Confusion or collapse = emergency. Cool them down and get medical help NOW.","danger")},
    {"id":"emergency","title":"Emergencies — Evacuation & Fire","icon":"&#128681;","color":"s-red",
     "items":["<strong>Know your two nearest exits</strong> and the assembly point for your area",
              "<strong>Exit routes stay clear, always</strong> &mdash; never pallet, strap or carton across a doorway",
              "<strong>Know the alarm, the extinguisher and eyewash locations</strong> for your zone",
              "<strong>Fire in a tire bay is serious</strong> &mdash; rubber burns hot and long. Evacuate and call it in",
              "<strong>RUBBER / CHEMICAL FIRE:</strong> evacuate, close doors behind you, never fight it alone",
              "<strong>Report every injury and near-miss</strong> the same shift"],
     "callout":("<strong>STOP WORK AUTHORITY:</strong> Any employee can stop any job they believe is unsafe &mdash; no retaliation, ever. If it doesn't look safe, it isn't.","danger")},
    {"id":"near_miss","title":"Near-Miss Reporting — Free Lessons","icon":"&#128269;","color":"s-blue",
     "short":["<strong>Report it before it becomes an injury</strong> &mdash; a near miss is a free lesson",
              "<strong>Describe what you SAW</strong>, not who was wrong",
              "<strong>No blame, no retaliation</strong> &mdash; ever"],
     "items":["<strong>A near miss is a free lesson</strong> &mdash; report it before it becomes an injury",
              "<strong>Report:</strong> near misses, small cuts, spills, damaged racking, near-overturns, dropped loads",
              "<strong>Describe what you SAW</strong>, not who you think was wrong",
              "<strong>No blame, no retaliation</strong> &mdash; ever. Blame kills reporting",
              "<strong>Report hazards even if they aren't yours</strong>",
              "<strong>Speak up during the huddle</strong> &mdash; it is the easiest safety control we have"],
     "callout":("<strong>WHY IT MATTERS:</strong> Companies that report near misses aggressively have <strong>fewer</strong> injuries, because they find the hazard before it finds someone.","tip")},
    {"id":"inspection_discipline","title":"Equipment Defects — Tag It, Report It","icon":"&#9998;","color":"s-amber",
     "items":["<strong>Any truck, jack, or lift found unsafe is out of service</strong> until repaired",
              "<strong>Tag it out</strong> and tell your supervisor before you walk away",
              "<strong>Repairs are by authorized personnel only</strong> &mdash; not you, not your buddy",
              "<strong>Record it</strong> so the next operator knows &mdash; defect history follows the truck",
              "<strong>Never &ldquo;just finish the shift&rdquo;</strong> on equipment you know is broken",
              "<strong>Batteries needing repair get the battery disconnected first</strong>"],
     "callout":("<strong>REMEMBER:</strong> The inspection sheet is not paperwork &mdash; it is the reason the next shift's operator finds a problem before they ride it.","tip")},
    {"id":"traffic_rules","title":"Warehouse Traffic Rules & Speed","icon":"&#128675;","color":"s-blue",
     "stat_cards":[("5 mph","Aisle max, unless posted lower"),("Horn","Sound at blind spots")],
     "items":["<strong>Observe the posted speed limit</strong> &mdash; in warehouses it is usually 5 mph, not 25",
              "<strong>Slow to a stop</strong> at intersections, blind corners, and doorways",
              "<strong>Sound the horn</strong> at cross-aisles and anywhere vision is obstructed",
              "<strong>Pedestrians and emergency equipment always have the right of way</strong>",
              "<strong>Obey all signs and floor markings</strong> &mdash; one-way aisles are one-way",
              "<strong>No passengers on forklifts, jacks or carts</strong> &mdash; ever"],
     "callout":("<strong>OSHA 1910.178(n):</strong> Slow down and sound the horn at cross-aisles and wherever vision is obstructed. Travel at a speed that lets you <strong>stop safely</strong>.","danger")},
]

# ---------------------------------------------------------------------------
# Spanish translations.  Keyed by topic id and merged onto the English entries by
# localized(), which keeps the icon / colour / layout keys in one place so the
# two languages can never drift apart structurally.  Only the text is replaced.
# Register: "usted" / imperative, as used in US workplace safety material.
# ---------------------------------------------------------------------------
TOPICS_ES = {
 "stretch_routine": {"title":"Estiramientos y Calentamiento — Cada Turno",
   "short":["<strong>Caliéntese antes de levantar:</strong> cuello, hombros, muñecas, caderas, piernas",
            "<strong>Pausa a media jornada:</strong> 3-5 minutos en su descanso",
            "Sostenga 15-20 seg, respire normal, <strong>nunca rebote</strong>"],
   "items":["<strong>Caliéntese ANTES de levantar una horquilla:</strong> 60 segundos de círculos de cuello, hombros y muñecas",
            "<strong>Piernas y caderas:</strong> flexiones, rotaciones de cadera, elevaciones de talón, círculos de tobillo",
            "<strong>Espalda:</strong> gato-vaca, rodilla al pecho, flexiones laterales del torso",
            "<strong>Manos y muñecas:</strong> sacudidas, flexión de muñecas, abanico de dedos — sobre todo con guantes",
            "<strong>Pausa a media jornada:</strong> 3-5 minutos en su descanso, antes de que aparezca el cansancio",
            "Respire normal — <strong>nunca rebote</strong> al estirar; sostenga 15-20 seg"],
   "callout":("<strong>RECUERDE:</strong> Estirarse es un complemento, nunca un sustituto de la técnica correcta de levantamiento ni de pedir ayuda con una carga pesada. Caliente músculos y articulaciones, y luego trabaje.","tip")},

 "manual_handling": {"title":"Levantamiento Manual — Conozca sus Límites",
   "stat_cards":[("51 lb","Recomendación NIOSH, levante ideal"),("4-6 pulg","Zona de potencia desde la columna")],
   "items":["<strong>51 lb es la recomendación de NIOSH</strong> para un levantamiento <em>ideal</em> &mdash; todo levantamiento real es menor. <strong>OSHA no fija límite de peso</strong>",
            "<strong>Zona de potencia:</strong> carga entre la mitad del muslo y la mitad del pecho, cerca del cuerpo",
            "<strong>Pruebe la carga</strong> con un levantamiento de prueba antes de comprometerse — cambie el agarre si se siente mal",
            "<strong>Piernas, no espalda.</strong> Empuje con las piernas y mantenga la carga cerca",
            "<strong>NUNCA gire el cuerpo</strong> — mueva los pies y gire con todo el cuerpo",
            "¿Pesada, voluminosa o inestable? <strong>Pida ayuda o use el transpaleta</strong>"],
   "callout":("<strong>10 lb fuera del piso pueden duplicar la carga en la zona lumbar</strong> porque la alejan más de su columna. Acérquela y luego levante.","danger")},

 "ergonomics": {"title":"Ergonomía — La Repetición es el Enemigo",
   "items":["Los <strong>trastornos musculoesqueléticos aparecen poco a poco</strong> — distensiones, tendinitis, túnel del carpo, lesiones de disco",
            "Reduzca <strong>peso</strong> > reduzca <strong>distancia</strong> > reduzca <strong>frecuencia</strong>",
            "Rote las tareas para que nadie haga el mismo movimiento todo el turno",
            "Coloque bins, transportadores y palés a la <strong>altura de la cintura</strong> — no en el piso",
            "<strong>Empuje, no jale</strong> — jalar es mucho más peligroso para el cuerpo",
            "Reporte el dolor <strong>temprano</strong> — un hormigueo hoy evita una cirugía mañana"],
   "callout":("<strong>NOTA:</strong> OSHA no tiene una norma general de ergonomía — pero la <strong>Cláusula de Deber General</strong> nos exige corregir los peligros que causarían o contribuirían a una lesión. Hable.","tip")},

 "musculoskeletal": {"title":"Esguinces, Distensiones y Lesiones Musculoesqueléticas",
   "items":["<strong>DETENGA la tarea</strong> en cuanto sienta dolor — no trabaje con dolor",
            "<strong>REPORTELO A SU LÍDER DE INMEDIATO</strong> — en el acto, ahí mismo",
            "<strong>No</strong> en el descanso, <strong>no</strong> al final del turno, <strong>no</strong> &ldquo;a ver si se calma&rdquo;",
            "<strong>Distensión:</strong> tirón de músculo o tendón (espalda, hombro). <strong>Esguince:</strong> torcedura de ligamento (tobillo, muñeca)",
            "Revíselo temprano — <strong>el hielo, el calor y las pastillas los decide la clínica</strong>, no el pasillo",
            "Nunca levante otra vez hasta que el dolor desaparezca — <strong>volver a lesionarse es lo que acaba con la espalda de la gente</strong>"],
   "callout":("<strong>REPORTE DE INMEDIATO.</strong> Una lesión reportada recibe atención en el acto. Esperar convierte una distensión menor en un problema crónico y en un reclamo por tiempo perdido. <strong>Sin reporte, sin atención.</strong>","danger")},

 "forklift_preop": {"title":"Inspección Pre-Operación del Montacargas — No Negociable",
   "checklist":["<strong>Apague y haga una ronda visual:</strong> llantas, horquillas, mástil, cadenas, protector superior",
                "<strong>Fugas de fluidos</strong> — hidráulico, refrigerante, combustible o electrolito debajo del montacargas",
                "<strong>Cinturón de seguridad</strong> presente, hebillas y cierres limpios",
                "<strong>Prueba en marcha:</strong> frenos, dirección, claxon, luces, alarma de reversa, hidráulico",
                "<strong>Horquillas:</strong> sin dobleces, grietas ni torsión; ambas a la misma altura",
                "<strong>Placa de datos y cinturón / protector superior en buen estado</strong>"],
   "callout":("<strong>OSHA exige esto al menos DIARIAMENTE</strong> (y tras cada turno en equipos continuos). ¿Defecto? Etiqueta de bloqueo y avise a su supervisor — solo personal autorizado repara.","danger")},

 "forklift_tipping": {"title":"Prevención de Volcaduras — El N.º 1 de Mortales",
   "items":["<strong>El triángulo de estabilidad:</strong> la carga, el eje delantero y la rueda trasera de pivote",
            "Cuanto más alta y más adelantada esté la carga, más fácil vuelca el montacargas hacia adelante",
            "<strong>Viaje con la carga BAJA</strong> y <strong>inclinada hacia ATRÁS</strong>",
            "<strong>Baje la carga antes de girar, frenar o acelerar — nunca gire con la carga elevada</strong>",
            "<strong>Suba y baje las rampas de frente</strong> — nunca en diagonal",
            "<strong>Cinturón puesto.</strong> El cinturón lo mantiene en el asiento y el montacargas pivota en lugar de usted"],
   "callout":("<strong>DATO:</strong> Las caídas de montacargas son la causa principal de muertes por montacargas — alrededor del <strong>25% de todas las muertes</strong>. Casi todas ocurren en menos de 5 segundos.","danger")},

 "forklift_load": {"title":"Capacidad de Carga y Estabilidad",
   "stat_cards":[("Nominal","Carga = montacargas + carga + personas"),("Centro","Lo más bajo y pesado al centro")],
   "items":["<strong>Lea la placa de datos</strong> — la capacidad depende del CENTRO de carga, no solo del peso",
            "La capacidad de carga <strong>cae en picado cuando la carga se mueve hacia adelante</strong>",
            "<strong>Extensión de la horquilla posterior</strong> — úsela siempre que la carga pueda deslizarse hacia atrás",
            "Nunca <strong>apile ni incline</strong> la carga más alto que la horquilla posterior",
            "Use <strong>inclinación hacia atrás</strong> solo para estabilizar, y solo lo suficiente",
            "<strong>Los pasajeros viajan con la carga, nunca sobre las horquillas</strong> — las horquillas no son asiento"],
   "callout":("<strong>REGLA:</strong> Si la carga le bloquea la vista, avance en <strong>REVERSA</strong> (salvo que suba una rampa). Las tablas de carga están en cada montacargas y en el manual de la cabina.","danger")},

 "forklift_pedestrian": {"title":"Seguridad de Peatones — El Montacargas Siempre Cede",
   "items":["<strong>El montacargas le cede el paso a la persona, siempre</strong> — es la regla más incumplida en nuestro edificio",
            "<strong>Contacto visual</strong> con el peatón antes de moverse, y <strong>respételo</strong>",
            "<strong>Esquinas ciegas:</strong> baje a velocidad mínima, toque el claxon, espere a cualquiera",
            "<strong>Las cargas elevadas bloquean la vista</strong> — su pasajero puede aparecer a ciegas",
            "<strong>Establezca contacto visual con el operador antes de cruzar su ruta</strong>",
            "Nunca se suba como pasajero en un transpaleta, carrito o montacargas"],
   "callout":("<strong>REGLA DE A PIE:</strong> Los peatones usan los pasillos marcados, están atentos y nunca asumen que el operador los ve. Nunca salgan de detrás de una estantería.","danger")},

 "forklift_attach": {"title":"Horquillas, Accesorios y Remolques",
   "items":["<strong>Baje las horquillas por completo al estacionar o dejarla sin vigilar</strong> — totalmente abajo",
            "<strong>Verifique que la carga esté estable e inclinada hacia atrás antes de moverse</strong>",
            "<strong>Horquillas elevadas + plataforma de remolque elevada = la carga se cae</strong> antes de que usted llegue arriba",
            "<strong>Altura del montacargas + altura del remolque vs. su espacio libre arriba</strong> — conozca los dos números",
            "Solo operadores capacitados y autorizados usan accesorios o desplazadores laterales",
            "<strong>Nunca pase ni se pare debajo de horquillas elevadas o de una carga elevada</strong>"],
   "callout":("<strong>RECUERDE:</strong> Horquillas que parecen dobladas — están dobladas. Así se deslizan las cargas. Reporte el daño de horquillas de inmediato.","tip")},

 "electric_forklift": {"title":"Montacargas Eléctricos — Ideales para el Almacén",
   "items":["<strong>Sin escape:</strong> son legales en interiores y mejores para el producto y el edificio",
            "<strong>El peso importa más de lo que parece</strong> — un equilibriador se siente más ligero pero puede volcar más rápido si se sobrecarga",
            "<strong>En pendiente:</strong> viaje con la carga subiendo de frente, o conduzca con la carga bajando — y despacio",
            "<strong>Piso mojado o contaminado = pérdida de tracción</strong> — baje mucho la velocidad",
            "<strong>Interruptor de llave y enchufe del cargador:</strong> están bajo su control. Reporte llaves flojas o dañadas",
            "No tiene tapa de combustible, pero SÍ tiene un <strong>enchufe del cargador que quema</strong> — conéctelo recto, sin chispas"],
   "callout":("<strong>CONSEJO:</strong> Son silenciosos: nadie lo oye llegar. Use el claxon y la alarma de reversa cuando no sean evidentes.","tip")},

 "battery_charging": {"title":"Baterías y Área de Carga",
   "checklist":["<strong>Estacione recto en el cargador</strong> — frenos puestas, neutral o aparcado, capó abierto",
                "<strong>Confirme el cargador correcto para el grupo de baterías</strong> antes de conectar",
                "<strong>Use el EPP:</strong> gafas o protector facial, guantes de hule, mandil, zapatos de seguridad",
                "<strong>Sin fumar, sin llama abierta, chispas ni arcos</strong> — se genera gas de hidrógeno",
                "<strong>Lavaojos y duchas de emergencia</strong> — sepa dónde están en el área de carga",
                "<strong>Reporte DE INMEDIATO una batería caliente, hinchada, con fuga o dañada</strong>"],
   "callout":("<strong>OSHA 1910.178(g):</strong> No fumar en el área de carga. Sin llamas abiertas, chispas ni arcos. La ventilación debe ser adecuada para baterías que generan gas. Capó abierto para disipar el calor.","danger")},

 "battery_electrolyte": {"title":"Electrolito y Gas de Hidrógeno",
   "items":["<strong>LAVAOJOS PRIMERO, preguntas después</strong> — enjuague 15 minutos y busque atención médica",
            "<strong>ÁCIDO EN AGUA — NUNCA agua en ácido.</strong> Echándole agua al ácido salpica ácido hirviendo",
            "<strong>Contacto con la piel:</strong> enjuague con agua y quítese la ropa contaminada",
            "El <strong>gas de hidrógeno</strong> es más ligero que el aire, se acumula cerca del techo y se enciende con facilidad",
            "<strong>Use una linterna, nunca un encendedor ni una prueba de llama</strong> para ver el nivel del electrolito",
            "<strong>Verifique las tapas de ventilación</strong> y mantenga el compartimento de la batería libre de herramientas metálicas"],
   "callout":("<strong>ENVENENAMIENTO POR PLOMO:</strong> Lávese las manos antes de comer, beber o salir del área de carga. El lavaojos y las duchas deben estar surtidos y funcionando.","danger")},

 "aerial_lifts": {"title":"Andamios de Tijera y Aéreos — 1910.29",
   "checklist":["<strong>Inspección antes de usar, CADA turno</strong> — si falla, póngale etiqueta de bloqueo",
                "<strong>Arnés sujeto a la plataforma o a la cesta</strong> — restricción de caída, no detención completa",
                "<strong>Barandales y puertas cerradas</strong> y con seguro mientras está elevado",
                "<strong>NUNCA conduzca con la plataforma elevada</strong> (a menos que el fabricante lo permita)",
                "<strong>Nunca use la plataforma como grúa</strong> ni monte horquillas sobre la plataforma",
                "<strong>Estabilizadores</strong> sobre placas, superficie firme y nivelada, frenos puestos, zona con conos"],
   "callout":("<strong>LÍNEAS DE ALTA TENSIÓN:</strong> Trate cada línea y cable como energizado y manténgase a <strong>por lo menos 10 pies de distancia</strong>. Nunca coloque la plataforma entre peligros aéreos si se puede evitar.","danger")},

 "heights": {"title":"Trabajo en Alturas y Caídas",
   "stat_cards":[("4 pies","Disparador OSHA de protección, industria general"),("6 pies","Altura aprox. del hombro en una escalera")],
   "items":["<strong>4 pies</strong> es el disparador de OSHA para protección contra caídas en industria general",
            "<strong>Escaleras y banastas:</strong> regla 4:1 (1 pie hacia afuera por cada 4 pies de altura), 3 puntos de apoyo",
            "<strong>Nunca se pare en el último escalón ni en la parte superior</strong> de una escalera o banasta",
            "<strong>No suba a las estanterías.</strong> Use la escalera o banasta correcta",
"Las aberturas de <strong>más de 4 pies</strong> necesitan barandal, cubierta o sistema personal de detención de caída",
             "<strong>La protección contra caídas le gana a la producción</strong> — todas y cada una de las veces"],
    "callout":("<strong>DATO:</strong> Las caídas desde escaleras, plataformas y muelles de carga están entre las 5 principales causas de muertes en almacenes. Una caída de 6 pies al concreto puede terminar una carrera.","danger")},

 "dock_safety": {"title":"Seguridad en el Muelle de Carga",
   "items":["<strong>Nunca se pare en el borde del muelle mientras un camión entra o sale</strong>",
            "<strong>Vigile el espacio entre el muelle y el remolque</strong> — su rueda y su pie se pueden caer ahí",
            "<strong>Use la rampa niveladora y asegúrela</strong>; guarde la placa o el borde de seguridad cuando no se use",
            "<strong>Bloqueo de muelle o restricción puesto</strong> cada vez que se cargue o descargue un remolque",
            "<strong>Verifique la visibilidad a nivel del piso</strong> antes de comprometer la carga dentro del remolque",
            "Mantenga el área del muelle <strong>libre de palés, cinchas y escombros</strong> — es zona de tropezones"],
   "callout":("<strong>ZONA DE PELIGRO:</strong> El movimiento de camión o remolque en el muelle no tiene margen de error. Manténgase aparte hasta que las ruedas tengan cuñas y el bloqueo.","danger")},

 "dock_edges": {"title":"Muelles, Remolques y Cuñas",
   "short":["<strong>Frenos PUESTOS</strong> y <strong>cuñas bajo las ruedas traseras</strong> antes de que alguien suba",
            "<strong>Bloqueo de muelle o restricción de ruedas puesto</strong> antes de empezar a cargar",
            "Nunca se pare en el borde del muelle mientras se mueve un remolque"],
   "checklist":["<strong>Frenos PUESTOS</strong> en el unidad de carretera antes de que alguien suba",
                "<strong>Cuñas bajo las ruedas traseras</strong> — todas y cada una de las veces",
                "<strong>Bloqueo de muelle o restricción de ruedas activado</strong> antes de empezar a cargar",
                "<strong>Gato fijo o patines de apoyo</strong> en remolques desacoplados para evitar que se volteen",
                "<strong>Asegure el piso y las puertas del remolque</strong> antes de conducir sobre él",
                "<strong>Verifique que el remolque sea lo bastante alto y fuerte</strong> para su carga"],
   "callout":("<strong>OSHA 1910.178(k):</strong> Frenos puestos y cuñas bajo las ruedas traseras <strong>antes</strong> de que un montacargas suba a un camión de carretera. Sin excepciones.","danger")},

 "tire_handling": {"title":"Manejo, Inflado y Montaje de Llantas",
   "items":["<strong>SIEMPRE infle dentro de un inflador con guarda o jaula de seguridad</strong> — nunca contra una rueda sin protección",
            "<strong>Ponga cuñas a la rueda en AMBAS direcciones</strong> antes de inflar o desinflar",
            "<strong>Manténgase fuera de la línea de reventón y del flanco</strong> — nunca sobre la llanta, nunca frente al aro",
            "<strong>Use protección ocular</strong> — la presión de inflado lanza partes y escombros",
"<strong>Nunca trabaje en una llanta cuya presión no pueda verificar</strong>",
             "<strong>Use solo aire comprimido de capacidad adecuada.</strong> Nunca oxígeno ni adaptadores improvisados"],
    "callout":("<strong>POR QUÉ LA JAULA:</strong> Una llanta o aro que falla al inflar se convierte en un proyectil. La jaula es lo único entre usted y eso. El procedimiento de la empresa rige este trabajo.","danger")},

 "tire_storage": {"title":"Almacenamiento y Apilado de Llantas",
   "items":["<strong>Respete la altura de apilado indicada en la estantería o el letrero</strong> — las llantas no andan gratis",
            "<strong>Llantas pesadas abajo, ligeras arriba</strong> — mantenga las pilas rectas y estables",
            "<strong>Nunca apile llantas en pasillos, frente a salidas ni bajo rociadores</strong>",
"<strong>El caucho es combustible.</strong> Un montón de llantas es carga de fuego — mantenga libres las salidas y los pasillos",
             "¿Llantas recargadas contra una pared o estantería? Se caen. <strong>Nunca las guarde así sueltas</strong>",
             "<strong>Mantenga los pasillos libres</strong> para el espacio del rociador y para el acceso"],
    "callout":("<strong>CONSEJO:</strong> Un área de llantas limpia, recta y bien apilada es más rápida y mucho más segura para quien trabaje ahí.","tip")},

 "racking": {"title":"Estanterías, Vigas y Cargas Almacenadas",
   "items":["<strong>Lea el letrero de carga de cada estantería</strong> — ese número es el máximo, no el objetivo",
            "<strong>Montantes y vigas dañados, abollados u oxidados = póngale etiqueta de bloqueo</strong> y repórtelo",
            "<strong>Distribuya las cargas parejo en las vigas</strong> — no sobrecargue los brazos exteriores",
            "<strong>Nunca suba, se pare ni se apoye en las estanterías</strong>",
"<strong>Mantenga libres los rociadores y el pasillo</strong> — las vigas de canal son para palés, no para personas",
             "<strong>Vigile el material que se desprende</strong> al retirar carga alta o desalineada"],
   "callout":("<strong>RECUERDE:</strong> El derrumbe de una estantería es súbito y total. Los palés van a la estantería clasificada para ellos, con la carga centrada — siempre.","danger")},

 "pallet_jack": {"title":"Transpaletas — Manuales y Eléctricas",
   "items":["<strong>Jale, no empuje, cuando pueda ver adelante</strong> — y nunca se monte en las horquillas",
            "<strong>Meta las horquillas por completo, hasta el fondo del palé</strong> — una inserción parcial tira la carga",
            "<strong>Nadie debajo de un palé elevado, nunca</strong>",
            "<strong>Eléctrica o deambulante:</strong> una mano en el timón, vigile el extremo de la carga Y el de arrastre",
            "<strong>Baje la velocidad en esquinas y puntos ciegos</strong> — un transpaleta no tiene carga nominal que lo salve",
            "<strong>Reporte ruedas u horquillas dañadas, o una elevación hidráulica con fuga</strong> antes de su siguiente tiro"],
   "callout":("<strong>Consejo de carga:</strong> Un transpaleta con <strong>horquillas bien metidas e inclinado hacia atrás</strong> es la forma más segura de mover producto en el almacén. Úselo.","tip")},

 "pallet_condition": {"title":"Integridad de Palés y Cargas",
   "items":["<strong>Inspeccione antes de levantar:</strong> tablas rotas, clavos salidos, largueros faltantes",
            "<strong>Nunca levante una carga inclinada, vencida o mal envuelta</strong> — rehágala",
            "<strong>Estire el plástico lo bastante firme</strong> para que sostenga la carga, no solo el palé",
            "<strong>Vigile el plástico y las cinchas</strong> bajo los pies y en las horquillas",
            "<strong>Nunca se suba a un palé</strong> para alcanzar algo",
            "Identifique y marque las <strong>cargas dañadas para rehacerlas</strong> en vez de pasar el problema"],
   "callout":("<strong>CONSEJO:</strong> Una pila de llantas o cajas puede verse sólida y fallar a la mitad. Pruebe las tablas de abajo antes de comprometer los brazos.","tip")},

 "conveyor": {"title":"Transportadores y Equipos Motorizados",
   "items":["<strong>Nunca se monte, se siente ni alcance un transportador en movimiento</strong>",
            "<strong>Nunca cruce un transportador en operación</strong> — use el cruce o puente designado",
            "<strong>Las guardas deben permanecer puestas.</strong> Una guarda faltante bloquea la máquina, no se evade",
            "<strong>Bloqueo y etiquetado antes de despejar una obstrucción</strong> — siempre, sin excepción",
            "<strong>Cabello largo, mangas sueltas, joyas, colgantes</strong> — nada suelto cerca de partes móviles",
            "<strong>Reporte de inmediato obstrucciones, desgarros y ruidos de funcionamiento</strong>"],
   "callout":("<strong>REGLA DE BLOQUEO:</strong> Los accidentes en transportadores ocurren al despejar obstrucciones. Cada obstrucción es un bloqueo. Siempre.","danger")},

 "loto": {"title":"Bloqueo y Etiquetado — Control de Energía",
   "items":["<strong>Apague, aísle, bloquee y etiquete</strong> — y la llave la conserva usted",
            "<strong>Verifique energía cero</strong> — pruebe el control de arranque antes de tocar nada",
            "<strong>Libere la energía almacenada:</strong> aire, hidráulica, gravedad, eléctrica, resorte",
            "<strong>Bloquee y sangre las líneas</strong> para que nada se mueva cuando esté debajo de una carga elevada",
            "<strong>Solo quien puso el candado lo quita</strong>",
            "<strong>Nunca defe, evada ni quite el candado de otra persona</strong>"],
   "callout":("<strong>1910.147:</strong> La energización inesperada es el peligro que mata. Si no puede identificar con certeza todas las fuentes de energía, no está listo para trabajar en eso.","danger")},

 "housekeeping": {"title":"Limpieza y Pasillos Despejados",
   "items":["<strong>Los pasillos y vías de paso se mantienen libres y sin obstrucción</strong> — siempre (OSHA 1910.176)",
            "<strong>Despeje el pasillo en cuanto vea un peligro</strong> — plástico estirable, flejes, madera, rollos de fleje",
            "<strong>Limpie los derrames de inmediato</strong> o delimite el área hasta que esté limpia",
            "<strong>El estado del piso importa:</strong> baches, bordes y escombros atrapan ruedas y tobillos",
            "<strong>No deje nada en las rutas de evacuación</strong> — las salidas se mantienen abiertas todo el tiempo",
            "<strong>La limpieza es deporte de equipo</strong> — si no es suyo, corríjalo o repórtelo"],
   "callout":("<strong>RECUERDE:</strong> Las caídas por resbalón, tropezón y caída son la lesión con tiempo perdido más común en un almacén — y casi todas empiezan con algo que quedó en el piso.","danger")},

 "aisle_safety": {"title":"Caminar y Trabajar en los Pasillos",
   "items":["<strong>Use su chaleco de alta visibilidad</strong> — obligatorio cuando hay equipo en operación",
            "<strong>Camine, no corra</strong> — y nunca tome atajos por un pasillo activo",
            "<strong>Sin audífonos ni teléfono en la oreja</strong> mientras se mueve por el almacén",
            "<strong>Teléfono en la mano = ojos abajo</strong> — deténgase y póngase en un espacio del pasillo primero",
            "<strong>Use una persona guía</strong> para espacios estrechos y aproximaciones ciegas",
            "<strong>Solo calzado adecuado</strong> — no sandalias, no pantuflas sueltas"],
   "callout":("<strong>CONSEJO:</strong> En un almacén la línea de visión es corta y los pasillos son estrechos. Tenga en cuenta que nadie lo ve hasta que ya está encima de usted.","tip")},

 "ppe": {"title":"Equipo de Protección Personal",
   "items":["<strong>Gafas de seguridad o gafas más protector facial</strong> en todas las áreas designadas",
            "<strong>Chaleco de alta visibilidad</strong> donde operen equipos motorizados",
            "<strong>Calzado con puntera de seguridad y antiderrapante</strong> — el único calzado permitido en el piso",
            "<strong>Guantes anticorte</strong> para flejes metálicos, banding y bordes afilados",
            "<strong>Guantes del tamaño correcto</strong> — no guantes sueltos y holgados (se enganchan y <em>reducen</em> el agarre)",
            "<strong>Casco</strong> donde haya trabajo encima de usted"],
   "callout":("<strong>DATO:</strong> Usar dos o más pares de guantes puede reducir su fuerza de agarre hasta un <strong>60%</strong>. El guante equivocado es peor que no usar guante.","tip")},

 "rubber_chemicals": {"title":"Caucho, Químicos y HDS (Hoja de Datos de Seguridad)",
   "items":["<strong>Conozca su HDS</strong> — están en la pared o en la aplicación, y toma 2 minutos abrir una",
            "<strong>Negro de humo y polvo de caucho</strong> — mantenga el área ventilada y el trabajo con polvo bajo control",
"<strong>Solventes, desengrasantes y reparadores de llantas:</strong> úselos solo en áreas <strong>ventiladas</strong>",
             "<strong>Revise la etiqueta y luego la HDS</strong> antes de cada tarea con químicos",
             "<strong>Lávese las manos</strong> antes de comer o salir del sitio",
            "<strong>Reporte de inmediato recipientes sin etiqueta</strong> y derrames"],
   "callout":("<strong>RECUERDE:</strong> Un producto sin HDS legible es un producto que usted no tiene derecho a usar. Pregunte a su supervisor.","tip")},

 "heat_cold": {"title":"Calor, Frío y Fatiga",
   "items":["<strong>Calor:</strong> agua, descanso y sombra antes de sentirse mal. Su decisión, sin preguntas",
            "<strong>Cuídense entre ustedes:</strong> dolor de cabeza, mareo, náuseas, sin sudor, confusión",
            "<strong>La enfermedad por calor es una emergencia médica</strong> — enfríe y pida ayuda de inmediato",
            "<strong>Trabajo-descanso</strong> importa más con calor — tome sus descansos aunque sienta que va atrasado",
            "<strong>Almacén frío:</strong> el agarre y la destreza bajan rápido; ajuste su ritmo y sus guantes",
            "<strong>La fatiga mata la atención.</strong> Si está desgastado, dígalo"],
   "callout":("<strong>PELIGRO:</strong> El agotamiento por calor puede volverse golpe de calor en minutos. Confusión o desmayo = emergencia. Enfríelo y busque ayuda médica AHORA.","danger")},

 "emergency": {"title":"Emergencias — Evacuación e Incendio",
   "items":["<strong>Conozca sus dos salidas más cercanas</strong> y el punto de reunión de su área",
            "<strong>Las rutas de salida se mantienen libres, siempre</strong> — nunca un palé, cincha o caja atravesada en una puerta",
            "<strong>Sepa dónde están la alarma, el extintor y el lavaojos</strong> de su zona",
            "<strong>Un incendio en un área de llantas es grave</strong> — el caucho quema caliente y por largo tiempo. Evacúe y avise",
            "<strong>INCENDIO DE CAUCHO O QUÍMICO:</strong> evacúe, cierre las puertas detrás de usted, nunca luche solo",
            "<strong>Reporte toda lesión y todo casi-accidente</strong> en el mismo turno"],
   "callout":("<strong>AUTORIDAD PARA DETENER EL TRABAJO:</strong> Cualquier empleado puede detener cualquier trabajo que considere inseguro — sin represalias, nunca. Si no se ve seguro, no lo es.","danger")},

 "near_miss": {"title":"Reporte de Casi-Accidentes — Lecciones Gratis",
   "short":["<strong>Repórtelo antes de que sea una lesión</strong> — un casi-accidente es una lección gratis",
            "<strong>Describa lo que VIO</strong>, no quién cree que se equivocó",
            "<strong>Sin culpas, sin represalias</strong> — nunca"],
   "items":["<strong>Un casi-accidente es una lección gratis</strong> — repórtelo antes de que sea una lesión",
            "<strong>Reporte:</strong> casi-accidentes, cortadillos, derrames, estanterías dañadas, casi-volcaduras, cargas caídas",
            "<strong>Describa lo que VIO</strong>, no quién cree que se equivocó",
            "<strong>Sin culpas, sin represalias</strong> — nunca. La culpa mata el reporte",
            "<strong>Reporte peligros aunque no sean suyos</strong>",
            "<strong>Hable durante la charla de seguridad</strong> — es el control de seguridad más fácil que tenemos"],
   "callout":("<strong>POR QUÉ IMPORTA:</strong> Las empresas que reportan casi-accidentes con frecuencia tienen <strong>menos</strong> lesiones, porque encuentran el peligro antes de que encuentre a alguien.","tip")},

 "inspection_discipline": {"title":"Defectos de Equipo — Etiquételo, Repórtelo",
   "items":["<strong>Cualquier montacargas, transpaleta o plataforma que se encuentre inseguro queda fuera de servicio</strong> hasta que se repare",
            "<strong>Póngale etiqueta de bloqueo</strong> y avise a su supervisor antes de irse",
            "<strong>Las reparaciones solo las hace personal autorizado</strong> — ni usted, ni su compañero",
            "<strong>Regístrelo</strong> para que el siguiente operador lo sepa — el historial de defectos sigue al equipo",
            "<strong>Nunca &ldquo;termine el turno nomás&rdquo;</strong> en equipo que sabe que está dañado",
            "<strong>Las baterías que necesiten reparación se desconectan primero</strong>"],
   "callout":("<strong>RECUERDE:</strong> La hoja de inspección no es papeleo — es la razón por la que el operador del siguiente turno encuentra el problema antes de subirse.","tip")},

 "traffic_rules": {"title":"Reglas de Tráfico y Velocidad del Almacén",
   "stat_cards":[("5 mph","Máx. en pasillo, salvo letrero menor"),("Claxon","Toque en puntos ciegos")],
   "items":["<strong>Respete el límite de velocidad indicado</strong> — en almacenes suele ser 5 mph, no 25",
            "<strong>Reduzca hasta parar</strong> en intersecciones, esquinas ciegas y puertas",
            "<strong>Toque el claxon</strong> en cruces de pasillo y donde la visibilidad esté obstruida",
            "<strong>Los peatones y el equipo de emergencia siempre tienen preferencia</strong>",
            "<strong>Obedezca todas las señales y marcas del piso</strong> — los pasillos de un sentido son de un sentido",
            "<strong>Sin pasajeros en montacargas, transpaletas o carritos</strong> — nunca"],
   "callout":("<strong>OSHA 1910.178(n):</strong> Reduzca la velocidad y toque el claxon en cruces de pasillo y donde la visibilidad esté obstruida. Viaje a una velocidad que le permita <strong>parar con seguridad</strong>.","danger")},
}

TEXT_KEYS = ("title","items","checklist","short","callout","stat_cards","columns")


def localized(lang):
    """Return the full topic pool in `lang`.

    Icons, colours and layout come from the English entries; only TEXT_KEYS are
    replaced from TOPICS_ES, so a missing or partial translation degrades to
    English for that field instead of dropping the section.
    """
    if lang == "en":
        return list(TOPICS)
    if lang != "es":
        raise ValueError(f"unknown language: {lang!r}")
    missing = [t["id"] for t in TOPICS if t["id"] not in TOPICS_ES]
    if missing:
        raise ValueError(f"Spanish pool is missing topics: {', '.join(missing)}")
    out = []
    for t in TOPICS:
        es = TOPICS_ES[t["id"]]
        m = dict(t)
        for k in TEXT_KEYS:
            if k in es:
                m[k] = es[k]
        out.append(m)
    return out


def topic_by_id(lang):
    return {t["id"]: t for t in localized(lang)}


TOPIC_BY_ID = {t["id"]: t for t in TOPICS}

CSS = """
@page{size:letter;margin:0.5in}
@media print{
  body{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  /* Print-only breathing room.  Measured sheet heights @748px (the printable
     width of US Letter at Chrome's default 0.4in margins) peaked at 1002px
     against 979px of printable height, so weeks 1 and 10 spilled a line onto
     page 2 and week 15 cleared by only 3px -- far too tight for a printer
     with larger non-printable margins.  These five trims recover ~69px. */
  .header{padding:6px 18px}
  .section{margin-bottom:1px}
  .section-body{padding:1px 8px 2px}
  ul li{margin-bottom:0}
  .bottom-strip{margin-top:3px}
  .section-header{padding:2px 8px}
  .tip-box,.danger-box{padding:2px 8px;margin-top:2px}
  .footer{padding:2px 12px;margin-top:3px}
  .stat-row{margin-top:2px}
  .bottom-strip>div{padding:3px 7px}
  .bottom-strip ul{font-size:8.6px}
  .bottom-strip strong{font-size:8.6px}
  /* one pane per language; "print both" is a 2-page bilingual sheet */
  .tabs{display:none !important}
  .pane{display:none !important}
  .pane.on{display:block !important}
  body.print-both .pane{display:block !important}
  body.print-both .pane#pane-en{page-break-after:always}
}
*{box-sizing:border-box;margin:0;padding:0}
/* 10px / 1.25 rather than 10.5px / 1.3: the Spanish pool runs ~15% longer than
   the English, and at the larger setting every one of the 32 Spanish weeks
   spilled onto page 2 (worst case 1008px against 960px of printable height).
   Applied to BOTH languages so the two sheets stay visually identical, and on
   screen as well as print so what you preview is what comes out of the printer. */
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;color:#1a1a2e;background:#fff;line-height:1.25;font-size:10px}
.header{background:linear-gradient(135deg,#0b1120 0%,#1b2b4a 100%);color:#fff;padding:8px 18px;display:flex;align-items:center;gap:12px;border-radius:7px;margin-bottom:6px}
.header img{height:38px;width:auto;border-radius:5px}
.header-text h1{font-size:15px;font-weight:700;letter-spacing:0.5px}
.header-text .subtitle{font-size:9.5px;opacity:0.8;margin-top:1px}
.header .date-box{margin-left:auto;text-align:right;font-size:9.5px;opacity:0.85}
.header .date-box .date{font-size:14px;font-weight:600}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.section{margin-bottom:5px;border:1.5px solid #e2e8f0;border-radius:5px;overflow:hidden}
.section-header{padding:3px 8px;font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:0.8px;display:flex;align-items:center;gap:5px}
.section-body{padding:3px 8px 4px}
.s-blue .section-header{background:#dbeafe;color:#1e40af;border-bottom:1.5px solid #bfdbfe}
.s-red .section-header{background:#fee2e2;color:#991b1b;border-bottom:1.5px solid #fecaca}
.s-green .section-header{background:#dcfce7;color:#166534;border-bottom:1.5px solid #bbf7d0}
.s-amber .section-header{background:#fef3c7;color:#92400e;border-bottom:1.5px solid #fde68a}
.s-purple .section-header{background:#f3e8ff;color:#6b21a8;border-bottom:1.5px solid #e9d5ff}
.s-slate .section-header{background:#f1f5f9;color:#334155;border-bottom:1.5px solid #cbd5e1}
ul{padding-left:14px}li{margin-bottom:1px}
.stat-row{display:flex;gap:6px;margin-top:3px}
.stat-card{flex:1;background:#f8fafc;border:1px solid #e2e8f0;border-radius:4px;padding:3px 6px;text-align:center}
.stat-card .num{font-size:15px;font-weight:800;color:#0b1120}
.stat-card .label{font-size:7.5px;text-transform:uppercase;letter-spacing:0.5px;color:#64748b;margin-top:0}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}
.checklist{list-style:none;padding:0}.checklist li{padding:2px 0 2px 20px;position:relative}
.checklist li::before{content:'';position:absolute;left:0;top:3px;width:12px;height:12px;border:1.5px solid #94a3b8;border-radius:3px;background:#fff}
.tip-box{background:#fffbeb;border-left:3px solid #f59e0b;padding:3px 8px;border-radius:0 4px 4px 0;margin-top:3px;font-size:9.5px}
.tip-box strong{color:#92400e}
.danger-box{background:#fef2f2;border-left:3px solid #dc2626;padding:3px 8px;border-radius:0 4px 4px 0;margin-top:3px;font-size:9.5px}
.danger-box strong{color:#991b1b}
.bottom-strip{display:flex;gap:6px;margin-top:4px}
.bottom-strip>div{flex:1;border-radius:5px;padding:4px 8px}
.bottom-strip strong{font-size:9px;text-transform:uppercase;letter-spacing:0.5px}
.bottom-strip ul{font-size:9.5px}
.footer{margin-top:5px;padding:4px 12px;background:#f1f5f9;border-radius:5px;text-align:center;font-size:9px;color:#64748b}
.footer strong{color:#1e40af}
/* ---- language tabs: screen-only chrome around two printable panes ---- */
.tabs{display:flex;gap:6px;margin:0 0 6px}
.tabs button{font:600 11px/1 'Segoe UI',system-ui,sans-serif;padding:6px 16px;
  border:1.5px solid #cbd5e1;background:#fff;color:#334155;border-radius:5px;cursor:pointer}
.tabs button.on{background:#0b1120;color:#fff;border-color:#0b1120}
.pane{display:none}
.pane.on{display:block}
"""


def select_topics(week_num, lang="en"):
    """Six rotating sections plus the three always-on bottom cards.

    The rotating window walks forward from a week-derived start index and skips
    the BOTTOM_IDS, so a topic that is already printed on every sheet never
    also burns one of the six rotating slots (15 of 32 weeks did before).
    """
    pool = localized(lang)
    by_id = {t["id"]: t for t in pool}
    n = len(pool)
    picked, i = [], 0
    while len(picked) < 6:
        t = pool[(week_num * ROTATION_STEP + i) % n]
        if t["id"] not in BOTTOM_IDS:
            picked.append(t)
        i += 1
        if i > n:                      # pool too small to fill six slots
            raise RuntimeError("not enough non-bottom topics to fill the sheet")
    left, right, bottom = picked[:3], picked[3:], [by_id[b] for b in BOTTOM_IDS]
    return left, right, bottom


def render_section(topic):
    c = topic.get("color","s-blue")
    ic = topic.get("icon","&#9679;")
    t = topic["title"]
    lines = [f'<div class="section {c}">',f'  <div class="section-header">{ic} {t}</div>',
             f'  <div class="section-body">']
    if "checklist" in topic:
        lines.append('    <ul class="checklist">')
        for i in topic["checklist"]: lines.append(f'      <li>{i}</li>')
        lines.append('    </ul>')
    elif "items" in topic:
        lines.append('    <ul>')
        for i in topic["items"]: lines.append(f'      <li>{i}</li>')
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
        txt,bt = topic["callout"]
        cls = "tip-box" if bt=="tip" else "danger-box"
        lines.append(f'    <div class="{cls}">{txt}</div>')
    lines += ['  </div>','</div>']
    return "\n".join(lines)


def render_bottom_card(topic):
    cmap = {"s-blue":("#1e40af","#eff6ff","#bfdbfe"),"s-red":("#991b1b","#fef2f2","#fecaca"),
            "s-green":("#166534","#f0fdf4","#bbf7d0"),"s-amber":("#92400e","#fefce8","#fde68a"),
            "s-purple":("#6b21a8","#faf5ff","#e9d5ff"),"s-slate":("#334155","#f1f5f9","#cbd5e1")}
    tc,bg,bd = cmap.get(topic.get("color","s-slate"),("#334155","#f1f5f9","#cbd5e1"))
    ic = topic.get("icon","&#9679;")
    t = topic["title"]
    lines = [f'<div style="flex:1;background:{bg};border:1.5px solid {bd};border-radius:5px;padding:4px 8px">',
             f'  <strong style="color:{tc};font-size:9px;text-transform:uppercase;letter-spacing:0.5px;">{ic} {t}</strong>',
             '  <ul style="margin-top:2px">']
    for i in topic.get("short") or topic.get("items",topic.get("checklist",[])):
        lines.append(f'    <li>{i}</li>')
    lines += ['  </ul>','</div>']
    return "\n".join(lines)


def week_dates(week_num, year=None):
    """Monday..Friday for an ISO week, and the year that week belongs to."""
    if year is None:
        year = datetime.date.today().year
    jan4 = datetime.date(year, 1, 4)
    start_w1 = jan4 - datetime.timedelta(days=jan4.weekday())
    monday = start_w1 + datetime.timedelta(weeks=week_num-1)
    return monday, monday + datetime.timedelta(days=4)


def render_sheet(week_num, lang, logo_b64, monday, friday):
    """One complete printable sheet in `lang` (header + sections + strip + footer)."""
    strings = LANG[lang]
    left, right, bottom = select_topics(week_num, lang)
    sections_html = "\n".join(render_section(t) for t in left)
    sections_html_r = "\n".join(render_section(t) for t in right)
    bottom_html = "\n".join(render_bottom_card(t) for t in bottom)
    month = MONTHS[lang][monday.month - 1]
    return f"""<div class="header">
  <img src="data:image/jpeg;base64,{logo_b64}" alt="U.S. AutoForce">
  <div class="header-text">
    <h1>{strings['h1']}</h1>
    <div class="subtitle">{strings['subtitle']}</div>
  </div>
  <div class="date-box">
    <div class="date">{LANG[lang]['week']} {week_num}</div>
    <div>{month} {monday.strftime('%d')} &mdash; {friday.strftime('%d, %Y')}</div>
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
  <strong>U.S. AutoForce</strong> &middot; {strings['ops']} &middot; Safety is Not a Priority &mdash; It's a Prerequisite &middot; {strings['footer_lead']}
</div>"""


# Screen-only tab switcher.  The generated sheet is a static file, so this is the
# one bit of behaviour it needs; printing is pure CSS (see the print block).
TAB_JS = """<script>
document.querySelectorAll('.tabs button').forEach(function(b){
  b.addEventListener('click', function(){
    document.querySelectorAll('.tabs button').forEach(function(x){x.classList.remove('on')});
    document.querySelectorAll('.pane').forEach(function(p){p.classList.remove('on')});
    b.classList.add('on');
    document.getElementById('pane-' + b.dataset.lang).classList.add('on');
  });
});
</script>"""


def generate(week_num=None, preview=False, lang="en"):
    if week_num is None:
        week_num = datetime.date.today().isocalendar()[1]
    if lang not in ("en", "es", "both"):
        raise ValueError(f"--lang must be en, es or both (got {lang!r})")
    monday, friday = week_dates(week_num)
    active = "en" if lang == "both" else lang
    logo_b64 = open(LOGO_B64_FILE).read().strip()

    panes = []
    for code in PRINT_ORDER:
        cls = "pane on" if code == active else "pane"
        if lang == "both":
            cls += " on"
        panes.append(f'<div class="{cls}" id="pane-{code}" lang="{code}">\n'
                     + render_sheet(week_num, code, logo_b64, monday, friday) + "\n</div>")
    tabs = ('<div class="tabs" role="tablist">'
            + "".join(f'<button type="button" data-lang="{c}" class="{"on" if c == active else ""}">'
                      f'{TAB_LABELS[c]}</button>' for c in PRINT_ORDER)
            + "</div>")

    html = f"""<!DOCTYPE html>
<html lang="{active}"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>U.S. AutoForce &mdash; {LANG[active]['h1']} Week {week_num}</title>
<style>{CSS}</style></head><body class="{"print-both" if lang == "both" else ""}">
{tabs}
{"".join(panes)}
{TAB_JS}
</body></html>"""

    os.makedirs(DESKTOP, exist_ok=True)
    suffix = "" if lang == "en" else f"-{lang}"
    stem = f"warehouse-safety-huddle-wk{week_num:02d}{suffix}"
    html_path = os.path.join(DESKTOP, stem + ".html")
    pdf_path = os.path.join(DESKTOP, stem + ".pdf")
    with open(html_path, "w") as f:
        f.write(html)
    print(f"HTML: {html_path}")

    r = subprocess.run(["google-chrome","--headless","--no-sandbox","--disable-gpu",
                        f"--print-to-pdf={pdf_path}","--no-pdf-header-footer",
                        f"file://{html_path}"], capture_output=True, text=True, timeout=60)
    if os.path.exists(pdf_path):
        print(f"PDF:  {pdf_path}")
    else:
        print(f"PDF generation failed: {r.stderr[:200]}")

    if preview:
        import webbrowser
        webbrowser.open(f"file://{html_path}")

    for code in PRINT_ORDER:
        left, right, _ = select_topics(week_num, code)
        print(f"\nWeek {week_num} — {TAB_LABELS[code]}:")
        for i, t in enumerate(left + right, 1):
            print(f"  {i}. {t['title']}")
    return html_path, pdf_path


def cmd_list(args):
    pool_es = {t["id"]: t for t in localized("es")}
    print(f"Topic Pool ({len(TOPICS)} topics, English / Español):\n")
    for i, t in enumerate(TOPICS, 1):
        print(f"  {i:2d}. {t['title']}")
        print(f"      ES: {pool_es[t['id']]['title']}")
    print(f"\nRotation: 6 topics per week (3 left + 3 right) + "
          f"{'/'.join(BOTTOM_IDS)} always in the bottom strip")
    import math
    cycle = len(TOPICS) // math.gcd(ROTATION_STEP, len(TOPICS))
    print(f"Covers {cycle} unique weeks before repeating.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--week","-w",type=int,help="ISO week number (default: this week)")
    p.add_argument("--lang","-b",choices=("en","es","both"),default="en",
                   help="language tab to open; 'both' also prints a 2-page bilingual PDF")
    p.add_argument("--list","-l",action="store_true",help="list all topics in both languages")
    p.add_argument("--preview",action="store_true",help="open in browser after generating")
    args = p.parse_args()
    if args.list:
        cmd_list(args)
    else:
        generate(args.week, args.preview, args.lang)


if __name__ == "__main__":
    main()