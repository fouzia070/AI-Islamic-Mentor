# ================================================
# Query Classification & Response Generation
# Updated: Quran.com API integration for number-based queries
# ================================================

import re
import requests
from typing import Optional, List
from langchain_core.messages import HumanMessage
from ai.llm import get_llm
from ai.prompts import (
    TAFSIR_PROMPT,
    HADITH_PROMPT,
    TARJUMA_PROMPT,
    NOTES_PROMPT,
    ISLAMIC_QA_PROMPT,
    GENERAL_PROMPT,
    URDU_TAFSIR_PROMPT,
)
from data.dataset_retriever import (
    get_quran_verses,
    get_all_tafsir,
    search_hadiths_local,
    search_hadiths_multilang,
    resolve_surah_and_ayahs,
)


# -----------------------------------------------
# Complete Surah Name Lookup (all 114)
# -----------------------------------------------

SURAH_NAMES = {
    1:   "Al-Fatihah",       2:   "Al-Baqarah",       3:   "Aal-e-Imran",
    4:   "An-Nisa",          5:   "Al-Maidah",         6:   "Al-An'am",
    7:   "Al-A'raf",         8:   "Al-Anfal",          9:   "At-Tawbah",
    10:  "Yunus",            11:  "Hud",               12:  "Yusuf",
    13:  "Ar-Ra'd",          14:  "Ibrahim",           15:  "Al-Hijr",
    16:  "An-Nahl",          17:  "Al-Isra",           18:  "Al-Kahf",
    19:  "Maryam",           20:  "Ta-Ha",             21:  "Al-Anbiya",
    22:  "Al-Hajj",          23:  "Al-Mu'minun",       24:  "An-Nur",
    25:  "Al-Furqan",        26:  "Ash-Shu'ara",       27:  "An-Naml",
    28:  "Al-Qasas",         29:  "Al-Ankabut",        30:  "Ar-Rum",
    31:  "Luqman",           32:  "As-Sajdah",         33:  "Al-Ahzab",
    34:  "Saba",             35:  "Fatir",              36:  "Ya-Sin",
    37:  "As-Saffat",        38:  "Sad",               39:  "Az-Zumar",
    40:  "Ghafir",           41:  "Fussilat",          42:  "Ash-Shura",
    43:  "Az-Zukhruf",       44:  "Ad-Dukhan",         45:  "Al-Jathiyah",
    46:  "Al-Ahqaf",         47:  "Muhammad",          48:  "Al-Fath",
    49:  "Al-Hujurat",       50:  "Qaf",               51:  "Adh-Dhariyat",
    52:  "At-Tur",           53:  "An-Najm",           54:  "Al-Qamar",
    55:  "Ar-Rahman",        56:  "Al-Waqi'ah",        57:  "Al-Hadid",
    58:  "Al-Mujadila",      59:  "Al-Hashr",          60:  "Al-Mumtahanah",
    61:  "As-Saf",           62:  "Al-Jumu'ah",        63:  "Al-Munafiqun",
    64:  "At-Taghabun",      65:  "At-Talaq",          66:  "At-Tahrim",
    67:  "Al-Mulk",          68:  "Al-Qalam",          69:  "Al-Haqqah",
    70:  "Al-Ma'arij",       71:  "Nuh",               72:  "Al-Jinn",
    73:  "Al-Muzzammil",     74:  "Al-Muddaththir",    75:  "Al-Qiyamah",
    76:  "Al-Insan",         77:  "Al-Mursalat",       78:  "An-Naba",
    79:  "An-Nazi'at",       80:  "Abasa",             81:  "At-Takwir",
    82:  "Al-Infitar",       83:  "Al-Mutaffifin",     84:  "Al-Inshiqaq",
    85:  "Al-Buruj",         86:  "At-Tariq",          87:  "Al-A'la",
    88:  "Al-Ghashiyah",     89:  "Al-Fajr",           90:  "Al-Balad",
    91:  "Ash-Shams",        92:  "Al-Layl",           93:  "Ad-Duha",
    94:  "Ash-Sharh",        95:  "At-Tin",            96:  "Al-Alaq",
    97:  "Al-Qadr",          98:  "Al-Bayyinah",       99:  "Az-Zalzalah",
    100: "Al-Adiyat",        101: "Al-Qari'ah",        102: "At-Takathur",
    103: "Al-Asr",           104: "Al-Humazah",        105: "Al-Fil",
    106: "Quraysh",          107: "Al-Ma'un",          108: "Al-Kawthar",
    109: "Al-Kafirun",       110: "An-Nasr",           111: "Al-Masad",
    112: "Al-Ikhlas",        113: "Al-Falaq",          114: "An-Nas",
}

