from langchain_groq import ChatGroq
from config import GROQ_API_KEY

def get_llm():
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=GROQ_API_KEY,
        temperature=0.1
    )
    return llm
