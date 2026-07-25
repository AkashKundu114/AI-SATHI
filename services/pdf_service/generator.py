from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select, func

from shared.config.settings import get_settings
from shared.storage.s3_client import get_s3_client
from shared.db.models import LedgerEntry, SHGGroup, User
from shared.db.session import get_db_session
from shared.i18n.bengali_calendar import GREGORIAN_MONTHS_BENGALI, format_bangla_calendar_label
from shared.i18n.bengali_numbers import to_bengali_digits

_TEMPLATE_DIR = "services/pdf_service/templates"

# autoescape=True is load-bearing: every field rendered here can originate
# from user voice input via LLM extraction. Combined with base_url=None below
# (no remote fetch), this closes an SSRF/injection path in the PDF renderer.
_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=True)

_TAG_RE = re.compile(r"<[^>]*>")

# NOTE: this dict now lives in shared/i18n/bengali_calendar.py as
# GREGORIAN_MONTHS_BENGALI — kept as a local alias only so any other code
# still importing BENGALI_MONTHS from this module doesn't break.
BENGALI_MONTHS = GREGORIAN_MONTHS_BENGALI

_BANK_LINKAGE_LABELS_BENGALI = {
    "NONE": "এখনও লিংক করা হয়নি",
    "PHASE1": "প্রথম পর্যায় (Phase 1)",
    "PHASE2": "দ্বিতীয় পর্যায় (Phase 2)",
    "PHASE3": "তৃতীয় পর্যায় (Phase 3)",
}


def _clean(value: str | None, max_len: int = 120) -> str:
    """Strip tags outright rather than relying on escaping alone — defense in
    depth for a renderer (WeasyPrint) that would otherwise have outbound
    network access if a tag with a remote src slipped through."""
    if not value:
        return ""
    return _TAG_RE.sub("", value).strip()[:max_len]


async def generate_monthly_report(user_id: str, year: int, month: int) -> dict:
    from weasyprint import HTML

    s = get_settings()

    async with get_db_session() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if user is None:
            raise ValueError(f"generate_monthly_report: unknown user_id={user_id}")

        shg = None
        if user.shg_id:
            shg = (await db.execute(select(SHGGroup).where(SHGGroup.id == user.shg_id))).scalar_one_or_none()

        period_start = date(year, month, 1)
        period_end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

        entries = (
            (
                await db.execute(
                    select(LedgerEntry)
                    .where(LedgerEntry.user_id == user_id)
                    .where(LedgerEntry.entry_date >= period_start)
                    .where(LedgerEntry.entry_date < period_end)
                    .order_by(LedgerEntry.entry_date)
                )
            )
            .scalars()
            .all()
        )

        # Business-continuity signal: banks weight a consistent multi-month
        # record far more than one good month in isolation (this is a
        # genuine, commonly-cited loan-underwriting heuristic, not specific
        # to this product). Computed across the user's FULL ledger history,
        # not just this reporting period.
        earliest_entry_date = (
            await db.execute(select(func.min(LedgerEntry.entry_date)).where(LedgerEntry.user_id == user_id))
        ).scalar_one_or_none()

    income_by_category: dict[str, float] = {}
    expense_by_category: dict[str, float] = {}
    for e in entries:
        cat = _clean(e.category) or "অন্যান্য"
        amt = float(e.amount_inr)
        if e.entry_type == "INCOME":
            income_by_category[cat] = income_by_category.get(cat, 0.0) + amt
        else:
            expense_by_category[cat] = expense_by_category.get(cat, 0.0) + amt

    total_income = sum(income_by_category.values())
    total_expense = sum(expense_by_category.values())

    # Bangla calendar label uses the last day of the reporting month as its
    # reference point — a secondary, clearly-marked "traditional/approximate"
    # display alongside the authoritative Gregorian month/year below. See
    # shared/i18n/bengali_calendar.py for the precision caveat.
    last_day_of_period = date.fromordinal(period_end.toordinal() - 1)
    bangla_calendar_label = format_bangla_calendar_label(last_day_of_period)

    months_of_history = _months_of_history(earliest_entry_date, last_day_of_period)
    bank_linkage_label = _BANK_LINKAGE_LABELS_BENGALI.get(
        (shg.bank_linkage_status if shg else None) or "NONE", "এখনও লিংক করা হয়নি"
    )

    template = _env.get_template("monthly_report.html")
    html_content = template.render(
        member_name=_clean(user.name) or "সদস্য",
        shg_name=_clean(shg.name) if shg else "",
        district=_clean(user.district),
        month_bengali=GREGORIAN_MONTHS_BENGALI[month],
        year=year,
        bangla_calendar_label=bangla_calendar_label,
        income_by_category=income_by_category,
        expense_by_category=expense_by_category,
        total_income=total_income,
        total_expense=total_expense,
        net_profit=total_income - total_expense,
        generated_date=datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        # --- bank-loan-grade additions, all rendered from data the schema
        # already had (shg_groups.grade_level existed; bank_linkage_status
        # is new, migrations/0005_shg_bank_linkage.sql). None of this is
        # LLM-generated — every value here is a direct DB read or a plain
        # date-arithmetic computation, kept in the same "deterministic
        # facts, never invented" spirit as the rest of the P&L numbers. ---
        months_of_history=months_of_history,
        months_of_history_bengali=to_bengali_digits(months_of_history),
        shg_grade_level=shg.grade_level if shg else None,
        bank_linkage_label=bank_linkage_label,
        declaration_text=(
            f"এই তথ্য {(_clean(user.name) or 'সদস্য')} কর্তৃক প্রদত্ত ভয়েস/টেক্সট এন্ট্রি থেকে "
            f"কোথা-খাতা দ্বারা স্বয়ংক্রিয়ভাবে গণনা করা হয়েছে। এটি একটি স্ব-ঘোষিত ও "
            f"সিস্টেম-গণনাকৃত বিবরণী, নিরীক্ষিত (audited) হিসাব নয়।"
        ),
    )

    pdf_bytes = HTML(string=html_content, base_url=None).write_pdf()

    s3_key = f"reports/{user_id}/{year}/{month}/{uuid.uuid4().hex[:8]}.pdf"
    s3 = get_s3_client()
    s3.put_object(
        Bucket=s.s3_bucket, Key=s3_key, Body=pdf_bytes,
        ContentType="application/pdf", ServerSideEncryption="AES256",
    )
    s3_url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": s.s3_bucket, "Key": s3_key}, ExpiresIn=86400
    )

    return {"s3_url": s3_url, "total_income": total_income, "total_expense": total_expense}


def _months_of_history(earliest_entry_date, as_of: date) -> int:
    """Whole months of ledger history, counted from the first ever entry to
    the report's period end — e.g. a first entry in January and a March
    report reads as 3. Returns 0 if there's no history yet (new user), never
    negative, never a fabricated 'estimate'."""
    if earliest_entry_date is None:
        return 0
    first = earliest_entry_date.date() if hasattr(earliest_entry_date, "date") else earliest_entry_date
    months = (as_of.year - first.year) * 12 + (as_of.month - first.month) + 1
    return max(0, months)
