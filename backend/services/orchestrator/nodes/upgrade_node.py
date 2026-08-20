from __future__ import annotations

import logging

from services.orchestrator.state import ConversationState

logger = logging.getLogger("upgrade_node")

UPGRADE_INFO_MESSAGE = (
    "🌟 *AI-SATHI প্রিমিয়াম প্ল্যান বিবরণী*\n\n"
    "আপনার ব্যবসার সুবিধার্থে বেছে নিন সেরা প্ল্যান:\n\n"
    "1️⃣ *বেসিক প্ল্যান* - ₹99 / মাস\n"
    "   • 600টি ভয়েস/টেক্সট AI মেসেজ\n"
    "   • 60টি ভিশন প্রোডাক্ট অ্যানালিসিস\n"
    "   • 50টি HD ক্যাটালগ পোস্টার\n\n"
    "2️⃣ *প্রো প্ল্যান* - ₹299 / মাস\n"
    "   • 2,000টি ভয়েস/টেক্সট AI মেসেজ\n"
    "   • 200টি ভিশন প্রোডাক্ট অ্যানালিসিস\n"
    "   • 200টি HD ক্যাটালগ পোস্টার\n\n"
    "3️⃣ *আনলিমিটেড প্ল্যান* - ₹499 / মাস\n"
    "   • সীমাহীন ব্যবহার\n"
    "   • অগ্রাধিকার ভিত্তিক সাপোর্ট\n\n"
    "💳 *আপগ্রেড করার নিয়ম:*\n"
    "যে কোনো UPI অ্যাপ (Google Pay / PhonePe / Paytm) থেকে আমাদের সাহায্য নম্বর বা UPI ID তে অর্থ প্রদান করে ট্রানজ্যাকশন আইকন বা রসিদ পাঠান।\n"
    "যোগাযোগ করুন: +91 9876543210 (AI-SATHI Support)"
)


async def upgrade_node(state: ConversationState) -> dict:
    return {
        "outbound_messages": [{"type": "text", "body": UPGRADE_INFO_MESSAGE}],
        "trace": ["upgrade_node:info_sent"],
    }
