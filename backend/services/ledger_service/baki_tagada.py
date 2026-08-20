from __future__ import annotations 

import logging 
from urllib .parse import quote 

logger =logging .getLogger ("baki_tagada")

def generate_upi_payment_link (upi_id :str ,payee_name :str ,amount_inr :float ,note :str ="Baki Payment")->str :

    if not upi_id :
        return ""
    pa =quote (upi_id .strip ())
    pn =quote (payee_name .strip ()or "AI-SATHI Merchant")
    am =f"{amount_inr :.2f}"
    tn =quote (note )
    return f"upi://pay?pa={pa }&pn={pn }&am={am }&cu=INR&tn={tn }"

def format_baki_reminder_message (
customer_name :str ,
amount_inr :float ,
shop_or_shg_name :str ="",
upi_id :str ="",
)->dict :

    sender =shop_or_shg_name or "আমাদের দোকান"
    amount_str =f"₹{amount_inr :.0f}"

    upi_link =generate_upi_payment_link (upi_id ,sender ,amount_inr )

    message_body =(
    f"নমস্কার {customer_name } মহাশয/মহাশয়া,\n\n"
    f"আশা করি ভালো আছেন। {sender }-এ আপনার মোট বাকি টাকার পরিমাণ: *{amount_str }*।\n"
    f"অনুগ্রহ করে সুবিধাজনক সময়ে পরিশোধ করার অনুরোধ জানাচ্ছি।\n"
    )

    if upi_id and upi_link :
        message_body +=f"\n💳 অনলাইনে সরাসরি পরিশোধ করতে এই লিঙ্কে ক্লিক করুন:\n{upi_link }\n(UPI ID: `{upi_id }`)\n"

    message_body +="\nআপনার সহযোগিতার জন্য ধন্যবাদ। 🙏"

    return {
    "customer_name":customer_name ,
    "amount_inr":amount_inr ,
    "reminder_text":message_body ,
    "upi_link":upi_link ,
    }
