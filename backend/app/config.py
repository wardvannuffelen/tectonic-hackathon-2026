import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5").strip()
DEMO_MODE = os.environ.get("DEMO_MODE", "false").strip().lower() == "true"
