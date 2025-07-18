import os
import logging
import textwrap
from datetime import datetime
from dotenv import load_dotenv
import requests

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "mistralai/mistral-7b-instruct"
API_KEY = os.getenv("OPENROUTER_API_KEY")


# Set up basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

VALID_BASE_CMDS = {
    "/dashboard",
    "/overview_summary",
    "/fraud_summary",
    "/daily_summary",
    "/client_summary",
}


# ──────────────────────────────────────────────
# Core LLM-calling logic
# ──────────────────────────────────────────────

def call_llm(user_message: str) -> str:
    """
    Maps a natural-language message to an existing slash command.

    Returns:
        str: the mapped command (e.g. "/fraud_summary 30") or "unknown"
    """

    prompt = textwrap.dedent(f"""
        You are a Slack bot's command generator for XYZ Bank's Transaction Dashboard.

        Given a user's plain English message, map it to the correct Slack slash command.
        Return ONLY the command and its arguments (if any) – NO extra text.

        Valid commands:
        - /dashboard
        - /overview_summary
        - /fraud_summary <days>
        - /daily_summary <YYYY-MM-DD>
        - /client_summary <client_id>

        Examples:
        • "Show me the overview" → /overview_summary
        • "Open the dashboard" → /dashboard
        • "Fraud for last 15 days" → /fraud_summary 15
        • "Daily summary for 2019-12-31" → /daily_summary 2019-12-31
        • "Tell me about client 12345" → /client_summary 12345

        User message:
        {user_message}

        Respond with ONE line containing the full command.
    """)


    if not API_KEY:
        logger.error("OPENROUTER_API_KEY not set.")
        return "unknown"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 50,
        "top_p": 0.9,
    }

    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()

        cmd = resp.json()["choices"][0]["message"]["content"]
        # Clean the response: remove backticks, quotes, punctuation, and normalize
        cmd = cmd.replace("`", "").strip()
        cmd = cmd.strip('"').strip("'")
        cmd = cmd.rstrip('.,!?')
        cmd = cmd.lower()

        if validate_command(cmd):
            logger.info(f"LLM mapped → {cmd}")
            return cmd
        else:
            logger.warning(f"Invalid command format from LLM: {cmd!r}")
            return "unknown"

    except requests.exceptions.RequestException as e:
        logger.error(f"LLM API error: {e}")
        return "unknown"
    except KeyError:
        logger.error("Unexpected response structure from LLM")
        return "unknown"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "unknown"


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def validate_command(command: str) -> bool:
    """Quick sanity-check for LLM output."""
    if not command or not command.startswith("/"):
        return False
    base = command.split()[0]
    return base in VALID_BASE_CMDS


def parse_command(command: str) -> tuple[str, list[str]]:
    """
    Splits a command string into (base_command, [args]).

    Returns:
        (base_command, args) or ("", []) if invalid.
    """
    if not validate_command(command):
        return "", []

    parts = command.strip().split()
    return parts[0], parts[1:]