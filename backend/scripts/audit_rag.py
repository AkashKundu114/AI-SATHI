from __future__ import annotations 

import argparse 
import asyncio 
import csv 
import random 
import sys 
from pathlib import Path 

sys .path .insert (0 ,str (Path (__file__ ).resolve ().parents [1 ]))

QUESTION_TEMPLATES =[
"{scheme} থেকে মাসে কত টাকা পাওয়া যায়?",
"{scheme} প্রকল্পে আবেদনের যোগ্যতা কী?",
"{scheme} এর জন্য কী কী কাগজপত্র লাগবে?",
"{scheme} তে আবেদন করলে টাকা পেতে কতদিন সময় লাগে?",
"{scheme} প্রকল্প কি এখনো চালু আছে?",
]

async def _active_scheme_names ()->list [str ]:
    from sqlalchemy import text 
    from shared .db .session import get_db_session 

    async with get_db_session ()as db :
        rows =(
        await db .execute (text ("SELECT DISTINCT scheme_name FROM scheme_documents WHERE is_active = true"))
        ).fetchall ()
    return [r [0 ]for r in rows ]

async def _run_one (scheme_name :str ,question :str )->dict :
    from services .rag_service .pipeline import query_scheme_rag 
    from services .rag_service .grounding_verifier import verify_grounding 

    result =await query_scheme_rag (
    query =question ,
    user_context ={"phone_number":"audit-script"},
    scheme_filter =[scheme_name ],
    )
    grounding =verify_grounding (result ["answer_bengali"],result ["citations_full"])
    return {
    "scheme_name":scheme_name ,
    "question":question ,
    "answer_bengali":result ["answer_bengali"],
    "all_grounded":grounding ["all_grounded"],
    "ungrounded_assertions":"; ".join (grounding ["ungrounded"]),
    "num_chunks_used":grounding ["num_chunks_used"],
    }

async def main_async (n :int ,output_path :Path ,only_scheme :str |None ,dry_run :bool )->None :
    schemes =[only_scheme ]if only_scheme else await _active_scheme_names ()

    if not schemes :
        print ("No active schemes found in scheme_documents. Seed some first with scripts/seed_schemes.py.")
        return 

    print (f"Found {len (schemes )} active scheme(s): {', '.join (schemes )}")

    pairs =[]
    for _ in range (n ):
        scheme =random .choice (schemes )
        question =random .choice (QUESTION_TEMPLATES ).format (scheme =scheme )
        pairs .append ((scheme ,question ))

    if dry_run :
        print (f"\n[dry-run] Would run {len (pairs )} Q&A pairs - no DB/model calls made:")
        for scheme ,question in pairs [:10 ]:
            print (f"  - [{scheme }] {question }")
        if len (pairs )>10 :
            print (f"  ... and {len (pairs )-10 } more")
        return 

    results =[]
    for i ,(scheme ,question )in enumerate (pairs ,start =1 ):
        print (f"[{i }/{len (pairs )}] {scheme }: {question }")
        try :
            results .append (await _run_one (scheme ,question ))
        except Exception as exc :
            results .append ({
            "scheme_name":scheme ,"question":question ,"answer_bengali":"",
            "all_grounded":False ,"ungrounded_assertions":f"ERROR: {exc }",
            "num_chunks_used":0 ,
            })

    results .sort (key =lambda r :r ["all_grounded"])

    with open (output_path ,"w",newline ="",encoding ="utf-8")as f :
        writer =csv .DictWriter (f ,fieldnames =[
        "scheme_name","question","answer_bengali","all_grounded",
        "ungrounded_assertions","num_chunks_used",
        ])
        writer .writeheader ()
        writer .writerows (results )

    ungrounded_count =sum (1 for r in results if not r ["all_grounded"])
    print (f"\nWrote {len (results )} rows to {output_path }")
    print (f"⚠️  {ungrounded_count }/{len (results )} flagged ungrounded - review those rows first.")
    if ungrounded_count :
        print (
        "A non-zero ungrounded count here means either: (a) a genuine grounding "
        "gap worth a bug report, or (b) the question asked something not covered "
        "by any seeded document for that scheme, which is the expected, correct "
        "fallback behavior - read the answer_bengali column to tell which."
        )

def main ()->None :
    parser =argparse .ArgumentParser (description =__doc__ ,formatter_class =argparse .RawDescriptionHelpFormatter )
    parser .add_argument ("--n",type =int ,default =50 ,help ="Number of Q&A pairs to sample (default: 50)")
    parser .add_argument ("--output",type =Path ,default =Path ("audit_report.csv"),help ="CSV output path")
    parser .add_argument ("--scheme",type =str ,default =None ,help ="Restrict sampling to a single scheme_name")
    parser .add_argument ("--dry-run",action ="store_true",
    help ="List the sampled Q&A pairs without calling the DB/model")
    args =parser .parse_args ()

    asyncio .run (main_async (args .n ,args .output ,args .scheme ,args .dry_run ))

if __name__ =="__main__":
    main ()
