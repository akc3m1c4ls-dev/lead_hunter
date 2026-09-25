import os
from pathlib import Path

from dotenv import load_dotenv
from brevo import Brevo
from brevo.transactional_emails import (
    SendTransacEmailRequestSender,
    SendTransacEmailRequestToItem,
)


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

BREVO_API_KEY = os.getenv("BREVO")
SENDER_EMAIL = os.getenv(
    "BREVO_EMAIL",
    "contact@automatelabs.me",
)
SENDER_NAME = os.getenv(
    "BREVO_NAME",
    "AutomateLabs",
)

# SAFETY:
# During testing EVERY email goes here.
TEST_EMAIL = "ak.c3m1c4ls@gmail.com"

TEST_MODE = False
TEST_LIMIT = 10

# Hard safety brake for real recipients. Increase deliberately only after
# reviewing the previous live batch.
LIVE_LIMIT = 5


# ============================================================
# BREVO CLIENT
# ============================================================

if not BREVO_API_KEY:
    raise RuntimeError(
        "BREVO_API_KEY is missing from .env"
    )

client = Brevo(
    api_key=BREVO_API_KEY,
    timeout=30.0,
)


# ============================================================
# SEND ONE EMAIL
# ============================================================

def send_email(
    *,
    html: str,
    subject: str,
    recipient_email: str,
    recipient_name: str = "",
):
    """
    Send one HTML email through Brevo.

    TEST_MODE prevents emails from being sent to real leads.
    """

    if TEST_MODE:
        actual_recipient = TEST_EMAIL
    else:
        actual_recipient = recipient_email

    print()
    print("=" * 70)
    print("BREVO SEND")
    print("=" * 70)

    print(f"Intended recipient : {recipient_email}")
    print(f"Actual recipient   : {actual_recipient}")
    print(f"Subject            : {subject}")
    print(f"Test mode          : {TEST_MODE}")

    result = client.transactional_emails.send_transac_email(
        subject=subject,
        html_content=html,

        sender=SendTransacEmailRequestSender(
            name=SENDER_NAME,
            email=SENDER_EMAIL,
        ),

        to=[
            SendTransacEmailRequestToItem(
                email=actual_recipient,
                name=recipient_name or "AutomateLabs Test",
            )
        ],

        request_options={
            "timeout_in_seconds": 30,
            "max_retries": 1,
        },
    )

    print(f"Brevo message ID   : {result.message_id}")
    print("=" * 70)

    return result.message_id


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    preview_file = Path(__file__).parent / "email-preview.html"

    if not preview_file.exists():
        raise FileNotFoundError(
            f"Preview not found: {preview_file}\n"
            "Run designer.py first."
        )

    html = preview_file.read_text(
        encoding="utf-8"
    )

    message_id = send_email(
        html=html,
        subject="[TEST] AutomateLabs outreach",
        recipient_email="REAL-LEAD-WOULD-GO-HERE@example.com",
        recipient_name="Test",
    )

    print()
    print("Test email submitted successfully.")
    print("Message ID:", message_id)