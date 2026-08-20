from __future__ import annotations 

import re 

MAX_OUTPUT_CHARS =1200 

_SECRET_PATTERNS =[
r"sk-[A-Za-z0-9]{20,}",
r"AIza[A-Za-z0-9_\-]{20,}",
r"Bearer\s+[A-Za-z0-9\-._~+/]{20,}=*",
r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
]
_SECRET_RE =re .compile ("|".join (_SECRET_PATTERNS ))

_AADHAAR_RE =re .compile (r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
_PAN_RE =re .compile (r"\b[A-Z]{5}\d{4}[A-Z]\b")
_LONG_ACCOUNT_NUMBER_RE =re .compile (r"\b\d{9,18}\b")
_OTP_MENTION_RE =re .compile (r"\bOTP\b[:\s]*\d{4,8}",re .IGNORECASE )

_URL_RE =re .compile (r"https?://\S+",re .IGNORECASE )

_SQL_RE =re .compile (r"\b(SELECT|INSERT INTO|UPDATE .* SET|DELETE FROM|DROP TABLE)\b",re .IGNORECASE )
_STACK_TRACE_RE =re .compile (r'Traceback \(most recent call last\)|File "[^"]+", line \d+')

def _contains_secret (text :str )->bool :
    return bool (_SECRET_RE .search (text ))

def _contains_sensitive_pii (text :str )->bool :
    if _AADHAAR_RE .search (text ):
        return True 
    if _PAN_RE .search (text ):
        return True 
    if _OTP_MENTION_RE .search (text ):
        return True 
    return False 

def _contains_url (text :str )->bool :
    return bool (_URL_RE .search (text ))

def _contains_sql_or_trace (text :str )->bool :
    return bool (_SQL_RE .search (text ))or bool (_STACK_TRACE_RE .search (text ))

def validate_output (text :str )->tuple [bool ,str |None ]:
    if not text :
        return True ,None 
    if _contains_secret (text ):
        return False ,"contains_secret_shaped_string"
    if _contains_sensitive_pii (text ):
        return False ,"contains_sensitive_pii"
    if _contains_url (text ):
        return False ,"contains_unexpected_url"
    if _contains_sql_or_trace (text ):
        return False ,"contains_sql_or_stack_trace"
    if len (text )>MAX_OUTPUT_CHARS :
        return False ,"exceeds_max_output_chars"
    return True ,None 

def enforce_output_guard (text :str ,fallback :str )->str :
    is_safe ,_reason =validate_output (text )
    return text if is_safe else fallback 
