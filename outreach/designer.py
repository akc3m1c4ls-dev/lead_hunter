import json
import os
from pathlib import Path
from html import escape
from typing import Iterable

from dotenv import load_dotenv
from google import genai

try:
    from .gemini_retry import call_gemini_with_retry
except ImportError:
    from gemini_retry import call_gemini_with_retry


# lead_hunter/outreach/designer.py
# parent       = outreach/
# parent.parent = lead_hunter/

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

# ============================================================
# CONFIG
# ============================================================

SITE_URL = "https://automatelabs.me"

MODEL = os.getenv(
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
        "reply": "Kas soovite midagi küsida?",
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
        "reply": "Задать вопрос",
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
        "reply": "Ask a Question",
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
            "AI-Chatbot",
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


PRODUCT_KEYS = (
    "online_booking",
    "ai_chatbot",
    "task_automation",
    "website_upgrade",
)


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

The final email has four content areas:

1. intro
2. recommended_products
3. other_title
4. other_points

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
- Make the intro problem-first. State the concrete missing capability or friction
  that makes the recommended product relevant, then briefly state its practical
  consequence. The product cards immediately below are the fix.
- Prefer a concrete customer-facing weakness from the draft, especially an old
  or outdated website, weak mobile experience, missing visible booking, missing
  visible chatbot, or another documented website friction.
- Do NOT use company background facts (customer count, languages, company size,
  years in business, service volume, etc.) as the intro unless the research
  explicitly identifies that fact itself as a problem.
- Never infer "manual work", "repetitive queries", "lost customers", "wasted
  time", or similar consequences from neutral business facts.
- When absence is confirmed by the supplied draft/research, direct wording is fine
  (for example: "We noticed you don't have a visible AI chatbot").
- When absence is not confirmed, use cautious wording such as "we couldn't find a
  visible AI chatbot" or "we didn't see an online booking option".
- Do not invent a deficiency merely to justify a product.
- Do not waste the intro on generic company growth, praise, background, customer
  counts, languages, or a description of what the company does. The recipient
  already knows their own business. Tell them what relevant weakness we noticed.
- Keep it natural rather than aggressively promotional.

RECOMMENDED PRODUCTS:

Choose 1 to 3 concrete AutomateLabs products that appear most relevant from the evidence in the draft.
Use ONLY these exact keys:
- online_booking
- ai_chatbot
- task_automation
- website_upgrade

The main "Our proposal" section is for these product recommendations.
Prioritise obvious practical gaps such as an old/outdated website, no visible AI chatbot, no visible online booking, or repetitive tasks.
Do NOT claim a product/feature is missing unless the supplied research supports that. If uncertain, frame the intro as an opportunity rather than a fact.

OTHER TITLE:

- Maximum approximately 6 words.
- Describe the personalised, company-specific automation idea found in the research.
- This appears later under "What else we can do".

OTHER POINTS:

- Return exactly 3 points.
- Keep every point very short.
- Prefer 3-7 words per point.
- Use simple everyday business language.
- Describe the result, not the technical implementation.
- Do not write full explanatory sentences when a short phrase works.
- Avoid phrases such as:
  "it is possible to"
  "can be used to"
  "can be connected"
  "we could implement"
  "on võimalik"
  "saab kasutada"
  "можно использовать"
  "можно реализовать"

Prefer:
"Uued soovitused otse CRM-i"
instead of:
"Saabuvaid soovitusi saab ühendada otse ettevõtte CRM-süsteemiga."

Prefer:
"Komisjonide automaatne arvutamine"
instead of:
"Komisjonitasude arvutust on võimalik täielikult automatiseerida."

Prefer:
"Lihtsam väljamaksete ettevalmistus"
instead of:
"Väljamaksete ettevalmistamist saab muuta kiiremaks ja lihtsamaks."

IMPORTANT:

The HTML template will use recommended_products as the MAIN "Our proposal" section.
The personalised company-specific automation idea belongs in the SECONDARY
"What else we can do" section. Keep that bespoke idea useful but secondary.
Never put the company name in the "Our proposal" heading.

WRITING STYLE:

Write for a normal business owner, not a technical expert.

Use simple, natural language.
Keep sentences short.
Avoid corporate, bureaucratic and technical wording.
Do not make simple ideas sound complicated.
Prefer concrete words over abstract business terminology.

The reader should understand the idea immediately while quickly scanning
the email.

First create the Estonian version.
Then translate its meaning naturally into English and Russian.
Do not translate word-for-word.
The three versions must communicate the same idea and approximately the
same level of simplicity.

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
    "et": {{
        "intro": "...",
        "recommended_products": ["website_upgrade", "ai_chatbot"],
        "other_title": "...",
        "other_points": [
            "...",
            "...",
            "..."
        ]
    }},
    "en": {{
        "intro": "...",
        "recommended_products": ["website_upgrade", "ai_chatbot"],
        "other_title": "...",
        "other_points": [
            "...",
            "...",
            "..."
        ]
    }},
    "ru": {{
        "intro": "...",
        "recommended_products": ["website_upgrade", "ai_chatbot"],
        "other_title": "...",
        "other_points": [
            "...",
            "...",
            "..."
        ]
    }}
}}

