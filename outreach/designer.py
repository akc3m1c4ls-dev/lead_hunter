from __future__ import annotations

import json
import os
from html import escape
from typing import Iterable

from google import genai


# ============================================================
# CONFIG
# ============================================================

SITE_URL = "https://automatelabs.me"

GEMINI_MODEL = os.getenv(
    "MODEL",
)

api_key = os.getenv("GEMINI")

DEFAULT_REPLY_EMAIL = "contact@automatelabs.me"


# ============================================================
# LOCALIZED TEMPLATE TEXT
# ============================================================

TEXT = {
    "et": {
        "greeting": "Tere,",
        "proposal": "Meie ettepanek",
        "other": "Mida veel saame teha",
        "view": "Vaata →",
        "visit": "Külasta AutomateLabs →",
        "reply": "Vasta",
        "tagline": "AI & BUSINESS AUTOMATION",
        "footer": "Vähem käsitööd. Rohkem aega olulisele.",
        "unsubscribe": "Loobu kirjadest",
    },

    "ru": {
        "greeting": "Здравствуйте,",
        "proposal": "Наше предложение",
        "other": "Что ещё мы можем сделать",
        "view": "Подробнее →",
        "visit": "Посетить AutomateLabs →",
        "reply": "Ответить",
        "tagline": "AI & BUSINESS AUTOMATION",
        "footer": "Меньше ручной работы. Больше времени на важное.",
        "unsubscribe": "Отписаться",
    },

    "en": {
        "greeting": "Hello,",
        "proposal": "Our proposal",
        "other": "What else we can do",
        "view": "View →",
        "visit": "Visit AutomateLabs →",
        "reply": "Reply",
        "tagline": "AI & BUSINESS AUTOMATION",
        "footer": "Less manual work. More time for what matters.",
        "unsubscribe": "Unsubscribe",
    },
}


# ============================================================
# STANDARD AUTOMATELABS PRODUCTS
# ============================================================

PRODUCTS = {
    "et": [
        (
            "Broneerimissüsteem",
            f"{SITE_URL}/EE/products/online-booking.html",
            "◫",
        ),
        (
            "AI vestlusbot",
            f"{SITE_URL}/EE/products/ai-chatbot.html",
            "✦",
        ),
        (
            "Ülesannete automatiseerimine",
            f"{SITE_URL}/EE/products/routine-task-automation.html",
            "⚙",
        ),
        (
            "Veebilehe uuendus",
            f"{SITE_URL}/EE/products/website-upgrade.html",
            "↗",
        ),
    ],

    "ru": [
        (
            "Онлайн-бронирование",
            f"{SITE_URL}/RU/products/online-booking.html",
            "◫",
        ),
        (
            "AI-чатбот",
            f"{SITE_URL}/RU/products/ai-chatbot.html",
            "✦",
        ),
        (
            "Автоматизация задач",
            f"{SITE_URL}/RU/products/routine-task-automation.html",
            "⚙",
        ),
        (
            "Обновление сайта",
            f"{SITE_URL}/RU/products/website-upgrade.html",
            "↗",
        ),
    ],

    "en": [
        (
            "Online Booking",
            f"{SITE_URL}/products/online-booking.html",
            "◫",
        ),
        (
            "AI Chatbot",
            f"{SITE_URL}/products/ai-chatbot.html",
            "✦",
        ),
        (
            "Task Automation",
            f"{SITE_URL}/products/routine-task-automation.html",
            "⚙",
        ),
        (
            "Website Upgrade",
            f"{SITE_URL}/products/website-upgrade.html",
            "↗",
        ),
    ],
}


# ============================================================
# HELPERS
# ============================================================

def safe(value: object) -> str:
    """Escape dynamic content before inserting it into HTML."""

    return escape(str(value), quote=True)


def normalize_language(language: str) -> str:
    language = (language or "en").lower().strip()

    if language not in TEXT:
        return "en"

    return language


