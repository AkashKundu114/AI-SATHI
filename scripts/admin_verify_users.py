import asyncio
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import select, update

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.db.session import get_db_session
from shared.db.models import User, UserVerification
from shared.config.settings import get_settings


async def review_verifications():
    print("[*] Connecting to database...")
    async with get_db_session() as db:
        result = await db.execute(
            select(UserVerification, User)
            .join(User, UserVerification.user_id == User.id)
            .where(UserVerification.status == "pending")
        )
        records = result.all()

        if not records:
            print("[+] No pending verifications found.")
            return

        print(f"[*] Found {len(records)} pending verifications.\n")
        
        for uv, user in records:
            print("-" * 50)
            print(f"User ID       : {user.id}")
            print(f"WhatsApp      : {user.whatsapp_number}")
            print(f"User Type     : {user.user_type}")
            print(f"Doc Type      : {uv.doc_type}")
            print(f"Doc ID Number : {uv.doc_id_number}")
            print(f"Doc Image S3  : {uv.doc_image_s3_key}")
            print(f"Submitted At  : {uv.submitted_at}")
            
            while True:
                choice = input("\n[A]pprove, [R]eject, or [S]kip? ").strip().upper()
                if choice in ["A", "R", "S"]:
                    break
            
            if choice == "S":
                continue
                
            status = "approved" if choice == "A" else "rejected"
            user_status = "verified" if choice == "A" else "rejected"
            notes = input("Reviewer notes (optional): ").strip()
            
            await db.execute(
                update(UserVerification)
                .where(UserVerification.id == uv.id)
                .values(
                    status=status,
                    reviewed_at=datetime.utcnow(),
                    reviewer_notes=notes
                )
            )
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(verification_status=user_status)
            )
            await db.commit()
            print(f"[+] User {user.whatsapp_number} marked as {user_status}.")
            
            # Note: In a real production system, you would enqueue a WhatsApp notification
            # via a background job or messaging queue here to inform the user.

        print("-" * 50)
        print("[+] Review complete.")


if __name__ == "__main__":
    asyncio.run(review_verifications())