# -----------------------------------------------
# AlQuran.cloud API config
# Free, no API key required.
# Editions: Arabic | Urdu (Jalandhari) | English (Sahih International)
# -----------------------------------------------

ALQURAN_API_BASE        = "https://api.alquran.cloud/v1"
ALQURAN_ARABIC_EDITION  = "quran-simple"
ALQURAN_URDU_EDITION    = "ur.jalandhry"
ALQURAN_ENGLISH_EDITION = "en.sahih"

# -----------------------------------------------
# Token budget control
# Groq free tier: 6000 TPM on llama-3.1-8b-instant
# Each trilingual ayah ≈ 60 tokens (Arabic + Urdu + English)
# We keep context under ~2500 tokens to leave room for
# the prompt template + instructions + LLM reply.
# 2500 / 60 ≈ 40 ayahs max per request.
# -----------------------------------------------
MAX_AYAHS_PER_REQUEST = 40   # hard cap — never send more than this to LLM
APPROX_TOKENS_PER_AYAH = 60  # estimate used for page-size messaging to user


# -----------------------------------------------
# AlQuran.cloud API fetch helpers
# -----------------------------------------------

def _api_fetch_full_surah(surah_num: int, edition: str) -> Optional[List]:
    """
    Fetches all ayahs of a surah from AlQuran.cloud for a given edition.
    Returns list of ayah dicts, or None on failure.
    """
    url = f"{ALQURAN_API_BASE}/surah/{surah_num}/{edition}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200:
                return data["data"]["ayahs"]
    except requests.RequestException:
        pass
    return None