# ============================================================
# GEMINI CONTENT EDITOR
# ============================================================

def design_draft_with_ai(
    *,
    company_name: str,
    raw_draft: str,
    preferred_language: str = "et",
) -> dict:
    """
    Gemini reads the full drafter output and selects/compresses the useful
    information for the visual AutomateLabs email.

    Gemini DOES NOT create HTML.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set."
        )

    client = genai.Client(api_key=api_key)

    preferred_language = normalize_language(preferred_language)

    prompt = f"""
You are the final content editor for AutomateLabs outreach emails.

Another AI has already researched the company and produced a raw outreach
draft.

Your task is NOT to redesign the email and NOT to write HTML.

Your task is to SELECT and COMPRESS the most useful information from the
draft for a short personalised AutomateLabs email.

COMPANY:
{company_name}

PREFERRED LANGUAGE:
{preferred_language}

RAW DRAFT:
------------------------------
{raw_draft}
------------------------------

The final email has only three personalised content areas:

1. intro
2. proposal_title
3. proposal_points

RULES:

- Keep the email short.
- Preserve genuinely useful company-specific observations.
- Do not invent facts.
- Do not invent problems the company has.
- Do not claim certainty where the draft only suggests an opportunity.
- Remove generic sales language.
- Remove repetition.
- Remove greetings and signatures from the draft.
- Remove descriptions of AutomateLabs itself.
- Do not include generic phrases such as:
  "unlock your potential",
  "transform your business",
  "increase efficiency",
  "take your business to the next level".

INTRO:

- Maximum 2 short sentences.
- Explain why this specific company is being contacted.
- Prefer a concrete observation from the draft.
- Keep it natural rather than aggressively promotional.

PROPOSAL TITLE:

- Maximum approximately 6 words.
- Describe the personalised AutomateLabs solution.
- It should describe something we could actually build or automate.

PROPOSAL POINTS:

- Return 2 to 4 points.
- Each point should be short.
- Each point should describe a concrete service or implementation.
- Prefer what AutomateLabs would DO rather than vague benefits.

Good examples:

"CRM-i ühendamine veebipäringutega"
"Automaatne kliendi järelteavitus"
"Komisjonide automaatne arvestus"
"Broneeringute ühendamine kalendriga"

Bad examples:

"Improve efficiency"
"Save time"
"Grow your business"
"Modernise operations"

IMPORTANT:

The HTML template separately displays these four standard AutomateLabs
products:

- Online Booking
- AI Chatbot
- Task Automation
- Website Upgrade

Do not waste the personalised proposal section merely listing those generic
products.

Instead, use the personalised proposal to describe what we could specifically
implement for THIS company.

LANGUAGE:

Use one of:

et
ru
en

Prefer {preferred_language}, unless the supplied draft clearly indicates
another supported language is more appropriate.

OUTPUT:

Return ONLY valid JSON in exactly this structure:

{{
    "language": "et",
    "intro": "...",
    "proposal_title": "...",
    "proposal_points": [
        "...",
        "...",
        "..."
    ]
}}

No markdown.
No explanation.
No text before or after the JSON.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty designer response."
        )

    try:
        content = json.loads(response.text)

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Gemini returned invalid JSON: {response.text}"
        ) from exc

    return validate_designed_content(
        content,
        preferred_language=preferred_language,
    )


# ============================================================
# VALIDATE GEMINI OUTPUT
# ============================================================

