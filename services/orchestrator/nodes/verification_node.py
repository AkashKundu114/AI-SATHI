from __future__ import annotations

import json
from sqlalchemy import update
from shared.db.session import get_db_session
from shared.db.models import User, UserVerification
from services.orchestrator.state import ConversationState


async def verification_node(state: ConversationState) -> dict:
    user_id = state.get("user_id")
    if not user_id:
        return {"trace": ["verification:no_user_id"]}

    v_step = state.get("verification_step") or "type_selection"
    v_status = state.get("user_profile", {}).get("verification_status", "unverified")

    if v_status == "pending":
        msg = "আপনার ভেরিফিকেশনটি এখন রিভিউ-এ আছে। আমরা খুব শীঘ্রই আপনাকে আপডেট জানাব। অনুগ্রহ করে অপেক্ষা করুন। 🙏"
        return {
            "outbound_messages": [{"type": "text", "body": msg}],
            "trace": ["verification:pending_notice"],
            "verification_step": "DONE"
        }

    raw_text = (state.get("raw_input_text") or "").strip()
    msg_type = state.get("last_message_type")

    # Step 1: Select Type
    if v_step == "type_selection":
        if raw_text in ["1", "2", "3"]:
            user_type = {"1": "shg", "2": "shopkeeper", "3": "micro_entrepreneur"}[raw_text]
            
            async with get_db_session() as db:
                await db.execute(
                    update(User).where(User.id == user_id).values(user_type=user_type)
                )
                await db.commit()
            
            if user_type == "shg":
                doc_req = "দয়া করে আপনার SHG রেজিস্ট্রেশন সার্টিফিকেট (Anandadhara/NRLM), ব্যাঙ্কের পাসবই, অথবা পঞ্চায়েতের শংসাপত্রের একটি পরিষ্কার ছবি তুলে পাঠান।"
            elif user_type == "shopkeeper":
                doc_req = "দয়া করে আপনার পঞ্চায়েত/পৌরসভার ট্রেড লাইসেন্স, অথবা আপনার দোকানের একটি পরিষ্কার ছবি তুলে পাঠান (যেখানে আপনাকে ও আপনার দোকান দেখা যাচ্ছে)।"
            else:
                doc_req = "দয়া করে আপনার Udyam/MSME রেজিস্ট্রেশন, আর্টজান কার্ড, অথবা আধার কার্ডের সাথে আপনার কাজের জায়গার একটি পরিষ্কার ছবি তুলে পাঠান।"
            
            return {
                "user_profile": {**state.get("user_profile", {}), "user_type": user_type},
                "verification_step": "doc_upload",
                "outbound_messages": [{"type": "text", "body": doc_req}],
                "trace": ["verification:type_selected"]
            }
            
        msg = (
            "⚠️ AI-SATHI ব্যবহার করার আগে আপনার ভেরিফিকেশন (KYC) প্রয়োজন।\n\n"
            "আপনি কোন ধরনের ব্যবসার সাথে যুক্ত, তা নিচে থেকে নির্বাচন করুন (শুধুমাত্র 1, 2, বা 3 লিখে রিপ্লাই দিন):\n\n"
            "1️⃣ স্বনির্ভর গোষ্ঠী (SHG)\n"
            "2️⃣ দোকানদার (Shopkeeper)\n"
            "3️⃣ ক্ষুদ্র উদ্যোক্তা / কারিগর (Micro-Entrepreneur / Artisan)"
        )
        return {
            "outbound_messages": [{"type": "text", "body": msg}],
            "trace": ["verification:prompt_type_selection"]
        }

    # Step 2: Document Upload (Image)
    if v_step == "doc_upload":
        if msg_type == "image":
            s3_key = state.get("raw_image_s3_key")
            if s3_key:
                msg = "✅ আপনার ডকুমেন্ট সফলভাবে আপলোড হয়েছে!\n\nদয়া করে আপনার ডকুমেন্টের আইডেন্টিফিকেশন নম্বরটি (ID Number) লিখে বা ভয়েস মেসেজে পাঠান (যদি না থাকে, তবে 'নেই' লিখুন):"
                return {
                    "verification_step": "id_entry",
                    "verification_doc_type": "uploaded_image",
                    "verification_doc_number": s3_key, # Temporary storing s3_key here
                    "outbound_messages": [{"type": "text", "body": msg}],
                    "trace": ["verification:image_received"]
                }
        
        msg = "⚠️ দয়া করে আপনার ডকুমেন্টের একটি পরিষ্কার ছবি (Image) তুলে পাঠান।"
        return {
            "outbound_messages": [{"type": "text", "body": msg}],
            "trace": ["verification:waiting_for_image"]
        }

    # Step 3: ID Entry and Final Submit
    if v_step == "id_entry":
        id_number = raw_text or state.get("raw_input_transcript") or ""
        if not id_number:
            return {
                "outbound_messages": [{"type": "text", "body": "দয়া করে আপনার ডকুমেন্টের আইডি নম্বরটি লিখুন অথবা ভয়েসে বলুন:"}],
                "trace": ["verification:waiting_for_id"]
            }
        
        s3_key = state.get("verification_doc_number") # Retrieve the s3_key saved in the previous step
        user_type = state.get("user_profile", {}).get("user_type", "unknown")
        
        async with get_db_session() as db:
            new_v = UserVerification(
                user_id=user_id,
                doc_type=f"{user_type}_verification",
                doc_id_number=id_number[:100],
                doc_image_s3_key=s3_key,
                status="pending"
            )
            db.add(new_v)
            await db.execute(
                update(User).where(User.id == user_id).values(verification_status="pending")
            )
            await db.commit()

        msg = (
            "🎉 ধন্যবাদ! আপনার ভেরিফিকেশন সফলভাবে জমা হয়েছে।\n\n"
            "আমাদের টিম এটি রিভিউ করছে। ভেরিফিকেশন সম্পূর্ণ হলে আপনাকে মেসেজের মাধ্যমে জানিয়ে দেওয়া হবে এবং আপনি AI-SATHI এর সমস্ত সুবিধা ব্যবহার করতে পারবেন। 🙏"
        )
        return {
            "user_profile": {**state.get("user_profile", {}), "verification_status": "pending"},
            "verification_step": "DONE",
            "outbound_messages": [{"type": "text", "body": msg}],
            "trace": ["verification:submitted"]
        }

    return {"trace": ["verification:unhandled"]}
