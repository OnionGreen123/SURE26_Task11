import os


MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
API_VERSION = os.getenv("GEMINI_API_VERSION", "v1beta")
TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", MODEL)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

DEFAULT_FPS = float(os.getenv("STREAM_FPS", "1.0"))
STREAM_SECONDS = float(os.getenv("STREAM_SECONDS", "2.0"))
MAX_WIDTH = int(os.getenv("STREAM_MAX_WIDTH", "1280"))

RESPONSE_MIME_TYPE = os.getenv("RESPONSE_MIME_TYPE", "application/json")

