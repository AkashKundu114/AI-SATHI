from __future__ import annotations

"""Shared knowledge base — the single source every orchestrator node reads
from for cultural, seasonal, and market-timing context.

WHY THIS EXISTS: the person asked for market/festival/seasonal/family-occasion
awareness to be "shared among all agents" rather than duplicated per node.
This module is that shared layer. `get_context_for_agents()` is the one
function every node (pricing, negotiation, catalog, market_predictor) calls
to get a consistent view of "what's going on right now that could move a
price or a customer's mood."

WHAT'S REAL VS. APPROXIMATE (read before extending this file):
- FESTIVALS: dates for lunar/religious festivals (Durga Puja, Kali Puja, Eid,
  Poush Mela, Rath Yatra, Saraswati Puja) shift year to year and were NOT
  looked up per-year here -- `month_hint` below is a typical-month pattern,
  not a fixed calendar. Before this goes to production, wire a real festival
  calendar (see `sources_todo` below) or fetch from a government/panchang
  API per year, the same way `bengali_calendar.py` already flags its
  Bangla-calendar approximation.
- LIFE-CYCLE OCCASIONS: names, sequence, and typical spend categories are
  drawn from real, cited sources -- see `source_note` on each entry.
  Hindu Bengali occasions: Wikipedia "Bengali Hindu wedding", "Aiburo
  Bhaat", "Annaprashana"; bengalipurohitbangalore.com's puja list.
  Muslim Bengali occasions (added in Pass 4, closing a gap flagged in
  Pass 1): Wikipedia "Bengali Muslim wedding" and "Walima" -- Gaye Holud is
  shared across both communities (also called "Haldi Kota"/"Tilwayi" in
  Muslim Bengali usage per that source) rather than exclusive to either;
  Nikah is the Islamic marriage contract ceremony (Mahr/dowry agreed,
  witnessed, Nikahnama signed); Walima is the groom's-family reception,
  functionally parallel to Bou Bhaat and sometimes called by that name in
  Bengali usage. Aqiqah (newborn naming/first-haircut rite) is standard,
  widely-documented Islamic practice, not from a single cited source here --
  flagged as general-knowledge rather than a specific citation, unlike the
  wedding entries above.
- WHAT'S DELIBERATELY NOT HERE: caste, gotro/gon, and rashi (zodiac). See
  the module docstring in `dignity_guidelines.py` for why -- short version:
  none of the requested features (pricing, negotiation, festival timing,
  loan documents) need it, and storing/personalizing on caste specifically
  creates real discrimination risk for a financial-assistance tool serving
  a population that can't easily contest misuse.
- SCALE: this is ~21 festivals/occasions per category, not "100+". Reaching
  100+ *verified* (not invented) entries needs either a live scraping
  pipeline against a panchang/government calendar API (see `sources_todo`
  at the bottom) or a manual research pass -- both are follow-up work, not
  something to fabricate here.
- CHRISTIAN BENGALI occasions (added Pass 5): sourcing here is genuinely
  weaker than the Hindu/Muslim entries above -- the wedding entry draws on
  a single non-academic source (a Medium personal-blog post), not a
  Wikipedia-level reference, and baptism/funeral entries are GENERAL
  Christian practice, not confirmed as Bengal-specific customs. Flagged
  per-entry via `source_note`, not silently presented as equally solid.
"""

from dataclasses import dataclass, field


@dataclass
class LifeEvent:
    slug: str
    name_bengali: str
    name_english: str
    community: str  # "hindu_bengali" | "muslim_bengali" | "shared" | "general"
    category: str  # "birth" | "wedding" | "death" | "religious" | "housewarming"
    typical_spend_categories: list[str] = field(default_factory=list)
    demand_note_bengali: str = ""
    source_note: str = ""


