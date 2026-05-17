"""
AI Query Service - Agriculture-specific intelligent assistant.
Priority: 1) Gemini API  2) Comprehensive local knowledge base  3) Generic fallback
"""
from __future__ import annotations
import os, requests
from typing import Optional
from dotenv import load_dotenv, find_dotenv
from utils.logger import logger

# find_dotenv() walks up from this file's dir, finds farmer_query_engine/.env
load_dotenv(find_dotenv(usecwd=False, raise_error_if_not_found=False))

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
GEMINI_API_URL = (
    'https://generativelanguage.googleapis.com/v1beta/models/'
    'gemini-1.5-flash:generateContent'
)

SYSTEM_PROMPT = """You are KrishiMitra, an expert AI agricultural assistant for Indian farmers.
You have deep expertise in:
- All aspects of crop cultivation, management, and harvesting
- Plant and crop disease identification, treatment, and prevention
- Soil health, fertilizer recommendations, and nutrient management
- Pest management using IPM (Integrated Pest Management)
- Irrigation methods and water management
- Weather interpretation and farming decisions
- Indian government agricultural schemes with official links
- Regional crop recommendations for all Indian states
- Organic farming, sustainable agriculture practices
- Post-harvest storage and marketing
- Seeds, varieties, and crop selection

Rules:
1. Answer EVERY agriculture-related question thoroughly - never refuse or redirect.
2. Be specific - give actual dosages, timings, quantities when relevant.
3. Personalize answers using provided context (crop, state, weather, disease).
4. If context includes weather data, incorporate it into farming advice.
5. For government schemes mention official websites.
6. Be farmer-friendly: clear, practical, actionable language.
7. For non-agriculture queries, politely explain you specialize in farming.
8. Structure responses with clear paragraphs; use bullet points for lists.
"""

# ── COMPREHENSIVE AGRICULTURAL KNOWLEDGE BASE ─────────────────────────────────

