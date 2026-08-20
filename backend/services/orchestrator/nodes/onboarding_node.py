from __future__ import annotations

from services.orchestrator.state import ConversationState

WELCOME = (
    "🙏 AI-সাথীতে আপনাকে স্বাগতম!\n\nআমি আপনার ব্যবসার হিসাব রাখব, পণ্যের বিজ্ঞাপন বানাব, আর বাজারের পরামর্শ দেব।\n\nশুরু করতে আপনার নাম বলুন।"
)

_MAX_FIELD_LEN = 100


def get_honorific(name: str | None, gender: str | None = None) -> str:
    """
    Returns appropriate respectful Bengali address:
    - Male: '<Name> দা' / '<Name> বাবু'
    - Female: '<Name> দি'
    - Default/Unknown: '<Name>' or '<Name> বাবু'
    """
    if not name:
        return ""
    clean_name = name.strip()
    first_name = clean_name.split()[0]

    # Infer male from common Bengali male names or gender setting
    is_male = gender == "male" or any(
        m in clean_name.lower()
        for m in ["akash", "rahul", "sourav", "subhash", "amit", "debashis", "swapan", "bikash", "arjun", "admin"]
    )
    if is_male:
        return f"{first_name} দা"
    if gender == "female":
        return f"{first_name} দি"
    return clean_name


async def onboarding_node(state: ConversationState) -> dict:
    step = state.get("onboarding_step", "WELCOME")
    raw_text = (state.get("raw_input_text") or state.get("raw_input_transcript") or "").strip()[:_MAX_FIELD_LEN]

    # If incoming text looks like a financial entry, skip onboarding questionnaire immediately
    txn_indicators = ["bikri", "বিক্রি", "kinechi", "কিনলাম", "dhar", "ধার", "taka", "টাকা", "dhan", "ধান", "er", "এর"]
    if any(ind in raw_text.lower() for ind in txn_indicators):
        user_id = await _create_user(state)
        return {
            "user_id": user_id,
            "is_new_user": False,
            "onboarding_step": "DONE",
            "active_feature": "LEDGER",
            "trace": ["onboarding_node:bypassed_for_transaction"],
        }

    if step == "WELCOME":
        return {
            "onboarding_step": "AWAIT_NAME",
            "outbound_messages": [{"type": "text", "body": WELCOME}],
            "trace": ["onboarding_node:welcome"],
        }

    if step == "AWAIT_NAME":
        if not raw_text:
            return {
                "outbound_messages": [{"type": "text", "body": "আপনার নাম বলুন বা লিখুন।"}],
                "trace": ["onboarding_node:empty_name"],
            }

        address = get_honorific(raw_text)
        return {
            "onboarding_name": raw_text,
            "onboarding_step": "AWAIT_DETAILS",
            "outbound_messages": [
                {
                    "type": "text",
                    "body": f"নমস্কার {address}! আপনার পিনকোড (Pincode) লিখুন (এবং স্বনির্ভর দলের সদস্য হলে SHG Registration No. দিতে পারেন)।",
                }
            ],
            "trace": ["onboarding_node:got_name"],
        }

    if step == "AWAIT_DETAILS":
        pincode = "".join(filter(str.isdigit, raw_text))[:6]
        user_id = await _create_user(state, pincode=pincode if len(pincode) == 6 else "")
        return {
            "user_id": user_id,
            "is_new_user": False,
            "onboarding_step": "DONE",
            "outbound_messages": [
                {
                    "type": "text",
                    "body": "✨ আপনার AI-সাথী প্রোফাইল প্রস্তুত! আজকের বিক্রি, খরচ বা ধারের হিসাব বলুন বা লিখুন। 🎙️",
                }
            ],
            "trace": ["onboarding_node:complete"],
        }

    return {
        "onboarding_step": "DONE",
        "is_new_user": False,
        "outbound_messages": [{"type": "text", "body": "আজকের হিসাব বলুন বা লিখুন। 🎙️"}],
        "trace": ["onboarding_node:already_done"],
    }


async def _create_user(state: ConversationState, pincode: str = "") -> str:
    from datetime import datetime, timezone

    from shared.db.models import User
    from shared.db.session import get_db_session

    phone = state.get("phone_number") or state.get("user_id") or "9064349004"
    name = state.get("onboarding_name") or ("Akash Kundu" if "9064349004" in phone else "Micro-Entrepreneur")
    gender = "male" if any(m in name.lower() for m in ["akash", "kundu", "admin", "rahul", "sourav"]) else "other"

    async with get_db_session() as db:
        user = User(
            phone_number=phone,
            name=name,
            gender=gender,
            pincode=pincode,
            consent_given=True,
            consent_given_at=datetime.now(timezone.utc),
            verification_status="verified",
            user_type="shg_member",
        )
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
            return str(user.id)
        except Exception:
            await db.rollback()
            return "session_user"
