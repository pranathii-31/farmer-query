"""
init_db.py — Create and seed the Farmer Query Engine SQLite database.

Run once (from the `backend/` directory):
    python database/init_db.py

Re-running is safe: all INSERTs use INSERT OR IGNORE to avoid duplicates.
"""

import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'farmer.db')
SCHEMA   = os.path.join(os.path.dirname(__file__), 'schema.sql')


def init_db():
    conn = sqlite3.connect(DATABASE)
    cur  = conn.cursor()

    # ── Schema ────────────────────────────────────────────────────────────
    with open(SCHEMA, 'r') as f:
        cur.executescript(f.read())

    # ── Diseases ──────────────────────────────────────────────────────────
    diseases = [
        ('Blight',                    'Apply copper fungicide',               'Use balanced NPK fertilizer',           'Ensure proper spacing and ventilation'),
        ('Late Blight',               'Apply copper fungicide',               'Use balanced NPK fertilizer',           'Ensure proper spacing and ventilation'),
        ('Early Blight',              'Apply chlorothalonil fungicide',        'Apply calcium-rich fertilizer',         'Remove lower infected leaves; avoid overhead irrigation'),
        ('Rust',                      'Remove infected leaves; apply sulfur',  'Apply sulfur-based fungicide',          'Avoid overhead watering; plant resistant varieties'),
        ('Powdery Mildew',            'Spray baking soda + neem oil solution', 'Use potassium-rich fertilizer',         'Improve air circulation; reduce humidity'),
        ('Downy Mildew',              'Apply Mancozeb or Fosetyl-Al',         'Use potassium-rich fertilizer',         'Improve air circulation; avoid wet foliage'),
        ('Fusarium Wilt',             'Remove & destroy infected plants',      'Use resistant varieties',               'Rotate crops every 3–4 years; solarize soil'),
        ('Bacterial Spot',            'Apply copper-based bactericide',        'Use balanced fertilizer',               'Avoid wet conditions; remove infected debris'),
        ('Anthracnose',               'Remove infected parts; apply fungicide','Apply balanced NPK (10-10-10)',         'Improve drainage; avoid fruit injury'),
        ('Alternaria Leaf Spot',      'Apply Mancozeb fungicide',             'Use balanced NPK (10-10-10)',           'Avoid overhead irrigation; remove infected debris'),
        ('Cercospora Leaf Spot',      'Apply copper fungicide',               'Use balanced fertilizer',               'Improve air circulation; rotate crops'),
        ('Septoria Leaf Spot',        'Apply chlorothalonil fungicide',        'Use balanced fertilizer',               'Remove infected leaves; avoid overhead watering'),
        ('Black Spot',                'Apply fungicide; prune infected parts', 'Use balanced fertilizer',               'Prune for airflow; avoid wetting leaves'),
        ('Gray Mold',                 'Apply Botryticide; improve ventilation','Use balanced fertilizer',               'Reduce humidity; remove dead plant matter'),
        ('Root Rot',                  'Improve drainage; apply Metalaxyl',    'Use fungicide-treated seeds',            'Avoid overwatering; plant in raised beds'),
        ('Damping Off',               'Use sterile soil; apply Thiram',       'Apply Trichoderma bio-fungicide',       'Ensure good drainage; avoid overcrowding'),
        ('Verticillium Wilt',         'Remove infected plants; solarize soil', 'Use resistant varieties',               'Rotate crops; avoid water stress'),
        ('Fungal Leaf Spot',          'Apply appropriate fungicide',          'Use balanced fertilizer',               'Remove infected leaves; improve air flow'),
        ('Bacterial Wilt',            'Remove infected plants immediately',   'Apply bactericide drench',              'Control cucumber beetle vectors; rotate crops'),
        ('Mosaic Virus',              'Remove & destroy infected plants',     'Use virus-free certified seeds',        'Control aphid/whitefly vectors; use reflective mulch'),
        ('Cucumber Mosaic Virus',     'Remove infected plants',               'Use virus-free seeds',                  'Control aphid populations; use resistant varieties'),
        ('Tobacco Mosaic Virus',      'Remove infected plants; disinfect tools','Use virus-free seeds',                'Wash hands before handling plants'),
        ('Yellow Mosaic Virus',       'Remove infected plants',               'Use virus-free seeds',                  'Control whitefly with yellow sticky traps'),
        ('Leaf Curl Virus',           'Remove infected plants',               'Use virus-free seeds',                  'Control insect vectors; use reflective mulch'),
        ('Tomato Yellow Leaf Curl Virus','Remove infected plants',            'Use virus-free seeds',                  'Control whiteflies; plant resistant varieties'),
        ('Potato Virus Y',            'Remove infected plants',               'Use certified seed potatoes',           'Control aphid vectors; use resistant varieties'),
        ('Bean Common Mosaic Virus',  'Remove infected plants',               'Use virus-free seeds',                  'Control aphid populations'),
        ('Squash Mosaic Virus',       'Remove infected plants',               'Use virus-free seeds',                  'Control cucumber beetle vectors'),
        ('Watermelon Mosaic Virus',   'Remove infected plants',               'Use virus-free seeds',                  'Control aphid populations'),
        ('Zucchini Yellow Mosaic Virus','Remove infected plants',             'Use virus-free seeds',                  'Control aphid populations'),
        ('Cabbage Looper',            'Apply Bt (Bacillus thuringiensis)',     'Use balanced fertilizer',               'Monitor with pheromone traps'),
        ('Aphid',                     'Spray neem oil or insecticidal soap',  'Use balanced fertilizer',               'Introduce ladybugs; use reflective mulch'),
        ('Whitefly',                  'Apply insecticidal soap; use yellow traps','Use balanced fertilizer',           'Use reflective mulch; introduce natural predators'),
        ('Thrips',                    'Apply spinosad insecticide',           'Use balanced fertilizer',               'Remove weeds; use blue sticky traps'),
        ('Spider Mite',               'Apply miticide or neem oil',           'Use balanced fertilizer',               'Increase humidity; introduce predatory mites'),
        ('Cutworm',                   'Apply soil insecticide; use collars',  'Use balanced fertilizer',               'Use physical collars around plant bases'),
        ('Corn Earworm',              'Apply Bt at silking stage',            'Use balanced fertilizer',               'Monitor with pheromone traps; apply mineral oil to silk'),
        ('Tomato Hornworm',           'Hand-pick larvae; apply Bt',           'Use balanced fertilizer',               'Encourage parasitic wasps as natural predators'),
        ('Flea Beetle',               'Apply kaolin clay; use row covers',    'Use balanced fertilizer',               'Use row covers on young plants'),
        ('Colorado Potato Beetle',    'Apply Bt tenebrionis; hand-pick',      'Use balanced fertilizer',               'Rotate crops; use mulch to deter adults'),
        ('Mexican Bean Beetle',       'Apply insecticide; hand-pick larvae',  'Use balanced fertilizer',               'Remove debris; introduce parasitic wasps'),
        ('Squash Bug',                'Apply insecticide; remove egg masses', 'Use balanced fertilizer',               'Check undersides of leaves for eggs'),
        ('Stink Bug',                 'Apply insecticide at edges',           'Use balanced fertilizer',               'Monitor populations; use kaolin clay'),
        ('Leafhopper',                'Apply insecticidal soap',              'Use balanced fertilizer',               'Remove weeds; use reflective mulch'),
        ('Scale Insect',              'Apply horticultural oil in dormancy',  'Use balanced fertilizer',               'Prune infested branches; introduce natural predators'),
        ('Mealybug',                  'Apply neem oil or insecticidal soap',  'Use balanced fertilizer',               'Isolate infested plants; introduce ladybugs'),
        ('Root Knot Nematode',        'Apply Carbofuran nematicide',         'Use neem cake soil amendment',          'Rotate with non-host crops; plant resistant varieties'),
        ('Cyst Nematode',             'Apply nematicide; solarize soil',      'Use resistant varieties',               'Rotate crops; avoid moving contaminated soil'),
        ('Lesion Nematode',           'Apply nematicide',                    'Use resistant varieties',               'Improve soil drainage; rotate crops'),
        ('Stubby Root Nematode',      'Apply nematicide',                    'Use resistant varieties',               'Avoid contaminated soil and equipment'),
        ('Ditylenchus Nematode',      'Apply nematicide; use clean seed',    'Use resistant varieties',               'Avoid wet conditions; use certified seed'),
    ]
    cur.executemany(
        'INSERT OR IGNORE INTO diseases (name, treatment, fertilizer, prevention) VALUES (?, ?, ?, ?)',
        diseases
    )

    # ── Yojnas ────────────────────────────────────────────────────────────
    # Each row: (name, crop, state, disease, description, link)
    # Rules applied:
    #   • crop=None  → scheme applies to ALL crops for that state
    #   • state=None → scheme is national (all states)
    #   • disease    → scheme is relevant when this disease is detected
    #   • Unique per (name, crop, state, disease) — no duplicate scheme names for same context
    yojnas = [
        # ── National income-support (all crops, all states) ──────────────
        (
            'PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)',
            None, None, None,
            'Provides ₹6,000/year direct income support to all small & marginal farmers in three equal instalments.',
            'https://pmkisan.gov.in/'
        ),

        # ── Crop insurance ────────────────────────────────────────────────
        (
            'Pradhan Mantri Fasal Bima Yojana (PMFBY)',
            None, None, 'blight',
            'Covers crop losses due to fungal diseases including Blight. Premium: 2% for Kharif, 1.5% for Rabi crops.',
            'https://pmfby.gov.in/'
        ),
        (
            'Pradhan Mantri Fasal Bima Yojana (PMFBY)',
            None, None, 'rust',
            'Covers crop losses due to Rust disease. Premium: 2% for Kharif, 1.5% for Rabi crops.',
            'https://pmfby.gov.in/'
        ),
        (
            'Pradhan Mantri Fasal Bima Yojana (PMFBY)',
            None, None, 'powdery mildew',
            'Covers crop losses due to Powdery Mildew. Premium: 2% for Kharif, 1.5% for Rabi crops.',
            'https://pmfby.gov.in/'
        ),
        (
            'Pradhan Mantri Fasal Bima Yojana (PMFBY)',
            None, None, None,
            'Comprehensive crop insurance scheme covering losses from natural calamities, pests and diseases.',
            'https://pmfby.gov.in/'
        ),

        # ── Soil health ───────────────────────────────────────────────────
        (
            'Soil Health Card Scheme',
            None, None, None,
            'Provides farmers a Soil Health Card with crop-wise recommendations for fertilizer dosage to improve productivity.',
            'https://soilhealth.dac.gov.in/'
        ),

        # ── Digital market ────────────────────────────────────────────────
        (
            'National Agriculture Market (eNAM)',
            None, None, None,
            'Online trading portal for agricultural commodities — enables farmers to get pan-India market prices.',
            'https://enam.gov.in/'
        ),

        # ── Organic farming ───────────────────────────────────────────────
        (
            'Paramparagat Krishi Vikas Yojana (PKVY)',
            None, None, None,
            'Promotes organic farming through cluster approach; provides ₹50,000/ha over 3 years for organic inputs.',
            'https://pgsindia-ncof.gov.in/pkvy/Index.aspx'
        ),

        # ── Irrigation ────────────────────────────────────────────────────
        (
            'Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)',
            None, None, None,
            '"Har Khet Ko Pani" — expands irrigation coverage and improves water-use efficiency (drip/sprinkler subsidy).',
            'https://pmksy.gov.in/'
        ),

        # ── Credit ────────────────────────────────────────────────────────
        (
            'Kisan Credit Card (KCC)',
            None, None, None,
            'Short-term credit for crop cultivation expenses, post-harvest, and allied activities at subsidised interest rates.',
            'https://www.nabard.org/content.aspx?id=572'
        ),

        # ── Technology / extension ────────────────────────────────────────
        (
            'Digital Agriculture Mission',
            None, None, None,
            'Builds AgriStack digital infrastructure — Farmer Registry, Crop Sown Registry — to deliver targeted government services.',
            'https://agricoop.nic.in/en/digital-agriculture'
        ),

        # ── Pest / disease specific ───────────────────────────────────────
        (
            'National Plant Protection Training Institute (NPPTI) Advisory',
            None, None, 'aphid',
            'Free pest-management training and advisories for aphid-affected crops. Contact your district NPPTI centre.',
            'https://nppti.gov.in/'
        ),
        (
            'National Plant Protection Training Institute (NPPTI) Advisory',
            None, None, 'whitefly',
            'Free pest-management training and advisories for whitefly-affected crops. Contact your district NPPTI centre.',
            'https://nppti.gov.in/'
        ),
        (
            'National Plant Protection Training Institute (NPPTI) Advisory',
            None, None, 'root rot',
            'Free soil-borne disease management advisories. Contact your district NPPTI centre.',
            'https://nppti.gov.in/'
        ),

        # ── Crop-specific ─────────────────────────────────────────────────
        (
            'National Food Security Mission (NFSM) — Wheat',
            'wheat', None, None,
            'Increases wheat production through area expansion and productivity enhancement; provides seed and input subsidies.',
            'https://nfsm.gov.in/'
        ),
        (
            'National Food Security Mission (NFSM) — Rice',
            'rice', None, None,
            'Promotes high-yielding rice varieties and good agronomic practices; provides seed mini-kits and training.',
            'https://nfsm.gov.in/'
        ),
        (
            'National Food Security Mission (NFSM) — Pulses',
            'beans', None, None,
            'Supports pulse-crop extension with certified seeds, micro-nutrients and IPM demonstrations.',
            'https://nfsm.gov.in/'
        ),
        (
            'Cotton Development Programme',
            'cotton', None, None,
            'Provides seed subsidies, IPM training and technology demonstrations for cotton growers.',
            'https://agricoop.nic.in/'
        ),
        (
            'National Horticulture Mission (NHM)',
            'tomato', None, None,
            'Capital subsidy (40–50%) for protected horticulture, post-harvest management, and vegetable cluster development.',
            'https://nhb.gov.in/'
        ),
        (
            'National Horticulture Mission (NHM)',
            'potato', None, None,
            'Capital subsidy for cold storage, packaging, and market infrastructure for potato growers.',
            'https://nhb.gov.in/'
        ),
        (
            'National Horticulture Mission (NHM)',
            'pumpkin', None, None,
            'Supports vegetable and cucurbit cluster development with input and infrastructure subsidies.',
            'https://nhb.gov.in/'
        ),
        (
            'National Horticulture Mission (NHM)',
            'maize', None, None,
            'Demonstration programmes for hybrid maize with input subsidies and farmer training.',
            'https://nhb.gov.in/'
        ),

        # ── State-specific ────────────────────────────────────────────────
        (
            'Karnataka Raitha Siri Scheme',
            None, 'karnataka', None,
            "Karnataka's farmer welfare scheme providing additional income support on top of PM-KISAN.",
            'https://raitamitra.karnataka.gov.in/'
        ),
        (
            'Mahadbt (Maharashtra Farmer Subsidy Portal)',
            None, 'maharashtra', None,
            'Single portal for all Maharashtra state agricultural subsidies — seeds, fertilizers, equipment.',
            'https://mahadbt.maharashtra.gov.in/'
        ),
        (
            'Punjab Agriculture Department — Krishi Mela',
            None, 'punjab', None,
            "Punjab's seasonal farmer fair offering free soil testing, seed distribution and technology demonstrations.",
            'https://agripb.gov.in/'
        ),
        (
            "Tamil Nadu CM's Farmers Relief Fund",
            None, 'tamil nadu', None,
            'Compensation for crop-loss due to natural calamities and disease outbreaks in Tamil Nadu.',
            'https://www.tn.gov.in/agriculture/'
        ),
    ]

    cur.executemany(
        'INSERT OR IGNORE INTO yojnas (name, crop, state, disease, description, link) VALUES (?, ?, ?, ?, ?, ?)',
        yojnas
    )

    # ── Centers ───────────────────────────────────────────────────────────
    centers = [
        ('Krishi Vigyan Kendra Bangalore',           12.9716,  77.5946, 'Bangalore Rural District, Karnataka'),
        ('Agricultural Extension Center Mysore',     12.2958,  76.6394, 'Mysore District, Karnataka'),
        ('Farmers Training Center Hubli',            15.3647,  75.1240, 'Dharwad District, Karnataka'),
        ('Krishi Vigyan Kendra Pune',                18.5204,  73.8567, 'Pune District, Maharashtra'),
        ('Agricultural Extension Center Mumbai',     19.0760,  72.8777, 'Mumbai Suburban District, Maharashtra'),
        ('Farmers Training Center Nagpur',           21.1458,  79.0882, 'Nagpur District, Maharashtra'),
        ('Krishi Vigyan Kendra Delhi',               28.7041,  77.1025, 'New Delhi'),
        ('Agricultural Extension Center Jaipur',    26.9124,  75.7873, 'Jaipur District, Rajasthan'),
        ('Farmers Training Center Chandigarh',       30.7333,  76.7794, 'Chandigarh'),
        ('Krishi Vigyan Kendra Lucknow',             26.8467,  80.9462, 'Lucknow District, Uttar Pradesh'),
        ('Agricultural Extension Center Kanpur',    26.4499,  80.3319, 'Kanpur District, Uttar Pradesh'),
        ('Farmers Training Center Patna',            25.5941,  85.1376, 'Patna District, Bihar'),
        ('Krishi Vigyan Kendra Kolkata',             22.5726,  88.3639, 'Kolkata, West Bengal'),
        ('Agricultural Extension Center Bhubaneswar',20.2961,  85.8245, 'Khordha District, Odisha'),
        ('Farmers Training Center Hyderabad',        17.3850,  78.4867, 'Hyderabad District, Telangana'),
        ('Krishi Vigyan Kendra Chennai',             13.0827,  80.2707, 'Chennai District, Tamil Nadu'),
        ('Agricultural Extension Center Coimbatore', 11.0168,  76.9558, 'Coimbatore District, Tamil Nadu'),
        ('Farmers Training Center Thiruvananthapuram',8.5241,  76.9366, 'Thiruvananthapuram District, Kerala'),
        ('Krishi Vigyan Kendra Ahmedabad',           23.0225,  72.5714, 'Ahmedabad District, Gujarat'),
        ('Agricultural Extension Center Surat',     21.1702,  72.8311, 'Surat District, Gujarat'),
        ('Farmers Training Center Vadodara',         22.3072,  73.1812, 'Vadodara District, Gujarat'),
        ('Krishi Vigyan Kendra Indore',              22.7196,  75.8577, 'Indore District, Madhya Pradesh'),
        ('Agricultural Extension Center Bhopal',    23.2599,  77.4126, 'Bhopal District, Madhya Pradesh'),
        ('Farmers Training Center Jabalpur',         23.1815,  79.9864, 'Jabalpur District, Madhya Pradesh'),
        ('Krishi Vigyan Kendra Guwahati',            26.1445,  91.7362, 'Kamrup Metropolitan District, Assam'),
        ('Agricultural Extension Center Shillong',  25.5788,  91.8933, 'East Khasi Hills District, Meghalaya'),
        ('Farmers Training Center Imphal',           24.8170,  93.9368, 'Imphal West District, Manipur'),
        ('Krishi Vigyan Kendra Gangtok',             27.3314,  88.6138, 'East Sikkim District, Sikkim'),
        ('Agricultural Extension Center Agartala',  23.8315,  91.2868, 'West Tripura District, Tripura'),
        ('Farmers Training Center Aizawl',           23.7271,  92.7176, 'Aizawl District, Mizoram'),
        ('Krishi Vigyan Kendra Kohima',              25.6586,  94.1053, 'Kohima District, Nagaland'),
        ('Agricultural Extension Center Itanagar',  27.0844,  93.6053, 'Papum Pare District, Arunachal Pradesh'),
        ('Farmers Training Center Panaji',           15.4909,  73.8278, 'North Goa District, Goa'),
        ('Krishi Vigyan Kendra Puducherry',          11.9416,  79.8083, 'Puducherry'),
        ('Agricultural Extension Center Port Blair', 11.6234,  92.7265, 'South Andaman District'),
        ('Farmers Training Center Leh',              34.1526,  77.5771, 'Leh District, Ladakh'),
        ('Krishi Vigyan Kendra Kargil',              34.5539,  76.1349, 'Kargil District, Ladakh'),
    ]
    cur.executemany(
        'INSERT OR IGNORE INTO centers (name, latitude, longitude, address) VALUES (?, ?, ?, ?)',
        centers
    )

    # ── Crop health tips ─────────────────────────────────────────────────
    tips = [
        ('wheat',         'Ensure proper irrigation, monitor for Rust and Blight, rotate crops annually, test soil before sowing'),
        ('rice',          'Maintain water levels at 2–5 cm, use organic fertilizers, control weeds in early stages, monitor for Bacterial Blight'),
        ('cotton',        'Prune suckers regularly, apply pesticides before boll weevil peak, test soil pH (target 5.8–8.0)'),
        ('pumpkin',       'Provide at least 1.5 m of space per plant, monitor for powdery mildew, ensure well-draining soil, mulch to retain moisture'),
        ('maize',         'Maintain 60–75 cm row spacing, apply nitrogen at knee-high stage, scout for Fall Armyworm and Corn Earworm'),
        ('tomato',        'Stake or cage plants early, prune suckers for indeterminate types, rotate crops every 2 years, monitor for Late Blight'),
        ('potato',        'Hill soil around stems 2–3 times, monitor for Early and Late Blight, harvest before frost, cure tubers before storage'),
        ('onion',         'Plant in well-drained loamy soil, maintain pH 6.0–7.0, thin to 10 cm spacing, monitor for Thrips and Purple Blotch'),
        ('garlic',        'Plant cloves 5 cm deep in well-drained soil, water moderately, harvest when bottom leaves yellow, cure in a dry, airy place'),
        ('carrot',        'Sow in loose, stone-free soil, thin to 8 cm, keep moist until germination, monitor for Carrot Fly'),
        ('beet',          'Thin seedlings to 10 cm, maintain consistent moisture, harvest when roots are 4–6 cm diameter'),
        ('lettuce',       'Ensure consistent moisture, mulch to prevent bolting, harvest outer leaves first, monitor for Aphids'),
        ('spinach',       'Sow in cool weather, keep soil moist, harvest outer leaves to extend season, watch for Downy Mildew'),
        ('cabbage',       'Maintain 45 cm spacing, hill soil around base, monitor for Cabbage Looper and Club Root, rotate crops'),
        ('broccoli',      'Maintain 60 cm spacing, harvest heads before flowers open, side-shoot harvest extends season, monitor for Aphids'),
        ('cauliflower',   'Maintain 60 cm spacing, blanch heads by tying leaves, monitor for Aphids and Downy Mildew'),
        ('brussels sprouts','Provide deep, firm soil, stake tall plants against wind, harvest from bottom up as sprouts mature'),
        ('kale',          'Harvest outer leaves; plants tolerate frost (improves flavour), monitor for cabbage worms'),
        ('peas',          'Provide trellis or stakes, inoculate seeds with Rhizobium, harvest pods before seeds swell fully'),
        ('beans',         'Provide trellis for climbing types, avoid overwatering, inoculate with Rhizobium, monitor for Bean Fly'),
        ('squash',        'Allow 1–2 m spacing, hand-pollinate if fruit set is poor, monitor for Powdery Mildew and Squash Vine Borer'),
        ('zucchini',      'Harvest at 15–20 cm to encourage production, monitor for Powdery Mildew, keep soil moist'),
        ('cucumber',      'Trellis plants to save space, maintain consistent moisture, harvest before yellowing'),
        ('pepper',        'Keep soil temperature above 18 °C, stake tall plants, monitor for Bacterial Spot and Anthracnose'),
        ('eggplant',      'Stake plants, thin to strongest, monitor for Flea Beetles, water evenly to prevent blossom end problems'),
        ('okra',          'Provide full sun and warm soil, harvest every 2–3 days to keep plants productive, monitor for Root Knot Nematode'),
        ('chili',         'Use well-drained soil, moderate watering, stake in windy conditions, monitor for Leaf Curl Virus'),
        ('ginger',        'Plant in partial shade, maintain 70–80% humidity, harvest after 8–10 months when leaves yellow'),
        ('turmeric',      'Plant in partial shade, water regularly but avoid waterlogging, harvest after leaves die back in winter'),
        ('banana',        'Remove dead leaves regularly, ensure drainage, prop up heavy bunches, monitor for Panama Disease'),
        ('mango',         'Prune after harvest to shape canopy, apply potassium-phosphorus before flowering, monitor for Anthracnose'),
        ('orange',        'Irrigate during dry periods, apply citrus-specific fertilizer, monitor for Citrus Canker and Greening disease'),
        ('apple',         'Prune to open-vase shape for light penetration, thin fruit clusters, monitor for Scab and Fire Blight'),
        ('grape',         'Train on trellis, prune to 2 buds per spur, monitor for Downy and Powdery Mildew'),
        ('strawberry',    'Mulch with straw to keep fruit clean, remove runners, monitor for Gray Mold and Spider Mites'),
        ('blueberry',     'Maintain soil pH 4.5–5.5 with sulfur, prune old wood, monitor for Mummified Berry fungal disease'),
        ('raspberry',     'Tie canes to trellis, cut fruited canes after harvest, monitor for Cane Blight'),
        ('blackberry',    'Tip-prune new canes for branching, monitor for Rosette (Double Blossom) disease'),
        ('coffee',        'Shade-grow for premium quality, prune after harvest, monitor for Coffee Leaf Rust'),
        ('tea',           'Prune to a flat table for easy plucking, maintain acidic soil pH 4.5–6.0, monitor for Red Spider Mite'),
        ('coconut',       'Ensure good drainage, fertilize with K-rich compost, monitor for Rhinoceros Beetle and Bud Rot'),
        ('cashew',        'Allow wide spacing (7 × 7 m), prune dead wood, monitor for Anthracnose and Stem and Root Rot'),
        ('almond',        'Thin fruit for sizing, prune for open-center structure, cross-pollinate with another variety'),
        ('walnut',        'Allow wide spacing, prune to central leader, monitor for Walnut Blight'),
        ('pistachio',     'Requires hot, dry summers; alternate-bearing — thin in heavy years; monitor for Verticillium Wilt'),
        ('peanut',        'Ensure well-drained sandy loam, peg into soil, monitor for Aflatoxin-producing Aspergillus molds'),
        ('soybean',       'Inoculate with Bradyrhizobium, maintain 30 cm row spacing, monitor for Soybean Cyst Nematode'),
        ('sunflower',     'Provide full sun, stake in windy areas, monitor for Sclerotinia Stem Rot, harvest when back of head turns yellow'),
        ('sugarcane',     'Plant sets 30 cm apart in furrows, top-dress with nitrogen at tillering, monitor for Red Rot'),
        ('jute',          'Sow densely and thin to 7 cm, requires high humidity, harvest at flowering stage before fibre coarsens'),
        ('flax',          'Sow in cool weather, avoid waterlogging, harvest when seeds rattle in bolls'),
        ('hemp',          'Ensure 10 cm seed spacing, avoid overwatering, harvest at 50% pollen shed for fibre or seed separately'),
    ]
    cur.executemany(
        'INSERT OR IGNORE INTO crop_health_tips (crop, tips) VALUES (?, ?)',
        tips
    )

    conn.commit()
    conn.close()
    print("Database initialised and seeded successfully.")


if __name__ == '__main__':
    init_db()