def fetch_from_quran_api(
    surah_num: int,
    start_ayah: int = 1,
    end_ayah: int = None,
    lang: str = "ur",
) -> str:
    """
    Fetches verified Quran data (Arabic + Urdu + English) from AlQuran.cloud.
    Returns a formatted context string ready to inject into the LLM prompt.
    TOKEN SAFETY:
      - Hard cap of MAX_AYAHS_PER_REQUEST (40) ayahs sent to LLM.
      - If a surah has more ayahs than the cap, only the first 40 are sent
        and a clear notice is added telling the user to ask for a specific
        range (e.g. "surah 2 ayat 1 to 40").
      - This keeps every request well under Groq's 6000 TPM limit.
    """
    confirmed_name = SURAH_NAMES.get(surah_num, f"Surah {surah_num}")
    context        = ""

    try:
        # ── Step 1: Fetch Arabic for the full surah (to know total ayah count) ──
        arabic_list = _api_fetch_full_surah(surah_num, ALQURAN_ARABIC_EDITION)
        if not arabic_list:
            return ""

        total_ayahs = len(arabic_list)

        # ── Step 2: Determine the actual range to serve ──────────────────────
        # start_ayah is 1-indexed; clamp to valid range
        actual_start = max(1, start_ayah)
        if end_ayah is None:
            # User asked for full surah — cap at MAX_AYAHS_PER_REQUEST
            actual_end = min(actual_start + MAX_AYAHS_PER_REQUEST - 1, total_ayahs)
        else:
            # User asked for explicit range — still cap it
            actual_end = min(end_ayah, actual_start + MAX_AYAHS_PER_REQUEST - 1, total_ayahs)

        is_truncated   = (actual_end < total_ayahs) and (end_ayah is None)
        ayahs_to_serve = actual_end - actual_start + 1

        # ── Step 3: Slice Arabic list to the capped range ────────────────────
        arabic_slice = arabic_list[actual_start - 1: actual_end]

        # ── Step 4: Fetch Urdu & English for ONLY the capped range ───────────
        # Use the juz/page endpoint trick: fetch full surah once, then slice.
        urdu_full    = _api_fetch_full_surah(surah_num, ALQURAN_URDU_EDITION)
        english_full = _api_fetch_full_surah(surah_num, ALQURAN_ENGLISH_EDITION)

        urdu_slice    = urdu_full[actual_start - 1: actual_end]    if urdu_full    else []
        english_slice = english_full[actual_start - 1: actual_end] if english_full else []

        # ── Step 5: Build lookup maps ─────────────────────────────────────────
        urdu_map    = {a["numberInSurah"]: a["text"] for a in urdu_slice}    if urdu_slice    else {}
        english_map = {a["numberInSurah"]: a["text"] for a in english_slice} if english_slice else {}

        # ── Step 6: Build the context string ─────────────────────────────────
        context += "\n\n" + "═" * 58 + "\n"
        context += "📖 VERIFIED QURAN DATA — AlQuran.cloud API\n"
        context += f"✅ CONFIRMED: Surah {surah_num} = {confirmed_name}\n"
        context += f"   Showing ayat {actual_start}–{actual_end} of {total_ayahs} total\n"
        context += "(Arabic: Tanzil | Urdu: Jalandhari | English: Sahih Int'l)\n"
        context += "═" * 58 + "\n\n"

        for ayah in arabic_slice:
            num     = ayah["numberInSurah"]
            arabic  = ayah["text"]
            urdu    = urdu_map.get(num, "")
            english = english_map.get(num, "")

            context += f"آیت / Ayat {num}:\n"
            context += f"  Arabic  : {arabic}\n"
            if urdu:
                context += f"  Urdu    : {urdu}\n"
            if english:
                context += f"  English : {english}\n"
            context += "\n"

        # ── Step 7: Reference + truncation notice ─────────────────────────────
        end_ref  = f"-{actual_end}" if actual_end != actual_start else ""
        ref_part = f"/{actual_start}{end_ref}" if actual_start > 1 else ""
        context += (
            f"🔗 Quran.com Reference: https://quran.com/{surah_num}{ref_part}\n"
            f"📡 Source: AlQuran.cloud (alquran.cloud/api)\n"
        )

        # Tell the LLM about truncation so it can inform the user naturally
        if is_truncated:
            next_start = actual_end + 1
            next_end   = min(next_start + MAX_AYAHS_PER_REQUEST - 1, total_ayahs)
            context += (
                f"\n⚠️ TRUNCATION NOTICE (for LLM — tell user this):\n"
                f"This surah has {total_ayahs} ayahs. Due to message size limits,\n"
                f"only ayat {actual_start}–{actual_end} are shown here.\n"
                f"To see the next section, the user should ask:\n"
                f"'Surah {surah_num} ayat {next_start} to {next_end} ka tarjuma'\n"
                f"Continue until all {total_ayahs} ayahs have been read.\n"
            )

    except Exception as e:
        context = f"\n[Quran API fetch error: {str(e)}]\n"

    return context


# -----------------------------------------------
# Number & range extraction helpers
# -----------------------------------------------

def _query_has_surah_number(user_input: str) -> bool:
    """
    Returns True if the query is asking for a Surah BY NUMBER.
    Catches patterns like:
      "surah 25", "25th surah", "surah number 25",
      "25 number ki surah", "give tarjuma of 4th surah"
    """
    text = user_input.lower()
    return bool(re.search(
        r'(surah\s*(no\.?|number|#)?\s*\d+'
        r'|\d+\s*(st|nd|rd|th|wi|vin|waan)?\s*surah'
        r'|\d+\s*(number\s*ki|no\.?)\s*surah'
        r'|surah\s*\d+\s*k[ia])',
        text
    ))


def _extract_surah_number_from_text(user_question: str):
    """
    Extracts the first valid surah number (1–114) from query text.
    Returns (surah_num, 1, None) or None if not found.
    """
    matches = re.findall(r'\b(\d{1,3})\b', user_question.lower())
    for m in matches:
        num = int(m)
        if 1 <= num <= 114:
            return (num, 1, None)
    return None


def _extract_ayah_range_from_text(user_question: str):
    """
    Tries to extract specific ayah range from query text.
    Examples:
      "surah 2 ayat 255"       → (255, 255)
      "surah 18 ayat 1 to 10"  → (1, 10)
      "surah 25"               → (1, None)  ← full surah
    """
    text = user_question.lower()

    # Range: "ayat 1 to 10" or "ayah 1-10"
    range_match = re.search(r'ayah?\s*(\d+)\s*(to|-)\s*(\d+)', text)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(3))

    # Single ayah: "ayat 255"
    single_match = re.search(r'ayah?\s*(\d+)', text)
    if single_match:
        n = int(single_match.group(1))
        return n, n

    return 1, None  # default: full surah from ayah 1