_CROP_DB = {
    'rice': {
        'season': 'Kharif (June–Nov). Some regions: Rabi (Nov–Apr)',
        'soil': 'Heavy clay or clay-loam with good water retention; pH 5.5–6.5',
        'seed_rate': '20–25 kg/ha (transplanted), 80–100 kg/ha (direct seeded)',
        'fertilizer': 'Basal: DAP 60 kg/ha + MOP 40 kg/ha. Top dress: Urea 120 kg/ha in 3 splits (basal, tillering, panicle initiation)',
        'irrigation': 'Keep 2–5 cm standing water during vegetative; drain at maturity. Needs 1200–2000 mm water.',
        'diseases': 'Blast (Pyricularia), Brown spot, Bacterial leaf blight, Sheath blight',
        'pests': 'Stem borer, Brown plant hopper (BPH), Gall midge, Leaf folder',
        'yield': '4–6 t/ha (improved varieties); 6–8 t/ha (SRI method)',
        'tips': 'SRI (System of Rice Intensification) reduces water 30–50% and increases yield.',
    },
    'wheat': {
        'season': 'Rabi (Oct–Apr); sow Oct–Nov, harvest Mar–Apr',
        'soil': 'Well-drained loamy or clay-loam; pH 6.0–7.5',
        'seed_rate': '100–125 kg/ha',
        'fertilizer': 'Basal: DAP 60 kg/ha + MOP 30 kg/ha. Top dress: Urea 120 kg/ha (1/2 basal, 1/4 CRI, 1/4 tillering)',
        'irrigation': '5–6 critical irrigations: CRI (21 days), tillering (40 days), jointing (60 days), booting (80 days), anthesis (100 days), grain filling (115 days)',
        'diseases': 'Yellow/stripe rust, Brown/leaf rust, Powdery mildew, Karnal bunt, Loose smut',
        'pests': 'Aphid, Hessian fly, Army worm, Termite',
        'yield': '4–6 t/ha irrigated; 2–3 t/ha rainfed',
        'tips': 'Avoid late sowing — each week delay after optimal window reduces yield 30–40 kg/ha/day.',
    },
    'cotton': {
        'season': 'Kharif (Apr–May sowing, harvest Oct–Jan)',
        'soil': 'Deep black cotton soil (Vertisols) or medium clay; pH 7.0–8.0',
        'seed_rate': '2.5–3 kg/ha (Bt hybrid)',
        'fertilizer': 'NPK 120:60:60 kg/ha. Apply 1/3 N + full P + full K at sowing; 1/3 N at square formation; 1/3 N at boll formation',
        'irrigation': 'Drip preferred. Critical stages: germination, square, flowering, boll development',
        'diseases': 'Bacterial blight, Fusarium/Verticillium wilt, Alternaria leaf spot, Root rot',
        'pests': 'Bollworm (major), Whitefly, Aphid, Jassid, Thrips, Mealybug',
        'yield': '20–25 quintals seed cotton/ha (Bt varieties)',
        'tips': 'Monitor whitefly closely — vector for CLCuV (Cotton Leaf Curl Virus). Use yellow sticky traps.',
    },
    'tomato': {
        'season': 'Rabi (Oct–Jan) best; also Kharif and summer crops',
        'soil': 'Well-drained sandy loam to clay loam; pH 6.0–7.0',
        'seed_rate': '400–500 g/ha (nursery transplanting)',
        'fertilizer': 'NPK 200:150:150 kg/ha. Split N into 4 doses. Foliar: Boron 0.2% at flowering',
        'irrigation': 'Drip irrigation saves 40–50% water. Maintain uniform moisture to prevent blossom end rot.',
        'diseases': 'Early blight, Late blight, Bacterial wilt, Fusarium wilt, TYLCV (Tomato Yellow Leaf Curl Virus)',
        'pests': 'Fruit borer (Helicoverpa), Whitefly, Spider mite, Aphid',
        'yield': '30–40 t/ha (hybrid varieties) under protected cultivation up to 80 t/ha',
        'tips': 'Stake plants for better air circulation. Remove infected plants immediately to stop spread.',
    },
    'potato': {
        'season': 'Rabi (Oct–Nov planting, Jan–Mar harvest)',
        'soil': 'Sandy loam to loam; pH 5.0–6.5; good drainage essential',
        'seed_rate': '2–2.5 t/ha (60–80 g seed tubers)',
        'fertilizer': 'NPK 180:80:100 kg/ha. Apply 1/2 N + full P + 1/2 K at planting; remaining at earthing-up',
        'irrigation': 'Sprinkler preferred. Avoid water stress at tuber initiation and bulking stages.',
        'diseases': 'Late blight (most destructive), Early blight, Black scurf, Common scab, Viral diseases',
        'pests': 'Aphid (virus vector), Cut worm, White grub, Colorado potato beetle',
        'yield': '25–35 t/ha; up to 45 t/ha with improved management',
        'tips': 'Late blight spreads explosively in cool, humid weather. Monitor daily and spray Mancozeb 0.2% preventively.',
    },
    'maize': {
        'season': 'Kharif (Jun–Sep), Rabi (Oct–Feb) in S India, Spring (Feb–Jun)',
        'soil': 'Well-drained loamy soil; pH 6.0–7.5',
        'seed_rate': '20–25 kg/ha (hybrid)',
        'fertilizer': 'NPK 150:75:75 kg/ha. Apply 1/3 N + full P + K at sowing; 1/3 N at knee-high; 1/3 N at tasseling',
        'irrigation': 'Critical: knee-high, tasseling, silking, grain filling. Drought at tasseling = major yield loss.',
        'diseases': 'Northern Corn Leaf Blight (NCLB), Downy mildew, Stalk rot, Smut',
        'pests': 'Fall Army Worm (FAW) - major threat, Stem borer, Aphid, Cob borer',
        'yield': '6–10 t/ha (hybrid varieties)',
        'tips': 'Fall Army Worm: spray Emamectin benzoate 0.5 g/L or Chlorantraniliprole 0.4 ml/L targeting whorls.',
    },
    'onion': {
        'season': 'Kharif: May–Jun transplant; Rabi: Oct–Nov transplant',
        'soil': 'Sandy loam to loam; pH 6.0–6.8',
        'seed_rate': '8–10 kg/ha (nursery)',
        'fertilizer': 'NPK 100:50:100 kg/ha. Avoid excess N late in season (soft bulbs).',
        'irrigation': 'Drip recommended. Stop irrigation 10–15 days before harvest for good dry matter.',
        'diseases': 'Purple blotch, Stemphylium blight, Downy mildew, Basal rot (Fusarium)',
        'pests': 'Thrips (most damaging), Cut worm, Leaf miner',
        'yield': '25–30 t/ha (Rabi); 15–20 t/ha (Kharif)',
        'tips': 'Thrips: spray Fipronil 0.1% or Spinosad 0.045%. NSKE 5% is an effective organic option.',
    },
    'sugarcane': {
        'season': 'Planted Oct–Nov (autumn) or Feb–Mar (spring); ratoon possible',
        'soil': 'Deep, rich loam or clay-loam; pH 6.0–8.0',
        'seed_rate': '8–10 t/ha setts (2–3 budded)',
        'fertilizer': 'NPK 300:80:120 kg/ha over crop period. Trash mulching reduces fertilizer need 20–25%.',
        'irrigation': 'Needs 1500–2500 mm. Drip saves 30–40% water + 20–30% yield increase.',
        'diseases': 'Red rot, Smut, Wilt, Grassy shoot (phytoplasma)',
        'pests': 'Top shoot borer, Internode borer (early), Root borer (late), White grub',
        'yield': '70–100 t/ha plant crop; 60–80 t/ha ratoon',
        'tips': 'Select seed cane from disease-free certified plots. Hot water treatment (50°C, 2h) prevents smut.',
    },
    'ragi': {
        'season': 'Kharif (Jun–Oct); some areas Rabi too',
        'soil': 'Well-drained red, laterite, or loamy soil; pH 5.5–8.0. Very drought tolerant.',
        'seed_rate': '8–10 kg/ha (transplanted); 3–4 kg/ha (line sowing)',
        'fertilizer': 'NPK 60:30:30 kg/ha. FYM 5 t/ha at land preparation. Azospirillum biofertilizer effective.',
        'irrigation': 'Rainfed crop mainly. 3–4 light irrigations if available: at transplanting, tillering, panicle initiation, grain filling.',
        'diseases': 'Blast (major), Finger millet blast, Brown spot, Downy mildew',
        'pests': 'Shoot fly, Earhead caterpillar, Aphid, Armyworm',
        'yield': '2–3 t/ha (rainfed); 3–4 t/ha (irrigated)',
        'tips': 'Ragi is extremely nutritious — high calcium, iron. GPU-28, GPU-67, MR-6 are high-yielding varieties.',
    },
    'jowar': {
        'season': 'Kharif (Jun–Oct) and Rabi (Oct–Feb) in peninsular India',
        'soil': 'Wide adaptability; best in medium-deep black or loam soil; pH 6.0–7.5',
        'seed_rate': '10–12 kg/ha',
        'fertilizer': 'NPK 80:40:40 kg/ha. Rainfed: reduce to 40:20:20.',
        'irrigation': 'Drought-tolerant. 2–3 irrigations if available: establishment, panicle initiation, grain filling.',
        'diseases': 'Grain mold (major), Downy mildew, Anthracnose, Smut',
        'pests': 'Shoot fly (most damaging), Stem borer, Aphid, Midge',
        'yield': '2–4 t/ha grain; 10–15 t/ha fodder',
        'tips': 'Shoot fly: use resistant varieties (CSH 16). Early sowing reduces shoot fly damage significantly.',
    },
    'bajra': {
        'season': 'Kharif (Jun–Sep) — very short duration, 75–90 days',
        'soil': 'Sandy loam; tolerates poor, low-fertility soils; pH 6.0–8.0',
        'seed_rate': '4–5 kg/ha',
        'fertilizer': 'NPK 60:30:30 kg/ha. Responds well to zinc (5 kg/ha ZnSO4).',
        'irrigation': 'Drought tolerant. 1–2 critical irrigations: panicle emergence, grain filling.',
        'diseases': 'Downy mildew (green ear disease — major), Smut, Rust, Ergot',
        'pests': 'Shoot fly, Stem borer, White grub, Blister beetle',
        'yield': '2–3 t/ha grain; 8–12 t/ha fodder',
        'tips': 'Excellent for Rajasthan, Gujarat, Haryana. HHB-67 Improved and 86M88 are popular hybrids.',
    },
    'groundnut': {
        'season': 'Kharif (Jun–Oct) in most areas; Rabi/summer in irrigated areas',
        'soil': 'Well-drained sandy loam to loam; pH 6.0–7.0. Needs calcium for pod filling.',
        'seed_rate': '80–100 kg/ha (bold seeded), 60–80 kg/ha (small seeded)',
        'fertilizer': 'NPK 25:50:50 kg/ha + gypsum 400–500 kg/ha at peg formation (critical for calcium).',
        'irrigation': 'Critical stages: flowering, peg formation, pod development. Avoid waterlogging.',
        'diseases': 'Early leaf spot, Late leaf spot, Tikka, Stem rot (Collar rot), Bud necrosis (TSWV)',
        'pests': 'Leaf miner, Jassid, Aphid, White grub, Spodoptera',
        'yield': '2–4 t/ha pods (improved varieties)',
        'tips': 'Gypsum application at 30 DAS is critical for pod filling. Tag-24, GG-20, ICGS-76 are popular varieties.',
    },
    'soybean': {
        'season': 'Kharif (Jun–Sep); 90–100 days crop',
        'soil': 'Well-drained loam to clay-loam; pH 6.0–7.5',
        'seed_rate': '65–75 kg/ha (large-seeded), 50–65 kg/ha (small-seeded)',
        'fertilizer': 'NPK 20:80:40 kg/ha. Seed treatment with Rhizobium + PSB biofertilizer essential — fixes atmospheric N.',
        'irrigation': 'Critical: flowering and pod filling. Avoid waterlogging at any stage.',
        'diseases': 'Yellow mosaic virus (YMV – major), Bacterial pustule, Cercospora leaf blight, Charcoal rot',
        'pests': 'Girdle beetle (stem girdler), Leaf eating caterpillar, Tobacco caterpillar, Aphid',
        'yield': '2–3 t/ha (improved varieties)',
        'tips': 'YMV spread by whitefly — control with Thiamethoxam seed treatment. JS-335 and MACS-1407 are top varieties.',
    },
    'mustard': {
        'season': 'Rabi (Oct–Mar); sow early October for best yield',
        'soil': 'Loam to clay-loam; pH 6.0–7.5',
        'seed_rate': '5–6 kg/ha',
        'fertilizer': 'NPK 80:40:40 kg/ha + 40 kg/ha S (sulphur is critical for oil content).',
        'irrigation': '2–3 irrigations: branching (25–30 DAS), flowering (45–50 DAS), pod development (65–70 DAS).',
        'diseases': 'Alternaria blight (major), White rust, Downy mildew, Sclerotinia stem rot',
        'pests': 'Aphid (most damaging), Painted bug, Sawfly, Stem weevil',
        'yield': '1.5–3.0 t/ha seeds',
        'tips': 'Aphid spray: Dimethoate 0.03% or Thiamethoxam. Timely sowing (1–15 Oct) is the most important yield factor.',
    },
    'gram': {
        'season': 'Rabi (Oct–Mar); also called chickpea or chana',
        'soil': 'Light loam to medium clay; pH 6.0–9.0; excellent drought tolerance',
        'seed_rate': '60–80 kg/ha (Desi type); 80–100 kg/ha (Kabuli)',
        'fertilizer': 'NPK 20:40:20 kg/ha. Seed treat with Rhizobium culture. Minimal N needed due to N-fixation.',
        'irrigation': '1–2 irrigations: pre-sowing + pod filling. Over-irrigation causes vegetative growth, low yield.',
        'diseases': 'Fusarium wilt (major), Collar rot, Dry root rot, Ascochyta blight, Botrytis grey mold',
        'pests': 'Pod borer (Helicoverpa – most destructive), Cut worm, Aphid',
        'yield': '1.5–3.0 t/ha',
        'tips': 'Pod borer: spray Emamectin benzoate 0.5 g/L or Indoxacarb. Use pheromone traps for monitoring.',
    },
    'moong': {
        'season': 'Kharif (Jun–Sep) and Zaid/summer (Mar–Jun); 60–75 day crop',
        'soil': 'Sandy loam to loam; pH 6.2–7.2',
        'seed_rate': '15–20 kg/ha',
        'fertilizer': 'NPK 20:40:20 kg/ha. Rhizobium seed treatment essential.',
        'irrigation': '3–4 irrigations: pre-sowing, flowering, pod development stages.',
        'diseases': 'Yellow mosaic virus (YMV – major control with Imidacloprid), Cercospora leaf spot, Powdery mildew',
        'pests': 'Whitefly (YMV vector), Pod borer, Thrips, Aphid',
        'yield': '1–1.5 t/ha',
        'tips': 'Short-duration crop ideal as intercrop or catch crop. Pusa Vishal, SML-668 are high-yielding varieties.',
    },
    'arhar': {
        'season': 'Kharif (Jun–Oct); 150–180 days; also called tur or pigeon pea',
        'soil': 'Wide adaptability; best in sandy loam to clay-loam; pH 6.5–8.0',
        'seed_rate': '15–20 kg/ha',
        'fertilizer': 'NPK 20:50:30 kg/ha + Rhizobium seed treatment.',
        'irrigation': '2–3 critical irrigations: pre-sowing, pod formation, grain filling.',
        'diseases': 'Fusarium wilt (major), Phytophthora blight, Sterility mosaic virus (SMV)',
        'pests': 'Pod borer (Helicoverpa – most serious), Blister beetle, Pod fly',
        'yield': '1.5–2.5 t/ha',
        'tips': 'SMV spreads through mites — spray Chlorfenapyr 0.1%. Intercrop with sorghum for natural pest suppression.',
    },
    'sunflower': {
        'season': 'Kharif (Jun–Sep), Rabi (Oct–Jan), and Zaid (Feb–May)',
        'soil': 'Well-drained loam; pH 6.0–7.5; deep-rooted — needs loose soil',
        'seed_rate': '5–8 kg/ha (hybrid)',
        'fertilizer': 'NPK 80:60:60 kg/ha + Boron 1.5 kg/ha (critical for seed set).',
        'irrigation': '5–6 irrigations. Critical: vegetative, bud, anthesis, and grain filling stages.',
        'diseases': 'Downy mildew, Alternaria leaf blight, Necrosis, Charcoal rot',
        'pests': 'Head borer, Capitulum borer, Aphid, Jassid',
        'yield': '2–3 t/ha (hybrid varieties)',
        'tips': 'Boron deficiency causes hollow stems and poor seed set — apply Borax 10 kg/ha or 0.2% foliar spray.',
    },
    'banana': {
        'season': 'Year-round planting; 11–15 months to harvest',
        'soil': 'Rich, well-drained loam; pH 6.0–7.5; cannot tolerate waterlogging',
        'seed_rate': '1500–2500 suckers/ha',
        'fertilizer': 'NPK 200:60:220 kg/ha in 4–6 splits. High potassium improves fruit quality and shelf life.',
        'irrigation': 'Drip recommended (40–50 L/plant/day). Very sensitive to water stress.',
        'diseases': 'Panama wilt (Fusarium), Sigatoka leaf spot, Bunchy top virus, Anthracnose',
        'pests': 'Rhizome weevil, Banana aphid (bunchy top vector), Thrips, Nematodes',
        'yield': '40–80 t/ha depending on variety and management',
        'tips': 'Panama wilt: no chemical cure — use resistant varieties (Saba, Karpuravalli, Grand Naine). Tissue culture plants ensure disease-free start.',
    },
    'mango': {
        'season': 'Perennial; flowers Dec–Jan; fruiting Mar–Jun',
        'soil': 'Deep, well-drained loam to laterite; pH 5.5–7.5',
        'seed_rate': '400–500 grafted plants/ha',
        'fertilizer': 'Mature tree (>10 yr): FYM 50 kg + NPK 2.5:1.5:1.5 kg/tree. Apply after harvest.',
        'irrigation': '2–3 pre-flowering irrigations (Nov–Jan), then regular. Stop 2 months before harvest for sugar development.',
        'diseases': 'Powdery mildew (major flowering season), Anthracnose, Malformation, Bacterial canker',
        'pests': 'Mango hopper (shoots/flowers), Fruit fly (mature fruit), Stem borer, Scale insects',
        'yield': '10–15 t/ha (Alphonso, Langra, Dashehari varieties)',
        'tips': 'Hopper management: spray Imidacloprid at panicle emergence. Fruit fly: use bait traps with methyl eugenol.',
    },
    'coconut': {
        'season': 'Perennial; planted year-round in tropics; productive for 60–80 years',
        'soil': 'Sandy loam coastal soil; pH 5.5–8.0; high tolerance to salinity',
        'seed_rate': '175–200 palms/ha',
        'fertilizer': 'NPK 1000:500:2000 g/palm/year in 2 splits (Jun and Dec). Micronutrients: 300 g MgSO4, 100 ppm B.',
        'irrigation': 'Drip: 16–25 L/palm/day. Very responsive to irrigation — doubles yield in coastal Karnataka and Kerala.',
        'diseases': 'Root wilt (lethal), Bud rot, Wilt, Leaf blight',
        'pests': 'Rhinoceros beetle (major), Red palm weevil, Coconut mite, eriophyid mite',
        'yield': '80–100 nuts/palm/year (improved hybrids 150–200)',
        'tips': 'Rhinoceros beetle: naphthalene balls in crown, biological control with Baculovirus. Micronutrient application critical in laterite soils.',
    },
    'ginger': {
        'season': 'Planted Mar–May (Kharif); harvested Nov–Jan (8–10 months)',
        'soil': 'Well-drained sandy loam to clay-loam rich in organic matter; pH 5.5–7.0',
        'seed_rate': '2000–2500 kg/ha rhizomes',
        'fertilizer': 'NPK 150:100:150 kg/ha + FYM 30–40 t/ha. High organic matter is essential.',
        'irrigation': 'Frequent light irrigation. Soil must stay moist but not waterlogged. Mulching critical.',
        'diseases': 'Rhizome rot (Pythium – most destructive), Bacterial wilt, Leaf spot',
        'pests': 'Shoot borer, Rhizome scale, Root-knot nematode',
        'yield': '15–25 t/ha fresh rhizomes',
        'tips': 'Use disease-free, healthy planting material. Treat rhizomes with Mancozeb 0.3% before planting. Mulching with dry leaves reduces moisture stress.',
    },
    'turmeric': {
        'season': 'Planted Apr–Jun; harvested Jan–Mar (8–9 months)',
        'soil': 'Well-drained loam to clay-loam rich in organic matter; pH 5.0–7.5',
        'seed_rate': '2500 kg/ha rhizomes',
        'fertilizer': 'NPK 60:50:120 kg/ha + FYM 40 t/ha. Split N into 3 doses.',
        'irrigation': 'Weekly irrigation needed. Mulching with paddy straw or dry leaves reduces weed and water need.',
        'diseases': 'Rhizome rot (Pythium), Leaf blotch, Leaf spot',
        'pests': 'Shoot borer, Scale insect, Thrips',
        'yield': '25–30 t/ha fresh rhizomes; 5–6 t/ha dry',
        'tips': 'Andhra Pradesh and Tamil Nadu are major producers. BST-1 (Salem) and Alleppey varieties fetch premium price from exporters.',
    },
}

