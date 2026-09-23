import os

from dotenv import load_dotenv


load_dotenv()


PLACES_API = os.getenv("PLACES_API")
if not PLACES_API:
    raise RuntimeError(
        "GOOGLE_MAPS_API_KEY is not set in .env"
    )


GEMINI = os.getenv("GEMINI")
if not GEMINI:
    raise RuntimeError(
        "GEMINI API is not set in .env"
    )


MODEL = os.getenv("MODEL")
if not MODEL:
    raise RuntimeError(
        "MODEL is not set in .env"
    )