from __future__ import annotations 

from sqlalchemy import select 

from services .orchestrator .state import ConversationState 
from shared .db .models import User 
from shared .db .session import get_db_session 

from shared .metering .usage_tracker import get_user_plan_tier 

async def load_user_profile_node (state :ConversationState )->dict :
    phone_number =state .get ("phone_number")or state .get ("user_id")or "+919876543210"
    db_error =False 

    try :
        async with get_db_session ()as db :
            user =(
            await db .execute (select (User ).where (User .phone_number ==phone_number ))
            ).scalar_one_or_none ()
    except Exception :
        db_error =True 
        user =None 

    if db_error :
        return {
        "is_new_user":True ,
        "user_id":None ,
        "user_profile":None ,
        "trace":["load_user_profile:db_error_treated_as_new_user"],
        }

    if user is None :
        return {
        "is_new_user":True ,
        "user_id":None ,
        "user_profile":None ,
        "trace":["load_user_profile:new_user"],
        }

    plan_tier =await get_user_plan_tier (str (user .id ))

    profile ={
    "business_categories":user .business_categories or [],
    "self_reported_literacy":user .self_reported_literacy ,
    "preferred_modality":user .preferred_modality ,
    "dialect_hint":user .dialect_hint ,
    "ledger_correction_rate":float (user .ledger_correction_rate or 0.0 ),
    "trust_stage":user .trust_stage ,
    "block":user .block or "সিঙ্গুর",
    "district":user .district or "হুগলী",
    "plan_tier":plan_tier ,
    "verification_status":getattr (user ,"verification_status","verified")or "verified",
    "user_type":getattr (user ,"user_type","shg_member"),
    }
    return {
    "is_new_user":False ,
    "onboarding_step":"DONE",
    "user_id":str (user .id ),
    "user_profile":profile ,
    "trace":["load_user_profile:loaded"],
    }