_DISEASE_TREATMENTS = {
    'blight': {
        'early': 'Apply Mancozeb 0.2% or Chlorothalonil 0.2% every 7–10 days. Remove infected lower leaves. Avoid overhead irrigation.',
        'late': 'Apply Metalaxyl+Mancozeb (Ridomil Gold) 0.25% immediately. Drainage critical. Destroy infected plant material.',
        'bacterial': 'Copper oxychloride 0.3% spray. No effective cure — use resistant varieties. Remove infected plants.',
    },
    'rust': 'Apply Propiconazole 0.1% (Tilt 25 EC @ 0.5 ml/L) or Tebuconazole 0.1%. Spray at first sign. Repeat every 14 days.',
    'mildew_powdery': 'Spray Sulphur 80 WP @ 3 g/L or Hexaconazole 0.1%. Avoid wetting foliage. Improve air circulation.',
    'mildew_downy': 'Metalaxyl+Mancozeb 2.5 g/L. Avoid overhead irrigation. Remove crop debris.',
    'wilt_fusarium': 'No effective chemical cure. Use resistant varieties. Soil drench with Carbendazim 0.1%. Crop rotation 3–4 years.',
    'wilt_bacterial': 'No cure. Remove and destroy infected plants. Soil solarization. Use resistant varieties next season.',
    'anthracnose': 'Carbendazim 0.1% or Mancozeb 0.2%. Avoid injuries to fruit. Post-harvest hot water dip (52°C, 5 min).',
    'mosaic_virus': 'No chemical cure. Control aphid/whitefly vectors with Imidacloprid 0.5 ml/L. Remove infected plants. Use virus-free certified seed.',
}

