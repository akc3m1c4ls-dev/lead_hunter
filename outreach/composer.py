from google import genai
from pathlib import Path

import json

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


def _generate_email(prompt: str) -> dict | None:
    response = call_gemini_with_retry(
        lambda: client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "OBJECT",
                    "properties": {
                        "subject": {"type": "STRING"},
                        "estonian": {"type": "STRING"},
                        "russian": {"type": "STRING"},
                        "english": {"type": "STRING"},
                    },
                    "required": ["subject", "estonian", "russian", "english"],
                },
            },
        ),
        label="Composer",
    )

    if response is None or not response.text:
        return None

    data = json.loads(response.text)
    return {
        "subject": data["subject"].strip(),
        "estonian": data["estonian"].strip(),
        "russian": data["russian"].strip(),
        "english": data["english"].strip(),
    }

def compose_email(lead: dict) -> dict | None:
    """
    Generate one personalised cold outreach email using
    Lead Hunter's stored analysis.

    Returns:
        {
            "subject": "...",
            "body": "..."
        }

    Nothing is sent here.
    """

    prompt = f"""
You write concise, professional B2B outreach emails for AutomateLabs,
a software automation company.

Your task is to write ONE personalised outreach email to the business
below.

The business has already been researched and analysed.
Use ONLY the supplied information.

BUSINESS

Name: {lead.get("business_name")}
Category: {lead.get("category")}
Location: {lead.get("location")}
Website: {lead.get("website")}

LEAD HUNTER ANALYSIS

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


EMAIL OBJECTIVE

Start a genuine conversation around the most relevant concrete AutomateLabs
product opportunities visible in the research. Prioritise practical gaps such
as Website Upgrade, AI Chatbot, Online Booking, or Routine Task Automation
when the supplied evidence supports them.

A more bespoke company-specific automation opportunity may be mentioned as
a secondary idea. Do not try to sell every service.


WRITING RULES

1. PERSONALISATION

The email must clearly be written for this specific business.

Use the supplied evidence, target problem and pitch angle.

Do not invent facts.

Do not claim you personally observed something unless it is supported
by the supplied information.


2. FOCUS

Prioritise 1-3 relevant AutomateLabs products supported by the research:
Website Upgrade, AI Chatbot, Online Booking, or Routine Task Automation.

If the research contains a more bespoke automation idea, keep it secondary.
Do not claim a website is old, or that chatbot/booking is absent, unless the
supplied research supports that observation. If evidence is uncertain, phrase
it as an opportunity rather than a confirmed deficiency.


3. TONE

Professional, natural and concise.

Sound like a person who researched the business.

Do not sound like mass marketing.

Avoid exaggerated sales language.


4. LENGTH AND READABILITY

Keep EACH language version short.

Target approximately 55-90 words per language.

Prefer 3-4 short paragraphs rather than one large paragraph.

Use whitespace between paragraphs so the email is visually easy to scan.

A good structure is:

Paragraph 1:
Open with a concrete weakness or missing capability visible in the research.
Prefer customer-facing website findings: an old/outdated website, weak mobile
experience, no visible online booking, no visible chatbot, or another clearly
documented friction. Say it politely and plainly: "We noticed that your website
looks dated..." or, when absence is uncertain, "We couldn't find an online
booking option...". Do NOT open by summarising what the company does, its size,
customer count, languages, growth, or other background facts. Those facts are
not problems by themselves.

Paragraph 2:
State only a consequence that directly follows from the observed weakness. Never
invent manual work, repetitive queries, lost customers, wasted time, or another
problem merely because it sounds plausible. Keep the standard product as the
obvious fix and bespoke automation secondary.

Paragraph 3:
A short practical benefit and low-pressure invitation to talk.

Final line:
A natural invitation to visit https://automatelabs.me

Do not add text merely to make the email longer.

Every sentence should have a purpose.


5. OPENING

Avoid generic openings such as:

"I hope this email finds you well."

Do not begin with a long introduction about AutomateLabs.


6. VALUE

Briefly explain:

- the concrete problem or missing capability we observed
- the practical consequence
- which standard AutomateLabs product directly fixes it
- the practical benefit

The opening should follow: OBSERVED WEAKNESS -> DIRECT CONSEQUENCE.
The product proposal below the intro provides the FIX.

IMPORTANT: A business fact is not automatically a weakness. For example,
"serves 500 people" or "works in 17 languages" must never be turned into
"high volume of repetitive queries/manual work" unless the research explicitly
supports that conclusion. Prefer a concrete website/product gap instead.

7.SIMPLICITY

Write for a business owner, manager or employee who may not be technical.

Prefer plain business language.

Avoid unnecessary technical terminology such as:

- API
- architecture
- webhook
- endpoint
- database synchronization
- integration layer
- data pipeline
- technical infrastructure

unless the term is genuinely necessary to understand the proposal.

Even when technical systems are mentioned in the research, explain the
business outcome rather than the implementation.

For example, prefer:

"automate the handling of partner commissions"

instead of:

"integrate the CRM API with the payment processing infrastructure".

Prefer:

"connect your existing systems"

instead of describing technical architecture.

The purpose of the first email is to start a conversation, not explain
how the solution will be engineered.

Do not explain the implementation unless it is essential to the pitch.

For first contact, prefer describing WHAT could be improved rather
than HOW the system would technically work.

Prefer:

"We could help automate partner commission handling and reduce the
manual work involved."

over:

"We could connect your online forms with your CRM to distribute
commissions based on deal stages."

Technical implementation can be discussed after the business replies.

8. UNCERTAINTY

The Lead Hunter analysis may contain hypotheses.

Never present uncertain information as confirmed fact.

When appropriate use language such as:

"It looks like..."
"From the information available..."
"I wondered whether..."
"There may be an opportunity to..."


9. CALL TO ACTION

End with a low-pressure invitation to discuss the idea.

Do not manufacture urgency.


10. SIGNATURE

Do NOT include an email signature.
The sending system will add it separately.


11. SUBJECT

Write a short, natural subject line.

Avoid spam-like subjects, excessive punctuation, emojis,
ALL CAPS, or clickbait.

12. LANGUAGE AND STRUCTURE

Generate the same outreach message in THREE languages.

The JSON response contains three separate fields:

"estonian" = Estonian version
"russian" = Russian version
"english" = English version

IMPORTANT:

Estonian is the PRIMARY version.

First write the complete Estonian email.

Then create the Russian version based on the Estonian version.

Finally create the English version based on the Estonian version.

All three versions must communicate the same message.

Do not introduce new facts, claims, services, technical details,
or promises in the Russian or English versions.

Write naturally in each language rather than translating
word-for-word.

Do NOT include language headings such as EESTI, РУССКИЙ or ENGLISH
inside the generated fields. The application adds those headings.

13.WEBSITE

At the end of EACH language version include a short natural
invitation to learn more about AutomateLabs at:

https://automatelabs.me

Do not invent any other URLs.

14.PARAGRAPH STRUCTURE

The email MUST NOT be one continuous paragraph.

Each language version should contain 3 or 4 short paragraphs separated
by blank lines.

Use this visual structure:

Paragraph 1:
Why we contacted this specific business and what we noticed.

Paragraph 2:
The problem or opportunity and, briefly, how AutomateLabs could help.

Paragraph 3:
A simple low-pressure invitation.

Final line:
AutomateLabs website.

Keep paragraphs short, normally 1-2 sentences each.

The website must be visually separated near the end:

https://automatelabs.me

Do not compress the whole email into one paragraph even when the total
word count is small.


15.CRITICAL ACCURACY RULES

Never invent software, APIs, payment providers, CRM systems,
technical architecture, internal processes, employee workflows,
or implementation details that are not explicitly present in
the supplied research.

For example, do not mention Stripe, HubSpot, Salesforce, Zapier,
specific APIs, or other technologies unless the supplied evidence
explicitly identifies them.

Separate observed facts from proposed ideas.

If proposing a technical solution, describe the capability rather
than inventing the technology used to implement it.

Never promise outcomes such as "instant", "guaranteed",
"error-free", or specific savings unless supported by evidence.


16.SUBJECT

Return one concise subject line in Estonian.

The subject should be natural and professional.
Do not use emojis, ALL CAPS, clickbait or excessive punctuation.


17.SIGNATURE

Do NOT generate an email signature.
The sending system will add the AutomateLabs signature separately.


Return structured JSON data only with exactly these fields:

subject
estonian
russian
english
"""

    return _generate_email(prompt)

