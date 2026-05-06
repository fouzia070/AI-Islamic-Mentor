import requests
import re

# -----------------------------------------------
# ACCURATE APIs
# -----------------------------------------------
QURANCOM_BASE_URL = "https://api.qurancdn.com/api/qdc"
HADITH_BASE_URL   = "https://hadith-api.vercel.app/v1"


def clean_text(text):
    """Removes non-Arabic/Urdu characters mixed in text."""
    if not text:
        return text
    cleaned = re.sub(r'(?<=[^\x00-\x7F])[a-zA-Z]+(?=[^\x00-\x7F])', '', text)
    cleaned = re.sub(r'[\u3000-\u9fff]', '', cleaned)
    cleaned = re.sub(r'[\u0900-\u097F]', '', cleaned)
    return cleaned.strip()


def get_sunnah_link(collection):
    """Generates working Sunnah.com link."""
    collection_map = {
        "bukhari"  : "bukhari",
        "muslim"   : "muslim",
        "tirmidhi" : "tirmidhi",
        "abudawud" : "abudawud",
        "nasai"    : "nasai",
        "ibnmajah" : "ibnmajah"
    }
    col = collection_map.get(collection.lower(), collection.lower())
    return f"https://sunnah.com/{col}"


# -----------------------------------------------
# QURAN FUNCTIONS
# -----------------------------------------------

def search_quran(keyword):
    """Searches Quran using Quran.com API."""
    try:
        url      = f"{QURANCOM_BASE_URL}/search?q={keyword}&size=3&page=1"
        response = requests.get(url, timeout=10)
        data     = response.json()
        results  = []
        hits     = data.get("search", {}).get("results", [])

        for hit in hits[:3]:
            verse_key = hit.get("verse_key", "")
            parts     = verse_key.split(":")
            results.append({
                "text"      : hit.get("text", ""),
                "surah"     : parts[0] if len(parts) > 0 else "",
                "ayah"      : parts[1] if len(parts) > 1 else "",
                "verse_key" : verse_key,
                "quran_link": f"https://quran.com/{verse_key.replace(':', '/')}"
            })

        return {"success": True, "results": results}

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_verse(surah_number, ayah_number):
    """Fetches single verse with Arabic + Urdu."""
    try:
        url = (
            f"{QURANCOM_BASE_URL}/verses/by_key/"
            f"{surah_number}:{ayah_number}"
            f"?translations=131,234"
            f"&fields=text_uthmani"
        )
        response     = requests.get(url, timeout=10)
        data         = response.json()
        verse        = data.get("verse", {})
        translations = verse.get("translations", [])

        english = ""
        urdu    = ""
        for t in translations:
            if t.get("resource_id") == 131:
                english = t.get("text", "")
            elif t.get("resource_id") == 234:
                urdu = t.get("text", "")

        return {
            "success": True,
            "arabic" : verse.get("text_uthmani", ""),
            "english": english,
            "urdu"   : urdu,
            "link"   : f"https://quran.com/{surah_number}/{ayah_number}"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_surah(surah_number):
    """Fetches complete Surah from Quran.com."""
    try:
        url      = (
            f"{QURANCOM_BASE_URL}/verses/by_chapter/{surah_number}"
            f"?translations=131,234"
            f"&fields=text_uthmani"
            f"&per_page=300"
        )
        response = requests.get(url, timeout=15)
        data     = response.json()
        verses   = data.get("verses", [])

        arabic  = []
        english = []
        urdu    = []

        for verse in verses:
            arabic.append(verse.get("text_uthmani", ""))
            for t in verse.get("translations", []):
                if t.get("resource_id") == 131:
                    english.append(t.get("text", ""))
                elif t.get("resource_id") == 234:
                    urdu.append(t.get("text", ""))

        return {
            "success"    : True,
            "arabic"     : arabic,
            "english"    : english,
            "urdu"       : urdu,
            "total_ayahs": len(verses)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------------------------
# HADITH FUNCTIONS
# -----------------------------------------------

def search_hadith(keyword):
    """Searches Hadiths from multiple collections."""
    try:
        results     = []
        collections = ["bukhari", "muslim", "tirmidhi", "abudawud"]

        for col in collections:
            url      = f"{HADITH_BASE_URL}/hadiths/{col}?page=1&limit=100"
            response = requests.get(url, timeout=10)
            data     = response.json()

            if "hadiths" in data:
                for h in data["hadiths"]:
                    text = h.get("hadith_english", "")
                    if keyword.lower() in text.lower():
                        results.append({
                            "text"      : text,
                            "collection": col.capitalize(),
                            "number"    : h.get("hadith_number", ""),
                            "link"      : get_sunnah_link(col)
                        })
                        if len(results) >= 3:
                            return {"success": True, "hadiths": results}

        return {"success": True, "hadiths": results}

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_hadith(collection="bukhari", page=1):
    """Fetches Hadiths from a collection."""
    try:
        url      = f"{HADITH_BASE_URL}/hadiths/{collection}?page={page}&limit=5"
        response = requests.get(url, timeout=10)
        data     = response.json()

        if "hadiths" in data:
            results = []
            for h in data["hadiths"]:
                results.append({
                    "text"      : h.get("hadith_english", ""),
                    "collection": collection.capitalize(),
                    "number"    : h.get("hadith_number", ""),
                    "link"      : get_sunnah_link(collection)
                })
            return {"success": True, "hadiths": results}

        return {"success": False}

    except Exception as e:
        return {"success": False, "error": str(e)}