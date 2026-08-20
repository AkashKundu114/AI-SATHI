from __future__ import annotations 

import json 
import re 

from services .orchestrator .model_router import route_vision_completion ,route_completion ,TaskCriticality 
from shared .catalog .local_products import CATEGORY_PRICE_RANGES ,find_local_product_by_slug 
from shared .knowledge .dignity_guidelines import DIGNITY_RULES_BENGALI 

VISION_PROMPT =(
"এই ছবিতে কী পণ্য দেখছ? শুধুমাত্র এই JSON ফরম্যাটে ফেরত দাও:\n"
'{"product_type": "<ইংরেজিতে সংক্ষিপ্ত, যেমন \'kantha saree\'>",\n'
' "material": "<যদি বোঝা যায়>",\n'
' "notable_features": ["<২-৩টি লক্ষণীয় বৈশিষ্ট্য>"],\n'
' "category": "<textile|food|handicraft|agriculture|other>"}'
)

CAPTION_SYSTEM =(
"তুমি গ্রামীণ স্বনির্ভর গোষ্ঠীর মহিলাদের জন্য একজন বিজ্ঞাপন লেখক।\n\n"
f"{DIGNITY_RULES_BENGALI }\n\n"
"দেওয়া পণ্যের তথ্যের ভিত্তিতে, শুধুমাত্র এই JSON ফরম্যাটে ফেরত দাও, অন্য কিছু লিখো না:\n\n"
'{"web_caption": "<৪ লাইনের মধ্যে: পণ্যের নাম, ১-২টি বৈশিষ্ট্য, '
'দামের পরিসীমা (₹X-₹Y), সংক্ষিপ্ত CTA - কাস্টমার গ্রুপে পাঠানোর উপযোগী, উষ্ণ সুরে>",\n'
' "ad_caption": "<২ লাইনের মধ্যে: হুক + জরুরিতা/আকর্ষণ + CTA - বিজ্ঞাপনের জন্য '
'সংক্ষিপ্ত ও আকর্ষণীয়, বেশি ইমোজি নয়>"}\n\n'
"নিয়ম: অতিরিক্ত প্রতিশ্রুতি বা মিথ্যা দাবি করো না - শুধু যা ছবিতে দেখা যাচ্ছে তার ভিত্তিতে লেখো। "
"পণ্যের মান নিয়ে কখনো নেতিবাচক বা করুণাসূচক মন্তব্য কোরো না (যেমন 'সাধারণ মানের হলেও')।"
)

_FALLBACK_WEB_CAPTION ="✨ নতুন পণ্য এসেছে! বিস্তারিত জানতে যোগাযোগ করুন।"
_FALLBACK_AD_CAPTION ="নতুন পণ্য এখন উপলব্ধ - আজই অর্ডার করুন!"

async def analyze_product_image (image_bytes :bytes ,user_id :str |None =None )->dict :
    result =await route_vision_completion (
    prompt =VISION_PROMPT ,image_bytes =image_bytes ,criticality =TaskCriticality .ROUTINE ,user_id =user_id 
    )
    try :
        parsed =json .loads (re .sub (r"```json|```","",result ["text"]).strip ())
    except (json .JSONDecodeError ,TypeError ):
        parsed ={"product_type":"পণ্য","category":"other","notable_features":[]}

    parsed ["vision_model_used"]=result ["model_used"]
    parsed .setdefault ("category","other")
    return parsed 

def _price_range_for (product_info :dict )->tuple [float ,float ]:
    product_type =product_info .get ("product_type","")
    local_match =find_local_product_by_slug (product_type )
    if local_match :
        return local_match ["price_min"],local_match ["price_max"]

    category =product_info .get ("category","other")
    return CATEGORY_PRICE_RANGES .get (category ,CATEGORY_PRICE_RANGES ["other"])

async def generate_captions (
product_info :dict ,shg_name :str ="",user_id :str |None =None 
)->tuple [dict ,tuple [float ,float ]]:
    price_min ,price_max =_price_range_for (product_info )

    prompt =(
    f"পণ্যের তথ্য: {json .dumps (product_info ,ensure_ascii =False )}\n"
    f"দামের পরিসীমা নির্দেশিকা: ₹{price_min }-₹{price_max }\n"
    f"গোষ্ঠীর নাম (যদি থাকে): {shg_name }\n\n"
    "উপরের তথ্যের ভিত্তিতে দুটি ক্যাপশন লেখো।"
    )
    result =await route_completion (
    system =CAPTION_SYSTEM ,prompt =prompt ,criticality =TaskCriticality .ROUTINE ,confidence_floor =0.0 ,user_id =user_id 
    )

    try :
        parsed =json .loads (re .sub (r"```json|```","",result ["text"]).strip ())
        captions ={
        "web_caption":parsed .get ("web_caption")or _FALLBACK_WEB_CAPTION ,
        "ad_caption":parsed .get ("ad_caption")or _FALLBACK_AD_CAPTION ,
        }
    except (json .JSONDecodeError ,TypeError ):
        captions ={"web_caption":_FALLBACK_WEB_CAPTION ,"ad_caption":_FALLBACK_AD_CAPTION }

    return captions ,(price_min ,price_max )