_PEST_GUIDE = {
    'aphid': 'Spray Imidacloprid 0.3 ml/L or Thiamethoxam 0.3 g/L. Organic: Neem oil 5 ml/L + soap 0.5 ml/L. Natural predators: ladybird beetles.',
    'whitefly': 'Yellow sticky traps (10/acre). Imidacloprid 0.5 ml/L or Acetamiprid 0.2 g/L. Organic: Neem oil 5 ml/L.',
    'thrips': 'Spinosad 0.3 ml/L or Fipronil 1.5 ml/L. Blue sticky traps. Spray at 7-day intervals.',
    'stem_borer': 'Carbofuran 3G @ 25 kg/ha in whorl. Coragen (Chlorantraniliprole) 0.4 ml/L. Release Trichogramma @ 50000/acre/week.',
    'bollworm': 'Neem oil 5 ml/L (early); Emamectin benzoate 0.5 g/L or Chlorantraniliprole 0.3 ml/L (heavy). Pheromone traps.',
    'spider_mite': 'Dicofol 1.5 ml/L or Abamectin 0.5 ml/L. Increase humidity. Avoid broad-spectrum pesticides that kill predators.',
    'fall_armyworm': 'Emamectin benzoate 0.5 g/L or Spinetoram 0.5 ml/L. Target whorls early morning. Pheromone traps 5/acre.',
    'mealybug': 'Dimethoate 1.5 ml/L. Spray forcefully to wet colonies. Remove plant debris. Biological: Cryptolaemus (ladybird beetle).',
}

_FERTILIZER_GUIDE = {
    'nitrogen': 'Sources: Urea (46% N), CAN (26% N), Ammonium sulphate (21% N). Apply in split doses to reduce losses. Top-dress when crop is actively growing.',
    'phosphorus': 'Sources: DAP (18-46-0), SSP (0-16-0). Apply at/before sowing — relatively immobile in soil. Low phosphorus = poor root development, delayed maturity.',
    'potassium': 'Sources: MOP/KCl (0-0-60), SOP (0-0-50). Improves quality, disease resistance, drought tolerance. Apply at sowing for best effect.',
    'micronutrients': 'Zinc deficiency (most common in India): ZnSO4 @ 25 kg/ha soil or 0.5% foliar spray. Boron: 1 kg/ha for flowering crops. Iron: Ferrous sulphate 0.5% foliar.',
    'organic': 'FYM 10–15 t/ha. Vermicompost 2–4 t/ha. Green manure: Dhaincha/Sunhemp. Biofertilizers: Rhizobium (legumes), PSB (phosphate solubilizing bacteria).',
    'testing': 'Soil test before fertilizing. Get test at local KVK or soil testing lab (Rs 50–200). Saves money and prevents over/under-application.',
}

_IRRIGATION_GUIDE = {
    'drip': 'Saves 40–60% water vs. flood. Delivers water directly to root zone. Best for vegetables, fruits, cotton, sugarcane. Subsidy available under PMKSY.',
    'sprinkler': 'Saves 25–40% vs. flood. Good for wheat, vegetables, shallow-rooted crops. Not suitable for crops needing high humidity.',
    'flood': 'Traditional method. High water use. Suitable for rice. Laser leveling reduces water use 15–20%.',
    'scheduling': 'Water when top 5 cm soil is dry. IW:CPE ratio method: irrigate when IW/CPE reaches 0.8–1.0. Tensiometer (30 kPa) = irrigation needed.',
    'deficit': 'Skip irrigation at non-critical stages to save water. Critical stages vary by crop: flowering and grain filling are most sensitive.',
}

_REGIONAL_CROPS = {
    'punjab': 'Rice-Wheat (dominant). Diversification needed: Maize, Cotton, Vegetables, Oilseeds. High water table problem — shift to less water-intensive crops.',
    'haryana': 'Rice-Wheat belt. Sugarcane, Cotton, Mustard. Water stress region — promote drip and sprinkler.',
    'uttar pradesh': 'Wheat, Rice, Sugarcane, Potato, Mustard, Pulses. Largest sugarcane producer in India.',
    'maharashtra': 'Cotton, Soybean, Sugarcane, Jowar, Bajra, Onion, Grapes. Highly variable rainfall — drought-prone districts.',
    'karnataka': 'Rice, Jowar, Maize, Cotton, Sugarcane, Groundnut, Horticulture. Ragi (Finger Millet) specialty.',
    'andhra pradesh': 'Rice, Tobacco, Groundnut, Chilli, Cotton. Krishna-Godavari delta — major rice bowl.',
    'telangana': 'Cotton, Rice, Maize, Soybean, Chilli. Telangana has Mission Kakatiya for tank restoration.',
    'tamil nadu': 'Rice, Bananas, Sugarcane, Groundnut, Cotton. Famous for Cauvery delta rice cultivation.',
    'kerala': 'Rubber, Coconut, Spices (Cardamom, Pepper, Ginger), Rice, Banana. High-value horticulture.',
    'gujarat': 'Cotton, Groundnut, Castor, Cumin, Wheat, Rice (coastal). Leading cotton and groundnut state.',
    'rajasthan': 'Bajra, Jowar, Wheat, Mustard, Cumin, Groundnut. Irrigation via interlinking and canal systems.',
    'madhya pradesh': 'Soybean (largest producer), Wheat, Gram, Maize, Cotton. Madhya Pradesh Kisan App useful.',
    'west bengal': 'Rice, Jute, Tea, Potato, Vegetables. Multiple rice crops per year in delta region.',
    'bihar': 'Rice, Wheat, Maize, Sugarcane, Potato. Litchi (Muzaffarpur), Makhana (Fox nut) specialties.',
}

_SCHEMES = [
    {'name': 'PM-KISAN', 'desc': 'Rs 6,000/year in 3 instalments direct to farmer bank accounts.', 'link': 'https://pmkisan.gov.in'},
    {'name': 'PM Fasal Bima Yojana (PMFBY)', 'desc': 'Low-premium crop insurance covering all losses.', 'link': 'https://pmfby.gov.in'},
    {'name': 'PM Krishi Sinchayi Yojana (PMKSY)', 'desc': 'Subsidy for drip and sprinkler irrigation systems.', 'link': 'https://pmksy.gov.in'},
    {'name': 'Kisan Credit Card (KCC)', 'desc': 'Low-interest short-term credit up to Rs 3 lakh @4% pa.', 'link': 'https://www.nabard.org'},
    {'name': 'Soil Health Card', 'desc': 'Free soil testing with fertilizer recommendations.', 'link': 'https://soilhealth.dac.gov.in'},
    {'name': 'eNAM', 'desc': 'Online mandi platform for better crop prices.', 'link': 'https://enam.gov.in'},
    {'name': 'PM Kisan MaanDhan Yojana', 'desc': 'Pension scheme for small/marginal farmers age 18–40.', 'link': 'https://pmkmy.gov.in'},
    {'name': 'Paramparagat Krishi Vikas Yojana (PKVY)', 'desc': 'Cluster-based organic farming support Rs 50,000/ha.', 'link': 'https://pkvy.nic.in'},
]

# ── GENERAL AGRONOMY KNOWLEDGE ────────────────────────────────────────────────