# -----------------------------------------------
# Query Classifier
# -----------------------------------------------

def classify_query(user_input):
    text = user_input.lower()

    # ── Surah-by-number: checked FIRST before everything else ────────────────
    if _query_has_surah_number(user_input):
        if any(w in text for w in [
            "urdu tafsir", "tafsir in urdu", "urdu mein tafsir",
            "urdu me tafsir", "urdu main tafsir",
            "israr ahmad", "ibn kathir urdu",
        ]):
            return "urdu_tafsir"
        if any(w in text for w in ["tafsir", "tafseer", "explanation", "explain"]):
            return "tafsir"
        return "tarjuma"

    # Urdu tafsir — before generic tafsir
    if any(word in text for word in [
        "urdu tafsir", "tafsir in urdu",
        "urdu mein tafsir", "urdu context",
        "urdu me tafsir", "urdu main tafsir",
        "israr ahmad", "ibn kathir urdu",
    ]):
        return "urdu_tafsir"

    elif any(word in text for word in [
        "tafsir", "tafseer", "explanation of",
        "explain quran", "quran says", "what does quran",
        "quran mein", "ayat ka matlab", "jalalayn", "maarif",
    ]):
        return "tafsir"

    elif any(word in text for word in [
        "tarjuma", "translation", "translate",
        "urdu meaning", "english meaning",
        "ka matlab", "in urdu", "in english",
        "ayah", "ayat", "surah", "verse",
    ]):
        return "tarjuma"

    elif any(word in text for word in [
        "hadith", "hadees", "prophet said",
        "sunnah", "narrated", "bukhari",
        "muslim", "tirmidhi", "abu dawud",
        "prophet's life", "sirah", "seerah",
        "sahaba", "nabi ne farmaya",
    ]):
        return "hadith"

    elif any(word in text for word in [
        "notes", "summary", "summarize",
        "key points", "main points",
        "brief explanation", "for exam",
        "revision", "short note",
    ]):
        return "notes"

    elif any(word in text for word in [
        "is it allowed", "is it permissible",
        "halal", "haram", "can i", "can muslims",
        "islamic ruling", "according to islam",
        "how to pray", "how to fast",
        "zakat", "hajj", "umrah", "ramadan",
        "five pillars", "namaz", "roza",
        "jaiz hai", "na jaiz", "gunah",
    ]):
        return "islamic_qa"

    elif any(word in text for word in [
        "islam", "islamic", "muslim", "allah",
        "faith", "iman", "mosque", "masjid",
        "quran", "prophet", "angel", "jannah",
        "jahannam", "day of judgment", "qiyamat",
        "islamic history", "fiqh", "sharia",
    ]):
        return "general"

    else:
        return "not_islamic"


def get_prompt_template(query_type):
    prompts = {
        "tafsir"      : TAFSIR_PROMPT,
        "urdu_tafsir" : URDU_TAFSIR_PROMPT,
        "hadith"      : HADITH_PROMPT,
        "tarjuma"     : TARJUMA_PROMPT,
        "notes"       : NOTES_PROMPT,
        "islamic_qa"  : ISLAMIC_QA_PROMPT,
        "general"     : GENERAL_PROMPT,
    }
    return prompts.get(query_type, GENERAL_PROMPT)


# -----------------------------------------------
# Language detection
# -----------------------------------------------

def _detect_lang_pref(text):
    """Returns 'ur' if query is Urdu-oriented, otherwise 'en'."""
    text_lower = text.lower()
    urdu_signals = [
        "urdu", "in urdu", "urdu mein", "urdu main",
        "urdu me", "ka matlab", "nabi ne farmaya", "tarjuma",
    ]
    if any(sig in text_lower for sig in urdu_signals):
        return "ur"
    return "en"


def _detect_hadith_lang(text):
    """Returns 'urd' if Urdu query, 'eng' otherwise."""
    return "urd" if _detect_lang_pref(text) == "ur" else "eng"


# -----------------------------------------------
# Main data fetcher
# -----------------------------------------------

