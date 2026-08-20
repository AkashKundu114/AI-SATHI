from __future__ import annotations 

_ALLOWED_CONFIRMATION_CHOICES ={"confirm_save","needs_correction","discard"}

def validate_ledger_confirm_payload (payload :dict )->str |None :
    if not isinstance (payload ,dict ):
        return None 
    if set (payload .keys ())!={"confirmation_choice"}:
        return None 
    choice =payload .get ("confirmation_choice")
    if not isinstance (choice ,str )or choice not in _ALLOWED_CONFIRMATION_CHOICES :
        return None 
    return choice 

def validate_scheme_eligibility_payload (payload :dict )->dict |None :
    if not isinstance (payload ,dict ):
        return None 
    required ={"scheme_name","age","has_swasthya_sathi","is_govt_employee"}
    if set (payload .keys ())!=required :
        return None 

    age_raw =payload .get ("age")
    try :
        age =int (age_raw )
    except (TypeError ,ValueError ):
        return None 
    if not (0 <age <130 ):
        return None 

    for bool_field in ("has_swasthya_sathi","is_govt_employee"):
        if payload .get (bool_field )not in ("yes","no"):
            return None 

    scheme_name =payload .get ("scheme_name")
    if not isinstance (scheme_name ,str )or not scheme_name .strip ():
        return None 

    return {**payload ,"age":age }
