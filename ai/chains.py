# ================================================
# Query Classification & Response Generation
# ================================================

from langchain_core.messages import HumanMessage
from ai.llm import get_llm
from ai.prompts import (
    TAFSIR_PROMPT,
    HADITH_PROMPT,
    TARJUMA_PROMPT,
    NOTES_PROMPT,
    ISLAMIC_QA_PROMPT,
    GENERAL_PROMPT,
    URDU_TAFSIR_PROMPT
)
from data.islamic_api import search_hadith, get_verse


def classify_query(user_input):
    text = user_input.lower()

    if any(word in text for word in [
        "urdu tafsir", "tafsir in urdu",
        "urdu mein tafsir", "in urdu",
        "urdu context", "urdu translation",
        "urdu me", "urdu main"
    ]):
        return "urdu_tafsir"
    
    elif any(word in text for word in [
        "tafsir", "tafseer", "ayat", "ayah",
        "surah", "verse", "quran says",
        "what does quran", "explain quran",
        "quran mein", "ayat ka matlab"
    ]):
        return "tafsir"

    elif any(word in text for word in [
        "hadith", "hadees", "prophet said",
        "sunnah", "narrated", "bukhari",
        "muslim", "tirmidhi", "abu dawud",
        "prophet's life", "sirah", "seerah",
        "sahaba", "nabi ne farmaya"
    ]):
        return "hadith"

    elif any(word in text for word in [
        "tarjuma", "translation", "translate",
        "urdu meaning", "english meaning",
        "ka matlab", "in urdu", "in english"
    ]):
        return "tarjuma"

    elif any(word in text for word in [
        "notes", "summary", "summarize",
        "key points", "main points",
        "brief explanation", "for exam",
        "revision", "short note"
    ]):
        return "notes"

    elif any(word in text for word in [
        "is it allowed", "is it permissible",
        "halal", "haram", "can i", "can muslims",
        "islamic ruling", "according to islam",
        "how to pray", "how to fast",
        "zakat", "hajj", "umrah", "ramadan",
        "five pillars", "namaz", "roza",
        "jaiz hai", "na jaiz", "gunah"
    ]):
        return "islamic_qa"

    elif any(word in text for word in [
        "islam", "islamic", "muslim", "allah",
        "faith", "iman", "mosque", "masjid",
        "quran", "prophet", "angel", "jannah",
        "jahannam", "day of judgment", "qiyamat",
        "islamic history", "fiqh", "sharia"
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
        "general"     : GENERAL_PROMPT
    }
    return prompts.get(query_type, GENERAL_PROMPT)


def fetch_real_islamic_data(user_question, query_type):
    """
    Fetches real authenticated data from
    Quran.com and Hadith APIs.
    """
    extra_context = ""

    try:
        if query_type in ["tafsir", "tarjuma", "urdu_tafsir"]:

            surah_map = {
    # 1–10
    "fatiha": (1, 7), "al-fatiha": (1, 7),
    "baqarah": (2, 286),
    "imran": (3, 200), "al-imran": (3, 200),
    "nisa": (4, 176),
    "maida": (5, 120),
    "anam": (6, 165),
    "araf": (7, 206), "a'raf": (7, 206),
    "anfal": (8, 75),
    "taubah": (9, 129), "tawbah": (9, 129),
    "yunus": (10, 109),

    # 11–20
    "hud": (11, 123),
    "yusuf": (12, 111),
    "raad": (13, 43), "rad": (13, 43),
    "ibrahim": (14, 52),
    "hijr": (15, 99),
    "nahl": (16, 128),
    "isra": (17, 111), "bani israel": (17, 111),
    "kahf": (18, 110),
    "maryam": (19, 98), "mariam": (19, 98),
    "taha": (20, 135),

    # 21–30
    "anbiya": (21, 112),
    "hajj": (22, 78),
    "muminoon": (23, 118),
    "nur": (24, 64),
    "furqan": (25, 77),
    "shuara": (26, 227),
    "naml": (27, 93),
    "qasas": (28, 88),
    "ankabut": (29, 69),
    "rum": (30, 60),

    # 31–40
    "luqman": (31, 34),
    "sajdah": (32, 30),
    "ahzab": (33, 73),
    "saba": (34, 54),
    "fatir": (35, 45),
    "yasin": (36, 83), "yaseen": (36, 83),
    "saffat": (37, 182),
    "sad": (38, 88),
    "zumar": (39, 75),
    "ghafir": (40, 85), "momin": (40, 85),

    # 41–50
    "fussilat": (41, 54),
    "shura": (42, 53),
    "zukhruf": (43, 89),
    "dukhan": (44, 59),
    "jathiyah": (45, 37),
    "ahqaf": (46, 35),
    "muhammad": (47, 38),
    "fath": (48, 29),
    "hujurat": (49, 18),
    "qaf": (50, 45),

    # 51–60
    "dhariyat": (51, 60),
    "tur": (52, 49),
    "najm": (53, 62),
    "qamar": (54, 55),
    "rahman": (55, 78),
    "waqiah": (56, 96),
    "hadid": (57, 29),
    "mujadila": (58, 22),
    "hashr": (59, 24),
    "mumtahina": (60, 13),

    # 61–70
    "saff": (61, 14),
    "jumuah": (62, 11),
    "munafiqoon": (63, 11),
    "taghabun": (64, 18),
    "talaq": (65, 12),
    "tahrim": (66, 12),
    "mulk": (67, 30),
    "qalam": (68, 52),
    "haqqah": (69, 52),
    "maarij": (70, 44),

    # 71–80
    "nuh": (71, 28),
    "jinn": (72, 28),
    "muzzammil": (73, 20),
    "muddaththir": (74, 56),
    "qiyamah": (75, 40),
    "insan": (76, 31), "dahr": (76, 31),
    "mursalat": (77, 50),
    "naba": (78, 40),
    "naziat": (79, 46),
    "abasa": (80, 42),

    # 81–90
    "takwir": (81, 29),
    "infitar": (82, 19),
    "mutaffifin": (83, 36), "tatfif": (83, 36),
    "inshiqaq": (84, 25),
    "buruj": (85, 22),
    "tariq": (86, 17),
    "ala": (87, 19),
    "ghashiyah": (88, 26),
    "fajr": (89, 30),
    "balad": (90, 20),

    # 91–100
    "shams": (91, 15),
    "layl": (92, 21),
    "duha": (93, 11),
    "ash sharh": (94, 8), "sharh": (94, 8),
    "tin": (95, 8),
    "alaq": (96, 19),
    "qadr": (97, 5),
    "bayyinah": (98, 8),
    "zalzalah": (99, 8),
    "adiyat": (100, 11),

    # 101–114
    "qariah": (101, 11),
    "at takathur": (102, 8),  "al takathur": (102, 8),
    "asr": (103, 3),
    "humazah": (104, 9),
    "fil": (105, 5),
    "quraysh": (106, 4),
    "maun": (107, 7),
    "kawthar": (108, 3),
    "kafirun": (109, 6),
    "nasr": (110, 3),
    "masad": (111, 5), "lahab": (111, 5),
    "ikhlas": (112, 4), "al-ikhlas": (112, 4),
    "al falaq": (113, 5), "falaq": (113, 5),
    "nas": (114, 6),

    # Special Case (placed at end)
    "ayat-ul-kursi": (2, 255),
}

            text = user_question.lower()

            # Sort by keyword length (longest first) to avoid wrong matches
            sorted_map = sorted(surah_map.items(), key=lambda x: len(x[0]), reverse=True)

            for keyword, (surah_num, last_ayah) in sorted_map:
                if keyword in text:
                    # Check for specific verse range
                    import re
                    range_match = re.search(
                        r'verse[s]?\s*(\d+)\s*(?:to|-)\s*(\d+)', text
                    )
                    single_match = re.search(
                        r'verse[s]?\s*(\d+)', text
                    )
                    ayah_match = re.search(
                        r'ayat?\s*(\d+)\s*(?:to|-|and)\s*(\d+)', text
                    )
                    num_match = re.search(
                        r'(\d+)\s*(?:to|-)\s*(\d+)', text
                    )

                    # Determine start and end verses
                    start_ayah = 1
                    end_ayah   = 10

                    if range_match:
                        start_ayah = int(range_match.group(1))
                        end_ayah   = int(range_match.group(2))
                    elif ayah_match:
                        start_ayah = int(ayah_match.group(1))
                        end_ayah   = int(ayah_match.group(2))
                    elif num_match:
                        start_ayah = int(num_match.group(1))
                        end_ayah   = int(num_match.group(2))
                    elif single_match:
                        start_ayah = int(single_match.group(1))
                        end_ayah   = start_ayah
                    elif "20" in text or "twenty" in text:
                        end_ayah = 20
                    elif "15" in text or "fifteen" in text:
                        end_ayah = 15
                    elif "5" in text or "five" in text:
                        end_ayah = 5
                    elif "complete" in text or "all" in text:
                        end_ayah = min(last_ayah, 20)

                    # Make sure within bounds
                    start_ayah = max(1, min(start_ayah, last_ayah))
                    end_ayah   = max(start_ayah, min(end_ayah, last_ayah))

                    extra_context += "\n\n📖 AUTHENTIC QURAN DATA (Quran.com):\n"
                    for ayah in range(start_ayah, end_ayah + 1):
                        verse = get_verse(surah_num, ayah)
                        if verse["success"]:
                            extra_context += f'Ayat {ayah}: {verse["arabic"]}\n'
                            extra_context += f'Urdu: {verse["urdu"]}\n\n'

                    extra_context += f'🔗 Quran.com Reference: https://quran.com/{surah_num}/{start_ayah}-{end_ayah}\n'
                    extra_context += f'\nCRITICAL INSTRUCTION:\n'
                    extra_context += f'1. The Arabic text above is from Quran.com API\n'
                    extra_context += f'1. Use EXACTLY this Arabic text — word for word\n'
                    extra_context += f'2. Do NOT replace or modify ANY Arabic word\n'
                    extra_context += f'3. Do NOT add Arabic from your own knowledge\n'
                    extra_context += f'4. Show Urdu translation for each verse\n'
                    extra_context += f'5. Include reference link at the END\n'
                    extra_context += f'5. If you change even ONE Arabic word, it is WRONG\n'
                    extra_context += f'7. Include reference link at the END\n'
                    break

        # -----------------------------------------------
        # HADITH SECTION (FIXED & OPTIMIZED)
        # -----------------------------------------------
        elif query_type == "hadith":

            keyword = user_question.lower()

            # Remove useless words
            stop_words = ["give", "me", "hadith", "on", "about", "the", "a"]

            keywords = [
                word for word in keyword.split()
                if word not in stop_words
            ]

            # Fallback if nothing remains
            if not keywords:
                keywords = ["faith"]

            hadith_data = {"success": True, "hadiths": []}
            seen = set()

            # Search using multiple keywords
            for word in keywords:
                result = search_hadith(word)

                if result["success"] and result["hadiths"]:
                    for h in result["hadiths"]:
                        key = f"{h['collection']}-{h['number']}"
                        if key not in seen:
                            hadith_data["hadiths"].append(h)
                            seen.add(key)

                if len(hadith_data["hadiths"]) >= 2:
                    break

            # Add to context
            if hadith_data["success"] and hadith_data["hadiths"]:
                extra_context += "\n\n📜 AUTHENTIC HADITH DATA:\n"

                for h in hadith_data["hadiths"][:2]:
                    extra_context += f'"{h["text"]}"\n'
                    extra_context += f'— ({h["collection"]}, #{h["number"]})\n'
                    extra_context += f'🔗 Reference: {h["link"]}\n\n'
    except Exception:
        pass

    return extra_context


def generate_response(user_question):
    try:
        query_type = classify_query(user_question)

        if query_type == "not_islamic":
            return {
                "answer": """🕌 Assalamu Alaikum!

I am AI Islamic Mentor and I only answer Islamic questions.

I can help you with:
- 📖 Tafsir — Quranic explanations
- 📜 Hadith — Prophet's traditions
- 🌍 Tarjuma — Translations
- 📝 Study Notes — Islamic summaries
- ❓ Islamic Q&A — Halal/Haram rulings
- 🎓 Islamic Studies — General knowledge

Please ask an Islamic question!
JazakAllah Khair 🌙""",
                "query_type": "not_islamic",
                "success"   : True
            }

        # Get real Islamic data first
        prompt_template = get_prompt_template(query_type)
        extra_context   = fetch_real_islamic_data(
            user_question, query_type
        )

        # For Quran queries — add extra reminder
        if query_type in ["tafsir", "tarjuma", "urdu_tafsir"] and extra_context:
            final_reminder = """

ABSOLUTE FINAL RULES:
- Copy Arabic EXACTLY from AUTHENTIC QURAN DATA
- Do NOT write your own Arabic
- Write Surah name FULLY in Urdu only — example: سورہ الملک NOT المulk
- Do NOT mix English letters in Urdu/Arabic text
"""
        else:
            final_reminder = ""

        filled_prompt = prompt_template.format(
            question=user_question
        ) + extra_context + final_reminder

        llm      = get_llm()
        messages = [HumanMessage(content=filled_prompt)]
        response = llm.invoke(messages)

        return {
            "answer"    : response.content,
            "query_type": query_type,
            "success"   : True
        }

    except Exception as e:
        return {
            "answer"    : f"Error: {str(e)}",
            "query_type": "error",
            "success"   : False
        }