_AGRONOMY_KB = {
    'intercropping': ('**Intercropping** is growing two or more crops simultaneously in the same field.\n\n'
        '**Benefits:** Higher land use efficiency, risk diversification, natural pest suppression, extra income.\n\n'
        '**Common combinations:**\n'
        '- Arhar + Soybean/Moong (1:3 row ratio)\n'
        '- Maize + Soybean\n'
        '- Cotton + Moong/Cowpea\n'
        '- Sugarcane + Potato/Onion\n\n'
        '**Key rule:** Companion crops should differ in height, maturity, and root depth to avoid competition.'),
    'crop rotation': ('**Crop rotation** means growing different crops in sequence on the same land.\n\n'
        '**Benefits:** Breaks pest/disease cycles, improves soil fertility (especially with legumes), reduces fertilizer cost.\n\n'
        '**Common rotations:**\n'
        '- Rice → Wheat → Maize\n'
        '- Cotton → Wheat → Moong\n'
        '- Soybean → Wheat (legume restores N for following wheat)\n\n'
        '**Golden rule:** Always follow a legume crop to replenish soil nitrogen naturally.'),
    'soil testing': ('**Soil testing** tells you exactly what your soil needs — saves money and prevents over/under-application.\n\n'
        '**What it measures:** NPK levels, pH, organic carbon, salinity, micronutrients.\n\n'
        '**How to collect sample:** Mix soil from 10–15 random spots in your field at 0–15 cm depth. Air dry and send 500 g.\n\n'
        '**Cost:** Rs 50–500 at government soil testing labs or KVKs.\n\n'
        '**Government portal:** Soil Health Card scheme — https://soilhealth.dac.gov.in'),
    'kharif': ('**Kharif crops** are sown with the onset of monsoon (June–July) and harvested October–November.\n\n'
        '**Main Kharif crops:** Rice, Maize, Cotton, Soybean, Groundnut, Jowar, Bajra, Arhar (Tur), Moong, Sugarcane.\n\n'
        '**Characteristics:** Require high temperatures (25–35°C), long days, and heavy rainfall during growth.'),
    'rabi': ('**Rabi crops** are sown after monsoon (October–November) and harvested March–April.\n\n'
        '**Main Rabi crops:** Wheat, Mustard, Gram (Chickpea), Potato, Onion, Sunflower, Lentils, Peas.\n\n'
        '**Characteristics:** Grow in cool temperatures, need mild frost for vernalisation (wheat). Depend on irrigation in North India.'),
    'zaid': ('**Zaid crops** are short-duration crops grown in summer (March–June) between Rabi and Kharif seasons.\n\n'
        '**Main Zaid crops:** Watermelon, Muskmelon, Cucumber, Bottle gourd, Bitter gourd, Fodder crops.\n\n'
        '**Characteristics:** Require warm conditions, short day length, and availability of irrigation.'),
    'drip irrigation': _IRRIGATION_GUIDE.get('drip', ''),
    'vermicompost': ('**Vermicompost** is produced by earthworms decomposing organic waste.\n\n'
        '**Benefits:** 5× more nutrients than FYM, improves soil structure and water holding, rich in beneficial microbes.\n\n'
        '**How to make:** Mix cow dung + crop waste + kitchen waste, inoculate with Eisenia foetida (red worms), maintain moisture at 40–60%, harvest in 45–60 days.\n\n'
        '**Application:** 2–4 t/ha in-field, or 2–4 kg/pit for vegetables.'),
    'drip subsidy': ('**Drip/Sprinkler Irrigation Subsidy** under PMKSY (Pradhan Mantri Krishi Sinchayee Yojana):\n\n'
        '- Small/Marginal farmers: 55% subsidy\n'
        '- Other farmers: 45% subsidy\n\n'
        '**Apply at:** your state agriculture department or online at https://pmksy.gov.in'),
    'msp': ('**MSP (Minimum Support Price)** is the guaranteed price the Government of India pays for 23 crops.\n\n'
        '**2024–25 MSP highlights:**\n'
        '- Paddy (Rice): Rs 2,300/quintal\n'
        '- Wheat: Rs 2,275/quintal\n'
        '- Soybean: Rs 4,892/quintal\n'
        '- Cotton (medium staple): Rs 7,121/quintal\n\n'
        '**Check latest MSP:** https://cacp.dacnet.nic.in\n\n'
        '**How to sell at MSP:** Register at e-Procurement portal or sell to FCI, NAFED, or State procurement agency.'),
    'ipm': ('**IPM (Integrated Pest Management)** is a science-based approach that combines multiple strategies:\n\n'
        '1. **Cultural control:** Crop rotation, resistant varieties, proper spacing\n'
        '2. **Mechanical control:** Pheromone traps, yellow/blue sticky traps, hand-picking\n'
        '3. **Biological control:** Trichogramma (egg parasitoid), ladybird beetles, Trichoderma (soil fungus)\n'
        '4. **Chemical control:** Use only when pest crosses Economic Threshold Level (ETL)\n\n'
        '**Key principle:** Pesticides are the LAST resort, not the first.'),
    'organic certification': ('**Organic Certification Process:**\n\n'
        '1. Contact an APEDA-accredited certification body (e.g., NPOP, USDA, ParamPara)\n'
        '2. Apply and pay inspection fee (Rs 5,000–30,000 depending on farm size)\n'
        '3. Conversion period: **3 years** from last chemical use\n'
        '4. Annual inspections and documentation required\n\n'
        '**Government support:** PKVY scheme — Rs 50,000/ha for 3 years for cluster organic farming. Visit: https://pkvy.nic.in\n\n'
        '**Market benefit:** Organic produce commands 20–40% premium price.'),
    'nutrient deficiency': ('**Common crop nutrient deficiency symptoms:**\n\n'
        '- **Nitrogen (N):** Yellowing starts from older/lower leaves; stunted growth; pale green color\n'
        '- **Phosphorus (P):** Purple/reddish color on leaves; delayed maturity; dark green then purple stems\n'
        '- **Potassium (K):** Leaf margin and tip burn (scorching); weak stems; poor grain filling\n'
        '- **Zinc (Zn):** Interveinal chlorosis (yellow strips between green veins); white bud in maize\n'
        '- **Iron (Fe):** Young leaf yellowing while veins stay green; common in alkaline soils\n'
        '- **Boron (B):** Hollow stems; flower drop; deformed fruits; most common in mustard, sunflower\n\n'
        '**Fix:** Get soil test first. Apply appropriate fertilizer or foliar spray.'),
}

# Aliases to handle variant queries
_CROP_ALIASES = {
    'finger millet': 'ragi', 'nachni': 'ragi', 'mandua': 'ragi',
    'sorghum': 'jowar', 'great millet': 'jowar',
    'pearl millet': 'bajra', 'kambu': 'bajra',
    'peanut': 'groundnut', 'mungfali': 'groundnut',
    'chana': 'gram', 'chickpea': 'gram', 'bengal gram': 'gram',
    'green gram': 'moong', 'mung': 'moong', 'mung bean': 'moong',
    'pigeon pea': 'arhar', 'tur': 'arhar', 'toor': 'arhar', 'red gram': 'arhar',
    'corn': 'maize', 'makai': 'maize',
    'paddy': 'rice', 'dhaan': 'rice',
    'gahu': 'wheat',
    'rapeseed': 'mustard', 'sarso': 'mustard', 'canola': 'mustard',
    'haldi': 'turmeric', 'curcuma': 'turmeric',
    'adrak': 'ginger',
}
_INTENTS = {
    # High-priority phrases checked first (order matters)
    'crop_selection': [
        'which crop', 'what crop', 'what to grow', 'what can i grow',
        'best crop', 'suitable crop', 'recommend crop', 'suggest crop',
        'crops to grow', 'crops suitable', 'crops in my region',
        'what should i plant', 'what should i grow',
        'crops for my area', 'crops for this season',
        'which vegetables', 'what vegetables', 'crop recommendation',
    ],
    'disease': [
        'disease', 'blight', 'rust', 'mildew', 'wilt', 'rot', 'spot',
        'yellowing leaves', 'browning leaves', 'dying plant', 'sick plant',
        'infected', 'lesion', 'mosaic', 'curl leaf', 'fungal', 'bacterial infection',
        'viral', 'black spot', 'white powder', 'leaf spot', 'plant disease',
    ],
    'pest': [
        'pest', 'insect', 'bug', 'aphid', 'whitefly', 'spider mite', 'worm',
        'larvae', 'caterpillar', 'beetle', 'thrips', 'nematode', 'bollworm',
        'armyworm', 'stem borer', 'mealy bug', 'infestation',
    ],
    'fertilizer': [
        'fertilizer', 'fertiliser', 'nutrient', 'npk', 'urea', 'dap',
        'nitrogen', 'phosphorus', 'potassium', 'manure', 'compost',
        'micronutrient', 'deficiency', 'stunted growth', 'yellowing',
    ],
    'irrigation': [
        'irrigat', 'drip system', 'sprinkler', 'flood irrigation',
        'how much water', 'when to water', 'watering schedule',
        'water management', 'drought stress',
    ],
    'weather': [
        'what is the weather', 'current weather', 'weather today',
        'will it rain', 'temperature today', 'weather forecast',
        'is it good weather for farming',
    ],
    'soil': [
        'soil health', 'soil type', 'soil ph', 'clay soil', 'sandy soil',
        'loam', 'organic matter', 'saline soil', 'acidic soil',
        'alkaline soil', 'soil test', 'improve soil',
    ],
    'harvest': [
        'when to harvest', 'harvest time', 'ready to harvest',
        'maturity', 'post-harvest', 'storage after harvest', 'yield expected',
    ],
    'scheme': [
        'scheme', 'yojna', 'yojana', 'subsidy', 'government loan',
        'pm-kisan', 'pmfby', 'kcc', 'kisan credit card',
        'government benefit', 'farmer benefit', 'insurance scheme',
    ],
    'market': [
        'price', 'msp', 'mandi price', 'market rate', 'sell crop',
        'enam', 'wholesale price', 'how much will i get',
    ],
    'organic': [
        'organic farming', 'natural farming', 'chemical free',
        'zero budget', 'vermicompost', 'bio fertilizer', 'neem based',
    ],
    'seed': [
        'which seed', 'best seed', 'which variety', 'best variety',
        'hybrid seed', 'certified seed', 'high yield variety',
    ],
    'general_crop': list(_CROP_DB.keys()),
}