def validate_designed_content(
    content: dict,
    *,
    preferred_language: str,
) -> dict:

    if not isinstance(content, dict):
        raise ValueError("Designer response must be an object.")

    language = normalize_language(
        content.get("language", preferred_language)
    )

    intro = str(
        content.get("intro", "")
    ).strip()

    proposal_title = str(
        content.get("proposal_title", "")
    ).strip()

    points = content.get(
        "proposal_points",
        []
    )

    if not isinstance(points, list):
        raise ValueError(
            "proposal_points must be a list."
        )

    points = [
        str(point).strip()
        for point in points
        if str(point).strip()
    ]

    # Keep the visual template under control.
    points = points[:4]

    if not intro:
        raise ValueError(
            "Designer produced an empty intro."
        )

    if not proposal_title:
        raise ValueError(
            "Designer produced an empty proposal title."
        )

    if len(points) < 2:
        raise ValueError(
            "Designer must produce at least 2 proposal points."
        )

    if len(intro) > 500:
        raise ValueError(
            "Designer intro is unexpectedly long."
        )

    if len(proposal_title) > 120:
        raise ValueError(
            "Designer proposal title is unexpectedly long."
        )

    return {
        "language": language,
        "intro": intro,
        "proposal_title": proposal_title,
        "proposal_points": points,
    }


# ============================================================
# PROPOSAL POINT HTML
# ============================================================

def render_proposal_points(
    points: Iterable[str],
) -> str:

    rows = []

    for point in list(points)[:4]:

        rows.append(
            f"""
            <tr>
              <td style="
                  padding:6px 0;
                  font-family:Arial,Helvetica,sans-serif;
                  font-size:16px;
                  line-height:1.45;
                  color:#eaf7f3;
              ">

                <span style="
                    display:inline-block;
                    width:24px;
                    height:24px;
                    line-height:24px;
                    text-align:center;
                    border-radius:50%;
                    background:#a9eadc;
                    color:#062f2d;
                    font-weight:bold;
                    margin-right:10px;
                ">✓</span>

                {safe(point)}

              </td>
            </tr>
            """
        )

    return "".join(rows)


# ============================================================
# STANDARD PRODUCT CARDS
# ============================================================

def render_product_cards(
    language: str,
) -> str:

    language = normalize_language(language)

    products = PRODUCTS[language]
    labels = TEXT[language]

    cells = []

    for title, url, icon in products:

        cells.append(
            f"""
            <td width="25%"
                valign="top"
                style="padding:5px;">

              <table
                  role="presentation"
                  width="100%"
                  cellspacing="0"
                  cellpadding="0"
                  border="0"
                  style="
                    border:1px solid #23766f;
                    border-radius:16px;
                    background:#073b38;
                  ">

                <tr>
                  <td
                      align="center"
                      style="
                        padding:18px 8px 16px 8px;
                      ">

                    <div style="
                        font-family:Arial,Helvetica,sans-serif;
                        font-size:25px;
                        color:#a9eadc;
                        margin-bottom:10px;
                    ">
                      {safe(icon)}
                    </div>

                    <div style="
                        min-height:44px;
                        font-family:Arial,Helvetica,sans-serif;
                        font-size:14px;
                        line-height:1.3;
                        font-weight:700;
                        color:#ffffff;
                    ">
                      {safe(title)}
                    </div>

                    <div style="
                        margin-top:12px;
                    ">

                      <a
                          href="{safe(url)}"
                          style="
                            color:#a9eadc;
                            font-family:Arial,Helvetica,sans-serif;
                            font-size:14px;
                            font-weight:700;
                            text-decoration:underline;
                          ">
                        {safe(labels["view"])}
                      </a>

                    </div>

                  </td>
                </tr>

              </table>

            </td>
            """
        )

    return "".join(cells)


# ============================================================
# HTML EMAIL RENDERER
# ============================================================