The three versions must communicate the same meaning.

Write the Estonian version first.
Translate it naturally into English and Russian.

Use simple, everyday language.
Avoid bureaucratic, corporate and unnecessarily technical wording.
Keep other points short and easy to understand.

No markdown.
No explanation.
No text before or after the JSON.

No markdown.
No explanation.
No text before or after the JSON.
"""

    response = call_gemini_with_retry(
        lambda: client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            },
        ),
        label="Designer",
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
        content
    )


# ============================================================
# VALIDATE GEMINI OUTPUT
# ============================================================

def validate_designed_content(content: dict) -> dict:

    if not isinstance(content, dict):
        raise ValueError("Designer response must be an object.")

    result = {}

    for language in ("et", "en", "ru"):
        section = content.get(language)
        if not isinstance(section, dict):
            raise ValueError(f"Designer response is missing language: {language}")

        intro = str(section.get("intro", "")).strip()
        recommended = section.get("recommended_products", [])
        other_title = str(section.get("other_title", "")).strip()
        points = section.get("other_points", [])

        if not isinstance(recommended, list):
            raise ValueError(f"{language}.recommended_products must be a list.")
        recommended = [str(x).strip() for x in recommended if str(x).strip()]
        recommended = list(dict.fromkeys(recommended))[:3]
        invalid = [x for x in recommended if x not in PRODUCT_KEYS]
        if invalid:
            raise ValueError(f"{language}: invalid product keys: {invalid}")
        if not recommended:
            raise ValueError(f"{language}: at least one recommended product required.")

        if not isinstance(points, list):
            raise ValueError(f"{language}.other_points must be a list.")
        points = [str(point).strip() for point in points if str(point).strip()][:4]

        if not intro:
            raise ValueError(f"{language}: empty intro.")
        if not other_title:
            raise ValueError(f"{language}: empty other title.")
        if len(points) < 2:
            raise ValueError(f"{language}: at least 2 other points required.")

        result[language] = {
            "intro": intro,
            "recommended_products": recommended,
            "other_title": other_title,
            "other_points": points,
        }

    return result


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
                  font-family:Verdana,Geneva,sans-serif;
                  font-size:22px;
                  line-height:1.45;
                  color:#eaf7f3;
              ">

                <span style="
                    display:inline-block;
                    width:24px;
                    height:24px;
                    line-height:22px;
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
    product_keys: Iterable[str] | None = None,
) -> str:
    """Render all four standard products and highlight business matches."""

    language = normalize_language(language)
    products = PRODUCTS[language]
    labels = TEXT[language]
    recommended = set(product_keys or [])

    badge_labels = {
        "et": "✓ Soovitame",
        "ru": "✓ Рекомендуем",
        "en": "✓ Recommended",
    }

    rows = []

    for key, (title, url, icon) in zip(PRODUCT_KEYS, products):
        is_recommended = key in recommended
        background = "#0b4b46" if is_recommended else "#073b38"
        border = "#a9eadc" if is_recommended else "#23766f"
        border_width = "2px" if is_recommended else "1px"
        badge = ""
        if is_recommended:
            badge = (
                '<div style="margin-bottom:5px;font-family:Verdana,Geneva,sans-serif;'
                'font-size:11px;line-height:1.2;font-weight:800;letter-spacing:.3px;'
                'color:#a9eadc;text-transform:uppercase;">'
                + safe(badge_labels[language])
                + '</div>'
            )

        rows.append(
            f"""
            <tr>
              <td style="padding:5px 0;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                    class="product-card" style="width:100%;background:{background};border:{border_width} solid {border};border-radius:16px;">
                  <tr>
                    <td class="product-icon" width="52" align="center" valign="middle"
                        style="width:52px;padding:18px 0 18px 10px;font-family:Verdana,Geneva,sans-serif;font-size:25px;line-height:1;text-align:center;color:#a9eadc;">
                      {safe(icon)}
                    </td>
                    <td class="product-title" valign="middle"
                        style="padding:18px 8px 18px 12px;font-family:Verdana,Geneva,sans-serif;font-size:16px;line-height:1.3;font-weight:700;text-align:left;color:#ffffff;word-break:normal;overflow-wrap:normal;">
                      {badge}
                      {safe(title)}
                    </td>
                    <td class="product-link" width="78" align="right" valign="middle"
                        style="width:78px;padding:18px 12px 18px 4px;text-align:right;">
                      <a href="{safe(url)}"
                          style="color:#a9eadc;font-family:Verdana,Geneva,sans-serif;font-size:14px;font-weight:700;text-decoration:none;white-space:nowrap;">
                        {safe(labels["view"])}
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            """
        )

    return "".join(rows)

# ============================================================
# LANGUAGE SECTION RENDERER
# ============================================================

def render_language_section(
    *,
    company_name: str,
    content: dict,
    language: str,
) -> str:
    """
    Render one complete language section:
    intro -> recommended AutomateLabs products -> personalised extra opportunity.
    """

    language = normalize_language(language)
    t = TEXT[language]

    intro_html = safe(content["intro"])
    other_title_html = safe(content["other_title"])

    points_html = render_proposal_points(
        content["other_points"]
    )

    products_html = render_product_cards(
        language, content["recommended_products"]
    )



    language_labels = {
        "et": "🇪🇪 EESTI",
        "en": "🇬🇧 ENGLISH",
        "ru": "🇷🇺 РУССКИЙ",
    }

    return f"""
    <!-- ======================================================
         LANGUAGE: {language.upper()}
    ======================================================= -->

    <tr>
      <td style="
          padding:30px 34px 10px 34px;
          border-top:1px solid #17635e;
          font-family:Verdana,Geneva,sans-serif;
          font-size:13px;
          font-weight:700;
          letter-spacing:2px;
          color:#a9eadc;
      ">
        {language_labels[language]}
      </td>
    </tr>

    <!-- INTRO -->

    <tr>
      <td style="
          padding:10px 34px 20px 34px;
      ">

        <div style="
            font-family:Verdana,Geneva,sans-serif;
            font-size:38px;
            font-weight:700;
            color:#ffffff;
        ">
          {safe(t["greeting"])}
        </div>

        <div style="
            margin-top:14px;
            max-width:560px;
            font-family:Verdana,Geneva,sans-serif;
            font-size:18px;
            line-height:1.55;
            color:#d5e4e1;
        ">
          {intro_html}
        </div>

      </td>
    </tr>

    <!-- PERSONALISED PROPOSAL -->

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
            <td style="padding:26px;">

              <div style="
                  font-family:Verdana,Geneva,sans-serif;
                  font-size:28px;
                  line-height:1.2;
                  font-weight:700;
                  color:#ffffff;
              ">
                ✦ {safe(t["proposal"])}
              </div>

              <table
                  role="presentation"
                  width="100%"
                  cellspacing="0"
                  cellpadding="0"
                  border="0"
                  style="margin-top:14px;">
                {products_html}
              </table>

            </td>
          </tr>

        </table>

      </td>
    </tr>

    <!-- OTHER AUTOMATELABS SERVICES -->

    <tr>
      <td style="
          padding:0 20px 30px 20px;
      ">

        <table
            role="presentation"
            width="100%"
            cellspacing="0"
            cellpadding="0"
            border="0"
            style="background:#063b38;border:1px solid #8ddfd1;border-radius:20px;">
          <tr>
            <td style="padding:26px;">
              <div style="font-family:Verdana,Geneva,sans-serif;font-size:27px;line-height:1.2;font-weight:700;color:#ffffff;">
                ✦ {safe(t["other"])}
              </div>
              <div style="margin-top:16px;font-family:Verdana,Geneva,sans-serif;font-size:20px;line-height:1.4;color:#a9eadc;">
                {other_title_html}
              </div>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-top:8px;">
                {points_html}
              </table>
            </td>
          </tr>
        </table>
        <!-- LANGUAGE CTA -->

        <tr>
          <td style="
              padding:5px 25px 35px 25px;
          ">

            <table
                role="presentation"
                width="100%"
                cellspacing="0"
                cellpadding="0"
                border="0">

              <tr>

                <!-- VISIT -->

                <td
                    width="50%"
                    style="padding:5px;">

                  <a
                      href="{SITE_URL}"
                      style="
                        display:block;
                        padding:18px 10px;
                        border-radius:14px;
                        background:#a9eadc;
                        color:#052d2b;
                        font-family:Verdana,Geneva,sans-serif;
                        font-size:16px;
                        font-weight:800;
                        text-align:center;
                        text-decoration:none;
                      ">
                    {safe(t["visit"])}
                  </a>

                </td>

                <!-- REPLY -->

                <td
                    width="50%"
                    style="padding:5px;">

                  <a
                      href="mailto:{safe(DEFAULT_REPLY_EMAIL)}"
                      style="
                        display:block;
                        padding:17px 10px;
                        border:1px solid #a9eadc;
                        border-radius:14px;
                        color:#ffffff;
                        font-family:Verdana,Geneva,sans-serif;
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

      </td>
    </tr>
    """


# ============================================================
# HTML EMAIL RENDERER
# ============================================================

def render_outreach_email(
    *,
    company_name: str,
    designed: dict,
    reply_email: str = DEFAULT_REPLY_EMAIL,
    unsubscribe_url: str = "#",
) -> str:
    """
    Render one multilingual email in this order:

    Header
    -> Estonian intro/proposal/services
    -> English intro/proposal/services
    -> Russian intro/proposal/services
    -> shared CTA
    -> shared footer
    """

    reply_email_html = safe(reply_email)
    unsubscribe_html = safe(unsubscribe_url)

    language_sections = "".join(
        render_language_section(
            company_name=company_name,
            content=designed[language],
            language=language,
        )
        for language in ("et", "en", "ru")
    )

    return f"""<!doctype html>