def _score_intents(query):
    lower = query.lower()
    scores = {intent: 0 for intent in _INTENTS}
    for intent, keywords in _INTENTS.items():
        for kw in keywords:
            if kw in lower:
                # Multi-word phrases score higher
                scores[intent] += len(kw.split())
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _extract_crop(query, crop_hint=None):
    if crop_hint:
        return crop_hint
    lower = query.lower()
    for crop in _CROP_DB:
        if crop in lower:
            return crop
    return None


def _extract_disease(query):
    lower = query.lower()
    for d in _DISEASE_TREATMENTS:
        if d.replace('_', ' ') in lower or d in lower:
            return d
    for d in ['blight', 'rust', 'mildew', 'wilt', 'anthracnose', 'mosaic']:
        if d in lower:
            return d
    return None


def _extract_pest(query):
    lower = query.lower()
    for p in _PEST_GUIDE:
        if p.replace('_', ' ') in lower:
            return p
    return None


def _extract_state_from_location(location_str):
    # type: (str) -> Optional[str]
    """Extract an Indian state name from a Nominatim reverse-geocode string."""
    if not location_str:
        return None
    lower = location_str.lower()
    # Check full state names
    for state in _REGIONAL_CROPS:
        if state in lower:
            return state
    # Common abbreviations / aliases
    aliases = {
        'ap': 'andhra pradesh', 'ts': 'telangana', 'tn': 'tamil nadu',
        'wb': 'west bengal', 'up': 'uttar pradesh', 'mp': 'madhya pradesh',
        'ka': 'karnataka', 'mh': 'maharashtra', 'gj': 'gujarat',
        'rj': 'rajasthan', 'pb': 'punjab', 'hr': 'haryana', 'br': 'bihar',
        'kl': 'kerala',
    }
    for alias, state in aliases.items():
        if alias in lower.split():
            return state
    return None