@dataclass
class Festival:
    slug: str
    name_bengali: str
    name_english: str
    month_hint: list[int]  # typical Gregorian month(s); NOT a fixed date -- see caveat above
    demand_categories: list[str] = field(default_factory=list)
    demand_note_bengali: str = ""


@dataclass
class SeasonalPricePattern:
    season_bengali: str
    months: list[int]
    weather_note_bengali: str
    price_effects: list[str]  # plain-language notes, not numeric claims


# ---------------------------------------------------------------------------
# Life-cycle occasions. `community` marks which population the term is most
# associated with -- several (Gaye Holud, Bou Bhaat/Walima) are shared or
# have direct parallels across communities; see source_note per entry.
# Used for: anticipating a seller's demand ("Kantha/saree orders rise before
# a wedding season"), and for the negotiation/pricing agent recognizing WHY
# a seller might need cash urgently around a family event, without ever
# asking the user to disclose more than they volunteer.
# ---------------------------------------------------------------------------
LIFE_EVENTS: list[LifeEvent] = [
    LifeEvent(
        "mukhe_bhaat", "মুখেভাত / অন্নপ্রাশন", "First rice ceremony (Annaprashan)",
        "hindu_bengali", "birth",
        typical_spend_categories=["food", "textile", "handicraft"],
        demand_note_bengali="নতুন পোশাক, মিষ্টি, ও উপহারের চাহিদা বাড়ে।",
        source_note="Wikipedia: Annaprashana -- Bengali mukhe bhaat, maternal uncle feeds first rice.",
    ),
    LifeEvent(
        "aqiqah", "আকিকা", "Aqiqah (newborn naming / first hair-cutting rite)",
        "muslim_bengali", "birth",
        typical_spend_categories=["food"],
        demand_note_bengali="মাংস ও খাবারের সামগ্রীর চাহিদা বাড়ে।",
        source_note="General, widely-documented Islamic practice -- not from a single cited source "
                     "in this pass, unlike the wedding entries below.",
    ),
    LifeEvent(
        "biye", "বিয়ে", "Wedding", "hindu_bengali", "wedding",
        typical_spend_categories=["textile", "food", "handicraft"],
        demand_note_bengali="শাড়ি, গয়নার মতো সাজ, ও মিষ্টির অর্ডার বাড়ে।",
        source_note="Wikipedia: Bengali Hindu wedding.",
    ),
    LifeEvent(
        "gaye_holud", "গায়ে হলুদ", "Turmeric ceremony", "shared", "wedding",
        typical_spend_categories=["textile", "food"],
        demand_note_bengali="হলুদ শাড়ি ও ফুলের সাজের চাহিদা বাড়ে।",
        source_note="Wikipedia: Bengali Hindu wedding AND Bengali Muslim wedding -- practiced across "
                     "both communities; also called Haldi Kota / Tilwayi in Muslim Bengali usage.",
    ),
    LifeEvent(
        "aiburo_bhaat", "আইবুড়ো ভাত", "Pre-wedding farewell rice meal (bride/groom's last meal as unmarried)",
        "hindu_bengali", "wedding",
        typical_spend_categories=["food"],
        demand_note_bengali="মাছ ও বিশেষ পদের চাহিদা বাড়ে -- ইলিশ, চিংড়ি প্রধান।",
        source_note="Wikipedia: Aiburo Bhaat.",
    ),
    LifeEvent(
        "nikah", "নিকাহ", "Nikah (Islamic marriage contract ceremony -- Mahr agreed, witnessed, Nikahnama signed)",
        "muslim_bengali", "wedding",
        typical_spend_categories=["food", "textile"],
        demand_note_bengali="নতুন পোশাক ও অনুষ্ঠানের খাবারের চাহিদা বাড়ে।",
        source_note="Wikipedia: Bengali Muslim wedding -- Kazi/Imam conducts, Mahr (mandatory gift to "
                     "bride) agreed, Nikahnama (marriage contract) signed by both parties.",
    ),
    LifeEvent(
        "walima", "ওলিমা", "Walima (groom's-family wedding reception, sometimes called Bou Bhaat in Bengali usage)",
        "muslim_bengali", "wedding",
        typical_spend_categories=["food", "textile"],
        demand_note_bengali="বড় অনুষ্ঠানের খাবার ও শাড়ি/পোশাকের চাহিদা বাড়ে।",
        source_note="Wikipedia: Walima -- reception banquet after Nikah, hosted by groom's family; "
                     "several Bengali sources use 'Bou Bhaat' and 'Walima' interchangeably for this event.",
    ),
    LifeEvent(
        "bou_bhaat", "বৌভাত", "Reception where the bride formally serves rice to the groom's family",
        "hindu_bengali", "wedding",
        typical_spend_categories=["food", "textile"],
        demand_note_bengali="বড় অনুষ্ঠানের খাবার ও শাড়ির চাহিদা বাড়ে -- ইলিশ ঐতিহ্যবাহী পদ।",
        source_note="Wikipedia: Bengali Hindu wedding; azafashions.com Boubhat guide.",
    ),
    LifeEvent(
        "sasthi_puja", "ষষ্ঠী পূজা", "Sasthi puja (child-protection / fertility rites, several forms through the year)",
        "hindu_bengali", "religious",
        typical_spend_categories=["food", "handicraft"],
        demand_note_bengali="ফল, মিষ্টি ও পূজার সামগ্রীর চাহিদা বাড়ে।",
        source_note="bengalipurohitbangalore.com puja list.",
    ),
    LifeEvent(
        "shraddha", "শ্রাদ্ধ", "Memorial rite for a deceased family member",
        "hindu_bengali", "death",
        typical_spend_categories=["food"],
        demand_note_bengali="নিরামিষ ভোজের সামগ্রীর চাহিদা বাড়ে; উদযাপনমূলক প্রচার এড়িয়ে চলা উচিত।",
        source_note="bengalipurohitbangalore.com; general Hindu samskara literature.",
    ),
    LifeEvent(
        "griha_pravesh", "গৃহপ্রবেশ", "Housewarming for a new home", "hindu_bengali", "housewarming",
        typical_spend_categories=["handicraft", "food"],
        demand_note_bengali="ঘর সাজানোর সামগ্রী ও মিষ্টির চাহিদা বাড়ে।",
        source_note="bengalipurohitbangalore.com puja list.",
    ),
    LifeEvent(
        "christian_bengali_wedding", "খ্রিস্টান বিয়ে", "Bengali Christian church wedding",
        "christian_bengali", "wedding",
        typical_spend_categories=["textile", "food"],
        demand_note_bengali="নতুন পোশাক ও অনুষ্ঠানের খাবারের চাহিদা বাড়ে।",
        source_note="WEAKER SOURCE than the entries above -- a single non-academic blog post "
                     "(Medium, 'Rituals followed by Bengali Christian in Wedding'), not a "
                     "Wikipedia-level reference: church ceremony, vows, ring exchange, candle "
                     "lighting; comparatively few pre/post-wedding rituals versus Hindu/Muslim "
                     "Bengali weddings per that source. Verify against a stronger source before "
                     "treating this as equally reliable to the entries above.",
    ),
    LifeEvent(
        "christian_bengali_baptism", "খ্রিস্টীয় দীক্ষাস্নান (ব্যাপ্টিজম)", "Baptism / christening",
        "christian_bengali", "birth",
        typical_spend_categories=["food", "textile"],
        demand_note_bengali="অতিথি আপ্যায়ন ও নতুন পোশাকের চাহিদা বাড়তে পারে।",
        source_note="GENERAL Christian practice (initiation rite, often water-based), not "
                     "confirmed as a specifically Bengal-documented custom in this pass -- same "
                     "honesty flag as the Aqiqah entry above.",
    ),
    LifeEvent(
        "christian_bengali_funeral_prayer", "প্রার্থনা সভা (খ্রিস্টীয় শেষকৃত্য)", "Christian funeral / memorial prayer service",
        "christian_bengali", "death",
        typical_spend_categories=["food"],
        demand_note_bengali="সাধারণ ভোজের সামগ্রীর চাহিদা সামান্য বাড়তে পারে; উদযাপনমূলক প্রচার এড়িয়ে চলা উচিত।",
        source_note="GENERAL Christian funeral-rite practice, not a specifically Bengal-documented "
                     "custom in this pass -- flagged the same way as the baptism entry above.",
    ),
]

