from __future__ import annotations 

import asyncio 
from datetime import datetime ,timedelta ,timezone 

from sqlalchemy import text 

from shared .db .session import get_db_session 

ALERT_BUDGET_CONSUMED_FRACTION =0.80 
ALERT_SINGLE_USER_SHARE_FRACTION =0.10 

async def _budget_rows ()->list [dict ]:
    async with get_db_session ()as db :
        rows =(
        await db .execute (
        text ("SELECT vendor, used, total_budget, degraded_mode, hard_stopped FROM credit_budget")
        )
        ).fetchall ()
    return [
    {
    "vendor":r [0 ],"used":float (r [1 ]),"total_budget":float (r [2 ]),
    "degraded_mode":bool (r [3 ]),"hard_stopped":bool (r [4 ]),
    }
    for r in rows 
    ]

async def _top_users_last_24h (vendor :str ,limit :int =5 )->list [tuple [str ,float ]]:
    since =datetime .now (timezone .utc )-timedelta (hours =24 )
    async with get_db_session ()as db :
        rows =(
        await db .execute (
        text (

        ),
        {"vendor":vendor ,"since":since ,"limit":limit },
        )
        ).fetchall ()
    return [(str (r [0 ]),float (r [1 ]))for r in rows ]

async def main ()->None :
    budgets =await _budget_rows ()
    if not budgets :
        print ("No rows in credit_budget - has migrations/0012_credit_budget.sql been applied?")
        return 

    print ("="*60 )
    print ("AI-SATHI - Credit Budget Status")
    print ("="*60 )

    for b in budgets :
        fraction =b ["used"]/b ["total_budget"]if b ["total_budget"]else 0.0 
        flag =""
        if b ["hard_stopped"]:
            flag ="  🛑 HARD-STOPPED"
        elif b ["degraded_mode"]:
            flag ="  ⚠️  DEGRADED MODE"
        elif fraction >=ALERT_BUDGET_CONSUMED_FRACTION :
            flag ="  ⚠️  ALERT: over 80% consumed"

        print (f"\n{b ['vendor'].upper ()}: {b ['used']:.1f} / {b ['total_budget']:.1f} credits used ({fraction :.0%}){flag }")

        top_users =await _top_users_last_24h (b ["vendor"])
        if top_users :
            print ("  Top users (last 24h):")
            for user_id ,total in top_users :
                share =total /b ["total_budget"]if b ["total_budget"]else 0.0 
                share_flag ="  ⚠️ >10% of TOTAL budget"if share >=ALERT_SINGLE_USER_SHARE_FRACTION else ""
                print (f"    {user_id }: {total :.1f} credits ({share :.1%} of total budget){share_flag }")

    print ("\n"+"="*60 )
    any_alert =any (
    b ["hard_stopped"]or b ["degraded_mode"]or (b ["used"]/b ["total_budget"]if b ["total_budget"]else 0 )>=ALERT_BUDGET_CONSUMED_FRACTION 
    for b in budgets 
    )
    if any_alert :
        print ("⚠️  One or more vendors need attention - see flags above.")
    else :
        print ("✅ All budgets within normal range.")

if __name__ =="__main__":
    asyncio .run (main ())
