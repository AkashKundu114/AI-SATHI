import argparse 
import os 
import sys 
from pathlib import Path 

REQUIRED =[
"WA_PHONE_NUMBER_ID",
"WA_ACCESS_TOKEN",
"WA_WEBHOOK_VERIFY_TOKEN",
"WA_APP_SECRET",
"POSTGRES_PASSWORD",
"DATABASE_URL",
]

PLACEHOLDER_VALUES ={"","changeme"}

def load_dotenv (path :str =".env")->dict :
    env ={}
    p =Path (path )
    if not p .exists ():
        return env 
    for line in p .read_text ().splitlines ():
        line =line .strip ()
        if not line or line .startswith ("#")or "="not in line :
            continue 
        k ,_ ,v =line .partition ("=")
        env [k .strip ()]=v .strip ()
    return env 

def main (quiet :bool =False )->int :
    def info (msg :str )->None :
        if not quiet :
            print (msg )

    env ={**load_dotenv (),**os .environ }
    missing =[k for k in REQUIRED if env .get (k ,"").strip ()in PLACEHOLDER_VALUES ]

    if missing :
        print ("Missing or placeholder values in .env - fill these in before `make dev`:\n")
        for k in missing :
            print (f"  - {k }")
        print ("\nSee .env.example for where each one comes from.")
        return 1 

    info ("✅ All required .env values are set.")

    sarvam_set =bool (env .get ("SARVAM_API_KEY","").strip ())
    local_enabled =env .get ("USE_LOCAL_MODELS","false").lower ()=="true"

    if not sarvam_set :
        print (
        "⚠️  SARVAM_API_KEY is blank - Sarvam is now the ONLY paid vendor "
        "(OpenAI has been removed entirely). Every agent will fail unless "
        "USE_LOCAL_MODELS=true and Ollama is actually reachable."
        )
    if not sarvam_set and not local_enabled :
        print (
        "❌ No paid tier (SARVAM_API_KEY) AND no free fallback "
        "(USE_LOCAL_MODELS=true) configured - every agent call will "
        "raise ModelUnavailableError. Set at least one before `make dev`."
        )
    if local_enabled :
        info ("ℹ️  USE_LOCAL_MODELS=true - make sure you run:")
        info ("    docker compose --profile local-models up -d ollama")
        info ("    docker compose exec ollama ollama pull "+env .get ("OLLAMA_LLM_MODEL","qwen2.5:7b-instruct-q4_K_M"))
        info ("    docker compose exec ollama ollama pull "+env .get ("OLLAMA_VISION_MODEL","qwen2-vl:7b-q4_K_M"))

    if not os .path .exists (env .get ("BENGALI_FONT_PATH","assets/fonts/NotoSansBengali-Bold.ttf")):
        info (
        "ℹ️  Bengali font not found at BENGALI_FONT_PATH - ad posters will "
        "fall back to plain photo + separate caption messages. See "
        "assets/fonts/README.md to enable full poster generation."
        )
    if not env .get ("FLUX_API_KEY","").strip ():
        info (
        "ℹ️  FLUX_API_KEY is blank - poster generation will use the free, "
        "local Pillow composite only (always works, no code change needed)."
        )

    if not env .get ("AZURE_STORAGE_CONNECTION_STRING","").strip ():
        print (
        "⚠️  AZURE_STORAGE_CONNECTION_STRING is blank - catalog images and "
        "PDF reports cannot be uploaded/delivered until this is set (see "
        "shared/storage/blob_client.py). Point it at the Azurite emulator "
        "for local dev, or the real Storage Account connection string in "
        "production (injected via Key Vault in the Azure deployment)."
        )
    elif "AccountKey="not in env .get ("AZURE_STORAGE_CONNECTION_STRING",""):
        print (
        "⚠️  AZURE_STORAGE_CONNECTION_STRING is set but doesn't look like a "
        "standard connection string (no 'AccountKey=' segment found) - "
        "generate_read_url() needs the account key to sign SAS tokens; "
        "double-check this value against .env.example's format."
        )

    db_url =env .get ("DATABASE_URL","")
    if db_url and not db_url .startswith ("postgresql+asyncpg://"):
        print (
        "⚠️  DATABASE_URL doesn't start with 'postgresql+asyncpg://' - "
        "shared/db/session.py uses SQLAlchemy's async engine, which "
        "requires the asyncpg driver prefix specifically (a plain "
        "'postgresql://' URL will fail at connection time, not at import "
        "time, which makes this easy to miss until the first real query)."
        )

    app_secret =env .get ("WA_APP_SECRET","")
    verify_token =env .get ("WA_WEBHOOK_VERIFY_TOKEN","")
    if app_secret and verify_token and app_secret ==verify_token :
        print (
        "❌ WA_APP_SECRET and WA_WEBHOOK_VERIFY_TOKEN are set to the SAME "
        "value. These are two different secrets from Meta with two "
        "different purposes and different exposure levels (the verify "
        "token is visible in the dashboard webhook-config URL, shared "
        "more casually than a secret; the app secret signs every webhook "
        "payload's HMAC and must stay confidential). Using the same value "
        "for both means anyone who has seen the verify token could forge "
        "webhook payloads. Set these to two distinct values - see "
        "Meta App Dashboard > Settings > Basic for the App Secret."
        )

    try :
        max_per_hour =int (env .get ("MAX_MESSAGES_PER_HOUR","30"))
        if max_per_hour <=0 :
            print ("⚠️  MAX_MESSAGES_PER_HOUR is <= 0 - every user message would be rate-limited immediately.")
    except ValueError :
        print ("⚠️  MAX_MESSAGES_PER_HOUR is not a valid integer.")

    info (
    "\nSummary: "
    +("Sarvam-primary"if sarvam_set else "no Sarvam")
    +(" + local-model fallback"if local_enabled else " (no local fallback provisioned)")
    +"."
    )
    return 0 

def _parse_args ()->argparse .Namespace :
    parser =argparse .ArgumentParser (description ="Validate required/optional AI-SATHI environment configuration.")
    parser .add_argument ("--quiet",action ="store_true",help ="Only print warnings/errors, suppress info-level notes")
    return parser .parse_args ()

if __name__ =="__main__":
    sys .exit (main (quiet =_parse_args ().quiet ))