# NOTE: only 14 entries above -- a real "100+" life-event catalog would need
# every named regional puja (Jagadhhatri, Bipattarini, Manosha, etc. --
# already listed by name only, no demand data, in the Hindu source above),
# deeper Muslim Bengali entries beyond the wedding/birth ones here, and
# stronger sourcing for the Christian Bengali entries just added. Flagged,
# not filled with guesses.


# ---------------------------------------------------------------------------
# West Bengal festival calendar -- month_hint is typical-month, NOT a fixed
# date (lunar festivals move every year). Wire a real panchang/government
# calendar API before relying on this for anything date-specific.
# ---------------------------------------------------------------------------
FESTIVALS: list[Festival] = [
    Festival("poila_boishakh", "পয়লা বৈশাখ", "Bengali New Year", [4],
             ["food", "handicraft", "textile"], "নতুন বছরের কেনাকাটা ও মিষ্টির চাহিদা বাড়ে।"),
    Festival("rath_yatra", "রথযাত্রা", "Rath Yatra", [6, 7],
             ["food", "handicraft"], "মেলার সামগ্রী ও খাবারের চাহিদা বাড়ে।"),
    Festival("saraswati_puja", "সরস্বতী পূজা", "Saraswati Puja", [1, 2],
             ["food", "handicraft"], "ফল, মিষ্টি ও পূজার সামগ্রীর চাহিদা বাড়ে।"),
    Festival("durga_puja", "দুর্গা পূজা", "Durga Puja", [9, 10],
             ["textile", "food", "handicraft"], "সবচেয়ে বড় মরসুম -- শাড়ি, নতুন পোশাক, মিষ্টির চাহিদা তুঙ্গে থাকে।"),
    Festival("kali_puja", "কালী পূজা / দীপাবলি", "Kali Puja / Diwali", [10, 11],
             ["food", "handicraft"], "মোমবাতি, প্রদীপ ও মিষ্টির চাহিদা বাড়ে।"),
    Festival("jagadhatri_puja", "জগদ্ধাত্রী পূজা", "Jagadhatri Puja", [11],
             ["food", "handicraft"], "স্থানীয়ভাবে (বিশেষত চন্দননগর) চাহিদা বাড়ে।"),
    Festival("nabanna", "নবান্ন", "Nabanna (new-harvest rice festival)", [11, 12],
             ["food"], "নতুন চালের পিঠা ও মিষ্টির চাহিদা বাড়ে।"),
    Festival("poush_mela", "পৌষ মেলা", "Poush Mela", [12],
             ["handicraft", "food"], "হস্তশিল্প ও পিঠার মেলা -- গ্রামীণ কারুশিল্পের চাহিদা বাড়ে।"),
    Festival("christmas", "বড়দিন", "Christmas", [12],
             ["food", "handicraft"], "কেক ও উপহারের চাহিদা বাড়ে, বিশেষত শহরাঞ্চলে।"),
    Festival("eid_ul_fitr", "ঈদ-উল-ফিতর", "Eid ul-Fitr", [3, 4, 5],
             ["food", "textile"], "নতুন পোশাক ও মিষ্টির চাহিদা বাড়ে। (চান্দ্র ক্যালেন্ডার -- তারিখ প্রতি বছর বদলায়)"),
    Festival("eid_ul_adha", "ঈদ-উল-আযহা / বকরি ঈদ", "Eid ul-Adha", [6, 7, 8],
             ["food"], "মাংসের চাহিদা বাড়ে। (চান্দ্র ক্যালেন্ডার -- তারিখ প্রতি বছর বদলায়)"),
]


