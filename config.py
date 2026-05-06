import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEBUG = True
SECRET_KEY = "islamic_mentor_secret_key"
APP_NAME = "AI Islamic Mentor"