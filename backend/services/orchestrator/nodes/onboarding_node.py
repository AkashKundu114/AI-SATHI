from __future__ import annotations

from services.orchestrator.state import ConversationState

WELCOME = (
    "🙏 AI-সাথীতে আপনাকে স্বাগতম!\n\n"
    "আমি আপনার ব্যবসার হিসাব রাখব, পণ্যের বিজ্ঞাপন বানাব, আর বাজারের পরামর্শ দেব।\n\n"
    "শুরু করতে আপনার নাম বলুন।"
)

_MAX_FIELD_LEN = 100


def get_honorific(name: str, gender: str | None = None) -> str:
    """
    Returns appropriate respectful address:
    - Male: '<Name> দা' / '<Name> বাবু'
    - Female: '<Name> দি'
    """
    clean = name.strip()
    is_male = gender == "male" or any(
        m in clean.lower()
        for m in [
            "akash",
            "rahul",
            "sourav",
            "subhash",
            "amit",
            "debashis",
            "swapan",
            "bikash",
            "arjun",
            "admin",
            "আকাশ",
        ]
    )
    if is_male:
        return f"{clean} দা"
    return f"{clean} দি"


async def onboarding_node(state: ConversationState) -> dict:
    step = state.get("onboarding_step") or "WELCOME"
    text = (state.get("raw_input_text") or state.get("raw_input_transcript") or "").strip()[:_MAX_FIELD_LEN]

    if step == "WELCOME":
        return {
            "onboarding_step": "AWAIT_NAME",
            "outbound_messages": [{"type": "text", "body": WELCOME}],
            "trace": ["onboarding_node:welcome"],
        }

    if step == "AWAIT_NAME":
        if not text:
            return {
                "outbound_messages": [{"type": "text", "body": "আপনার নাম বলুন বা লিখুন।"}],
                "trace": ["onboarding_node:empty_name"],
            }
        address = get_honorific(text)
        return {
            "onboarding_name": text,
            "onboarding_step": "AWAIT_BLOCK",
            "outbound_messages": [{"type": "text", "body": f"{address}, আপনার এলাকার পিনকোড (Pincode) কত?"}],
            "trace": ["onboarding_node:got_name"],
        }

    if step == "AWAIT_BLOCK" or step == "AWAIT_PINCODE":
        if not text:
            return {
                "outbound_messages": [{"type": "text", "body": "আপনার এলাকার পিনকোড (Pincode) লিখুন বা বলুন।"}],
                "trace": ["onboarding_node:empty_block"],
            }
        return {
            "onboarding_block": text,
            "onboarding_pincode": text,
            "onboarding_step": "AWAIT_CONSENT",
            "outbound_messages": [
                {
                    "type": "text",
                    "body": (
                        "AI-সাথী ব্যবহারের আগে:\n"
                        "✅ আপনার হিসাব শুধু আপনি দেখতে পাবেন\n"
                        "✅ কোনো ব্যক্তিগত তথ্য বিক্রি হবে না\n"
                        "✅ ভয়েস মেসেজ প্রসেসিংয়ের পরপরই মুছে ফেলা হয়\n\n"
                        "রাজি থাকলে 'হ্যাঁ' লিখুন।"
                    ),
                }
            ],
            "trace": ["onboarding_node:got_block"],
        }

    if step == "AWAIT_CONSENT":
        if text.lower() not in {"হ্যাঁ", "হ্যা", "ha", "haan", "yes"}:
            return {
                "outbound_messages": [{"type": "text", "body": "রাজি হলে 'হ্যাঁ' লিখুন, তাহলে শুরু করতে পারব।"}],
                "trace": ["onboarding_node:consent_not_given"],
            }
        try:
            user_id = await _create_user(state)
        except Exception:
            return {
                "outbound_messages": [{"type": "text", "body": "একটু সমস্যা হয়েছে। একটু পরে আবার 'হ্যাঁ' লিখুন।"}],
                "trace": ["onboarding_node:create_user_failed"],
            }
        return {
            "user_id": user_id,
            "is_new_user": False,
            "onboarding_step": "DONE",
            "outbound_messages": [{"type": "text", "body": "✨ আপনার AI-সাথী তৈরি! আজকের বিক্রি বা খরচ ভয়েসে বলুন। 🎙️"}],
            "trace": ["onboarding_node:complete"],
        }

    return {
        "outbound_messages": [{"type": "text", "body": "শুরু করতে 'শুরু' লিখুন।"}],
        "trace": ["onboarding_node:already_done"],
    }


async def _create_user(state: ConversationState) -> str:
    from datetime import datetime, timezone

    from sqlalchemy import or_, select

    from shared.db.models import User
    from shared.db.session import get_db_session

    name = state.get("onboarding_name") or "User"
    gender = "male" if any(m in name.lower() for m in ["akash", "kundu", "admin", "rahul", "sourav", "আকাশ"]) else "other"
    phone = state.get("phone_number") or state.get("user_id") or "+919876543210"
    block = state.get("onboarding_block") or "সিঙ্গুর"
    pincode_raw = state.get("onboarding_pincode") or state.get("onboarding_block") or ""
    pincode = "".join(filter(str.isdigit, pincode_raw))[:6]

    digits = "".join(filter(str.isdigit, str(phone)))
    last10 = digits[-10:] if len(digits) >= 10 else digits

    async with get_db_session() as db:
        existing = (
            await db.execute(
                select(User).where(
                    or_(
                        User.phone_number == phone,
                        User.username == phone,
                        User.phone_number == last10 if last10 else False,
                        User.phone_number == f"+91{last10}" if last10 else False,
                        User.phone_number.endswith(last10) if len(last10) == 10 else False,
                    )
                )
            )
        ).scalars().first()

        if existing:
            existing.name = name if name != "User" else existing.name
            existing.gender = gender or existing.gender
            existing.block = block or existing.block
            if pincode:
                existing.pincode = pincode
            existing.consent_given = True
            existing.consent_given_at = datetime.now(timezone.utc)
            await db.commit()
            return str(existing.id)

        try:
            user = User(
                phone_number=phone,
                name=name,
                gender=gender,
                block=block,
                pincode=pincode if pincode else None,
                consent_given=True,
                consent_given_at=datetime.now(timezone.utc),
                verification_status="verified",
                user_type="shg_member",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return str(user.id)
        except Exception:
            await db.rollback()
            # If insert failed due to concurrent creation or conflict, fetch existing
            fallback_user = (
                await db.execute(
                    select(User).where(
                        or_(
                            User.phone_number.endswith(last10) if len(last10) == 10 else False,
                            User.username == phone,
                        )
                    )
                )
            ).scalars().first()
            if fallback_user:
                return str(fallback_user.id)
            return "session_user"