# ---------------------------------------------------------------------------
# Seasonal weather -> generic price pattern. Plain-language, non-numeric --
# these are directional notes ("monsoon disrupts leafy-vegetable supply"),
# not price predictions. Real numeric seasonality should come from
# `market_service/aggregator.py`'s own ledger-derived trend classification
# (already built) and Agmarknet, not from this static file.
# ---------------------------------------------------------------------------
SEASONAL_PATTERNS: list[SeasonalPricePattern] = [
    SeasonalPricePattern(
        "গ্রীষ্ম (এপ্রিল-জুন)", [4, 5, 6],
        "তীব্র গরম -- পচনশীল সবজি ও ফুল তাড়াতাড়ি নষ্ট হয়।",
        ["তাজা শাকসবজির সরবরাহ কমে, দাম বাড়তে পারে",
         "আম, লিচুর মৌসুম -- সরবরাহ বেশি থাকলে দাম কমে",
         "শুকনো/সংরক্ষিত পণ্য (মুড়ি, পাপড়) বিক্রি স্থিতিশীল থাকে"],
    ),
    SeasonalPricePattern(
        "বর্ষা (জুলাই-সেপ্টেম্বর)", [7, 8, 9],
        "ভারী বৃষ্টি -- যাতায়াত ও ফসল তোলা ব্যাহত হতে পারে।",
        ["শাকসবজি সরবরাহ অনিয়মিত হয়, দাম ওঠানামা করে",
         "মাছ ধরা কমতে পারে নদী/পুকুরে জল বাড়লে, তবে ইলিশের মৌসুমও এই সময়",
         "তাঁত/সেলাইয়ের কাজ ঘরে বসে করার সময় বেশি পাওয়া যায়"],
    ),
    SeasonalPricePattern(
        "শরৎ-হেমন্ত (অক্টোবর-নভেম্বর)", [10, 11],
        "পূজার মরসুম, আবহাওয়া মনোরম -- বিক্রির সেরা সময়।",
        ["টেক্সটাইল ও হস্তশিল্পের চাহিদা তুঙ্গে (দুর্গা পূজা, কালী পূজা)",
         "নতুন ধান ওঠে -- চাল ও চালজাত পণ্যের সরবরাহ বাড়ে"],
    ),
    SeasonalPricePattern(
        "শীত (ডিসেম্বর-ফেব্রুয়ারি)", [12, 1, 2],
        "শুকনো, ঠান্ডা আবহাওয়া -- সবজি চাষের ভালো মরসুম।",
        ["শীতকালীন সবজি (ফুলকপি, বাঁধাকপি, মটরশুঁটি) সরবরাহ বেশি, দাম কম থাকে",
         "পিঠা-পুলি ও মধুর চাহিদা বাড়ে (নবান্ন, পৌষ মেলা)",
         "খেজুর গুড়ের মৌসুম -- বাড়তি দামে ভালো বিক্রি হতে পারে"],
    ),
    SeasonalPricePattern(
        "বসন্ত (মার্চ)", [3],
        "শুষ্ক, উষ্ণ হতে শুরু করা আবহাওয়া।",
        ["সরস্বতী পূজার সামগ্রীর চাহিদা (ফেব্রুয়ারি থেকে চলতে থাকে)",
         "গ্রীষ্মের আগে হালকা সুতির কাপড়ের চাহিদা বাড়তে শুরু করে"],
    ),
]