def fetch_real_islamic_data(user_question, query_type):
    """
    Data source priority for Quran queries:
      1. Surah asked BY NUMBER  → AlQuran.cloud API directly (most reliable)
      2. Surah asked by NAME    → local dataset first, API fallback if empty
      3. All sources fail       → hard refusal block (LLM cannot hallucinate)
    """
    extra_context = ""

    try:
        # ===================================================
        # TARJUMA
        # ===================================================
        if query_type == "tarjuma":

            # ── PRIORITY 1: Number-based query → straight to API ─────────────
            if _query_has_surah_number(user_question):
                resolved = _extract_surah_number_from_text(user_question)
                if resolved:
                    surah_num, _, _ = resolved
                    start_ayah, end_ayah = _extract_ayah_range_from_text(user_question)
                    lang = _detect_lang_pref(user_question)

                    api_context = fetch_from_quran_api(
                        surah_num, start_ayah, end_ayah, lang
                    )
                    if api_context:
                        extra_context += api_context
                        extra_context += _quran_instructions()
                        return extra_context  # Done — skip local dataset entirely

            # ── PRIORITY 2: Name-based query → local dataset ──────────────────
            resolved = resolve_surah_and_ayahs(user_question)
            if resolved:
                surah_num, start_ayah, end_ayah = resolved
                lang   = _detect_lang_pref(user_question)
                verses = get_quran_verses(surah_num, start_ayah, end_ayah, lang=lang)

                if verses:
                    confirmed_name = SURAH_NAMES.get(surah_num, f"Surah {surah_num}")
                    surah_name     = verses[0].get("surah_name", confirmed_name)
                    extra_context += f"\n✅ CONFIRMED SURAH: {surah_num} = {confirmed_name}\n"
                    extra_context += "\n\n📖 QURAN TARJUMA — Local Tanzil Dataset:\n"
                    extra_context += f"Surah: {surah_name} ({surah_num})\n\n"

                    for v in verses:
                        extra_context += f'Ayat {v["ayah"]}:\n'
                        extra_context += f'  Arabic  : {v["arabic"]}\n'
                        extra_context += f'  English : {v["english"]}\n'
                        extra_context += f'  Urdu    : {v["urdu"]}\n\n'

                    end_ref = f'-{end_ayah}' if end_ayah and end_ayah != start_ayah else ''
                    extra_context += (
                        f'🔗 Quran.com Reference: '
                        f'https://quran.com/{surah_num}/{start_ayah}{end_ref}\n'
                    )
                    extra_context += _quran_instructions()

                else:
                    # ── PRIORITY 3: Local empty → API fallback ────────────────
                    api_context = fetch_from_quran_api(
                        surah_num, start_ayah, end_ayah or start_ayah
                    )
                    if api_context:
                        extra_context += api_context
                        extra_context += _quran_instructions()

        # ===================================================
        # TAFSIR (English)
        # ===================================================
        elif query_type == "tafsir":
            resolved = resolve_surah_and_ayahs(user_question)
            if not resolved:
                resolved = _extract_surah_number_from_text(user_question)

            if resolved:
                surah_num, start_ayah, end_ayah = resolved
                confirmed_name = SURAH_NAMES.get(surah_num, f"Surah {surah_num}")
                extra_context += f"\n✅ CONFIRMED SURAH: {surah_num} = {confirmed_name}\n"

                verses = get_quran_verses(surah_num, start_ayah, end_ayah, lang="en")
                tafsir = get_all_tafsir(surah_num, start_ayah, end_ayah, lang="en")

                if verses:
                    surah_name = verses[0].get("surah_name", confirmed_name)
                    extra_context += "\n\n📖 QURAN TEXT (Local Tanzil):\n"
                    extra_context += f"Surah: {surah_name} ({surah_num})\n\n"
                    for v in verses:
                        extra_context += f'Ayat {v["ayah"]}:\n'
                        extra_context += f'  Arabic  : {v["arabic"]}\n'
                        extra_context += f'  English : {v["english"]}\n\n'
                else:
                    # API fallback for verse text
                    api_context = fetch_from_quran_api(
                        surah_num, start_ayah, end_ayah or start_ayah, lang="en"
                    )
                    if api_context:
                        extra_context += api_context

                if tafsir:
                    source_label = tafsir[0].get("source_label", "Tafsir")
                    extra_context += f'\n📚 TAFSIR FROM LOCAL DATASET ({source_label}):\n\n'
                    for t in tafsir:
                        extra_context += f'Ayat {t["ayah"]} — {t["text"]}\n\n'

                if verses or tafsir:
                    extra_context += (
                        f'🔗 Reference: https://quran.com/{surah_num}/{start_ayah}\n'
                    )
                    extra_context += _quran_instructions()

        # ===================================================
        # URDU TAFSIR
        # ===================================================
        elif query_type == "urdu_tafsir":
            resolved = resolve_surah_and_ayahs(user_question)
            if not resolved:
                resolved = _extract_surah_number_from_text(user_question)

            if resolved:
                surah_num, start_ayah, end_ayah = resolved
                confirmed_name = SURAH_NAMES.get(surah_num, f"Surah {surah_num}")
                extra_context += f"\n✅ CONFIRMED SURAH: {surah_num} = {confirmed_name}\n"

                verses = get_quran_verses(surah_num, start_ayah, end_ayah, lang="ur")
                tafsir = get_all_tafsir(surah_num, start_ayah, end_ayah, lang="ur")

                if verses:
                    surah_name = verses[0].get("surah_name", confirmed_name)
                    extra_context += "\n\n📖 QURAN TEXT (Local Tanzil):\n"
                    extra_context += f"Surah: {surah_name} ({surah_num})\n\n"
                    for v in verses:
                        extra_context += f'آیت {v["ayah"]}:\n'
                        extra_context += f'  عربی  : {v["arabic"]}\n'
                        extra_context += f'  اردو  : {v["urdu"]}\n\n'
                else:
                    api_context = fetch_from_quran_api(
                        surah_num, start_ayah, end_ayah or start_ayah, lang="ur"
                    )
                    if api_context:
                        extra_context += api_context

                if tafsir:
                    source_label = tafsir[0].get("source_label", "تفسیر")
                    extra_context += f'\n📚 TAFSIR (LOCAL — {source_label}):\n\n'
                    for t in tafsir:
                        extra_context += f'آیت {t["ayah"]} — {t["text"]}\n\n'

                if verses or tafsir:
                    extra_context += (
                        f'🔗 Reference: https://quran.com/{surah_num}/{start_ayah}\n'
                    )
                    extra_context += _quran_instructions()

        # ===================================================
        # HADITH
        # ===================================================
        elif query_type == "hadith":
            keywords = _extract_hadith_keywords(user_question)
            lang     = _detect_hadith_lang(user_question)

            hadiths = search_hadiths_local(keywords, max_results=3, lang=lang)
            if not hadiths and lang != "eng":
                hadiths = search_hadiths_local(keywords, max_results=3, lang="eng")

            if hadiths:
                extra_context += "\n\n📜 AUTHENTIC HADITH — Local Dataset:\n"
                for h in hadiths[:3]:
                    extra_context += f'\n"{h["text"]}"\n'
                    extra_context += f'— {h["collection"]}, Hadith #{h["number"]}\n'
                    extra_context += f'🔗 {h["link"]}\n'
                extra_context += _hadith_instructions()

    except Exception as e:
        extra_context += f"\n[Dataset retrieval note: {str(e)}]\n"

    # ── Hard refusal block: all sources failed ───────────────────────────────
    if not extra_context.strip() and query_type in ["tarjuma", "tafsir", "urdu_tafsir"]:
        fallback_num  = _extract_surah_number_from_text(user_question)
        fallback_link = (
            f"https://quran.com/{fallback_num[0]}"
            if fallback_num else "https://quran.com"
        )
        extra_context = (
            "\n\n⚠️ ALL DATA SOURCES FAILED — NO VERIFIED DATA AVAILABLE.\n"
            "═══════════════════════════════════════════════════════════\n"
            "ABSOLUTE RULE: Do NOT generate, guess, fabricate, or\n"
            "reconstruct ANY Quranic Arabic text or Urdu/English translation.\n"
            "Your own training knowledge of the Quran is NOT an allowed source.\n"
            "═══════════════════════════════════════════════════════════\n"
            "Respond ONLY with this message:\n"
            "'Assalamu Alaikum! Maafi chahta hoon — is waqt is Surah\n"
            " ka verified data available nahi hua. Meherbani karke\n"
            f" yahan dekhen: {fallback_link}  — JazakAllah Khair.'\n"
            "═══════════════════════════════════════════════════════════\n"
            "Do NOT show any Arabic. Do NOT show any translation.\n"
        )

    return extra_context