def _intelligent_fallback(query, crop=None, disease=None, state=None,
                          weather_context=None, location_context=None, conv_history=None):
    # type: (str, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[list]) -> str
    """
    Answers any agricultural question directly and conversationally.
    Rules:
    - ALWAYS answer the question first, context second.
    - Never prepend weather unless user asked about weather.
    - Extract state from location_context when state param is missing.
    """
    lower_q = query.lower() if query else ''

    # ── Resolve state from location string when not explicitly provided ─────────
    if not state and location_context:
        state = _extract_state_from_location(location_context)

    # ── Context Awareness from History ──────────────────────────────────────────
    # If crop is not mentioned in current query, look at recent conversation history
    if not crop and conv_history:
        for msg in reversed(conv_history):
            text = msg.get('text', '').lower()
            hist_crop = _extract_crop(text)
            if hist_crop:
                crop = hist_crop
                break
    
    # Same for disease history
    if not disease and conv_history:
        for msg in reversed(conv_history):
            text = msg.get('text', '').lower()
            hist_disease = _extract_disease(text)
            if hist_disease:
                disease = hist_disease
                break

    top_crop    = _extract_crop(query, crop)
    top_pest    = _extract_pest(query)
    top_disease = _extract_disease(query) or disease
    intent_scores   = _score_intents(query)
    primary_intent  = intent_scores[0][0] if intent_scores and intent_scores[0][1] > 0 else 'general'
    secondary_intent = intent_scores[1][0] if len(intent_scores) > 1 else ''

    # ── 1. CROP SELECTION — answer with actual crop names ──────────────────────
    if primary_intent == 'crop_selection':
        if state and state in _REGIONAL_CROPS:
            loc_label = location_context.split(',')[0].strip() if location_context else state.title()
            answer = 'Based on your location in **{0}** ({1}), here are the most suitable crops:\n\n'.format(
                state.title(), loc_label)
            answer += _REGIONAL_CROPS[state]
            answer += ('\n\n**Seasonal guide:**\n'
                       '- **Kharif (June–Oct):** Sow with monsoon onset\n'
                       '- **Rabi (Oct–Mar):** Cool-season crops after monsoon\n'
                       '- **Zaid (Mar–Jun):** Short-duration summer crops\n\n'
                       'Want details on any specific crop? Just ask!')
            if weather_context:
                answer += '\n\n**Current weather note:** {0}'.format(
                    weather_context.split('.')[0])  # just one sentence
        elif weather_context:
            w = weather_context.lower()
            if any(k in w for k in ['rain', 'drizzle', 'shower', 'humid']):
                season_crops = 'Rice, Maize, Cotton, Soybean, Groundnut, Jowar, Bajra'
                season = 'Kharif (monsoon)'
            else:
                season_crops = 'Wheat, Mustard, Chickpea (Gram), Potato, Onion, Peas, Lentils'
                season = 'Rabi (cool season)'
            answer = ('Based on current weather conditions ({0}), **{1} crops** are most suitable:\n\n'
                      '**Recommended:** {2}\n\n'
                      'Please share your **state/region** for more specific local recommendations!'
                      ).format(weather_context.split(',')[0], season, season_crops)
        else:
            answer = ('Here are crop recommendations by season:\n\n'
                      '**Kharif crops (Monsoon — Jun to Oct):**\nRice, Maize, Cotton, Soybean, '
                      'Groundnut, Jowar, Bajra, Tur (Arhar), Green Gram (Moong)\n\n'
                      '**Rabi crops (Winter — Oct to Mar):**\nWheat, Mustard, Gram (Chickpea), '
                      'Potato, Onion, Peas, Lentils (Masoor), Sunflower\n\n'
                      '**Zaid crops (Summer — Mar to Jun):**\nWatermelon, Muskmelon, Cucumber, '
                      'Summer Vegetables, Fodder crops\n\n'
                      '**For region-specific advice:** Share your state or location. '
                      'For example: Telangana farmers should prioritize Cotton, Rice and Soybean.')
        return answer

    # ── 2. SPECIFIC CROP QUERY ─────────────────────────────────────────────────
    if top_crop and top_crop in _CROP_DB:
        info = _CROP_DB[top_crop]
        if primary_intent == 'fertilizer' or secondary_intent == 'fertilizer':
            ans = '**{0} — Fertilizer Guide:**\n\n{1}'.format(top_crop.title(), info['fertilizer'])
            ans += '\n\n**Soil test first:** {0}'.format(_FERTILIZER_GUIDE['testing'])
            return ans
        if primary_intent == 'irrigation' or secondary_intent == 'irrigation':
            ans = '**{0} — Irrigation Guide:**\n\n{1}'.format(top_crop.title(), info['irrigation'])
            return ans
        if primary_intent == 'disease':
            ans = '**{0} — Common Diseases:**\n\n{1}'.format(top_crop.title(), info['diseases'])
            if top_disease:
                d_key = next((k for k in _DISEASE_TREATMENTS if k in top_disease), None)
                if d_key:
                    d_val = _DISEASE_TREATMENTS[d_key]
                    ans += '\n\n**Treatment ({0}):**\n'.format(top_disease.replace('_', ' ').title())
                    if isinstance(d_val, dict):
                        for sub, advice in d_val.items():
                            ans += '\n• **{0}:** {1}'.format(sub.title(), advice)
                    else:
                        ans += d_val
            return ans
        if primary_intent == 'pest':
            ans = '**{0} — Pest Management:**\n\nCommon pests: {1}'.format(
                top_crop.title(), info['pests'])
            if top_pest and top_pest in _PEST_GUIDE:
                ans += '\n\n**{0}:** {1}'.format(
                    top_pest.replace('_', ' ').title(), _PEST_GUIDE[top_pest])
            return ans
        if primary_intent == 'harvest':
            return ('**{0} — Harvest Guide:**\n\n'
                    '- **Season/timing:** {1}\n'
                    '- **Expected yield:** {2}\n\n'
                    '**Expert tip:** {3}').format(
                top_crop.title(), info['season'], info['yield'], info.get('tips', ''))
        if primary_intent == 'seed':
            return ('**{0} — Variety & Sowing Guide:**\n\n'
                    '- **Season:** {1}\n'
                    '- **Seed rate:** {2}\n'
                    '- **Soil:** {3}\n'
                    '- **Yield potential:** {4}\n\n'
                    '**Tip:** {5}').format(
                top_crop.title(), info['season'], info['seed_rate'],
                info['soil'], info['yield'], info.get('tips', ''))
        # General / how to grow
        return ('**How to grow {0}:**\n\n'
                '- **Season:** {1}\n'
                '- **Soil:** {2}\n'
                '- **Seed rate:** {3}\n'
                '- **Fertilizer:** {4}\n'
                '- **Irrigation:** {5}\n'
                '- **Watch for diseases:** {6}\n'
                '- **Key pests:** {7}\n'
                '- **Expected yield:** {8}\n\n'
                '**Expert tip:** {9}').format(
            top_crop.title(), info['season'], info['soil'], info['seed_rate'],
            info['fertilizer'], info['irrigation'], info['diseases'],
            info['pests'], info['yield'], info.get('tips', ''))

    # ── 3. DISEASE (no specific crop) ─────────────────────────────────────────
    if primary_intent == 'disease':
        if top_disease:
            d_key = next((k for k in _DISEASE_TREATMENTS if k in top_disease), None)
            if d_key:
                d_val = _DISEASE_TREATMENTS[d_key]
                ans = '**Disease: {0}**\n\n'.format(top_disease.replace('_', ' ').title())
                if isinstance(d_val, dict):
                    for sub, advice in d_val.items():
                        ans += '**{0}:** {1}\n\n'.format(sub.title(), advice)
                else:
                    ans += d_val
                return ans
        return ('**Common crop disease management:**\n\n'
                '- **Fungal diseases** (blight, rust, mildew): Apply Mancozeb 0.2% or '
                'Propiconazole 0.1%. Improve air circulation, avoid waterlogging.\n'
                '- **Bacterial diseases** (wilt, spot): Copper oxychloride 0.3%. Remove '
                'infected plants. Use disease-free seeds.\n'
                '- **Viral diseases** (mosaic, curl): Control insect vectors (aphids, whitefly) '
                'with Imidacloprid 0.5 ml/L. No direct chemical cure.\n\n'
                'Share a photo for precise disease identification!')

    # ── 4. PEST ───────────────────────────────────────────────────────────────
    if primary_intent == 'pest':
        if top_pest and top_pest in _PEST_GUIDE:
            return ('**{0} Management:**\n\n{1}\n\n'
                    '**General IPM approach:**\n'
                    '- Monitor twice a week — catch problems early\n'
                    '- Use pheromone traps for moth pests\n'
                    '- Release natural enemies (Trichogramma, ladybird beetles)\n'
                    '- Spray only when pest crosses economic threshold').format(
                top_pest.replace('_', ' ').title(), _PEST_GUIDE[top_pest])
        return ('**Integrated Pest Management (IPM) for crops:**\n\n'
                '- **Aphids:** Imidacloprid 0.3 ml/L or Neem oil 5 ml/L\n'
                '- **Whitefly:** Yellow sticky traps + Acetamiprid 0.2 g/L\n'
                '- **Stemborers:** Coragen 0.4 ml/L or Carbofuran granules\n'
                '- **Bollworms:** Emamectin benzoate 0.5 g/L\n'
                '- **Thrips:** Spinosad 0.3 ml/L + Blue sticky traps\n\n'
                'For best results, identify the pest first. Share a photo!')

    # ── 5. FERTILIZER ─────────────────────────────────────────────────────────
    if primary_intent == 'fertilizer':
        if 'nitrogen' in lower_q or 'urea' in lower_q:
            return '**Nitrogen Fertilizer Guide:**\n\n' + _FERTILIZER_GUIDE['nitrogen']
        if 'phosphorus' in lower_q or 'dap' in lower_q:
            return '**Phosphorus Fertilizer Guide:**\n\n' + _FERTILIZER_GUIDE['phosphorus']
        if 'potassium' in lower_q or 'potash' in lower_q:
            return '**Potassium Fertilizer Guide:**\n\n' + _FERTILIZER_GUIDE['potassium']
        if 'organic' in lower_q or 'manure' in lower_q or 'compost' in lower_q:
            return '**Organic Fertilizer Guide:**\n\n' + _FERTILIZER_GUIDE['organic']
        if 'zinc' in lower_q or 'micro' in lower_q or 'boron' in lower_q:
            return '**Micronutrient Guide:**\n\n' + _FERTILIZER_GUIDE['micronutrients']
        return ('**Fertilizer Guide for Crops:**\n\n'
                '- **Nitrogen (N):** {0}\n\n'
                '- **Phosphorus (P):** {1}\n\n'
                '- **Potassium (K):** {2}\n\n'
                '- **Micronutrients:** {3}\n\n'
                '- **Organic fertilizers:** {4}\n\n'
                '**Pro tip:** {5}').format(
            _FERTILIZER_GUIDE['nitrogen'], _FERTILIZER_GUIDE['phosphorus'],
            _FERTILIZER_GUIDE['potassium'], _FERTILIZER_GUIDE['micronutrients'],
            _FERTILIZER_GUIDE['organic'], _FERTILIZER_GUIDE['testing'])

    # ── 6. IRRIGATION ─────────────────────────────────────────────────────────
    if primary_intent == 'irrigation':
        if 'drip' in lower_q:
            return '**Drip Irrigation:**\n\n' + _IRRIGATION_GUIDE['drip']
        if 'sprinkler' in lower_q:
            return '**Sprinkler Irrigation:**\n\n' + _IRRIGATION_GUIDE['sprinkler']
        if 'when' in lower_q or 'schedul' in lower_q or 'how often' in lower_q:
            return '**Irrigation Scheduling:**\n\n' + _IRRIGATION_GUIDE['scheduling']
        return ('**Irrigation Methods Comparison:**\n\n'
                '- **Drip:** {0}\n\n'
                '- **Sprinkler:** {1}\n\n'
                '- **Flood:** {2}\n\n'
                '**Scheduling tip:** {3}').format(
            _IRRIGATION_GUIDE['drip'], _IRRIGATION_GUIDE['sprinkler'],
            _IRRIGATION_GUIDE['flood'], _IRRIGATION_GUIDE['scheduling'])

    # ── 7. SOIL ───────────────────────────────────────────────────────────────
    if primary_intent == 'soil':
        ans = ('**Soil Health Management:**\n\n'
               '**Soil testing:** {0}\n\n'
               '**pH management:**\n'
               '- Acidic soil (pH < 6.0): Add agricultural lime (CaCO3) 2–4 t/ha\n'
               '- Alkaline soil (pH > 8.0): Add gypsum 2–3 t/ha or sulphur 200 kg/ha\n\n'
               '**Organic matter:** Target 0.8–1.2% OC. Add FYM 10 t/ha, vermicompost 2 t/ha annually.\n\n'
               '**Salinity:** EC > 4 dS/m is harmful. Apply gypsum + heavy leaching. '
               'Grow salt-tolerant crops (barley, sugarbeet, cotton).').format(
            _FERTILIZER_GUIDE['testing'])
        if state and state in _REGIONAL_CROPS:
            ans += '\n\n**Soils in {0}:** {1}'.format(state.title(), _REGIONAL_CROPS[state])
        return ans

    # ── 8. GOVERNMENT SCHEMES ─────────────────────────────────────────────────
    if primary_intent == 'scheme':
        ans = '**Government Schemes for Farmers:**\n\n'
        for s in _SCHEMES:
            ans += '**{0}:** {1}\nApply at: {2}\n\n'.format(s['name'], s['desc'], s['link'])
        ans += ('**How to apply:** Visit your nearest CSC (Common Service Centre), '
                'Gram Panchayat, or Krishi Vigyan Kendra (KVK).\n'
                'Helpline: **1800-180-1551** (toll-free, 24x7)')
        return ans

    # ── 9. MARKET / PRICES ────────────────────────────────────────────────────
    if primary_intent == 'market':
        return ('**Agricultural Market Information:**\n\n'
                '**MSP (Minimum Support Price):** Government guarantees this price for 23 crops. '
                'Check latest MSP at: https://cacp.dacnet.nic.in\n\n'
                '**eNAM (National Agriculture Market):** Sell your produce online at best prices. '
                'Register at: https://enam.gov.in\n\n'
                '**Daily Mandi Prices:** Check real-time prices at: https://agmarknet.gov.in\n\n'
                '**Farmer Producer Organizations (FPOs):** Join an FPO for group selling, '
                'better negotiation power, and access to credit and inputs.\n\n'
                '**APMC reforms:** Direct selling contracts and e-trading now allowed in many states.')

    # ── 10. ORGANIC FARMING ───────────────────────────────────────────────────
    if primary_intent == 'organic':
        return ('**Organic / Natural Farming Guide:**\n\n'
                '**Zero Budget Natural Farming (ZBNF) — 4 pillars:**\n'
                '1. **Bijamrita** — Seed treatment with cow dung + urine solution\n'
                '2. **Jivamrita** — Soil inoculant (cow dung + urine + jaggery + legume flour)\n'
                '3. **Mulching** — Cover soil to retain moisture and suppress weeds\n'
                '4. **Whapasa** — Maintain 50:50 air:water balance in soil\n\n'
                '**Key organic inputs:**\n'
                '- Vermicompost: 2–4 t/ha\n'
                '- FYM: 10–15 t/ha\n'
                '- Neem oil (5 ml/L) for pest control\n'
                '- NSKE 5% (Neem Seed Kernel Extract)\n'
                '- Bt (Bacillus thuringiensis) for caterpillar pests\n\n'
                '**Certification:** Takes 3 transition years. Get certified by APEDA-accredited body. '
                'Premium price 20–40% higher in organic markets.\n\n'
                '**Scheme:** PKVY (Paramparagat Krishi Vikas Yojana) — Rs 50,000/ha for 3 years. '
                'Visit: https://pkvy.nic.in')

    # ── 11. WEATHER QUERY ─────────────────────────────────────────────────────
    if primary_intent == 'weather':
        if weather_context:
            ans = '**Current weather for your location:**\n\n{0}'.format(weather_context)
            ans += ('\n\n**Farming advice based on current conditions:**\n')
            wl = weather_context.lower()
            if any(k in wl for k in ['rain', 'drizzle', 'shower']):
                ans += ('- Postpone spraying operations — rain will wash chemicals\n'
                        '- Check field drainage, avoid waterlogging\n'
                        '- Risk of fungal diseases in 3–5 days — be ready with fungicide\n'
                        '- Good time for transplanting nursery seedlings')
            elif any(str(t) in weather_context for t in range(36, 46)):
                ans += ('- Irrigate early morning (before 9am) or evening (after 5pm)\n'
                        '- Apply mulching to conserve moisture\n'
                        '- Avoid pesticide spraying in peak heat (10am–3pm)\n'
                        '- Watch for heat stress: wilting, leaf scorch')
            else:
                ans += ('- Conditions suitable for regular field operations\n'
                        '- Good time for pesticide or fertilizer application\n'
                        '- Maintain normal irrigation schedule')
            return ans
        return ('I can give you real-time weather-based farming advice! '
                'Please **share your location** using the location button below, '
                'and I will tell you what farming activities are suitable today.')

    # ── 12. HARVEST ───────────────────────────────────────────────────────────
    if primary_intent == 'harvest':
        return ('**Crop Harvest & Post-Harvest Guide:**\n\n'
                '**Signs of maturity:**\n'
                '- Grain crops: Grain moisture 18–22%, straw yellowing\n'
                '- Vegetables: Reach target size, colour change\n'
                '- Fruits: Sugar-acid ratio, colour, aroma\n\n'
                '**Post-harvest tips:**\n'
                '- Dry grains to 12–14% moisture before storage\n'
                '- Use hermetic storage bags to prevent insect/fungal damage\n'
                '- Cold storage for perishables (tomato, potato, onion)\n\n'
                'Tell me which crop you are harvesting for specific guidance!')

    # ── 13. SEED SELECTION ────────────────────────────────────────────────────
    if primary_intent == 'seed':
        return ('**Seed Selection Guide:**\n\n'
                '- **Certified seeds** from govt agencies (NSC, SFCI, state seed corps) ensure purity\n'
                '- **Hybrid varieties** give 20–40% higher yield but seeds cannot be saved\n'
                '- **Disease-resistant varieties** reduce pesticide cost\n'
                '- Choose varieties approved for **your agro-climatic zone**\n\n'
                '**Where to buy certified seeds:**\n'
                '- National Seeds Corporation: https://indseed.co.in\n'
                '- State Seed Corporations, KVKs, ICAR institutes\n\n'
                'Tell me which crop you need seed recommendations for!')

    # ── 14. REGIONAL QUERY (state detected from location but no clear intent) ──
    if state and state in _REGIONAL_CROPS:
        return ('**Farming in {0}:**\n\n'
                'Key crops: {1}\n\n'
                'What would you like to know more about? I can help with:\n'
                '- Specific crop cultivation guides\n'
                '- Disease and pest management\n'
                '- Fertilizer recommendations\n'
                '- Government schemes for {0} farmers').format(
            state.title(), _REGIONAL_CROPS[state])

    # ── 15. Check GENERAL AGRONOMY KB if no intent/crop detected ──────────────
    for topic, info in _AGRONOMY_KB.items():
        if topic in lower_q:
            return info

    # ── 16. ABSOLUTE FALLBACK — still helpful ─────────────────────────────────
    return ('I am KrishiMitra, your AI farming assistant. I can answer any question about:\n\n'
            '- **Crop cultivation:** Wheat, Rice, Cotton, Tomato, Potato, Maize and more\n'
            '- **Diseases & pests:** Identification, treatment, prevention\n'
            '- **Fertilizers:** NPK dosing, organic options, deficiency symptoms\n'
            '- **Irrigation:** Drip, sprinkler, scheduling\n'
            '- **Government schemes:** PM-KISAN, PMFBY, soil health cards\n'
            '- **Crop selection:** Based on your region and season\n\n'
            'Please describe your farming question or problem in detail!')