def render_outreach_email(
    *,
    company_name: str,
    intro: str,
    proposal_title: str,
    proposal_points: Iterable[str],
    language: str = "et",
    reply_email: str = DEFAULT_REPLY_EMAIL,
    unsubscribe_url: str = "#",
) -> str:

    language = normalize_language(language)

    t = TEXT[language]

    company = safe(company_name)
    intro_html = safe(intro)
    proposal_title_html = safe(proposal_title)

    reply_email_html = safe(reply_email)
    unsubscribe_html = safe(unsubscribe_url)

    points_html = render_proposal_points(
        proposal_points
    )

    products_html = render_product_cards(
        language
    )

    return f"""<!doctype html>

<html lang="{language}">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1">

<title>AutomateLabs</title>

</head>


<body style="
    margin:0;
    padding:0;
    background:#031f1e;
    color:#ffffff;
">


<table
    role="presentation"
    width="100%"
    cellspacing="0"
    cellpadding="0"
    border="0"
    style="
      background:#031f1e;
    ">

<tr>

<td
    align="center"
    style="
      padding:28px 12px;
    ">


<table
    role="presentation"
    width="100%"
    cellspacing="0"
    cellpadding="0"
    border="0"
    style="
      max-width:680px;
      background:#052d2b;
      border:1px solid #17635e;
      border-radius:24px;
      overflow:hidden;
    ">


<!-- ======================================================
     HEADER
======================================================= -->

<tr>

<td style="
    padding:30px 34px;
    border-bottom:1px solid #17635e;
    background:#073734;
">

<div style="
    font-family:Georgia,'Times New Roman',serif;
    font-size:38px;
    line-height:1;
    font-weight:700;
    color:#ffffff;
">
AutomateLabs
</div>

<div style="
    margin-top:9px;
    font-family:Arial,Helvetica,sans-serif;
    font-size:11px;
    letter-spacing:3px;
    color:#a9eadc;
">
{safe(t["tagline"])}
</div>

</td>

</tr>


<!-- ======================================================
     INTRO
======================================================= -->

<tr>

<td style="
    padding:34px 34px 20px 34px;
">

<div style="
    font-family:Georgia,'Times New Roman',serif;
    font-size:38px;
    font-weight:700;
    color:#ffffff;
">
{safe(t["greeting"])}
</div>


<div style="
    margin-top:14px;
    max-width:560px;
    font-family:Arial,Helvetica,sans-serif;
    font-size:18px;
    line-height:1.55;
    color:#d5e4e1;
">
{intro_html}
</div>

</td>

</tr>


<!-- ======================================================
     PERSONALISED PROPOSAL
======================================================= -->

<tr>

<td style="
    padding:10px 20px 28px 20px;
">

<table
    role="presentation"
    width="100%"
    cellspacing="0"
    cellpadding="0"
    border="0"
    style="
      background:#063b38;
      border:1px solid #8ddfd1;
      border-radius:20px;
    ">

<tr>

<td style="
    padding:26px;
">


<div style="
    font-family:Georgia,'Times New Roman',serif;
    font-size:28px;
    line-height:1.2;
    font-weight:700;
    color:#ffffff;
">

✦ {safe(t["proposal"])}: {company}

</div>


<div style="
    margin-top:8px;
    margin-bottom:14px;
    font-family:Arial,Helvetica,sans-serif;
    font-size:19px;
    line-height:1.4;
    color:#a9eadc;
">

{proposal_title_html}

</div>


<table
    role="presentation"
    cellspacing="0"
    cellpadding="0"
    border="0">

{points_html}

</table>


</td>

</tr>

</table>

</td>

</tr>


<!-- ======================================================
     OTHER AUTOMATELABS SERVICES
======================================================= -->

<tr>

<td style="
    padding:0 20px 22px 20px;
">

<div style="
    padding:0 8px 12px 8px;
    font-family:Georgia,'Times New Roman',serif;
    font-size:27px;
    font-weight:700;
    color:#ffffff;
">

{safe(t["other"])}

</div>


<table
    role="presentation"
    width="100%"
    cellspacing="0"
    cellpadding="0"
    border="0">

<tr>

{products_html}

</tr>

</table>


</td>

</tr>


<!-- ======================================================
     CALL TO ACTION
======================================================= -->

<tr>

<td style="
    padding:10px 25px 34px 25px;
">

<table
    role="presentation"
    width="100%"
    cellspacing="0"
    cellpadding="0"
    border="0">

<tr>


<td
    width="50%"
    style="
      padding:5px;
    ">

<a
    href="{SITE_URL}"
    style="
      display:block;
      padding:18px 10px;
      border-radius:14px;
      background:#a9eadc;
      color:#052d2b;
      font-family:Arial,Helvetica,sans-serif;
      font-size:16px;
      font-weight:800;
      text-align:center;
      text-decoration:none;
    ">

{safe(t["visit"])}

</a>

</td>


<td
    width="50%"
    style="
      padding:5px;
    ">

<a
    href="mailto:{reply_email_html}"
    style="
      display:block;
      padding:17px 10px;
      border:1px solid #a9eadc;
      border-radius:14px;
      color:#ffffff;
      font-family:Arial,Helvetica,sans-serif;
      font-size:16px;
      font-weight:800;
      text-align:center;
      text-decoration:none;
    ">

{safe(t["reply"])}

</a>

</td>


</tr>

</table>

</td>

</tr>


<!-- ======================================================
     FOOTER
======================================================= -->

<tr>

<td style="
    padding:25px 34px 30px 34px;
    border-top:1px solid #17635e;
    background:#042725;
">

<div style="
    font-family:Georgia,'Times New Roman',serif;
    font-size:24px;
    font-weight:700;
    color:#ffffff;
">

AutomateLabs

</div>


<div style="
    margin-top:5px;
    font-family:Arial,Helvetica,sans-serif;
    font-size:12px;
    color:#a9eadc;
">

{safe(t["footer"])}

</div>


<div style="
    margin-top:18px;
    font-family:Arial,Helvetica,sans-serif;
    font-size:12px;
    line-height:1.7;
    color:#88aaa5;
">

<a
    href="{SITE_URL}"
    style="
      color:#a9eadc;
      text-decoration:none;
    ">
automatelabs.me
</a>

&nbsp; • &nbsp;

Tallinn, Estonia

<br>


<a
    href="{unsubscribe_html}"
    style="
      color:#88aaa5;
      text-decoration:underline;
    ">

{safe(t["unsubscribe"])}

</a>


</div>

</td>

</tr>


</table>


</td>

</tr>

</table>


</body>

</html>
"""