@dataclass
class DistrictMela:
    """District/block-specific fairs, distinct from the statewide FESTIVALS
    list above. Added Pass 6, closing the 'add block-specific melas once
    sourced per-block' item in sources_todo. `district` uses the same
    plain-text district names as `users.district`/`shg_groups.district`
    elsewhere in this schema (e.g. 'Birbhum', 'Bankura') -- matched via
    simple substring containment in get_context_for_agents, not an exact
    enum, since district spelling varies across this codebase's own free-text
    fields (see shared/db/models.py -- district is a plain VARCHAR, not a
    lookup table)."""
    slug: str
    name_bengali: str
    name_english: str
    district: str
    month_hint: list[int]
    demand_categories: list[str] = field(default_factory=list)
    demand_note_bengali: str = ""
    source_note: str = ""


DISTRICT_MELAS: list[DistrictMela] = [
    DistrictMela(
        "gangasagar_mela", "গঙ্গাসাগর মেলা", "Gangasagar Mela", "South 24 Parganas", [1],
        ["food", "handicraft"],
        "মকর সংক্রান্তির সময় (মধ্য জানুয়ারি) সাগরদ্বীপে লক্ষ লক্ষ তীর্থযাত্রীর সমাগম হয় -- "
        "খাবার ও ধর্মীয় সামগ্রীর চাহিদা তুঙ্গে থাকে।",
        source_note="Multiple sources (testbook.com, indianholiday.com, two-together.com): one of "
                     "India's largest religious gatherings, held annually at Sagar Island on Makar "
                     "Sankranti (mid-January).",
    ),
    DistrictMela(
        "joydev_kenduli_mela", "জয়দেব কেন্দুলি মেলা / বাউল মেলা", "Joydev Kenduli Mela (Baul Mela)",
        "Birbhum", [1],
        ["handicraft", "food"],
        "মকর সংক্রান্তিতে ৩ দিনের মেলা -- বাউল গান ও হস্তশিল্পের চাহিদা বাড়ে।",
        source_note="cultureandheritage.org, theholidaystory.com: 3-day fair at Kenduli village on "
                     "the Ajay River, Birbhum district, starting Makar Sankranti (mid-January); "
                     "famous for Baul (UNESCO-recognized) musicians.",
    ),
    DistrictMela(
        "bishnupur_mela", "বিষ্ণুপুর মেলা", "Bishnupur/Vishnupur Mela", "Bankura", [12],
        ["handicraft"],
        "ডিসেম্বরে টেরাকোটা ও হস্তশিল্পের মেলা -- কারুশিল্পের চাহিদা বাড়ে।",
        source_note="adotrip.com, testbook.com: annual December festival in Bishnupur, Bankura "
                     "district, centered on terracotta temple heritage and classical (Bishnupur "
                     "Gharana) music.",
    ),
    DistrictMela(
        "rash_mela", "রাস মেলা", "Rash Mela", "Cooch Behar", [11, 12],
        ["handicraft", "food"],
        "নভেম্বর-ডিসেম্বরে (কার্তিক মাসে) মাসব্যাপী মেলা -- হস্তশিল্প ও খাবারের চাহিদা বাড়ে।",
        source_note="indianetzone.com, testbook.com: month-long fair in Cooch Behar during the "
                     "Hindu month of Kartik, tied to the Cooch Behar royal Rash Leela tradition.",
    ),
    DistrictMela(
        "tusu_mela", "টুসু মেলা / পরব", "Tusu Mela / Tusu Parab", "Purulia", [12, 1],
        ["handicraft", "food"],
        "টুসু পরব ডিসেম্বর থেকে মকর সংক্রান্তি পর্যন্ত -- আদিবাসী হস্তশিল্পের চাহিদা বাড়ে।",
        source_note="two-together.com: month-long tribal harvest festival across Purulia, Bankura, "
                     "and parts of Paschim Medinipur, starting Aghrayan Sankranti and culminating "
                     "at Makar Sankranti (mid-January) with choudala immersion; primarily a "
                     "women-led festival per the same source.",
    ),
]