# -----------------------------------------------
# Hadith keyword extractor
# -----------------------------------------------

HADITH_STOP_WORDS = {
    "give", "me", "hadith", "hadees", "on", "about", "the", "a", "an",
    "show", "find", "get", "share", "tell", "what", "is", "are",
    "from", "in", "of", "and", "or", "bukhari", "muslim",
}

def _extract_hadith_keywords(text):
    words    = text.lower().split()
    keywords = [w for w in words if w not in HADITH_STOP_WORDS and len(w) > 2]
    return keywords if keywords else ["faith"]


# -----------------------------------------------
# Instruction blocks injected into the LLM prompt
# -----------------------------------------------

def _quran_instructions():
    return (
        "\nCRITICAL INSTRUCTIONS FOR QURAN TEXT:\n"
        "1. Use EXACTLY the Arabic text from the data block above — word for word\n"
        "2. Do NOT replace, modify, or paraphrase ANY Arabic word\n"
        "3. Do NOT add any Arabic from your own training knowledge\n"
        "4. Display Arabic + Urdu + English for every ayah shown above\n"
        "5. If a tafsir excerpt is provided, incorporate it in your explanation\n"
        "6. Write Surah name fully in Urdu script — no English in Arabic/Urdu text\n"
        "7. Include the reference link at the END of your response\n"
        "8. NEVER invent Quranic verses not present in the data block above\n"
        "9. If the data block is empty, say data unavailable — do NOT guess\n"
        "10. The ✅ CONFIRMED SURAH line is authoritative — use that Surah ONLY\n"
        "11. NEVER confuse Surah numbers — e.g. Surah 25=Al-Furqan, 48=Al-Fath\n"
        "12. Your training knowledge of Quranic text is FORBIDDEN as a source\n"
        "13. If data came from AlQuran.cloud API, mention that in your response\n"
    )


