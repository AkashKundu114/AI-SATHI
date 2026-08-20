from __future__ import annotations 

from dataclasses import dataclass 

@dataclass 
class CropSeason :
    slug :str 
    name_bengali :str 
    name_english :str 
    main_districts :list [str ]
    sowing_months :list [int ]
    harvest_months :list [int ]
    note_bengali :str 
    source_note :str =""

CROP_CALENDAR :list [CropSeason ]=[
CropSeason (
"aman_paddy","আমন ধান","Aman paddy (main monsoon-season rice)",
["Nadia","Bardhaman","Birbhum","Hooghly"],
sowing_months =[6 ,7 ,8 ],harvest_months =[11 ,12 ],
note_bengali ="সবচেয়ে বড় ধানের ফসল -- নভেম্বর-ডিসেম্বরে কাটা হয়, তখন চালের দাম "
"সাধারণত সবচেয়ে কম থাকে।",
source_note ="agrifarming.in, westbengal.pscnotes.com: Aman is WB's largest rice crop by "
"area, grown across most rice-producing districts; monsoon-transplanted, "
"winter-harvested is the standard Eastern India Aman pattern.",
),
CropSeason (
"boro_paddy","বোরো ধান","Boro paddy (irrigated winter/dry-season rice)",
["Bardhaman","Birbhum"],
sowing_months =[11 ,12 ,1 ],harvest_months =[4 ,5 ],
note_bengali ="সেচ-নির্ভর ধান, এপ্রিল-মে মাসে কাটা হয় -- গ্রীষ্মের আগে চালের সরবরাহ বাড়ে।",
source_note ="edurev.in (WBCS notes): Boro grown extensively in Burdwan/Birbhum, irrigated, "
"winter-sown/summer-harvested per the standard Eastern India pattern.",
),
CropSeason (
"aus_paddy","আউশ ধান","Aus paddy (pre-monsoon rice)",
["Nadia","Murshidabad"],
sowing_months =[4 ,5 ],harvest_months =[7 ,8 ],
note_bengali ="বর্ষার আগে বোনা, বর্ষার মধ্যে কাটা হয় -- তুলনামূলক কম এলাকায় চাষ হয়।",
source_note ="expora.in, agrifarming.in: West Bengal grows all three rice seasons "
"(Aus/Aman/Boro); Aus is the smallest of the three by area.",
),
CropSeason (
"jute","পাট","Jute",
["Nadia","Murshidabad","North 24 Parganas"],
sowing_months =[3 ,4 ],harvest_months =[7 ,8 ,9 ],
note_bengali ="ভারতের পাটের প্রায় দুই-তৃতীয়াংশ পশ্চিমবঙ্গ থেকে আসে -- বর্ষায় কাটা ও "
"জাগ দেওয়া হয়, তারপর সরবরাহ বাড়ে।",
source_note ="agrifarming.in: West Bengal meets about 66% of India's jute needs; standard "
"spring-sown/monsoon-harvested-and-retted pattern for jute in this region.",
),
CropSeason (
"potato","আলু","Potato",
["Hooghly","Bardhaman","Paschim Medinipur"],
sowing_months =[10 ,11 ],harvest_months =[1 ,2 ,3 ],
note_bengali ="হুগলি ও বর্ধমান প্রধান উৎপাদক জেলা -- জানুয়ারি-মার্চে তোলা হয়, তখন দাম "
"সবচেয়ে কম থাকে; কোল্ড স্টোরেজে রাখা আলু পরে বেশি দামে বিক্রি হয়।",
source_note ="agrifarming.in, edurev.in (WBCS notes): Hooghly and Bardhaman named "
"specifically as major potato-producing districts; West Bengal ranks 2nd "
"nationally in potato production after Uttar Pradesh (pscnotes.com).",
),
CropSeason (
"mustard","সরিষা","Mustard (oilseed)",
["Bankura","Purulia","Murshidabad"],
sowing_months =[10 ,11 ],harvest_months =[2 ,3 ],
note_bengali ="আমন ধান কাটার পর বোনা রবি শস্য -- ফেব্রুয়ারি-মার্চে ফসল ওঠে, তখন সরিষার "
"তেলের কাঁচামাল সস্তা হতে পারে।",
source_note ="westbengal.pscnotes.com: Bankura, Purulia, Murshidabad named as mustard-"
"growing districts; standard rabi-oilseed sowing/harvest window (sown after "
"monsoon, harvested Feb-Apr) matches this and the ICAR/pscnotes rabi pattern "
"described for similar oilseed/pulse crops in this region.",
),
]

def crops_at_harvest (month :int )->list [CropSeason ]:
    return [c for c in CROP_CALENDAR if month in c .harvest_months ]

def crops_being_sown (month :int )->list [CropSeason ]:
    return [c for c in CROP_CALENDAR if month in c .sowing_months ]

def find_crop (slug :str )->CropSeason |None :
    return next ((c for c in CROP_CALENDAR if c .slug ==slug ),None )

def crops_for_district (district :str )->list [CropSeason ]:
    if not district :
        return []
    d =district .strip ().lower ()
    return [c for c in CROP_CALENDAR if any (d in dist .lower ()or dist .lower ()in d for dist in c .main_districts )]
