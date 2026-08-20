from __future__ import annotations 

from services .orchestrator .state import ConversationState 
from shared .guardrails .input_guard import evaluate_input 

async def input_guard_node (state :ConversationState )->dict :
    if state .get ("last_message_type")=="interactive":
        return {"guardrail_blocked":False ,"trace":["input_guard_node:skipped_interactive"]}

    text =state .get ("raw_input_text")or state .get ("raw_input_transcript")or ""
    result =evaluate_input (text )

    if result .action =="reject":
        return {
        "guardrail_blocked":True ,
        "outbound_messages":[{"type":"text","body":result .canned_reply }],
        "trace":[f"input_guard_node:rejected:{result .reason }"],
        }

    if result .action =="trivial_reply":
        return {
        "guardrail_blocked":True ,
        "outbound_messages":[{"type":"text","body":result .canned_reply }],
        "trace":["input_guard_node:trivial_reply"],
        }

    updates :dict ={"guardrail_blocked":False ,"trace":["input_guard_node:proceed"]}
    if state .get ("raw_input_text")is not None :
        updates ["raw_input_text"]=result .sanitized_text 
    elif state .get ("raw_input_transcript")is not None :
        updates ["raw_input_transcript"]=result .sanitized_text 
    return updates 
