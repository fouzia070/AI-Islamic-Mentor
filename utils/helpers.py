# ================================================
# Helper Functions
# ================================================

def format_response(response_text):
    """
    Cleans and formats the AI response.
    Removes any Hindi/Devanagari characters.
    """
    if not response_text:
        return "No response generated."

    # Remove Devanagari (Hindi) characters
    import re
    cleaned = re.sub(r'[\u0900-\u097F]', '', response_text)

    return cleaned.strip()

def validate_question(question):
    """
    Checks if question is valid
    before sending to AI.
    """
    if not question:
        return False, "Please type a question."

    if len(question.strip()) < 3:
        return False, "Question is too short."

    if len(question) > 1000:
        return False, "Question is too long. Please be more specific."

    return True, "Valid"


def get_query_type_label(query_type):
    """
    Returns a friendly label for
    each query type to show in UI.
    """
    labels = {
        "tafsir"      : "📖 Tafsir",
        "hadith"      : "📜 Hadith",
        "tarjuma"     : "🌍 Tarjuma",
        "notes"       : "📝 Study Notes",
        "islamic_qa"  : "❓ Islamic Q&A",
        "general"     : "🎓 Islamic Studies",
        "not_islamic" : "⚠️ Out of Scope"
    }
    return labels.get(query_type, "🕌 Islamic Mentor")