def revise_email(
        lead: dict,
        draft: dict,
        feedback: str,
    ) -> dict | None:
        """
        Revise an existing outreach draft based on Drafter feedback.

        The revised email must remain grounded exclusively in the
        Lead Hunter research supplied in `lead`.
        """

        revision_prompt = f"""
    You previously generated an outreach email for AutomateLabs.

    A review system compared the draft against the original Lead Hunter
    research and found problems that need to be corrected.

    Your task is to REVISE the existing draft.

    Do not create a completely different sales angle unless the review
    feedback specifically requires it.

    ORIGINAL BUSINESS RESEARCH

    Business: {lead.get("business_name")}
    Category: {lead.get("category")}
    Location: {lead.get("location")}
    Website: {lead.get("website")}

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


    CURRENT DRAFT

    Subject:
    {draft.get("subject")}

    ESTONIAN:
    {draft.get("estonian")}

    RUSSIAN:
    {draft.get("russian")}

    ENGLISH:
    {draft.get("english")}


    REVIEW FEEDBACK

    {feedback}


    REVISION RULES

    Correct every issue identified in the review feedback.

    Preserve parts of the draft that are already correct.

    Never invent facts.

    Never introduce software, APIs, integrations, internal processes,
    statistics, savings, or technical implementation details that are
    not supported by the supplied research.

    Clearly distinguish observed information from proposed ideas.

    The Estonian version is the primary version.

    The Russian and English versions must communicate the same meaning
    as the Estonian version.

    Write naturally in all three languages.

    Each language version must contain:
    https://automatelabs.me

    Do not include an email signature.

    Keep the outreach concise, professional and low-pressure.

    Return structured JSON data only with exactly these fields:

    subject
    estonian
    russian
    english
    """

        return _generate_email(revision_prompt)

if __name__ == "__main__":
    from outreach.selector import get_next_lead

    print("Selecting next lead...")

    lead = get_next_lead()

    if lead is None:
        print("No eligible leads found.")
        raise SystemExit(0)

    print(f"Selected: {lead['business_name']}")
    print(f"Email: {lead['email']}")
    print(f"Score: {lead['score']}")
    print()
    print("Generating draft with Gemini...")

    draft = compose_email(lead)

    if draft is None:
        print("Failed to generate draft.")
        raise SystemExit(1)

    print()
    print("=" * 70)
    print("OUTREACH DRAFT")
    print("=" * 70)
    print(f"To:      {lead['email']}")
    print(f"Subject: {draft['subject']}")
    print("-" * 70)
    print()
    print("EESTI")
    print()
    print(draft["estonian"])

    print()
    print("-" * 70)
    print()
    print("РУССКИЙ")
    print()
    print(draft["russian"])

    print()
    print("-" * 70)
    print()
    print("ENGLISH")
    print()
    print(draft["english"])    
    print("=" * 70)

    