def get_context_for_agents(month: int, block: str | None = None, district: str | None = None) -> dict:
    """The single shared entry point every orchestrator node should call
    (pricing_node, negotiation_node, catalog_node, market_predictor_node)
    to get consistent seasonal/festival context instead of each node
    hand-rolling its own guess. Returns plain data, not phrased Bengali
    prose -- nodes still route final phrasing through model_router per the
    existing "deterministic core, LLM only for language" pattern.

    `block` is accepted for backward compatibility but not used to filter
    anything -- West Bengal's statewide FESTIVALS are the same everywhere.
    `district` (added Pass 6) DOES filter DISTRICT_MELAS below, via a
    simple case-insensitive substring match against `users.district` /
    `shg_groups.district`'s free-text value -- deliberately loose rather
    than an exact-match enum, since this schema stores district as plain
    text (see shared/db/models.py) and "Birbhum" vs "birbhum " vs
    "Birbhum district" should all still match. Returns an empty list, never
    a guess, if `district` is unset or doesn't match anything known.
    """
    upcoming_festivals = [f for f in FESTIVALS if month in f.month_hint]
    season = next((s for s in SEASONAL_PATTERNS if month in s.months), None)

    upcoming_melas: list[DistrictMela] = []
    if district:
        district_norm = district.strip().lower()
        upcoming_melas = [
            m for m in DISTRICT_MELAS
            if month in m.month_hint and (m.district.lower() in district_norm or district_norm in m.district.lower())
        ]

    return {
        "month": month,
        "upcoming_festivals": [
            {"slug": f.slug, "name_bengali": f.name_bengali, "demand_categories": f.demand_categories,
             "note": f.demand_note_bengali}
            for f in upcoming_festivals
        ],
        "upcoming_district_melas": [
            {"slug": m.slug, "name_bengali": m.name_bengali, "district": m.district,
             "demand_categories": m.demand_categories, "note": m.demand_note_bengali}
            for m in upcoming_melas
        ],
        "season": None if season is None else {
            "name": season.season_bengali, "weather_note": season.weather_note_bengali,
            "price_effects": season.price_effects,
        },
    }


