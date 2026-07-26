# AI-SATHI — Red-Team Pass #2
### Attacking beyond `docs/security.md`

**Method:** treat every trust boundary as hostile. For each one: try to read data I
shouldn't, write data I shouldn't, crash a process, or make the system spend money/GPU
on my behalf. Where an attempt failed, I noted *why* and moved to the next angle rather
than assuming "safe." Looped three passes over the repo; findings below survived all
three (i.e., they're real, not a misread of one file in isolation).

Severity: **CRIT** = full outage or data breach with low effort. **HIGH** = real damage,
needs some setup. **MED** = degraded trust/quality, not an outage.

---

## CRIT-1 — Redis/Postgres/Ollama are unauthenticated and exposed to the host network

**File:** `docker-compose.yml`

```yaml
redis:
  image: redis:7-alpine
  ports: ["6379:6379"]
  command: redis-server --appendonly yes   # <-- no requirepass
ollama:
  ports: ["11434:11434"]                    # <-- no auth layer at all
```

`ports: "6379:6379"` binds to `0.0.0.0` on the host by default. Combined with no
`requirepass`, **anyone who can reach the VM's IP on port 6379 can run `redis-cli`
against it with zero credentials.** That Redis instance is simultaneously:
- the session store (`session:{number}`)
- the webhook dedup set (`dedup:{message_id}`)
- the rate-limit counters (`ratelimit:{number}:{hour}`)
- the **Celery broker and result backend**

Exploit path (single command, no auth): `redis-cli -h <ip> FLUSHALL` wipes every active
conversation, every dedup record (re-enabling the H1 replay bug from the original
audit), and every rate-limit counter — instant, total denial of service, and it
re-opens an already-"fixed" vulnerability. A less noisy attacker can instead `redis-cli
LPUSH` directly into the Celery queue key to inject arbitrary task messages, or just
read every user's session JSON (phone-number-keyed, i.e. PII) with `KEYS session:*`.

Ollama on `11434` has no auth layer either — an outsider can hit `/api/generate`
directly, exhausting the single shared GPU that the real ledger-extraction path depends
on. Since `model_router.py`'s ROUTINE path falls back to Claude when the local model is
slow/low-confidence, a saturated Ollama silently shifts 100% of traffic to the paid
Claude tier — this is also a **cost-exhaustion vector**, not just latency.

**Fix:**
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
  ports:
    - "127.0.0.1:6379:6379"      # loopback only — no host-network exposure
ollama:
  ports:
    - "127.0.0.1:11434:11434"
postgres:
  ports:
    - "127.0.0.1:5432:5432"      # already password-protected, but still shouldn't be world-reachable
```
And update `REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0` in `.env.example`.
Internal services (`gateway`, `orchestrator-worker`) still reach these by service name
on the compose network — only the *host port* binding changes. Also explicitly pin the
Celery serializer to close off a task-injection RCE surface if the broker is ever
reachable again:
```python
# services/orchestrator/celery_entrypoint.py
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])
```

> **Status as of Pass #3, §11 below: superseded, not merely fixed.** Redis and Ollama
> are no longer part of the Azure deployment at all — see
> `docs/architecture.md` §11. This finding's *specific* exploit paths (unauthenticated
> `redis-cli`, unauthenticated Ollama) can't recur because there's nothing at those
> ports to attack. Postgres remains, and Pass #3 re-examines its exposure on its own
> terms rather than assuming the original fix still fully applies — see §11.1.

---

## CRIT-2 — PDF generation is an SSRF + injection primitive (Jinja2 autoescape is OFF)

**Files:** `services/pdf_service/generator.py`, `services/pdf_service/templates/monthly_report.html`

```python
_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR))   # no autoescape=True
...
template.render(member_name=user.name or "সদস্য", ... category names from LLM extraction ...)
```

Jinja2's `Environment()` does **not** autoescape by default unless you pass
`autoescape=True` or use `select_autoescape()`. Every field rendered here —
`member_name`, `shg_name`, `district`, and every category key in
`income_by_category`/`expense_by_category` — ultimately originates from **user voice
input, passed through an LLM extraction step** (`ledger_node.py`'s
`item_bengali` field becomes `LedgerEntry.category`). Nothing sanitizes it before it
lands in an HTML template.

WeasyPrint then renders that HTML to PDF **and fetches remote resources it finds in the
markup** (images, stylesheets, `@import`). So a category string like:
```
পাপড়<img src="http://169.254.169.254/latest/meta-data/iam/security-credentials/">
```
gets stored as a ledger category via a normal voice/text "correction" flow, and the
next time that user requests a report, the **pdf-service container itself makes an
outbound HTTP request to wherever the attacker put in the tag** — classic SSRF, with
the added twist that it can also read local files via `file://` URIs resolved against
`base_url="templates/"`, and exfiltrate their contents by observing which external URL
gets hit (or just embedding local file content directly into the rendered PDF page,
which then gets emailed/WhatsApp'd to a bank).

This one is more dangerous than an ordinary XSS finding because there's no browser and
no CSP to save you — WeasyPrint is a standalone renderer with real network access from
inside your infra.

**Fix (two independent layers, both required):**
```python
# services/pdf_service/generator.py
from markupsafe import escape
_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=True)  # layer 1

def _clean(s: str | None, max_len: int = 120) -> str:
    """Strip anything that isn't plain text before it ever reaches the template,
    independent of autoescape — defense in depth for a WeasyPrint renderer with
    outbound network access."""
    if not s:
        return ""
    s = re.sub(r"<[^>]*>", "", s)          # strip tags outright, don't rely on escaping alone
    return s[:max_len]

# apply _clean() to member_name, shg_name, district, and every category key
income_by_category = {_clean(cat): amt for cat, amt in income_by_category.items()}
expense_by_category = {_clean(cat): amt for cat, amt in expense_by_category.items()}
```
```python
# WeasyPrint call — disable remote fetch entirely, this document never needs it
pdf_bytes = HTML(string=html_content, base_url=None).write_pdf(
    presentational_hints=True,
)
```
And drop the Google Fonts `@import` from the template in favor of a locally bundled
Noto Sans Bengali font file, so the renderer has *zero* legitimate reason to make
outbound requests — removing the SSRF surface rather than just filtering it.

**Status:** still fixed and unaffected by the Azure/Pass #3 changes below — the fix
(`autoescape=True`, `_clean()`, `base_url=None`) is all in `generator.py`'s own logic
and doesn't touch storage or the task queue. §11.3 below only changes *where the
finished PDF bytes get uploaded to* (Azure Blob instead of S3/MinIO), not how they're
rendered.

---

## HIGH-1 — Webhook signature verification uses the wrong secret (silent, not a crash)

**File:** `services/gateway/main.py`

```python
expected = "sha256=" + hmac.new(s.wa_webhook_verify_token.encode(), body, hashlib.sha256).hexdigest()
```

Meta signs `X-Hub-Signature-256` with the WhatsApp **App Secret**, not the webhook
**verify token** (the verify token is only used in the one-time GET handshake
challenge/response — a completely different value with a completely different purpose).
As written, this check will either (a) always fail against real Meta traffic if the
values genuinely differ, silently dropping all production messages, or (b) "pass" only
because someone set `WA_WEBHOOK_VERIFY_TOKEN` and the app secret to the same string,
which means anyone who ever saw the verify token (it's visible in the Meta dashboard
URL config, shared more casually than a secret) can now forge webhook payloads.

**Fix:**
```python
# shared/config/settings.py
wa_app_secret: str  # separate from wa_webhook_verify_token — get from Meta App Dashboard > Settings > Basic

# services/gateway/main.py
expected = "sha256=" + hmac.new(s.wa_app_secret.encode(), body, hashlib.sha256).hexdigest()
```

**Status:** still fixed, unaffected by Pass #3 — `main.py`'s HMAC check is identical in
the Azure version (see the current `services/gateway/main.py`).

---

## HIGH-2 — Voice notes have zero size/duration validation before hitting ffmpeg/GPU

**File:** `shared/whatsapp/media.py`, called from `services/gateway/main.py`

The original audit (H9) flagged this for the old `stt`, but the *current*
production path (`voice_gateway`/`provider_cascade.py`, invoked from `main.py`) has the
exact same gap and was never covered:

```python
elif msg.message_type == "audio":
    audio_bytes = await download_whatsapp_audio(msg.audio_id)   # no cap, no streaming check
    stt_result = await transcribe(audio_bytes)                   # straight into Sarvam/Bhashini/Whisper
```

Image at least gets a post-download size check (too late to save bandwidth, but at
least rejects it before S3 upload). Audio gets **nothing** — no cap, and it's fed
straight into `whisper_local_provider.transcribe()`, which runs on the single shared
GPU. An oversized or malformed OGG blob (WhatsApp's own client caps voice notes, but
nothing stops a modified client or a direct API call to your webhook from Meta with a
crafted payload) can hang or OOM the GPU worker, taking down transcription for every
concurrent pilot user — the "shared blast radius" risk the original audit warned about
under H9, just via the path that's actually wired up.

**Fix:**
```python
# shared/whatsapp/media.py
MAX_AUDIO_BYTES = 6 * 1024 * 1024  # ~3 min OGG/OPUS per PRD FR1.1, generous margin

async def _download(media_id: str, max_bytes: int | None = None) -> bytes:
    s = get_settings()
    async with httpx.AsyncClient() as client:
        url_resp = await client.get(f"https://graph.facebook.com/v19.0/{media_id}",
                                     headers={"Authorization": f"Bearer {s.wa_access_token}"})
        url_resp.raise_for_status()
        meta = url_resp.json()
        if max_bytes and int(meta.get("file_size", 0)) > max_bytes:
            raise ValueError("media_too_large")
        media_resp = await client.get(meta["url"], headers={"Authorization": f"Bearer {s.wa_access_token}"})
        media_resp.raise_for_status()
        if max_bytes and len(media_resp.content) > max_bytes:
            raise ValueError("media_too_large")
        return media_resp.content

async def download_whatsapp_audio(media_id: str) -> bytes:
    return await _download(media_id, max_bytes=MAX_AUDIO_BYTES)
```
And in `main.py`, wrap the call so an oversized note gets a friendly Bengali reply
instead of an unhandled exception bubbling out of a background task (which currently
just vanishes silently — a debuggability problem on top of the security one).

**Status, updated for Pass #3:** the fix itself (size cap in `media.py`) still stands
unchanged. But the **blast radius changed** now that Celery's separate worker process
is gone (`docs/architecture.md` §11.2) — a GPU/CPU-hogging oversized audio note now
directly competes with the same container that's also trying to ack the next incoming
webhook, rather than only starving an isolated worker. See new finding §11.2 below.

---

## HIGH-3 — Grounding verifier can be defeated by spelling the number out in words

**File:** `services/rag_service/grounding_verifier.py`

```python
_AMOUNT_RE = re.compile(r"(₹\s?[০-৯0-9,]+|[০-৯0-9,]+\s?টাকা)")
```

This is the system's single most important safety mechanism (per
`docs/archive/product/uvp.md`, it's *the* differentiator) — and it only
extracts assertions that use digits. Bengali financial speech routinely uses number
*words* ("এক হাজার টাকা" = "one thousand rupees"). If the LLM hallucinates an amount
and phrases it in words instead of digits — which is a completely ordinary, unforced
generation choice, not even an adversarial prompt-injection — `_extract_assertions`
never sees it as an assertion at all, so it can never be flagged ungrounded. A
fabricated scheme amount phrased in words sails through with `all_grounded: True`.

I confirmed this isn't theoretical: `ml/llm/finetune_qlora.py`'s own training
data uses exactly this style ("Bengali number words: এক=1, দুই=2..."), meaning the
fine-tuned model is *specifically trained* to sometimes produce word-form numbers —
directly undermining the verifier that's supposed to catch it downstream.

**Fix (extend assertion extraction to catch word-numbers before scheme names):**
```python
_NUMBER_WORDS = {
    "এক": 1, "দুই": 2, "তিন": 3, "চার": 4, "পাঁচ": 5, "দশ": 10, "পনেরো": 15,
    "বিশ": 20, "পঁচিশ": 25, "ত্রিশ": 30, "পঞ্চাশ": 50, "একশো": 100,
    "দুইশো": 200, "তিনশো": 300, "পাঁচশো": 500, "হাজার": 1000,
}
_WORD_AMOUNT_RE = re.compile(
    r"(" + "|".join(re.escape(w) for w in _NUMBER_WORDS) + r")(?:\s+(টাকা|হাজার))?"
)

def _extract_assertions(answer_bengali: str) -> list[tuple[str, int]]:
    assertions = []
    for m in _AMOUNT_RE.finditer(answer_bengali):
        assertions.append((m.group(1).strip(), m.start()))
    for m in _DATE_RE.finditer(answer_bengali):
        assertions.append((m.group(1).strip(), m.start()))
    for m in _WORD_AMOUNT_RE.finditer(answer_bengali):
        assertions.append((m.group(0).strip(), m.start()))   # flag it; even an
        # imperfect word->digit conversion is strictly better than silently
        # skipping it — a false "ungrounded" triggers the safe fallback message,
        # which is the correct fail-safe direction for this product.
    return assertions
```
Add this as its own test case (`test_word_form_hallucination_is_caught`) alongside the
existing nine — treat it as a first-class regression, not a nice-to-have, given how
central this check is to the product's actual safety claim.

**Status:** still fixed, unaffected by Pass #3 — this lives entirely inside
`grounding_verifier.py`'s text logic and has nothing to do with storage/queue/infra.

---

## HIGH-4 — Ledger amounts are stored with no bounds checking, and the save path has no exception handling

**File:** `services/orchestrator/nodes/ledger_confirm_node.py`, `shared/db/models.py`

```python
amount_inr: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)   # max ~99,999,999.99
```
```python
async def _save(state, pending):
    ...
    async with get_db_session() as db:
        for tx in pending.get("transactions", []):
            amt = float(tx.get("amount_inr", 0) or 0)     # <-- no range check at all
            entry = LedgerEntry(..., amount_inr=amt, ...)
            db.add(entry)
        await db.commit()   # <-- not inside try/except
```
The LLM extraction has no upper/lower bound enforced on `amount_inr` before it's
written. A negative amount, a NaN, or a value that overflows `NUMERIC(10,2)` will
either corrupt every downstream P&L calculation (negative income silently flips a
profit/loss report) or raise a `DataError` on `commit()` that is **not caught anywhere
in this function** — it propagates up through the LangGraph node, into
`celery_entrypoint.py`'s `_process_turn_async`, which also has no try/except around
`graph.ainvoke(...)`. The Celery task then retries (per
`@celery_app.task(..., max_retries=2)`) against the same bad input, fails identically
twice more, and the user gets silence — no error message, no confirmation, nothing —
while burning three LLM calls per bad input.

**Fix:** `_validate_amount()` bounds check + try/except around `commit()` + wrapping
`graph.ainvoke(...)` similarly at the call site — see the original write-up above for
the exact code (unchanged in substance).

**Status, updated for Pass #3:** the fix itself is unchanged and still applied. The
call site that needs the outer try/except is now
`services/gateway/turn_processor.py::process_turn_and_dispatch` (the direct successor
to `celery_entrypoint.py::_process_turn_async` — same wrapping, no Celery retry
mechanism to rely on anymore, see new finding §11.2).

---

## MED-1 — Docker images run as root

None of the Dockerfiles (`gateway`, `pdf_service`, `orchestrator`, `voice_gateway`,
`stt`) declare a `USER` directive, so every container runs its process as
`root` by default.

**Fix:**
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

**Status:** still fixed, and the merged single Dockerfile in the Azure deployment
(`services/gateway/Dockerfile`) keeps the same `useradd`/`USER appuser` pattern —
verify this each time that Dockerfile is edited, since it's now the *only* image and
there's no second Dockerfile to catch a regression by comparison.

---

## MED-2 — WhatsApp Flow `interactive_payload` is trusted JSON with no schema

**File:** `shared/whatsapp/parser.py`

The Flow's `nfm_reply.response_json` is parsed and forwarded into the graph as raw text
with no schema validation. Low-impact since nothing consumed it at the time of the
original audit; worth a pydantic schema before it's relied on more heavily.

**Status:** unchanged, still open, unaffected by Pass #3.

---

## Summary checklist (Pass #2)

| # | Finding | Fixed here | Status after Pass #3 |
|---|---|---|---|
| CRIT-1 | Redis/Postgres/Ollama unauthenticated + host-exposed | ✅ compose port binding + requirepass + Celery serializer pin | ⏫ Superseded — Redis/Ollama removed entirely, see §11.1 |
| CRIT-2 | PDF SSRF + HTML injection via unescaped ledger fields | ✅ autoescape + strip-tags + WeasyPrint network disabled | ✅ Unaffected |
| HIGH-1 | Webhook HMAC uses wrong secret | ✅ new `wa_app_secret` setting | ✅ Unaffected |
| HIGH-2 | No size cap on voice notes before GPU processing | ✅ size check in `media.py` | ⚠️ Blast radius changed, see §11.2 |
| HIGH-3 | Grounding verifier misses word-form hallucinated amounts | ✅ `_WORD_AMOUNT_RE` extension + new test | ✅ Unaffected |
| HIGH-4 | Unbounded ledger amounts, uncaught DB exceptions | ✅ `_validate_amount` + try/except + graph-level catch | ⚠️ Call site moved, see §11.2 |
| MED-1 | Containers run as root | ✅ non-root `USER` in Dockerfiles | ✅ Unaffected (now one Dockerfile, not five) |
| MED-2 | Unvalidated Flow JSON payload | ⚠️ flagged, not fixed | ⚠️ Still open |

Everything above is additive to `security.md` (H1–H12), not a replacement.

---

# AI-SATHI — Red-Team Pass #3
## Attacking the Azure low-cost architecture (Redis/Celery/MinIO removed)

**Method, same as Pass #2:** treat every new trust boundary introduced by
`docs/architecture.md` §11 as hostile — Postgres now doing Redis's old jobs, one
container doing two processes' old jobs, Azure Blob Storage doing MinIO's old job.
Findings below are scoped to *what changed*; everything in Pass #2 not called out as
superseded above still applies unchanged.

## 11.1 MED — Postgres dedup/rate-limit tables have no retention cleanup, and are a new write-amplification surface

**Files:** `migrations/0007_webhook_dedup.sql`, `shared/db/dedup.py`

`webhook_dedup` gets one row per inbound message forever — there is no scheduled
`DELETE FROM webhook_dedup WHERE created_at < NOW() - INTERVAL '7 days'` anywhere in
this codebase (the old Redis key had a 24h TTL for free; a Postgres table does not
expire rows on its own). At 2,000 msgs/day this grows by ~2,000 rows/day indefinitely —
not an outage risk at pilot scale over a period of months, but it **is** an
unattended-growth footgun: nothing currently stops this table (or `rate_limit_counters`,
which additionally never removes old hour-buckets per phone number) from becoming a
genuine bloat/vacuum problem a year into a pilot nobody revisits.

More pressing at pilot scale: **every single inbound webhook message now costs at
least one, usually two, synchronous Postgres round-trips** (`mark_seen_or_skip` +
`check_and_increment_rate_limit`) on the *same* connection pool the LangGraph
checkpointer and every domain read/write already share. This is explicitly flagged as
an acceptable trade-off in `docs/architecture.md` §11.1 at 2,000 msgs/day — this
red-team finding is not "this is broken," it's "this is the thing to watch first if
traffic grows," matching that section's own stated trigger.

**Fix:**
```sql
-- Run as a scheduled job (Azure Container Apps has no built-in cron; use an
-- Azure Function on a Timer trigger, or a `pg_cron` extension if your Flexible
-- Server tier supports it) — NOT wired up anywhere in this codebase yet.
DELETE FROM webhook_dedup WHERE created_at < NOW() - INTERVAL '7 days';
DELETE FROM rate_limit_counters WHERE hour_bucket < (EXTRACT(EPOCH FROM NOW()) / 3600 - 168)::BIGINT;
```
Flagged, not fixed — add this before treating the pilot as "set and forget" for more
than a few months.

## 11.2 HIGH — No Celery isolation means a slow/heavy turn now shares CPU/memory with the webhook ack itself

**Files:** `services/gateway/main.py`, `services/gateway/turn_processor.py`

`docs/architecture.md` §11.2 documents this trade-off explicitly, but it's worth
red-teaming as an actual DoS vector, not just a latency inconvenience: `FastAPI
BackgroundTasks` run in the same event loop / process as the webhook handler. A
message that triggers heavy synchronous work — WeasyPrint PDF rendering (CRIT-2's
renderer, still CPU-bound even with the SSRF fix applied), `faster-whisper` CPU
transcription (HIGH-2's un-isolated blast radius, now sharper), or a slow Sarvam call
that falls all the way through to `ModelUnavailableError` after exhausting retries —
now directly competes for the same worker process handling `POST /webhook/whatsapp`
for every other concurrent user.

At this pilot's actual traffic (a few messages/minute), this is very unlikely to be
noticeable. It becomes a real concern under either (a) an unexpectedly bursty day
(a group event where many SHG members message at once) or (b) a deliberate attacker
who has your webhook URL and app secret's public verification requirements figured
out well enough to send crafted, expensive-to-process payloads repeatedly (e.g.
maximum-size images/audio right at HIGH-2's size cap, back to back). Because there is
exactly **one replica** (`maxReplicas: 1`, `docs/architecture.md` §11.6), there is no
horizontal headroom to absorb this — a sustained burst degrades the webhook's own
ack latency, which risks Meta's own retry/backoff behavior kicking in and compounding
load.

**Fix, in order of effort:**
1. Cheapest: raise `maxReplicas` to 2 in `infra/modules/containerapps.bicep` — gives
   Container Apps' own CPU-based autoscale a second instance to shed load to, at
   roughly double the compute line-item cost. Still no queue, but removes the
   single-point-of-saturation risk.
2. Correct, if traffic genuinely grows: reintroduce a real queue (Azure Service Bus +
   a second, independently-scaled Container App consuming it) exactly as
   `docs/architecture.md` §11.2 already recommends as the first thing to do if this
   tier is outgrown — do not silently keep raising `maxReplicas` indefinitely as a
   substitute for that.

## 11.3 MED — Azure Blob Storage account key is parsed directly out of the connection string for SAS generation

**File:** `shared/storage/blob_client.py`

```python
def _account_key_from_connection_string(conn_str: str) -> str:
    parts = dict(p.split("=", 1) for p in conn_str.split(";") if "=" in p)
    return parts["AccountKey"]
```

`generate_read_url()` needs the raw account key to sign a SAS token, and the only
place that key currently lives is inside `AZURE_STORAGE_CONNECTION_STRING` — the same
secret used for every other Blob operation. This is not a vulnerability by itself (the
key is already in Key Vault, injected as a Container App secret the same way every
other credential in this deployment is), but it does mean **the single connection
string secret has full read/write/delete access to the entire storage account**, not
a narrower "generate read-only SAS tokens only" scope. Compare this to the AWS
presigned-URL pattern the old `s3_client.py` used, which *could* (though this codebase
didn't do so) be issued from an IAM credential scoped down to exactly that one
operation.

**Fix, if this deployment's threat model warrants it:** use a **User Delegation SAS**
(requires Azure AD auth + an RBAC role scoped to the storage account, rather than the
account key) instead of an account-key SAS, or split credentials — a
write-capable identity for `upload_bytes`/`download_bytes` used only by the app's own
backend code, and a separate, narrowly-scoped key used only for SAS generation. Not
done in this pass; flagged because "one secret, full account access" is a bigger blast
radius than the old MinIO setup's equivalent credential, which was already scoped to
a single bucket by convention (not by IAM, but at least not shared with a whole Azure
subscription's storage account).

## 11.4 LOW — Single Container App replica means no security-patch rolling deploy

**File:** `infra/modules/containerapps.bicep`

With `minReplicas: 1, maxReplicas: 1`, any deploy (including a security patch to a
dependency) briefly takes the app offline rather than rolling traffic to a second
healthy replica first. Not a vulnerability in the traditional sense, but worth naming
in a security document: **the cheapest configuration and the most-available
configuration are in direct tension here**, and this deployment has explicitly chosen
cost over availability at this pilot scale (`docs/architecture.md` §11.6 already
states this trade-off; this finding just makes the security-patching angle of it
explicit rather than leaving it implied).

## Summary checklist (Pass #3)

| # | Finding | Status |
|---|---|---|
| 11.1 | Postgres dedup/rate-limit tables: no retention cleanup, added write load | ⚠️ Flagged, not fixed — matches architecture.md §11.1's stated trade-off |
| 11.2 | No queue isolation — a heavy turn can degrade webhook ack latency under load | ⚠️ Flagged, mitigation options given, not applied |
| 11.3 | Blob SAS generation uses full-access account key, not a scoped credential | ⚠️ Flagged, not fixed |
| 11.4 | Single replica means no rolling security-patch deploy | ⚠️ Named trade-off, not a code fix |

None of Pass #3's findings are CRIT — they're the honest cost of the savings described
in `docs/architecture.md` §11, not new holes introduced by carelessness. Re-run this
pass (or a lighter version of it) before any decision to grow past the 100-user pilot
tier, per `docs/product.md` §10.5's stated scale-up triggers.
