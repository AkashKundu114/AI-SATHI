from __future__ import annotations 

import re 

_E164_PHONE_RE =re .compile (r"^\+?[1-9]\d{7,15}$")
_CONTROL_CHARS_RE =re .compile (r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

def sanitize_text_input (text :str ,max_chars :int =2000 )->str :

    if not text :
        return ""
    clean =_CONTROL_CHARS_RE .sub ("",text )
    return clean .strip ()[:max_chars ]

def validate_phone_number (phone_number :str )->bool :

    if not phone_number :
        return False 
    return bool (_E164_PHONE_RE .match (phone_number .strip ()))
