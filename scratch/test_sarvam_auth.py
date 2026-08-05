import os
import asyncio
from dotenv import load_dotenv

load_dotenv("d:/AI-SATHI/.env")

# Set the same environment variables as the settings
os.environ["DATABASE_URL"] = "postgresql+asyncpg://aisathi:gaganakash1152@127.0.0.1:5432/aisathi"

from shared.config.settings import get_settings
from services.translation_service import sarvam_client

async def test_sarvam():
    s = get_settings()
    print("Sarvam API Key:", s.sarvam_api_key)
    print("Sarvam Chat Model:", s.sarvam_chat_model)
    try:
        res = await sarvam_client.chat_completion(
            system="You are a helpful assistant.",
            prompt="Hello, this is a test.",
            model=s.sarvam_chat_model,
            max_tokens=100
        )
        print("Success! Response:")
        print(res)
    except Exception as exc:
        print("Failed with exception:")
        print(type(exc), exc)

if __name__ == "__main__":
    asyncio.run(test_sarvam())