def _hadith_instructions():
    return (
        "\nCRITICAL INSTRUCTIONS FOR HADITH:\n"
        "1. Use EXACTLY the hadith text provided above\n"
        "2. Do NOT fabricate or alter any hadith text\n"
        "3. Always mention the collection name and hadith number\n"
        "4. Include the sunnah.com reference link\n"
        "5. Add brief explanation/context after the hadith text\n"
    )


# -----------------------------------------------
# Main response generator
# -----------------------------------------------

def generate_response(user_question):
    try:
        query_type = classify_query(user_question)

        if query_type == "not_islamic":
            return {
                "answer": """🕌 Assalamu Alaikum!
I am AI Islamic Mentor and I only answer Islamic questions.
I can help you with:
- 📖 Tafsir — Quranic explanations (English: Jalalayn & Ma'arif | Urdu: Ibn Kathir & Israr Ahmad)
- 📜 Hadith — Bukhari (English, Urdu, Arabic)
- 🌍 Tarjuma — Quran translations (Arabic + English + Urdu)
- 📝 Study Notes — Islamic summaries
- ❓ Islamic Q&A — Halal/Haram rulings
- 🎓 Islamic Studies — General knowledge
Please ask an Islamic question!
JazakAllah Khair 🌙""",
                "query_type": "not_islamic",
                "success"   : True,
            }

        prompt_template = get_prompt_template(query_type)
        extra_context   = fetch_real_islamic_data(user_question, query_type)

        if query_type in ["tafsir", "tarjuma", "urdu_tafsir"] and extra_context.strip():
            final_reminder = (
                "\n\nABSOLUTE FINAL RULES:\n"
                "- Copy Arabic EXACTLY from the data block above — no exceptions\n"
                "- Do NOT write your own Arabic under any circumstance\n"
                "- The ✅ CONFIRMED SURAH / API header is the only valid Surah\n"
                "- Write Surah name FULLY in Urdu script — e.g. سورۃ الفرقان NOT 'Al-Furqan'\n"
                "- Do NOT mix English letters in Urdu/Arabic text\n"
                "- Do NOT use your training data as a Quran source\n"
                "- If data came from AlQuran.cloud API, say so in your response\n"
            )
        else:
            final_reminder = ""

        filled_prompt = (
            prompt_template.format(question=user_question)
            + extra_context
            + final_reminder
        )

        llm      = get_llm()
        messages = [HumanMessage(content=filled_prompt)]
        response = llm.invoke(messages)

        return {
            "answer"    : response.content,
            "query_type": query_type,
            "success"   : True,
        }

    except Exception as e:
        return {
            "answer"    : f"Error: {str(e)}",
            "query_type": "error",
            "success"   : False,
        }