def _call_gemini(prompt, image_b64=None, conv_history=None):
    # type: (str, Optional[str], Optional[list]) -> Optional[str]
    if not GEMINI_API_KEY:
        return None
    try:
        # Build contents array with history
        contents = []
        if conv_history:
            for msg in conv_history:
                # Gemini maps 'bot' to 'model'
                role = 'model' if msg.get('role') == 'bot' else 'user'
                text = msg.get('text', '')
                if text:
                    contents.append({'role': role, 'parts': [{'text': text}]})
        
        # Add current prompt
        current_parts = []
        if image_b64:
            current_parts.append({'inline_data': {'mime_type': 'image/jpeg', 'data': image_b64}})
        current_parts.append({'text': prompt})
        
        contents.append({'role': 'user', 'parts': current_parts})

        payload = {
            'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
            'contents': contents,
            'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 1024},
        }
        url = '{0}?key={1}'.format(GEMINI_API_URL, GEMINI_API_KEY)
        resp = requests.post(url, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get('candidates', [])
        if candidates:
            content = candidates[0].get('content', {})
            out_parts = content.get('parts', [])
            if out_parts:
                return out_parts[0].get('text', '').strip()
    except Exception as e:
        logger.error('Gemini API error: {0}'.format(e))
    return None


def get_ai_response(
    query,
    image_b64=None,
    crop=None,
    state=None,
    disease=None,
    weather_context=None,
    location_context=None,
    conv_history=None,
):
    # type: (str, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[list]) -> str

    # Build enriched prompt with all context
    ctx = []
    if location_context:
        ctx.append('Farmer location: {0}'.format(location_context))
    if weather_context:
        ctx.append('Current weather: {0}'.format(weather_context))
    if crop:
        ctx.append('Crop: {0}'.format(crop))
    if state:
        ctx.append('State: {0}'.format(state))
    if disease:
        ctx.append('Detected disease: {0}'.format(disease))

    ctx_str = '\n'.join(ctx)
    base = query if query else 'Please analyse this crop image and provide disease identification, treatment, fertilizer and prevention advice.'
    full_prompt = '{0}\n\nFarmer question: {1}'.format(ctx_str, base) if ctx_str else base

    # 1. Try Gemini
    logger.info('Attempting Gemini AI response')
    gemini_resp = _call_gemini(full_prompt, image_b64=image_b64, conv_history=conv_history)
    if gemini_resp:
        logger.info('Gemini response obtained')
        return gemini_resp

    # 2. Comprehensive intelligent fallback (passes location_context so state can be extracted)
    logger.info('Using intelligent knowledge-base fallback')
    return _intelligent_fallback(
        query or '',
        crop=crop,
        disease=disease,
        state=state,
        weather_context=weather_context,
        location_context=location_context,
        conv_history=conv_history,
    )