<html lang="et">

<head>
  <meta charset="utf-8">

  <meta
      name="viewport"
      content="width=device-width,initial-scale=1">

  <title>AutomateLabs</title>
  <style>
    /* Gmail and other modern mobile mail clients */
    @media only screen and (max-width: 600px) {{
      .product-card {{ width:100% !important; table-layout:auto !important; }}
      .product-icon {{ width:36px !important; padding:16px 0 16px 6px !important; text-align:center !important; }}
      .product-title {{ width:auto !important; padding:16px 6px 16px 6px !important; font-size:15px !important; line-height:1.28 !important; text-align:left !important; word-break:normal !important; overflow-wrap:normal !important; }}
      .product-title div {{ text-align:left !important; }}
      .product-link {{ width:62px !important; padding:16px 8px 16px 2px !important; }}
      .product-link a {{ font-size:13px !important; }}
    }}
  </style>
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
    font-family:Verdana,Geneva,sans-serif;
    font-size:38px;
    line-height:1;
    font-weight:700;
    color:#ffffff;
">
  AutomateLabs
</div>

<div style="
    margin-top:9px;
    font-family:Verdana,Geneva,sans-serif;
    font-size:11px;
    letter-spacing:3px;
    color:#a9eadc;
">
  AI &amp; BUSINESS AUTOMATION
</div>

</td>

</tr>

<!-- ======================================================
     EE -> EN -> RU
======================================================= -->

{language_sections}



<!-- ======================================================
     SHARED FOOTER
======================================================= -->

<tr>

<td style="
    padding:25px 34px 30px 34px;
    border-top:1px solid #17635e;
    background:#042725;
">

<div style="
    font-family:Verdana,Geneva,sans-serif;
    font-size:24px;
    font-weight:700;
    color:#ffffff;
">
  AutomateLabs
</div>

<div style="
    margin-top:5px;
    font-family:Verdana,Geneva,sans-serif;
    font-size:12px;
    color:#a9eadc;
">
  Less manual work. More time for what matters.
</div>

<div style="
    margin-top:18px;
    font-family:Verdana,Geneva,sans-serif;
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
  Unsubscribe
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
        designed=designed,
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