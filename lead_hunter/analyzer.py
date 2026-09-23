from google import genai
from google.genai.errors import ServerError
import json
import time

from config import GEMINI, MODEL
from lead_hunter.models import Business, BusinessAnalysis, WebsiteResearch
from database.db import get_pending_businesses


client = genai.Client(api_key=GEMINI)


MAX_RETRIES = 3
RETRY_DELAYS = [10, 30, 60]


def analyze_business(
    business: Business,
    research: WebsiteResearch | None = None,
) -> BusinessAnalysis | None:

    website_text = ""
    website_links = ""

    if research:
        website_text = research.text
        website_links = "\n".join(research.links)

    prompt = f"""
You are a sales-oriented software automation analyst.

Analyze this local business using ONLY the supplied website research.
Your goal is to determine whether there is a specific, evidence-based
automation opportunity worth contacting the business about.

BUSINESS
Name: {business.name}
Category: {business.category}
Location: {business.location}
Website: {business.website}
Phone: {business.phone}

WEBSITE RESEARCH
Title: {research.title if research else "None"}
Description: {research.description if research else "None"}

Website text:
{website_text}

Website links:
{website_links}

ANALYSIS RULES

1. FACTS FIRST
   Separate observed facts from hypotheses.
   Never invent missing information.

2. EXISTING SYSTEMS
   Identify important systems and features already present.
   Existing functionality is NOT an opportunity by itself.

3. GAPS
   Find concrete, evidence-based weaknesses, manual processes,
   missing capabilities, or integration opportunities.

4. OPPORTUNITIES
   Propose only solutions that address an identified gap.
   Never recommend replacing a system that already works unless
   there is evidence of a specific limitation.

5. TARGETED SALES OPPORTUNITY
   Select the strongest opportunity and explain:
   - what the problem is
   - what could be built
   - what evidence supports it
   - why this business specifically is a good target

6. SCORE

Return an integer from 0 to 100.

Score ONLY the strength of a concrete, sellable automation
opportunity supported by the evidence.

Increase the score for:
- clear operational pain
- clear manual work
- meaningful business value
- a specific automation gap
- strong website evidence
- a realistic solution supported by evidence of a business need

Decrease the score for:
- existing systems that already solve the problem
- weak or indirect evidence
- speculative problems
- solutions that would merely duplicate existing functionality
- opportunities with unclear business value

Use this scale:

90-100  Exceptional: clear, high-value gap with strong evidence
80-89   Very strong: specific gap with strong evidence
70-79   Good: credible opportunity, but some limitations
60-69   Moderate: plausible opportunity with limited evidence
40-59   Weak: mostly speculative or low-value
0-39    Poor: no meaningful actionable opportunity

CRITICAL:
An existing mature feature is NOT an opportunity.

If the business already has effective online booking,
do not award points for booking automation.

If no significant gap can be demonstrated, score below 70.

After choosing the score, explain the calculation in
SCORE_REASONING.

SCORE_REASONING must contain 3-5 concise sentences:
1. strongest evidence increasing the score
2. existing systems reducing the score
3. strongest remaining opportunity
4. why the score is not higher
5. why the score is not lower

EVIDENCE STANDARD

Do not treat the existence of a business process as evidence
that the process needs automation.

A possible automation opportunity is NOT enough to increase
the score.

Only increase the score substantially when the research provides
evidence of an actual gap, manual process, limitation, or
inefficiency.

If an opportunity is based mainly on what "could" be useful,
label it as speculative and keep the score lower.

Never infer that a process is manual merely because it exists.
Never infer operational problems from business complexity alone.

Return structured data only.
"""

    response = None

    for attempt in range(MAX_RETRIES):

        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "OBJECT",
                        "properties": {
                            "problems": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "opportunities": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "existing_systems": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "target_problem": {
                                "type": "STRING",
                            },
                            "proposed_solution": {
                                "type": "STRING",
                            },
                            "evidence": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "pitch_angle": {
                                "type": "STRING",
                            },
                            "reasoning": {
                                "type": "STRING",
                            },
                            "confidence": {
                                "type": "NUMBER",
                            },
                            "score": {
                                "type": "INTEGER",
                            },
                            "score_reasoning": {
                                "type": "STRING",
                            },
                        },
                        "required": [
                            "problems",
                            "opportunities",
                            "existing_systems",
                            "target_problem",
                            "proposed_solution",
                            "evidence",
                            "pitch_angle",
                            "reasoning",
                            "confidence",
                            "score",
                            "score_reasoning",
                        ],
                    },
                },
            )

            break

        except ServerError as e:

            print(
                f"    Gemini error "
                f"(attempt {attempt + 1}/{MAX_RETRIES}): {e}"
            )

            if attempt == MAX_RETRIES - 1:
                print("    ✗ Gemini failed after retries")
                return None

            delay = RETRY_DELAYS[attempt]

            print(
                f"    Waiting {delay}s before retry..."
            )

            time.sleep(delay)

    if response is None:
        return None

    data = json.loads(response.text)

    return BusinessAnalysis(
        problems=data["problems"],
        opportunities=data["opportunities"],
        existing_systems=data["existing_systems"],

        target_problem=data["target_problem"],
        proposed_solution=data["proposed_solution"],
        evidence=data["evidence"],
        pitch_angle=data["pitch_angle"],

        reasoning=data["reasoning"],
        score_reasoning=data["score_reasoning"],

        confidence=float(data["confidence"]),
        score=int(data["score"]),
    )