from __future__ import annotations 

import asyncio 
import logging 

from sqlalchemy import text 
from shared .db .session import get_db_session 

logger =logging .getLogger ("prune_dedup_tables")
logging .basicConfig (level =logging .INFO )

async def prune ()->tuple [int ,int ]:
    async with get_db_session ()as db :
        row =(await db .execute (text ("SELECT * FROM prune_webhook_dedup();"))).fetchone ()
        await db .commit ()
    return row [0 ],row [1 ]

async def main ()->None :
    dedup_deleted ,rate_limit_deleted =await prune ()
    logger .info (
    "pruned %d webhook_dedup rows and %d rate_limit_counters rows",
    dedup_deleted ,rate_limit_deleted ,
    )

if __name__ =="__main__":
    asyncio .run (main ())
