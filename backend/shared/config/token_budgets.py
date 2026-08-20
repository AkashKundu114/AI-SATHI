from __future__ import annotations 

TOKEN_BUDGETS :dict [str ,int ]={
"greeting":50 ,
"trivial_reply":50 ,
"general_conversation":150 ,
"ledger_extraction":250 ,
"ledger_correction":200 ,
"pricing_explanation":150 ,
"negotiation_reason":100 ,
"price_chat_reply":120 ,
"market_report":350 ,
"scheme_rag_answer":300 ,
"catalog_captions":250 ,
}

DEFAULT_TOKEN_BUDGET =300 

def token_budget_for (task_name :str )->int :
    return TOKEN_BUDGETS .get (task_name ,DEFAULT_TOKEN_BUDGET )
