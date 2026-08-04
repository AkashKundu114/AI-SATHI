import os
import asyncio
from dotenv import load_dotenv

load_dotenv("d:/AI-SATHI/.env")
os.environ["DATABASE_URL"] = "postgresql+asyncpg://aisathi:gaganakash1152@127.0.0.1:5432/aisathi"

from shared.config.settings import get_settings
from services.translation_service import sarvam_client
from services.orchestrator.nodes.ledger_node import EXTRACTION_SYSTEM

async def test_extract():
    s = get_settings()
    prompt = "রিনা 300 ধার নিয়েছে"
    print("Prompt:", prompt)
    try:
        res = await sarvam_client.chat_completion(
            system=EXTRACTION_SYSTEM,
            prompt=prompt,
            model=s.sarvam_chat_model,
            max_tokens=4096,
            temperature=0.1
        )
        print("Success! Raw Response:")
        print(res.encode('utf-8'))
    except Exception as exc:
        print("Failed with exception:")
        print(type(exc), exc)

if __name__ == "__main__":
    asyncio.run(test_extract())