def find_life_event(slug: str) -> LifeEvent | None:
    return next((e for e in LIFE_EVENTS if e.slug == slug), None)


def life_events_by_community(community: str) -> list[LifeEvent]:
    """`community` matches "hindu_bengali" | "muslim_bengali" | "shared".
    Note "shared" entries (e.g. Gaye Holud) should be included for BOTH
    communities' views -- callers wanting a specific community's full list
    should union their community's entries with "shared" ones, not query
    "shared" alone."""
    return [e for e in LIFE_EVENTS if e.community == community]


# Follow-up research needed before claiming "100+ verified" coverage:
sources_todo = [
    "Wire a real panchang/lunar-calendar API (e.g. drikpanchang.com has no "
    "free API; check for a government or licensed provider) for exact "
    "yearly festival dates instead of month_hint approximations.",
    "Strengthen sourcing for the three Christian Bengali entries added in "
    "Pass 5 -- currently one weak blog source (wedding) plus two "
    "general-practice entries (baptism, funeral) with no Bengal-specific "
    "citation. Find an academic or Wikipedia-level source before treating "
    "these as equally solid to the Hindu/Muslim entries.",
    "Add MORE block/district-specific melas beyond the 5 added in Pass 6 "
    "(Gangasagar, Joydev Kenduli, Bishnupur, Rash Mela, Tusu) -- e.g. "
    "Poush Mela (Santiniketan/Birbhum), Chandidas Mela (Nanoor, Birbhum), "
    "and district fairs outside the ones already sourced.",
    "Replace static SEASONAL_PATTERNS with live weather-API-driven notes "
    "(IMD West Bengal forecast) for the current week, not just typical-month.",
    "Verify Aqiqah's Bengal-specific customs/spend pattern with a real "
    "source -- currently general Islamic-practice knowledge, not a "
    "Bengal-specific citation like the wedding entries.",
]
