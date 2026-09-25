from google import genai

import json

from pathlib import Path

import os 

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

GEMINI = os.getenv("GEMINI")
MODEL = os.getenv("MODEL")



client = genai.Client(api_key=GEMINI)

try:
    from .gemini_retry import call_gemini_with_retry
except ImportError:
    from gemini_retry import call_gemini_with_retry


def review_draft(
    lead: dict,
    draft: dict,
) -> dict | None:
    """
    Review an outreach draft against the original Lead Hunter research.

    Returns:
        {
            "approved": True/False,
            "issues": [...],
            "revision_instructions": "...",
            "reasoning": "..."
        }

    Nothing is modified or sent here.
    """

    prompt = f"""
You are the quality-control reviewer for AutomateLabs outreach emails.

Your job is NOT to rewrite the email.

Your job is to compare the generated outreach email against the
original Lead Hunter research and determine whether the email is
accurate, relevant and ready for human review.

==================================================
ORIGINAL LEAD RESEARCH
==================================================

Business:
{lead.get("business_name")}

Category:
{lead.get("category")}

Location:
{lead.get("location")}

Website:
{lead.get("website")}

Problems:
{lead.get("problems")}

Opportunities:
{lead.get("opportunities")}

Existing systems:
{lead.get("existing_systems")}

Target problem:
{lead.get("target_problem")}

Proposed solution:
{lead.get("proposed_solution")}

Evidence:
{lead.get("evidence")}

Pitch angle:
{lead.get("pitch_angle")}

Signals:
{lead.get("signals")}

Score:
{lead.get("score")}

Confidence:
{lead.get("confidence")}


==================================================
GENERATED EMAIL
==================================================

SUBJECT:
{draft.get("subject")}


ESTONIAN:
{draft.get("estonian")}


RUSSIAN:
{draft.get("russian")}


ENGLISH:
{draft.get("english")}


==================================================
REVIEW RULES
==================================================

Carefully compare the generated email against the original research.

The intended sales structure is product-first: when supported by the research,
the email should foreground relevant AutomateLabs products such as Website
Upgrade, AI Chatbot, Online Booking, or Routine Task Automation. A bespoke
company-specific automation idea is secondary. Do not reject a draft merely
because it mentions more than one relevant standard product, provided each is
supported as an opportunity and no absence is invented.


1. FACTUAL ACCURACY

Every factual statement about the business must be supported by
the supplied research.

Reject invented facts.

Reject invented:

- software
- APIs
- integrations
- CRM systems
- payment providers
- internal processes
- employee workflows
- statistics
- technical architecture
- implementation details

A proposed AutomateLabs solution does NOT need to already exist at
the business.

However, it must clearly be presented as a proposal or possibility,
not as something the business already uses.


2. DATABASE EVIDENCE

The original Lead Hunter research is the source of truth for this
review.

Check whether claims made in the email can reasonably be traced
back to:

- evidence
- problems
- opportunities
- existing systems
- target problem
- proposed solution
- pitch angle
- signals

Do not assume information that is absent from the research.

Reject an intro that merely summarizes the company instead of identifying a
product-relevant weakness when such a weakness exists in the research. Reject
unsupported causal leaps from neutral facts. For example, customer count or
number of languages does NOT prove repetitive queries, manual work, wasted time,
or lost customers. Prefer supported website weaknesses such as an outdated site,
weak mobile experience, no visible booking, or no visible chatbot.


3. UNCERTAINTY

The Lead Hunter research may contain hypotheses rather than
confirmed facts.

The email must not convert uncertain research into confirmed facts.

When appropriate, uncertainty should be expressed naturally with
language equivalent to:

"It looks like..."
"From the information available..."
"I wondered whether..."
"There may be an opportunity to..."

Do not require these exact phrases.


4. SALES ANGLE

The email should primarily focus on ONE automation opportunity.

The proposed idea must reasonably follow from the research.

Reject unrelated or unsupported services added merely to make the
offer sound broader.


5. PERSONALISATION

The email should clearly relate to this particular business.

It should use meaningful information from the research.

Reject generic outreach that could be sent unchanged to almost any
business.


6. LANGUAGE CONSISTENCY

Estonian is the PRIMARY version.

The Russian and English versions must communicate substantially
the same meaning as the Estonian version.

They do not need to be literal word-for-word translations.

Reject the draft if Russian or English introduces important:

- facts
- claims
- promises
- services
- technical details

that are absent from the Estonian version.


7. SUBJECT

The subject must be in Estonian.

It should be concise, natural and professional.

It must not contain:

- clickbait
- emojis
- excessive punctuation
- unsupported claims


8. TONE

The email should be:

- professional
- natural
- concise
- low-pressure
- relevant

It should not sound like generic mass marketing.

Do not reject a good draft simply because another wording might
sound slightly better.


9. UNSUPPORTED OUTCOME CLAIMS

Reject unsupported promises or measurable outcomes.

Examples include:

"guaranteed"
"error-free"
"instant"
"saves 50%"
"doubles conversions"

unless directly supported by the supplied research.


10. WEBSITE

Each language version must contain exactly the legitimate
AutomateLabs website:

https://automatelabs.me

Do not approve invented or unrelated URLs.


11. SIGNATURE

The generated draft must NOT contain an email signature.

The sending system will add the signature separately.


12. LENGTH

The email should remain reasonably concise for cold B2B outreach.

Do not reject the draft for a very small length difference if the
message remains focused and effective.

13. NATURAL LANGUAGE QUALITY

Each version must sound as though it was naturally written in that
language, not mechanically translated from another language.

Check grammar, word choice, sentence structure and business tone.

Reject the draft when wording is noticeably awkward, unnatural,
ambiguous or changes who is performing or benefiting from an action.

Pay particular attention to Estonian because it is the primary
outreach language.

Do not reject for tiny stylistic preferences. Reject only wording
that would make the email noticeably less professional or natural
to a native reader.


==================================================
DECISION
==================================================

Set "approved" to true ONLY if there are no meaningful problems
requiring Composer to revise the draft.

Do not reject a good email merely because you personally prefer
different wording.

Minor stylistic preferences are not sufficient reason for rejection.


IF APPROVED:

approved = true

issues must be an empty list.

revision_instructions must be an empty string.

reasoning should briefly explain:

- why the claims are supported by the research
- why the chosen automation angle makes sense
- why the email is suitable for human review


IF REJECTED:

approved = false

issues must contain a list of specific problems.

Each issue should identify exactly what is wrong.

revision_instructions must give Composer clear and actionable
instructions for fixing the problems.

Do not tell Composer simply to "improve the email".

Explain specifically what must change and why.

reasoning should briefly explain why the current version cannot
yet be approved.


IMPORTANT:

You are a REVIEWER.

Do NOT rewrite the email yourself.

Do NOT generate a replacement email.

Do NOT introduce new business information.

Return structured JSON data only.
"""

    response = call_gemini_with_retry(
        lambda: client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "OBJECT",
                    "properties": {
                        "approved": {"type": "BOOLEAN"},
                        "issues": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "revision_instructions": {"type": "STRING"},
                        "reasoning": {"type": "STRING"},
                    },
                    "required": [
                        "approved",
                        "issues",
                        "revision_instructions",
                        "reasoning",
                    ],
                },
            },
        ),
        label="Drafter",
    )

    if response is None or not response.text:
        return None

    data = json.loads(response.text)

    return {
        "approved": bool(data["approved"]),
        "issues": data["issues"],
        "revision_instructions": (
            data["revision_instructions"].strip()
        ),
        "reasoning": data["reasoning"].strip(),
    }


