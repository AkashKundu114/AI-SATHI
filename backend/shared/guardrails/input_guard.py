from __future__ import annotations 

import re 
from dataclasses import dataclass 

_INJECTION_PATTERNS =[
r"ignore (all |the )?(previous|above|prior) instructions?",
r"disregard (all |the )?(previous|above|prior) instructions?",
r"reveal (your |the )?system prompt",
r"show (me )?(your |the )?(system prompt|instructions)",
r"print (your |the )?(hidden|system) instructions?",
r"what (are|is) your (system prompt|instructions)",
r"repeat (the words|everything) above",
r"you are now (in )?(developer|debug|admin|god) mode",
r"act as (a |an )?(developer|admin|unrestricted|jailbroken)",
r"pretend (you are|to be) (an? )?(ai|assistant) (with no|without) (restrictions|rules|filters)",
r"\bdan mode\b",
r"do anything now",
r"ignore (your |all )?safety",
r"bypass (your |the )?(filters?|restrictions?|guardrails?)",
r"forget (your |all )?(rules|instructions|training)",
]
_INJECTION_RE =re .compile ("|".join (_INJECTION_PATTERNS ),re .IGNORECASE )

_ROLE_MARKER_RE =re .compile (
r"(?im)^\s*(system|assistant|developer|user)\s*:\s*|<\s*/?\s*(system|assistant|developer)\s*>"
)

_CONTROL_TOKEN_RE =re .compile (r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

MAX_INPUT_CHARS_FOR_LLM =1500 

def contains_injection_attempt (text :str )->bool :
    if not text :
        return False 
    return bool (_INJECTION_RE .search (text ))or bool (_ROLE_MARKER_RE .search (text ))

def sanitize_for_prompt (text :str )->str :
    if not text :
        return text 
    cleaned =_ROLE_MARKER_RE .sub ("",text )
    cleaned =_CONTROL_TOKEN_RE .sub ("",cleaned )
    return cleaned .strip ()[:MAX_INPUT_CHARS_FOR_LLM ]

_REPEATED_CHAR_RE =re .compile (r"(.)\1{7,}")
_REPEATED_WORD_RE =re .compile (r"\b(\S+)\b(?:\s+\1\b){4,}",re .IGNORECASE )
_ALL_DIGITS_RE =re .compile (r"^\d{10,}$")
_ALL_PUNCTUATION_RE =re .compile (r"^[^\w\u0980-\u09FF]+$")

def looks_like_spam (text :str )->bool :
    if not text :
        return False 
    stripped =text .strip ()
    if not stripped :
        return False 
    if _REPEATED_CHAR_RE .search (stripped ):
        return True 
    if _REPEATED_WORD_RE .search (stripped ):
        return True 
    if _ALL_DIGITS_RE .match (stripped ):
        return True 
    if _ALL_PUNCTUATION_RE .match (stripped ):
        return True 
    return False 

_TRIVIAL_REPLIES ={
"hi":"নমস্কার! হিসাব, বিজ্ঞাপন, বা বাজারের পরামর্শ - কী দরকার বলুন।",
"hello":"নমস্কার! হিসাব, বিজ্ঞাপন, বা বাজারের পরামর্শ - কী দরকার বলুন।",
"হাই":"নমস্কার! হিসাব, বিজ্ঞাপন, বা বাজারের পরামর্শ - কী দরকার বলুন।",
"নমস্কার":"নমস্কার! হিসাব, বিজ্ঞাপন, বা বাজারের পরামর্শ - কী দরকার বলুন।",
"ok":"ঠিক আছে 🙂",
"okay":"ঠিক আছে 🙂",
"ঠিক আছে":"ঠিক আছে 🙂",
"thanks":"স্বাগতম! 🙏",
"thank you":"স্বাগতম! 🙏",
"ধন্যবাদ":"স্বাগতম! 🙏",
}
_EMOJI_ONLY_RE =re .compile (
r"^[\U0001F300-\U0001FAFF\U00002600-\U000027BF\s]+$"
)

def trivial_reply_for (text :str )->str |None :
    if not text :
        return None 
    normalized =text .strip ().lower ()
    if normalized in _TRIVIAL_REPLIES :
        return _TRIVIAL_REPLIES [normalized ]
    if _EMOJI_ONLY_RE .match (text .strip ()):
        return "🙂"
    return None 

@dataclass 
class InputGuardResult :
    action :str 
    canned_reply :str |None =None 
    reason :str |None =None 
    sanitized_text :str |None =None 

def evaluate_input (text :str )->InputGuardResult :
    if not text or not text .strip ():
        return InputGuardResult (action ="proceed",sanitized_text =text )

    if contains_injection_attempt (text ):
        return InputGuardResult (
        action ="reject",
        canned_reply ="দুঃখিত, এই অনুরোধটি প্রক্রিয়া করা যাচ্ছে না। হিসাব, বিজ্ঞাপন, বা বাজারের পরামর্শের জন্য জিজ্ঞাসা করুন।",
        reason ="prompt_injection_or_role_marker",
        )

    if looks_like_spam (text ):
        return InputGuardResult (
        action ="reject",
        canned_reply ="বুঝতে পারলাম না। হিসাব, বিজ্ঞাপন, বা বাজারের পরামর্শের জন্য লিখুন।",
        reason ="spam_pattern",
        )

    canned =trivial_reply_for (text )
    if canned is not None :
        return InputGuardResult (action ="trivial_reply",canned_reply =canned ,reason ="trivial_message")

    return InputGuardResult (action ="proceed",sanitized_text =sanitize_for_prompt (text ))