# ============================================================
# FULL PIPELINE:
#
# RAW DRAFT
#     ↓
# GEMINI EDITOR
#     ↓
# HTML DESIGNER
# ============================================================

def render_draft_with_ai(
    *,
    company_name: str,
    raw_draft: str,
    preferred_language: str = "et",
    reply_email: str = DEFAULT_REPLY_EMAIL,
    unsubscribe_url: str = "#",
) -> tuple[str, dict]:

    designed = design_draft_with_ai(
        company_name=company_name,
        raw_draft=raw_draft,
        preferred_language=preferred_language,
    )

    html = render_outreach_email(
        company_name=company_name,
        intro=designed["intro"],
        proposal_title=designed["proposal_title"],
        proposal_points=designed["proposal_points"],
        language=designed["language"],
        reply_email=reply_email,
        unsubscribe_url=unsubscribe_url,
    )

    return html, designed


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    demo_draft = """
TIPPMAAKLER operates the Tippvihje Klubi referral network.

The available information suggests that managing multiple partner levels,
commissions and referrals may involve repetitive administrative work.

One possible AutomateLabs solution would be to connect incoming referrals
with the company's CRM, automate commission calculations and streamline
partner payout preparation.

We could also provide various other automation services and help modernise
business workflows.
"""

    print("Sending demo draft to Gemini...")

    html, designed = render_draft_with_ai(
        company_name="TIPPMAAKLER",
        raw_draft=demo_draft,
        preferred_language="et",
        unsubscribe_url="#unsubscribe",
    )

    print("\nGemini selected:")
    print(
        json.dumps(
            designed,
            ensure_ascii=False,
            indent=2,
        )
    )

    with open(
        "email-preview.html",
        "w",
        encoding="utf-8",
    ) as file:

        file.write(html)

    print("\nCreated email-preview.html")