# ---------------------------------------------------------
# TEMPORARY TEST
# ---------------------------------------------------------

if __name__ == "__main__":
    from outreach.selector import get_next_lead
    from outreach.composer import compose_email

    print("Selecting next lead...")

    lead = get_next_lead()

    if lead is None:
        print("No eligible leads found.")
        raise SystemExit(0)

    print(f"Selected: {lead['business_name']}")
    print(f"Email: {lead['email']}")
    print(f"Score: {lead['score']}")
    print()

    print("Generating draft...")

    draft = compose_email(lead)

    if draft is None:
        print("Failed to generate draft.")
        raise SystemExit(1)

    print("Draft generated.")
    print()
    print("Reviewing draft...")

    review = review_draft(lead, draft)

    if review is None:
        print("Failed to review draft.")
        raise SystemExit(1)

    print()
    print("=" * 70)
    print("DRAFTER REVIEW")
    print("=" * 70)

    print(f"Approved: {review['approved']}")
    print()

    print("Issues:")

    if review["issues"]:
        for issue in review["issues"]:
            print(f"- {issue}")
    else:
        print("- None")

    print()
    print("Revision instructions:")
    print(review["revision_instructions"] or "None")

    print()
    print("Reasoning:")
    print(review["reasoning"])

    print("=" * 70)